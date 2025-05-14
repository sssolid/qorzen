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
    """Schema for validating configuration data.

    This model defines the expected structure and default values for the
    application configuration.
    """
    database: Dict[str, Any] = Field(
        default_factory=lambda: {
            'type': 'sqlite',
            'host': 'localhost',
            'port': 5432,
            'name': 'qorzen',
            'user': 'username',
            'password': '',
            'pool_size': 5,
            'max_overflow': 10,
            'echo': False,
        },
        description='Database connection settings',
    )
    logging: Dict[str, Any] = Field(
        default_factory=lambda: {
            'level': 'INFO',
            'format': 'json',
            'file': {
                'enabled': True,
                'path': 'logs/qorzen.log',
                'rotation': '10 MB',
                'retention': '30 days',
            },
            'console': {
                'enabled': True,
                'level': 'INFO',
            },
            'database': {
                'enabled': False,
                'level': 'WARNING',
            },
            'elk': {
                'enabled': False,
                'host': 'localhost',
                'port': 9200,
                'index': 'qorzen',
            },
        },
        description='Logging settings',
    )
    event_bus_manager: Dict[str, Any] = Field(
        default_factory=lambda: {
            'thread_pool_size': 4,
            'max_queue_size': 1000,
            'publish_timeout': 5.0,
            'external': {
                'enabled': False,
                'type': 'rabbitmq',
                'host': 'localhost',
                'port': 5672,
                'username': 'guest',
                'password': 'guest',
                'exchange': 'qorzen_events',
                'queue': 'qorzen_queue',
            },
        },
        description='Event bus settings',
    )
    thread_pool: Dict[str, Any] = Field(
        default_factory=lambda: {
            'worker_threads': 4,
            'max_queue_size': 100,
            'thread_name_prefix': 'qorzen-worker',
        },
        description='Thread pool settings',
    )
    api: Dict[str, Any] = Field(
        default_factory=lambda: {
            'enabled': True,
            'host': '0.0.0.0',
            'port': 8000,
            'workers': 4,
            'cors': {
                'origins': ['*'],
                'methods': ['*'],
                'headers': ['*'],
            },
            'rate_limit': {
                'enabled': True,
                'requests_per_minute': 100,
            },
        },
        description='REST API settings',
    )

    @model_validator(mode='after')
    def validate_api_port(self) -> 'ConfigSchema':
        """Validate that the API port is an integer."""
        if not isinstance(self.api.get('port'), int):
            raise ValueError('API port must be an integer.')
        return self

    security: Dict[str, Any] = Field(
        default_factory=lambda: {
            'jwt': {
                'secret': 'default_test_secret',
                'algorithm': 'HS256',
                'access_token_expire_minutes': 30,
                'refresh_token_expire_days': 7,
            },
            'password_policy': {
                'min_length': 8,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digit': True,
                'require_special': True,
            },
        },
        description='Security settings',
    )
    plugins: Dict[str, Any] = Field(
        default_factory=lambda: {
            'directory': 'plugins',
            'autoload': True,
            'enabled': [],
            'disabled': [],
        },
        description='Plugin settings',
    )
    files: Dict[str, Any] = Field(
        default_factory=lambda: {
            'base_directory': 'data',
            'temp_directory': 'data/temp',
            'plugin_data_directory': 'data/plugins',
            'backup_directory': 'data/backups',
        },
        description='File management settings',
    )
    monitoring: Dict[str, Any] = Field(
        default_factory=lambda: {
            'enabled': True,
            'prometheus': {
                'enabled': True,
                'port': 9090,
            },
            'alert_thresholds': {
                'cpu_percent': 80,
                'memory_percent': 80,
                'disk_percent': 90,
            },
            'metrics_interval_seconds': 10,
        },
        description='Monitoring settings',
    )
    cloud: Dict[str, Any] = Field(
        default_factory=lambda: {
            'provider': 'none',
            'storage': {
                'enabled': False,
                'type': 'local',
                'bucket': '',
                'prefix': '',
            },
        },
        description='Cloud provider settings',
    )
    app: Dict[str, Any] = Field(
        default_factory=lambda: {
            'name': 'Qorzen Test',
            'version': '0.1.0',
            'environment': 'development',
            'debug': True,
            'ui': {
                'enabled': True,
                'theme': 'light',
                'language': 'en',
            },
        },
        description='Application settings',
    )

    @model_validator(mode='after')
    def validate_jwt_secret(self) -> 'ConfigSchema':
        """Validate that a JWT secret is set when API is enabled."""
        api = self.api
        security = self.security
        if api.get('enabled', False) and (not security.get('jwt', {}).get('secret', '')):
            raise ValueError(
                'JWT secret must be set when API is enabled. '
                'Please provide a secure random string for security.jwt.secret.'
            )
        return self


class ConfigManager(QorzenManager):
    """Asynchronous configuration manager for the application.

    This manager handles loading, validating, and providing access to
    configuration settings from files and environment variables.

    Attributes:
        _config_path: Path to the configuration file
        _env_prefix: Prefix for environment variables
        _config: The loaded configuration
        _loaded_from_file: Whether configuration was loaded from a file
        _env_vars_applied: Set of applied environment variables
        _listeners: Dictionary of config change listeners
    """

    def __init__(
            self,
            config_path: Optional[Union[str, pathlib.Path]] = None,
            env_prefix: str = 'NEXUS_'
    ) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file
            env_prefix: Prefix for environment variables
        """
        super().__init__(name='config_manager')
        self._config_path = pathlib.Path(config_path) if config_path else pathlib.Path('config.yaml')
        self._env_prefix = env_prefix
        self._config: Dict[str, Any] = {}
        self._loaded_from_file = False
        self._env_vars_applied: Set[str] = set()
        self._listeners: Dict[str, List[Callable[[str, Any], Awaitable[None]]]] = {}
        self._logger: Optional[logging.Logger] = None

    async def initialize(self) -> None:
        """Initialize the configuration manager asynchronously.

        Loads configuration from default schema, file, and environment variables.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            self._config = ConfigSchema().model_dump()
            await self._load_from_file()
            self._apply_env_vars()
            await self._validate_config()

            self._initialized = True
            self._healthy = True
        except Exception as e:
            raise ManagerInitializationError(
                f'Failed to initialize AsyncConfigManager: {str(e)}',
                manager_name=self.name
            ) from e

    def set_logger(self, logger: Any) -> None:
        from qorzen.core import LoggingManager
        self._logger: LoggingManager = logger.get_logger('config_manager')

    async def _load_from_file(self) -> None:
        """Load configuration from a file asynchronously.

        Reads and parses the configuration file if it exists.

        Raises:
            ConfigurationError: If the file cannot be parsed
        """
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
                    raise ConfigurationError(
                        f'Unsupported config file format: {self._config_path.suffix}',
                        config_key='config_path'
                    )

                if file_config:
                    self._merge_config(file_config)
                    self._loaded_from_file = True
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(
                f'Error parsing config file {self._config_path}: {str(e)}',
                config_key='config_path'
            ) from e

    def _apply_env_vars(self) -> None:
        """Apply environment variables to the configuration.

        Overrides configuration values with environment variables.
        """
        for env_name, env_value in os.environ.items():
            if not env_name.startswith(self._env_prefix):
                continue

            config_path = env_name[len(self._env_prefix):].lower().split('_')
            self._set_nested_value(self._config, config_path, self._parse_env_value(env_value))
            self._env_vars_applied.add(env_name)

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse environment variable values into appropriate types.

        Args:
            value: The string value from the environment

        Returns:
            The parsed value (bool, int, float, or string)
        """
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
        """Set a nested value in the configuration dictionary.

        Args:
            config: The configuration dictionary
            path: List of keys forming the path to the value
            value: The value to set
        """
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
        """Validate the configuration against the schema.

        Raises:
            ConfigurationError: If the configuration is invalid
        """
        try:
            validated_config = ConfigSchema(**self._config).model_dump()
            self._config = validated_config
        except ValidationError as e:
            errors = e.errors()
            error_details = ', '.join((
                f"{'.'.join((str(loc) for loc in error['loc']))}: {error['msg']}"
                for error in errors
            ))
            raise ConfigurationError(
                f'Invalid configuration: {error_details}',
                details={'validation_errors': errors}
            ) from e

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key (dot-separated for nested values)
            default: Default value if the key doesn't exist

        Returns:
            The configuration value or default

        Raises:
            ConfigurationError: If the manager isn't initialized
        """
        if not self._initialized:
            raise ConfigurationError(
                'Cannot access configuration before initialization',
                config_key=key
            )

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
        """Set a configuration value by key.

        Args:
            key: The configuration key (dot-separated for nested values)
            value: The value to set

        Raises:
            ConfigurationError: If the manager isn't initialized or the value is invalid
        """
        if not self._initialized:
            raise ConfigurationError(
                'Cannot modify configuration before initialization',
                config_key=key
            )

        new_config = deepcopy(self._config)
        parts = key.split('.')
        self._set_nested_value(new_config, parts, value)

        try:
            validated_config = ConfigSchema(**new_config).model_dump()
            self._config = validated_config
            await self._notify_listeners(key, value)
            await self._save_to_file()
        except ValidationError as e:
            raise ConfigurationError(
                f'Invalid configuration value for {key}: {str(e)}',
                config_key=key,
                details={'validation_errors': e.errors()}
            ) from e

    async def _check_file_updated(self) -> None:
        """Check if the configuration file has been updated."""
        # This method is a placeholder for future implementation
        # It could check file modification time and reload if needed
        pass

    async def _save_to_file(self) -> None:
        """
        Save configuration to file with improved error handling.
        """
        if not self._loaded_from_file:
            return

        try:
            # Use a temporary file for atomic writes
            import tempfile
            import os
            import pathlib

            config_path = pathlib.Path(self._config_path)
            config_dir = config_path.parent

            # Ensure directory exists
            os.makedirs(config_dir, exist_ok=True)

            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=config_dir, suffix='.tmp') as tmp:
                if config_path.suffix.lower() in ('.yaml', '.yml'):
                    import yaml
                    yaml.dump(self._config, tmp, default_flow_style=False)
                elif config_path.suffix.lower() == '.json':
                    import json
                    json.dump(self._config, tmp, indent=2)
                else:
                    # Not supported format
                    tmp.close()
                    os.unlink(tmp.name)
                    return

            # Atomic replace
            os.replace(tmp.name, str(config_path))

        except Exception as e:
            print(f'Error saving configuration to {self._config_path}: {str(e)}')

    def _merge_config(
            self,
            from_config: Dict[str, Any],
            to_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Merge a configuration dictionary into another.

        Args:
            from_config: The source configuration
            to_config: The target configuration (defaults to self._config)
        """
        if to_config is None:
            to_config = self._config

        for key, value in from_config.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._merge_config(value, self._config[key])
            elif value not in [None, '', {}]:
                to_config[key] = value

    async def register_listener(
            self,
            key: str,
            callback: Callable[[str, Any], Awaitable[None]]
    ) -> None:
        """Register a listener for configuration changes.

        Args:
            key: The configuration key to listen for
            callback: Async callback function to call when the key changes
        """
        if key not in self._listeners:
            self._listeners[key] = []
        if callback not in self._listeners[key]:
            self._listeners[key].append(callback)

    async def unregister_listener(
            self,
            key: str,
            callback: Callable[[str, Any], Awaitable[None]]
    ) -> None:
        """Unregister a listener for configuration changes.

        Args:
            key: The configuration key
            callback: The callback function to unregister
        """
        if key in self._listeners and callback in self._listeners[key]:
            self._listeners[key].remove(callback)
            if not self._listeners[key]:
                del self._listeners[key]

    async def _notify_listeners(self, key: str, value: Any) -> None:
        """Notify listeners about a configuration change.

        Args:
            key: The changed configuration key
            value: The new value
        """
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
        """Shut down the configuration manager."""
        if self._initialized and self._loaded_from_file:
            await self._save_to_file()
        self._initialized = False
        self._healthy = False

    def status(self) -> Dict[str, Any]:
        """Get the status of the configuration manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()
        status.update({
            'config_file': str(self._config_path) if self._loaded_from_file else None,
            'loaded_from_file': self._loaded_from_file,
            'env_vars_applied': len(self._env_vars_applied),
            'registered_listeners': sum(len(callbacks) for callbacks in self._listeners.values())
        })
        return status