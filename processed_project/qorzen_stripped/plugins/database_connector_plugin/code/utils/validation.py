from __future__ import annotations
'\nValidation utilities for the Database Connector Plugin.\n\nThis module provides functionality for validating database data according to\nuser-defined rules, enabling data quality checks and verification.\n'
import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, ValidationError
from ..models import ValidationRule, ValidationRuleType, ValidationResult, QueryResult
class ValidationEngine:
    def __init__(self, database_manager: Any, logger: Any, validation_connection_id: Optional[str]=None) -> None:
        self._db_manager = database_manager
        self._logger = logger
        self._validation_connection_id = validation_connection_id
        self._validators = self._create_validators()
    async def initialize(self) -> None:
        if not self._validation_connection_id:
            self._logger.warning('No validation database connection configured')
            return
        try:
            await self._create_validation_tables()
            self._logger.info('Validation engine initialized')
        except Exception as e:
            self._logger.error(f'Failed to initialize validation engine: {str(e)}')
            raise DatabaseError(message=f'Failed to initialize validation engine: {str(e)}', details={'original_error': str(e)})
    async def _create_validation_tables(self) -> None:
        statements = ['\n            CREATE TABLE IF NOT EXISTS db_validation_rules\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                description TEXT,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                field_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                rule_type VARCHAR\n            (\n                50\n            ) NOT NULL,\n                parameters TEXT NOT NULL,\n                error_message TEXT NOT NULL,\n                active BOOLEAN NOT NULL DEFAULT TRUE,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n            ', '\n            CREATE TABLE IF NOT EXISTS db_validation_results\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                rule_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                field_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                validated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                success BOOLEAN NOT NULL,\n                failures TEXT,\n                total_records INTEGER NOT NULL,\n                failed_records INTEGER NOT NULL,\n                FOREIGN KEY\n            (\n                rule_id\n            ) REFERENCES db_validation_rules\n            (\n                id\n            ) ON DELETE CASCADE\n                )\n            ']
        try:
            for stmt in statements:
                await self._db_manager.execute_raw(sql=stmt, connection_name=self._validation_connection_id)
            self._logger.debug('Validation tables created or already exist')
        except Exception as e:
            self._logger.error(f'Failed to create validation tables: {str(e)}')
            raise DatabaseError(message=f'Failed to create validation tables: {str(e)}', details={'original_error': str(e)})
    def _create_validators(self) -> Dict[ValidationRuleType, Any]:
        return {ValidationRuleType.RANGE: self._validate_range, ValidationRuleType.PATTERN: self._validate_pattern, ValidationRuleType.NOT_NULL: self._validate_not_null, ValidationRuleType.UNIQUE: self._validate_unique, ValidationRuleType.LENGTH: self._validate_length, ValidationRuleType.REFERENCE: self._validate_reference, ValidationRuleType.ENUMERATION: self._validate_enumeration, ValidationRuleType.CUSTOM: self._validate_custom}
    async def create_rule(self, rule: ValidationRule) -> ValidationRule:
        if not self._validation_connection_id:
            raise DatabaseError(message='No validation database connection configured', details={})
        try:
            insert_sql = '\n                         INSERT INTO db_validation_rules (id, name, description, connection_id, table_name, field_name,                                                           rule_type, parameters, error_message, active, created_at,                                                           updated_at)                          VALUES (:id, :name, :description, :connection_id, :table_name, :field_name,                                  :rule_type, :parameters, :error_message, :active, :created_at, :updated_at)                          '
            rule_dict = rule.dict()
            rule_dict['parameters'] = json.dumps(rule_dict['parameters'])
            await self._db_manager.execute_raw(sql=insert_sql, params=rule_dict, connection_name=self._validation_connection_id)
            self._logger.info(f'Created validation rule: {rule.name}')
            return rule
        except Exception as e:
            self._logger.error(f'Failed to create validation rule: {str(e)}')
            raise DatabaseError(message=f'Failed to create validation rule: {str(e)}', details={'original_error': str(e)})
    async def update_rule(self, rule: ValidationRule) -> ValidationRule:
        if not self._validation_connection_id:
            raise DatabaseError(message='No validation database connection configured', details={})
        try:
            update_sql = '\n                         UPDATE db_validation_rules                          SET name          = :name,                              description   = :description,                              connection_id = :connection_id,                              table_name    = :table_name,                              field_name    = :field_name,                              rule_type     = :rule_type,                              parameters    = :parameters,                              error_message = :error_message,                              active        = :active,                              updated_at    = :updated_at\n                         WHERE id = :id                          '
            rule.updated_at = datetime.datetime.now()
            rule_dict = rule.dict()
            rule_dict['parameters'] = json.dumps(rule_dict['parameters'])
            await self._db_manager.execute_raw(sql=update_sql, params=rule_dict, connection_name=self._validation_connection_id)
            self._logger.info(f'Updated validation rule: {rule.name}')
            return rule
        except Exception as e:
            self._logger.error(f'Failed to update validation rule: {str(e)}')
            raise DatabaseError(message=f'Failed to update validation rule: {str(e)}', details={'original_error': str(e)})
    async def delete_rule(self, rule_id: str) -> bool:
        if not self._validation_connection_id:
            raise DatabaseError(message='No validation database connection configured', details={})
        try:
            delete_sql = 'DELETE FROM db_validation_rules WHERE id = :id'
            await self._db_manager.execute_raw(sql=delete_sql, params={'id': rule_id}, connection_name=self._validation_connection_id)
            self._logger.info(f'Deleted validation rule: {rule_id}')
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete validation rule: {str(e)}')
            raise DatabaseError(message=f'Failed to delete validation rule: {str(e)}', details={'original_error': str(e)})
    async def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        if not self._validation_connection_id:
            raise DatabaseError(message='No validation database connection configured', details={})
        try:
            results = await self._db_manager.execute_raw(sql='SELECT * FROM db_validation_rules WHERE id = :id', params={'id': rule_id}, connection_name=self._validation_connection_id)
            if not results:
                return None
            row = results[0]
            rule_dict = {'id': row['id'], 'name': row['name'], 'description': row['description'], 'connection_id': row['connection_id'], 'table_name': row['table_name'], 'field_name': row['field_name'], 'rule_type': row['rule_type'], 'parameters': json.loads(row['parameters']), 'error_message': row['error_message'], 'active': row['active'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
            return ValidationRule(**rule_dict)
        except Exception as e:
            self._logger.error(f'Failed to get validation rule: {str(e)}')
            raise DatabaseError(message=f'Failed to get validation rule: {str(e)}', details={'original_error': str(e)})
    async def get_all_rules(self, connection_id: Optional[str]=None, table_name: Optional[str]=None) -> List[ValidationRule]:
        if not self._validation_connection_id:
            raise DatabaseError(message='No validation database connection configured', details={})
        try:
            sql = 'SELECT * FROM db_validation_rules'
            params = {}
            if connection_id or table_name:
                sql += ' WHERE'
                if connection_id:
                    sql += ' connection_id = :connection_id'
                    params['connection_id'] = connection_id
                    if table_name:
                        sql += ' AND table_name = :table_name'
                        params['table_name'] = table_name
                elif table_name:
                    sql += ' table_name = :table_name'
                    params['table_name'] = table_name
            sql += ' ORDER BY name'
            results = await self._db_manager.execute_raw(sql=sql, params=params, connection_name=self._validation_connection_id)
            rules: List[ValidationRule] = []
            for row in results:
                rule_dict = {'id': row['id'], 'name': row['name'], 'description': row['description'], 'connection_id': row['connection_id'], 'table_name': row['table_name'], 'field_name': row['field_name'], 'rule_type': row['rule_type'], 'parameters': json.loads(row['parameters']), 'error_message': row['error_message'], 'active': row['active'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
                rules.append(ValidationRule(**rule_dict))
            return rules
        except Exception as e:
            self._logger.error(f'Failed to get validation rules: {str(e)}')
            raise DatabaseError(message=f'Failed to get validation rules: {str(e)}', details={'original_error': str(e)})
    async def validate_data(self, rule: ValidationRule, data: QueryResult) -> ValidationResult:
        try:
            field_exists = False
            for col in data.columns:
                if col.name.lower() == rule.field_name.lower():
                    field_exists = True
                    break
            if not field_exists:
                raise ValidationError(message=f"Field '{rule.field_name}' not found in the query results", details={'available_fields': [col.name for col in data.columns]})
            validator = self._validators.get(rule.rule_type)
            if not validator:
                raise ValidationError(message=f'No validator available for rule type: {rule.rule_type}', details={})
            total_records = len(data.records)
            failures = []
            for i, record in enumerate(data.records):
                field_value = None
                for field_name, value in record.items():
                    if field_name.lower() == rule.field_name.lower():
                        field_value = value
                        break
                try:
                    is_valid = validator(field_value, rule.parameters)
                    if not is_valid:
                        failures.append({'row': i, 'field': rule.field_name, 'value': field_value, 'error': rule.error_message})
                except Exception as e:
                    failures.append({'row': i, 'field': rule.field_name, 'value': field_value, 'error': f'Validation error: {str(e)}'})
            validation_result = ValidationResult(rule_id=rule.id, table_name=rule.table_name, field_name=rule.field_name, validated_at=datetime.datetime.now(), success=len(failures) == 0, failures=failures, total_records=total_records, failed_records=len(failures))
            if self._validation_connection_id:
                await self._save_validation_result(validation_result)
            return validation_result
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            self._logger.error(f'Validation error: {str(e)}')
            raise ValidationError(message=f'Failed to validate data: {str(e)}', details={'original_error': str(e)})
    async def validate_all_rules(self, connection_id: str, table_name: str, data: QueryResult) -> List[ValidationResult]:
        try:
            rules = await self.get_all_rules(connection_id=connection_id, table_name=table_name)
            active_rules = [rule for rule in rules if rule.active]
            if not active_rules:
                return []
            results = []
            for rule in active_rules:
                try:
                    result = await self.validate_data(rule, data)
                    results.append(result)
                except Exception as e:
                    self._logger.error(f'Error validating rule {rule.id}: {str(e)}')
            return results
        except Exception as e:
            self._logger.error(f'Validation error: {str(e)}')
            raise ValidationError(message=f'Failed to validate data: {str(e)}', details={'original_error': str(e)})
    async def get_validation_results(self, rule_id: Optional[str]=None, limit: int=100) -> List[ValidationResult]:
        if not self._validation_connection_id:
            raise DatabaseError(message='No validation database connection configured', details={})
        try:
            if rule_id:
                sql = '\n                      SELECT *                       FROM db_validation_results\n                      WHERE rule_id = :rule_id\n                      ORDER BY validated_at DESC LIMIT :limit                       '
                params = {'rule_id': rule_id, 'limit': limit}
            else:
                sql = '\n                      SELECT *                       FROM db_validation_results\n                      ORDER BY validated_at DESC LIMIT :limit                       '
                params = {'limit': limit}
            results = await self._db_manager.execute_raw(sql=sql, params=params, connection_name=self._validation_connection_id)
            validation_results: List[ValidationResult] = []
            for row in results:
                result_dict = {'id': row['id'], 'rule_id': row['rule_id'], 'table_name': row['table_name'], 'field_name': row['field_name'], 'validated_at': row['validated_at'], 'success': row['success'], 'failures': json.loads(row['failures']) if row['failures'] else [], 'total_records': row['total_records'], 'failed_records': row['failed_records']}
                validation_results.append(ValidationResult(**result_dict))
            return validation_results
        except Exception as e:
            self._logger.error(f'Failed to get validation results: {str(e)}')
            raise DatabaseError(message=f'Failed to get validation results: {str(e)}', details={'original_error': str(e)})
    async def _save_validation_result(self, result: ValidationResult) -> None:
        try:
            insert_sql = '\n                         INSERT INTO db_validation_results (id, rule_id, table_name, field_name, validated_at,                                                             success, failures, total_records, failed_records)                          VALUES (:id, :rule_id, :table_name, :field_name, :validated_at,                                  :success, :failures, :total_records, :failed_records)                          '
            result_dict = result.dict()
            result_dict['failures'] = json.dumps(result_dict['failures'])
            await self._db_manager.execute_raw(sql=insert_sql, params=result_dict, connection_name=self._validation_connection_id)
        except Exception as e:
            self._logger.error(f'Failed to save validation result: {str(e)}')
    def _validate_range(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        try:
            if not isinstance(value, (int, float)):
                value = float(value)
            min_val = parameters.get('min')
            max_val = parameters.get('max')
            if min_val is not None:
                if value < min_val:
                    return False
            if max_val is not None:
                if value > max_val:
                    return False
            return True
        except (ValueError, TypeError):
            return False
    def _validate_pattern(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        pattern = parameters.get('pattern')
        if not pattern:
            return False
        try:
            str_value = str(value)
            regex = re.compile(pattern)
            return bool(regex.match(str_value))
        except (TypeError, re.error):
            return False
    def _validate_not_null(self, value: Any, parameters: Dict[str, Any]) -> bool:
        return value is not None
    def _validate_unique(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        unique_values = parameters.get('unique_values', {})
        if not unique_values:
            return True
        str_value = str(value)
        return unique_values.get(str_value, 0) <= 1
    def _validate_length(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        try:
            str_value = str(value)
            length = len(str_value)
            min_length = parameters.get('min_length')
            max_length = parameters.get('max_length')
            if min_length is not None:
                if length < min_length:
                    return False
            if max_length is not None:
                if length > max_length:
                    return False
            return True
        except TypeError:
            return False
    def _validate_reference(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        reference_values = parameters.get('reference_values', [])
        if not reference_values:
            return False
        str_value = str(value)
        return str_value in [str(v) for v in reference_values]
    def _validate_enumeration(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        allowed_values = parameters.get('allowed_values', [])
        if not allowed_values:
            return False
        str_value = str(value)
        allowed_str_values = [str(v) for v in allowed_values]
        return str_value in allowed_str_values
    def _validate_custom(self, value: Any, parameters: Dict[str, Any]) -> bool:
        if value is None:
            return False
        expression = parameters.get('expression')
        if not expression:
            return False
        try:
            local_vars = {'value': value}
            result = eval(expression, {'__builtins__': {}}, local_vars)
            return bool(result)
        except Exception:
            return False
def create_range_rule(connection_id: str, table_name: str, field_name: str, name: Optional[str]=None, description: Optional[str]=None, min_value: Optional[Union[int, float]]=None, max_value: Optional[Union[int, float]]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        if min_value is not None and max_value is not None:
            name = f'Range check for {field_name} ({min_value} to {max_value})'
        elif min_value is not None:
            name = f'Minimum value check for {field_name} (>= {min_value})'
        elif max_value is not None:
            name = f'Maximum value check for {field_name} (<= {max_value})'
        else:
            name = f'Range check for {field_name}'
    if error_message is None:
        if min_value is not None and max_value is not None:
            error_message = f'Value must be between {min_value} and {max_value}'
        elif min_value is not None:
            error_message = f'Value must be at least {min_value}'
        elif max_value is not None:
            error_message = f'Value must be at most {max_value}'
        else:
            error_message = 'Value is outside the allowed range'
    parameters = {}
    if min_value is not None:
        parameters['min'] = min_value
    if max_value is not None:
        parameters['max'] = max_value
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.RANGE, parameters=parameters, error_message=error_message)
def create_pattern_rule(connection_id: str, table_name: str, field_name: str, pattern: str, name: Optional[str]=None, description: Optional[str]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        name = f'Pattern check for {field_name}'
    if error_message is None:
        error_message = f'Value must match pattern: {pattern}'
    parameters = {'pattern': pattern}
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.PATTERN, parameters=parameters, error_message=error_message)
def create_not_null_rule(connection_id: str, table_name: str, field_name: str, name: Optional[str]=None, description: Optional[str]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        name = f'Not null check for {field_name}'
    if error_message is None:
        error_message = 'Value cannot be null'
    parameters = {}
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.NOT_NULL, parameters=parameters, error_message=error_message)
def create_unique_rule(connection_id: str, table_name: str, field_name: str, name: Optional[str]=None, description: Optional[str]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        name = f'Uniqueness check for {field_name}'
    if error_message is None:
        error_message = 'Value must be unique'
    parameters = {}
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.UNIQUE, parameters=parameters, error_message=error_message)
def create_length_rule(connection_id: str, table_name: str, field_name: str, min_length: Optional[int]=None, max_length: Optional[int]=None, name: Optional[str]=None, description: Optional[str]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        if min_length is not None and max_length is not None:
            name = f'Length check for {field_name} ({min_length} to {max_length})'
        elif min_length is not None:
            name = f'Minimum length check for {field_name} (>= {min_length})'
        elif max_length is not None:
            name = f'Maximum length check for {field_name} (<= {max_length})'
        else:
            name = f'Length check for {field_name}'
    if error_message is None:
        if min_length is not None and max_length is not None:
            error_message = f'Length must be between {min_length} and {max_length}'
        elif min_length is not None:
            error_message = f'Length must be at least {min_length}'
        elif max_length is not None:
            error_message = f'Length must be at most {max_length}'
        else:
            error_message = 'Length is outside the allowed range'
    parameters = {}
    if min_length is not None:
        parameters['min_length'] = min_length
    if max_length is not None:
        parameters['max_length'] = max_length
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.LENGTH, parameters=parameters, error_message=error_message)
def create_enumeration_rule(connection_id: str, table_name: str, field_name: str, allowed_values: List[Any], name: Optional[str]=None, description: Optional[str]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        name = f'Enumeration check for {field_name}'
    if error_message is None:
        values_str = ', '.join([str(v) for v in allowed_values])
        error_message = f'Value must be one of: {values_str}'
    parameters = {'allowed_values': allowed_values}
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.ENUMERATION, parameters=parameters, error_message=error_message)
def create_custom_rule(connection_id: str, table_name: str, field_name: str, expression: str, name: Optional[str]=None, description: Optional[str]=None, error_message: Optional[str]=None) -> ValidationRule:
    if name is None:
        name = f'Custom check for {field_name}'
    if error_message is None:
        error_message = 'Value failed custom validation'
    parameters = {'expression': expression}
    return ValidationRule(name=name, description=description, connection_id=connection_id, table_name=table_name, field_name=field_name, rule_type=ValidationRuleType.CUSTOM, parameters=parameters, error_message=error_message)