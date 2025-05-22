from __future__ import annotations
import enum
from typing import Any, Dict, List, Literal, Optional, Union, TypedDict, get_args, get_origin
import pydantic
from pydantic import Field, validator
class ConfigFieldType(str, enum.Enum):
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'
    BOOLEAN = 'boolean'
    SELECT = 'select'
    MULTISELECT = 'multiselect'
    COLOR = 'color'
    FILE = 'file'
    DIRECTORY = 'directory'
    PASSWORD = 'password'
    JSON = 'json'
    CODE = 'code'
    DATETIME = 'datetime'
    DATE = 'date'
    TIME = 'time'
class ValidationRule(pydantic.BaseModel):
    rule_type: str
    parameters: Dict[str, Any] = {}
    error_message: Optional[str] = None
class ConfigField(pydantic.BaseModel):
    name: str
    type: ConfigFieldType
    label: str
    description: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = False
    visible: bool = True
    order: int = 0
    group: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    conditional_display: Optional[Dict[str, Any]] = None
    @validator('options')
    def validate_options(cls, v, values):
        if v is None and values.get('type') in [ConfigFieldType.SELECT, ConfigFieldType.MULTISELECT]:
            raise ValueError(f"Options must be provided for {values.get('type')} fields")
        return v
    @validator('default_value')
    def validate_default_value(cls, v, values):
        if v is None:
            return v
        field_type = values.get('type')
        if field_type == ConfigFieldType.INTEGER and (not isinstance(v, int)):
            raise ValueError(f'Default value for INTEGER field must be an integer, got {type(v)}')
        elif field_type == ConfigFieldType.FLOAT and (not isinstance(v, (int, float))):
            raise ValueError(f'Default value for FLOAT field must be a number, got {type(v)}')
        elif field_type == ConfigFieldType.BOOLEAN and (not isinstance(v, bool)):
            raise ValueError(f'Default value for BOOLEAN field must be a boolean, got {type(v)}')
        elif field_type == ConfigFieldType.SELECT:
            if values.get('options') and v not in [opt.get('value') for opt in values.get('options', [])]:
                raise ValueError(f"Default value '{v}' not found in options")
        elif field_type == ConfigFieldType.MULTISELECT:
            if not isinstance(v, list):
                raise ValueError(f'Default value for MULTISELECT field must be a list, got {type(v)}')
            if values.get('options'):
                allowed_values = [opt.get('value') for opt in values.get('options', [])]
                for item in v:
                    if item not in allowed_values:
                        raise ValueError(f"Default value item '{item}' not found in options")
        return v
class ConfigGroup(pydantic.BaseModel):
    name: str
    label: str
    description: Optional[str] = None
    order: int = 0
    collapsed: bool = False
class ConfigSchema(pydantic.BaseModel):
    fields: List[ConfigField]
    groups: List[ConfigGroup] = Field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)
    def get_default_values(self) -> Dict[str, Any]:
        defaults = {}
        for field in self.fields:
            if field.default_value is not None:
                defaults[field.name] = field.default_value
        return defaults
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        validated = {}
        errors = {}
        for field in self.fields:
            if field.required and field.name not in config:
                errors[field.name] = f"Required field '{field.name}' is missing"
                continue
            if field.name not in config:
                if field.default_value is not None:
                    validated[field.name] = field.default_value
                continue
            value = config[field.name]
            try:
                if field.type == ConfigFieldType.INTEGER:
                    value = int(value)
                elif field.type == ConfigFieldType.FLOAT:
                    value = float(value)
                elif field.type == ConfigFieldType.BOOLEAN:
                    if isinstance(value, str):
                        value = value.lower() in ['true', 'yes', 'y', '1']
                    else:
                        value = bool(value)
                elif field.type == ConfigFieldType.SELECT:
                    if field.options and value not in [opt.get('value') for opt in field.options]:
                        errors[field.name] = f"Invalid value '{value}' for field '{field.name}'"
                        continue
                elif field.type == ConfigFieldType.MULTISELECT:
                    if not isinstance(value, list):
                        errors[field.name] = f"Expected list for field '{field.name}', got {type(value)}"
                        continue
                    if field.options:
                        allowed_values = [opt.get('value') for opt in field.options]
                        for item in value:
                            if item not in allowed_values:
                                errors[field.name] = f"Invalid value '{item}' in field '{field.name}'"
                                break
            except (ValueError, TypeError) as e:
                errors[field.name] = f"Invalid type for field '{field.name}': {str(e)}"
                continue
            for rule in field.validation_rules:
                if not self._apply_validation_rule(field.name, value, rule):
                    error_msg = rule.error_message or f"Validation failed for field '{field.name}'"
                    errors[field.name] = error_msg
                    break
            if field.name not in errors:
                validated[field.name] = value
        if errors:
            raise ValueError(f'Configuration validation failed: {errors}')
        return validated
    def _apply_validation_rule(self, field_name: str, value: Any, rule: ValidationRule) -> bool:
        rule_type = rule.rule_type
        params = rule.parameters
        if rule_type == 'min':
            return value >= params.get('value', 0)
        elif rule_type == 'max':
            return value <= params.get('value', 0)
        elif rule_type == 'min_length':
            return len(value) >= params.get('value', 0)
        elif rule_type == 'max_length':
            return len(value) <= params.get('value', 0)
        elif rule_type == 'pattern':
            import re
            pattern = params.get('pattern', '')
            return bool(re.match(pattern, str(value)))
        elif rule_type == 'enum':
            return value in params.get('values', [])
        elif rule_type == 'custom':
            return True
        else:
            return True
def convert_pydantic_to_schema(model_class: type) -> ConfigSchema:
    fields = []
    for name, field_info in model_class.__fields__.items():
        field_type = _get_field_type(field_info.outer_type_)
        field_metadata = field_info.field_info.extra
        config_field = ConfigField(name=name, type=field_type, label=field_metadata.get('title', name), description=field_metadata.get('description'), default_value=field_info.default if field_info.default is not None else None, required=field_info.required, order=field_metadata.get('order', 0), group=field_metadata.get('group'), options=_get_options_from_field(field_info), validation_rules=_get_validation_rules(field_info))
        fields.append(config_field)
    groups = []
    if hasattr(model_class, 'Config') and hasattr(model_class.Config, 'field_groups'):
        for group_name, group_info in model_class.Config.field_groups.items():
            groups.append(ConfigGroup(name=group_name, label=group_info.get('label', group_name), description=group_info.get('description'), order=group_info.get('order', 0), collapsed=group_info.get('collapsed', False)))
    return ConfigSchema(fields=fields, groups=groups)
def _get_field_type(type_annotation: Any) -> ConfigFieldType:
    origin = get_origin(type_annotation)
    args = get_args(type_annotation)
    if origin is Union and type(None) in args:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _get_field_type(non_none_args[0])
    if origin is Literal:
        return ConfigFieldType.SELECT
    if origin is list or origin is List:
        inner_type = args[0] if args else Any
        inner_field_type = _get_field_type(inner_type)
        if inner_field_type == ConfigFieldType.SELECT:
            return ConfigFieldType.MULTISELECT
        return ConfigFieldType.MULTISELECT
    if type_annotation is str or type_annotation is Optional[str]:
        return ConfigFieldType.STRING
    elif type_annotation is int or type_annotation is Optional[int]:
        return ConfigFieldType.INTEGER
    elif type_annotation is float or type_annotation is Optional[float]:
        return ConfigFieldType.FLOAT
    elif type_annotation is bool or type_annotation is Optional[bool]:
        return ConfigFieldType.BOOLEAN
    if 'datetime' in str(type_annotation).lower():
        return ConfigFieldType.DATETIME
    elif 'date' in str(type_annotation).lower():
        return ConfigFieldType.DATE
    elif 'time' in str(type_annotation).lower():
        return ConfigFieldType.TIME
    return ConfigFieldType.STRING
def _get_options_from_field(field_info: Any) -> Optional[List[Dict[str, Any]]]:
    field_type = field_info.outer_type_
    origin = get_origin(field_type)
    args = get_args(field_type)
    if origin is Literal:
        return [{'value': arg, 'label': str(arg)} for arg in args]
    if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
        return [{'value': item.value, 'label': item.name} for item in field_type]
    options = field_info.field_info.extra.get('options')
    if options:
        if isinstance(options, list):
            if options and isinstance(options[0], (str, int, float, bool)):
                return [{'value': opt, 'label': str(opt)} for opt in options]
            return options
    return None
def _get_validation_rules(field_info: Any) -> List[ValidationRule]:
    rules = []
    field_metadata = field_info.field_info.extra
    if 'ge' in field_metadata:
        rules.append(ValidationRule(rule_type='min', parameters={'value': field_metadata['ge']}, error_message=f"Value must be greater than or equal to {field_metadata['ge']}"))
    if 'gt' in field_metadata:
        rules.append(ValidationRule(rule_type='min', parameters={'value': field_metadata['gt'] + 1}, error_message=f"Value must be greater than {field_metadata['gt']}"))
    if 'le' in field_metadata:
        rules.append(ValidationRule(rule_type='max', parameters={'value': field_metadata['le']}, error_message=f"Value must be less than or equal to {field_metadata['le']}"))
    if 'lt' in field_metadata:
        rules.append(ValidationRule(rule_type='max', parameters={'value': field_metadata['lt'] - 1}, error_message=f"Value must be less than {field_metadata['lt']}"))
    if 'min_length' in field_metadata:
        rules.append(ValidationRule(rule_type='min_length', parameters={'value': field_metadata['min_length']}, error_message=f"Value must have at least {field_metadata['min_length']} characters"))
    if 'max_length' in field_metadata:
        rules.append(ValidationRule(rule_type='max_length', parameters={'value': field_metadata['max_length']}, error_message=f"Value must have at most {field_metadata['max_length']} characters"))
    if 'regex' in field_metadata:
        rules.append(ValidationRule(rule_type='pattern', parameters={'pattern': field_metadata['regex']}, error_message=field_metadata.get('regex_message', 'Value must match the required pattern')))
    validation_rules = field_metadata.get('validation_rules', [])
    for rule in validation_rules:
        if isinstance(rule, dict):
            rules.append(ValidationRule(**rule))
        else:
            rules.append(rule)
    return rules