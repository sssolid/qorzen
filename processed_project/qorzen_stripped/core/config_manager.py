from __future__ import annotations
import json
import logging
import os
import pathlib
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Union, Awaitable, cast
import aiofiles
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ConfigurationError, ManagerInitializationError
class ConfigSchema(BaseModel):
    database: Dict[str, Any] = Field(default_factory=lambda: {'enabled': True, 'type': 'postgresql', 'host': 'localhost', 'port': 5432, 'name': 'qorzen', 'user': 'postgres', 'password': '', 'pool_size': 5, 'max_overflow': 10, 'pool_recycle': 3600, 'echo': False, 'field_mapping': {'enabled': True, 'connection_id': 'default'}, 'history': {'enabled': True, 'connection_id': 'default', 'auto_cleanup': True}, 'validation': {'enabled': True, 'connection_id': 'default'}, 'non_blocking': True}, description='Database connection and utility settings')
    logging: Dict[str, Any] = Field(default_factory=lambda: {'level': 'INFO', 'format': 'json', 'file': {'enabled': True, 'path': 'logs/qorzen.log', 'rotation_size': 10, 'retention_count': 30}, 'console': {'enabled': True, 'level': 'INFO'}, 'database': {'enabled': False, 'level': 'WARNING'}, 'elk': {'enabled': False, 'host': 'localhost', 'port': 9200, 'index': 'qorzen'}}, description='Logging settings')
    event_bus_manager: Dict[str, Any] = Field(default_factory=lambda: {'thread_pool_size': 4, 'max_queue_size': 1000, 'publish_timeout': 5.0, 'external': {'enabled': False, 'type': 'rabbitmq', 'host': 'localhost', 'port': 5672, 'username': 'guest', 'password': 'guest', 'exchange': 'qorzen_events', 'queue': 'qorzen_queue'}}, description='Event bus settings')
    tasks: Dict[str, Any] = Field(default_factory=lambda: {'max_concurrent_tasks': 20, 'keep_completed_tasks': 100, 'default_timeout': 300.0})
    thread_pool: Dict[str, Any] = Field(default_factory=lambda: {'worker_threads': 4, 'io_threads': 8, 'process_workers': 2, 'enable_process_pool': True})
    api: Dict[str, Any] = Field(default_factory=lambda: {'enabled': True, 'host': '0.0.0.0', 'port': 8000, 'workers': 4, 'cors': {'origins': ['*'], 'methods': ['*'], 'headers': ['*']}, 'rate_limit': {'enabled': True, 'requests_per_minute': 100}}, description='REST API settings')
    @model_validator(mode='after')
    def validate_api_port(self) -> 'ConfigSchema':
        if not isinstance(self.api.get('port'), int):
            raise ValueError('API port must be an integer.')
        return self
    security: Dict[str, Any] = Field(default_factory=lambda: {'jwt': {'secret': 'default_test_secret', 'algorithm': 'HS256', 'access_token_expire_minutes': 30, 'refresh_token_expire_days': 7}, 'password_policy': {'min_length': 8, 'require_uppercase': True, 'require_lowercase': True, 'require_digit': True, 'require_special': True, 'bcrypt_rounds': 12}})
    plugins: Dict[str, Any] = Field(default_factory=lambda: {'directory': 'plugins', 'autoload': True, 'enabled': [], 'disabled': []}, description='Plugin settings')
    files: Dict[str, Any] = Field(default_factory=lambda: {'base_directory': 'data', 'temp_directory': 'data/temp', 'plugin_data_directory': 'data/plugins', 'backup_directory': 'data/backups', 'max_concurrent_locks': 100}, description='File management settings')
    monitoring: Dict[str, Any] = Field(default_factory=lambda: {'enabled': True, 'prometheus': {'enabled': True, 'port': 9090}, 'alert_thresholds': {'cpu_percent': 80, 'memory_percent': 80, 'disk_percent': 90}, 'metrics_interval_seconds': 10}, description='Monitoring settings')
    cloud: Dict[str, Any] = Field(default_factory=lambda: {'provider': 'none', 'storage': {'enabled': False, 'type': 'local', 'bucket': '', 'prefix': ''}}, description='Cloud provider settings')
    app: Dict[str, Any] = Field(default_factory=lambda: {'name': 'Qorzen Test', 'version': '0.1.0', 'environment': 'development', 'debug': True, 'ui': {'enabled': True, 'theme': 'light', 'language': 'en'}}, description='Application settings')
    @model_validator(mode='after')
    def validate_jwt_secret(self) -> 'ConfigSchema':
        api = self.api
        security = self.security
        if api.get('enabled', False) and (not security.get('jwt', {}).get('secret', '')):
            raise ValueError('JWT secret must be set when API is enabled. Please provide a secure random string for security.jwt.secret.')
        return self
class ConfigManager(QorzenManager):
    def __init__(self, config_path: Optional[Union[str, pathlib.Path]]=None, env_prefix: str='NEXUS_') -> None:
        super().__init__(name='config_manager')
        self._config_path = pathlib.Path(config_path) if config_path else pathlib.Path('config.yaml')
        self._env_prefix = env_prefix
        self._config: Dict[str, Any] = {}
        self._loaded_from_file = False
        self._env_vars_applied: Set[str] = set()
        self._listeners: Dict[str, List[Callable[[str, Any], Awaitable[None]]]] = {}
        self._logger: Optional[logging.Logger] = None
    async def initialize(self) -> None:
        try:
            self._config = ConfigSchema().model_dump()
            await self._load_from_file()
            self._apply_env_vars()
            await self._validate_config()
            self._initialized = True
            self._healthy = True
        except Exception as e:
            raise ManagerInitializationError(f'Failed to initialize AsyncConfigManager: {str(e)}', manager_name=self.name) from e
    def set_logger(self, logger: Any) -> None:
        from qorzen.core import LoggingManager
        self._logger: LoggingManager = logger.get_logger('config_manager')
    async def _load_from_file(self) -> None:
        if not self._config_path.exists():
            return
        try:
            async with aiofiles.open(self._config_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if self._config_path.suffix.lower() in ('.yaml', '.yml'):
                    file_config = yaml.safe_load(content)
                elif self._config_path.suffix.lower() == '.json':
                    file_config = json.loads(content)
                else:
                    raise ConfigurationError(f'Unsupported config file format: {self._config_path.suffix}', config_key='config_path')
                if file_config:
                    self._merge_config(file_config)
                    self._loaded_from_file = True
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f'Error parsing config file {self._config_path}: {str(e)}', config_key='config_path') from e
    def _apply_env_vars(self) -> None:
        for env_name, env_value in os.environ.items():
            if not env_name.startswith(self._env_prefix):
                continue
            config_path = env_name[len(self._env_prefix):].lower().split('_')
            self._set_nested_value(self._config, config_path, self._parse_env_value(env_value))
            self._env_vars_applied.add(env_name)
    @staticmethod
    def _parse_env_value(value: str) -> Any:
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        try:
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value)
            return float(value)
        except ValueError:
            return value
    def _set_nested_value(self, config: Dict[str, Any], path: List[str], value: Any) -> None:
        if not path:
            return
        if len(path) == 1:
            config[path[0]] = value
            return
        key = path[0]
        if key not in config:
            config[key] = {}
        if not isinstance(config[key], dict):
            config[key] = {}
        self._set_nested_value(config[key], path[1:], value)
    async def _validate_config(self) -> None:
        try:
            validated_config = ConfigSchema(**self._config).model_dump()
            self._config = validated_config
        except ValidationError as e:
            errors = e.errors()
            error_details = ', '.join((f"{'.'.join((str(loc) for loc in error['loc']))}: {error['msg']}" for error in errors))
            raise ConfigurationError(f'Invalid configuration: {error_details}', details={'validation_errors': errors}) from e
    async def get(self, key: str, default: Any=None) -> Any:
        if not self._initialized:
            raise ConfigurationError('Cannot access configuration before initialization', config_key=key)
        if self._loaded_from_file and self._config_path.exists():
            await self._check_file_updated()
        parts = key.split('.')
        result = self._config
        try:
            for part in parts:
                result = result[part]
            return result
        except (KeyError, TypeError):
            return default
    async def set(self, key: str, value: Any) -> None:
        if not self._initialized:
            raise ConfigurationError('Cannot modify configuration before initialization', config_key=key)
        new_config = deepcopy(self._config)
        parts = key.split('.')
        self._set_nested_value(new_config, parts, value)
        try:
            validated_config = ConfigSchema(**new_config).model_dump()
            self._config = validated_config
            await self._notify_listeners(key, value)
            await self._save_to_file()
        except ValidationError as e:
            raise ConfigurationError(f'Invalid configuration value for {key}: {str(e)}', config_key=key, details={'validation_errors': e.errors()}) from e
    async def _check_file_updated(self) -> None:
        pass
    async def _save_to_file(self) -> None:
        if not self._loaded_from_file:
            return
        try:
            import tempfile
            import os
            import pathlib
            config_path = pathlib.Path(self._config_path)
            config_dir = config_path.parent
            os.makedirs(config_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=config_dir, suffix='.tmp') as tmp:
                if config_path.suffix.lower() in ('.yaml', '.yml'):
                    import yaml
                    yaml.dump(self._config, tmp, default_flow_style=False)
                elif config_path.suffix.lower() == '.json':
                    import json
                    json.dump(self._config, tmp, indent=2)
                else:
                    tmp.close()
                    os.unlink(tmp.name)
                    return
            os.replace(tmp.name, str(config_path))
        except Exception as e:
            print(f'Error saving configuration to {self._config_path}: {str(e)}')
    def _merge_config(self, from_config: Dict[str, Any], to_config: Optional[Dict[str, Any]]=None) -> None:
        if to_config is None:
            to_config = self._config
        for key, value in from_config.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._merge_config(value, self._config[key])
            elif value not in [None, '', {}]:
                to_config[key] = value
    async def register_listener(self, key: str, callback: Callable[[str, Any], Awaitable[None]]) -> None:
        if key not in self._listeners:
            self._listeners[key] = []
        if callback not in self._listeners[key]:
            self._listeners[key].append(callback)
    async def unregister_listener(self, key: str, callback: Callable[[str, Any], Awaitable[None]]) -> None:
        if key in self._listeners and callback in self._listeners[key]:
            self._listeners[key].remove(callback)
            if not self._listeners[key]:
                del self._listeners[key]
    async def _notify_listeners(self, key: str, value: Any) -> None:
        for listener_key, callbacks in list(self._listeners.items()):
            if listener_key == key:
                for callback in callbacks:
                    try:
                        await callback(key, value)
                    except Exception as e:
                        print(f'Error in config listener for {key}: {str(e)}')
            elif key.startswith(f'{listener_key}.'):
                for callback in callbacks:
                    try:
                        await callback(key, value)
                    except Exception as e:
                        print(f'Error in config listener for {key}: {str(e)}')
    async def shutdown(self) -> None:
        if self._initialized and self._loaded_from_file:
            await self._save_to_file()
        self._initialized = False
        self._healthy = False
    def status(self) -> Dict[str, Any]:
        status = super().status()
        status.update({'config_file': str(self._config_path) if self._loaded_from_file else None, 'loaded_from_file': self._loaded_from_file, 'env_vars_applied': len(self._env_vars_applied), 'registered_listeners': sum((len(callbacks) for callbacks in self._listeners.values()))})
        return status