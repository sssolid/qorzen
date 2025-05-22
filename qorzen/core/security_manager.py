from __future__ import annotations

import asyncio
import datetime
import hashlib
import os
import re
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable, Awaitable

import jwt
from passlib.context import CryptContext

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, SecurityError


class UserRole(Enum):
    """User roles in the system.

    Attributes:
        ADMIN: Administrator role with full access
        OPERATOR: Operator role with system management access
        USER: Regular user with limited access
        VIEWER: Read-only user
    """
    ADMIN = 'admin'
    OPERATOR = 'operator'
    USER = 'user'
    VIEWER = 'viewer'


@dataclass
class User:
    """User information.

    Attributes:
        id: Unique user ID
        user: Username
        email: Email address
        hashed_password: Hashed password
        roles: List of user roles
        active: Whether the user is active
        created_at: When the user was created
        last_login: When the user last logged in
        metadata: Additional metadata
    """
    id: str
    username: str
    email: str
    hashed_password: str
    roles: List[UserRole]
    active: bool = True
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_login: Optional[datetime.datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Permission:
    """Permission definition.

    Attributes:
        id: Unique permission ID
        name: Permission name
        description: Permission description
        resource: Resource being protected
        action: Action being controlled
        roles: Roles that have this permission
    """
    id: str
    name: str
    description: str
    resource: str
    action: str
    roles: List[UserRole] = field(default_factory=list)


@dataclass
class AuthToken:
    """Authentication token information.

    Attributes:
        token: The token string
        token_type: Type of token (access, refresh)
        user_id: User ID the token belongs to
        expires_at: When the token expires
        issued_at: When the token was issued
        jti: Unique token identifier
        metadata: Additional metadata
    """
    token: str
    token_type: str
    user_id: str
    expires_at: datetime.datetime
    issued_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    jti: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityManager(QorzenManager):
    """Asynchronous security manager.

    This manager handles authentication, authorization, user management,
    and token management.

    Attributes:
        _config_manager: Configuration manager
        _logger: Logger instance
        _event_bus_manager: Event bus manager
        _db_manager: Database manager
        _pwd_context: Password hashing context
        _users: Dictionary of users
        _username_to_id: Mapping of usernames to user IDs
        _email_to_id: Mapping of emails to user IDs
        _permissions: Dictionary of permissions
        _token_blacklist: Set of blacklisted token JTIs
        _active_tokens: Dictionary of active tokens by user ID
    """

    def __init__(
            self,
            config_manager: Any,
            logger_manager: Any,
            event_bus_manager: Any,
            db_manager: Optional[Any] = None
    ) -> None:
        """Initialize the security manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logging manager
            event_bus_manager: Event bus manager
            db_manager: Optional database manager
        """
        super().__init__(name='security_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('security_manager')
        self._event_bus_manager = event_bus_manager
        self._db_manager = db_manager

        # Password hashing
        self._pwd_context: Optional[CryptContext] = None

        # User storage
        self._users: Dict[str, User] = {}
        self._username_to_id: Dict[str, str] = {}
        self._email_to_id: Dict[str, str] = {}

        # Permissions
        self._permissions: Dict[str, Permission] = {}

        # Token management
        self._token_blacklist: Set[str] = set()
        self._token_blacklist_lock = asyncio.Lock()
        self._active_tokens: Dict[str, List[AuthToken]] = {}
        self._active_tokens_lock = asyncio.Lock()

        # JWT configuration
        self._jwt_secret: Optional[str] = None
        self._jwt_algorithm = 'HS256'
        self._access_token_expire_minutes = 30
        self._refresh_token_expire_days = 7

        # Password policy
        self._password_policy = {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True
        }

        # Default permissions
        self._default_permissions: List[Permission] = []

        # Storage type
        self._use_memory_storage = True

    async def initialize(self) -> None:
        """Initialize the security manager asynchronously.

        Sets up JWT configuration, permissions, and default users.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            security_config = await self._config_manager.get('security', {})
            if not security_config:
                self._logger.error("Security configuration not found in configuration")

            # JWT configuration
            jwt_config = security_config.get('jwt', {})
            self._jwt_secret = jwt_config.get('secret')

            if not self._jwt_secret:
                self._jwt_secret = secrets.token_hex(32)
                self._logger.warning(
                    'No JWT secret provided in configuration, generated a random one. '
                    'This is insecure for production use.'
                )

            if not hasattr(jwt_config, 'algorithm'):
                self._logger.warning("Security jwt algorithm not set in configuration")
            if not hasattr(jwt_config, 'expire_minutes'):
                self._logger.warning('Expire minutes jwt not set in configuration')
            if not hasattr(jwt_config, 'expire_days'):
                self._logger.warning('Expire days jwt not set in configuration')

            self._jwt_algorithm = jwt_config.get('algorithm', 'HS256')
            self._access_token_expire_minutes = jwt_config.get(
                'access_token_expire_minutes', 30)
            self._refresh_token_expire_days = jwt_config.get('refresh_token_expire_days', 7)

            # Password policy
            if not hasattr(security_config, 'password_policy'):
                self._logger.warning("Security password policy not set in configuration")

            if not hasattr(security_config.get('password_policy'), 'bcrypt_rounds'):
                self._logger.warning("Security password policy bcrypt rounds not set in configuration")

            password_policy_config = security_config.get('password_policy', self._password_policy)

            bcrypt_rounds = password_policy_config.get('bcrypt_rounds', 12)
            self._pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=bcrypt_rounds)

            # Storage type
            self._use_memory_storage = self._db_manager is None

            # Initialize default permissions
            self._initialize_default_permissions()

            # Create default admin if no users exist
            if self._use_memory_storage and (not self._users):
                await self._initialize_default_admin()

            # Subscribe to token events
            await self._event_bus_manager.subscribe(
                event_type='security/token_revoke',
                callback=self._on_token_revoke_event,
                subscriber_id='security_manager'
            )

            # Register configuration listener
            await self._config_manager.register_listener('security', self._on_config_changed)

            self._initialized = True
            self._healthy = True

            self._logger.info('Security Manager initialized')

        except Exception as e:
            self._logger.error(f'Failed to initialize Security Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize AsyncSecurityManager: {str(e)}',
                manager_name=self.name
            ) from e

    def _initialize_default_permissions(self) -> None:
        """Initialize default permissions for the system."""
        self._add_permission(
            name='system.view',
            description='View system information and status',
            resource='system',
            action='view',
            roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.USER]
        )

        self._add_permission(
            name='system.manage',
            description='Manage system configuration and settings',
            resource='system',
            action='manage',
            roles=[UserRole.ADMIN]
        )

        self._add_permission(
            name='users.view',
            description='View user information',
            resource='users',
            action='view',
            roles=[UserRole.ADMIN, UserRole.OPERATOR]
        )

        self._add_permission(
            name='users.manage',
            description='Create, update, and delete users',
            resource='users',
            action='manage',
            roles=[UserRole.ADMIN]
        )

        self._add_permission(
            name='plugins.view',
            description='View plugin information',
            resource='plugins',
            action='view',
            roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.USER]
        )

        self._add_permission(
            name='plugins.manage',
            description='Install, update, and remove plugins',
            resource='plugins',
            action='manage',
            roles=[UserRole.ADMIN]
        )

        self._add_permission(
            name='files.view',
            description='View files and directories',
            resource='files',
            action='view',
            roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.USER, UserRole.VIEWER]
        )

        self._add_permission(
            name='files.manage',
            description='Create, update, and delete files',
            resource='files',
            action='manage',
            roles=[UserRole.ADMIN, UserRole.OPERATOR, UserRole.USER]
        )

    async def _initialize_default_admin(self) -> None:
        """Create a default admin user if no users exist."""
        try:
            default_admin_password = 'admin'
            admin_user = await self.create_user(
                username='admin',
                email='admin@example.com',
                password=default_admin_password,
                roles=[UserRole.ADMIN],
                metadata={'default_user': True}
            )

            if admin_user:
                self._logger.warning(
                    "Created default admin user with username 'admin' and "
                    "password 'admin'. Please change this password immediately."
                )
        except Exception as e:
            self._logger.error(f'Failed to create default admin user: {str(e)}')

    def _add_permission(
            self,
            name: str,
            description: str,
            resource: str,
            action: str,
            roles: List[UserRole]
    ) -> Permission:
        """Add a permission to the system.

        Args:
            name: Permission name
            description: Permission description
            resource: Resource being protected
            action: Action being controlled
            roles: Roles that have this permission

        Returns:
            The created permission
        """
        permission_id = f'{resource}.{action}'
        permission = Permission(
            id=permission_id,
            name=name,
            description=description,
            resource=resource,
            action=action,
            roles=roles
        )

        self._permissions[permission_id] = permission
        self._default_permissions.append(permission)

        return permission

    async def create_user(
            self,
            username: str,
            email: str,
            password: str,
            roles: List[UserRole],
            metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a new user.

        Args:
            username: Username
            email: Email address
            password: Password
            roles: User roles
            metadata: Additional metadata

        Returns:
            The user ID if creation was successful, None otherwise

        Raises:
            SecurityError: If user creation fails
        """
        if not self._initialized:
            raise SecurityError('Security Manager not initialized')

        if not username or not email or (not password):
            raise SecurityError('Username, email, and password are required')

        if not self._is_valid_username(username):
            raise SecurityError(
                'Invalid username. Username must be 3-32 characters and can only '
                'contain letters, numbers, dots, hyphens, and underscores.'
            )

        if not self._is_valid_email(email):
            raise SecurityError('Invalid email address')

        password_validation = self._validate_password(password)
        if not password_validation['valid']:
            raise SecurityError(f"Invalid password: {password_validation['reason']}")

        if self._use_memory_storage:
            # Check if username or email already exists
            if username.lower() in self._username_to_id:
                raise SecurityError(f"Username '{username}' already exists")

            if email.lower() in self._email_to_id:
                raise SecurityError(f"Email '{email}' already exists")

            # Create user
            user_id = str(uuid.uuid4())
            hashed_password = self._pwd_context.hash(password)

            user = User(
                id=user_id,
                username=username,
                email=email,
                hashed_password=hashed_password,
                roles=roles,
                active=True,
                metadata=metadata or {}
            )

            self._users[user_id] = user
            self._username_to_id[username.lower()] = user_id
            self._email_to_id[email.lower()] = user_id

            self._logger.info(
                f"Created user '{username}'",
                extra={'user_id': user_id, 'email': email}
            )

            # Publish user created event
            await self._event_bus_manager.publish(
                event_type='security/user_created',
                source='security_manager',
                payload={
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'roles': [role.value for role in roles]
                }
            )

            return user_id
        else:
            # Database-backed storage is not implemented yet
            self._logger.warning('Database-backed user creation not implemented yet')
            return None

    async def authenticate_user(
            self,
            username_or_email: str,
            password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username/email and password.

        Args:
            username_or_email: Username or email address
            password: Password

        Returns:
            Dictionary with user info and tokens if authentication succeeded, None otherwise
        """
        if not self._initialized:
            return None

        user = self._get_user_by_username_or_email(username_or_email)

        if not user:
            self._logger.warning(
                f"Authentication failed: User '{username_or_email}' not found",
                extra={'username_or_email': username_or_email}
            )
            return None

        if not user.active:
            self._logger.warning(
                f"Authentication failed: User '{username_or_email}' is inactive",
                extra={'username_or_email': username_or_email, 'user_id': user.id}
            )
            return None

        if not self._verify_password(password, user.hashed_password):
            self._logger.warning(
                f"Authentication failed: Invalid password for user '{username_or_email}'",
                extra={'username_or_email': username_or_email, 'user_id': user.id}
            )
            return None

        # Create access and refresh tokens
        access_token = await self._create_token(
            user_id=user.id,
            token_type='access',
            expires_delta=datetime.timedelta(minutes=self._access_token_expire_minutes)
        )

        refresh_token = await self._create_token(
            user_id=user.id,
            token_type='refresh',
            expires_delta=datetime.timedelta(days=self._refresh_token_expire_days)
        )

        # Update last login time
        user.last_login = datetime.datetime.now()

        self._logger.info(
            f"User '{username_or_email}' authenticated successfully",
            extra={'username_or_email': username_or_email, 'user_id': user.id}
        )

        # Publish login event
        await self._event_bus_manager.publish(
            event_type='security/user_login',
            source='security_manager',
            payload={
                'user_id': user.id,
                'username': user.username,
                'timestamp': user.last_login.isoformat()
            }
        )

        # Return user info and tokens
        return {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': [role.value for role in user.roles],
            'access_token': access_token.token,
            'token_type': 'bearer',
            'expires_in': self._access_token_expire_minutes * 60,
            'refresh_token': refresh_token.token,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            Dictionary with new access token if successful, None otherwise
        """
        if not self._initialized:
            return None

        try:
            # Verify the refresh token
            payload = await self._verify_token(refresh_token)

            if not payload or payload.get('token_type') != 'refresh':
                self._logger.warning(
                    'Token refresh failed: Invalid token or not a refresh token',
                    extra={'token_sub': payload.get('sub') if payload else None}
                )
                return None

            # Check if token is blacklisted
            user_id = payload.get('sub')
            jti = payload.get('jti')

            async with self._token_blacklist_lock:
                if jti in self._token_blacklist:
                    self._logger.warning(
                        'Token refresh failed: Token is blacklisted',
                        extra={'token_sub': user_id, 'jti': jti}
                    )
                    return None

            # Check if user exists and is active
            user = self._get_user_by_id(user_id) if user_id else None

            if not user or not user.active:
                self._logger.warning(
                    'Token refresh failed: User not found or inactive',
                    extra={'user_id': user_id}
                )
                return None

            # Create new access token
            access_token = await self._create_token(
                user_id=user.id,
                token_type='access',
                expires_delta=datetime.timedelta(minutes=self._access_token_expire_minutes)
            )

            self._logger.info(
                f"Generated new access token for user '{user.username}'",
                extra={'user_id': user.id}
            )

            # Return new token info
            return {
                'access_token': access_token.token,
                'token_type': 'bearer',
                'expires_in': self._access_token_expire_minutes * 60
            }

        except Exception as e:
            self._logger.error(f'Error refreshing token: {str(e)}')
            return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token.

        Args:
            token: The token to revoke

        Returns:
            True if revocation was successful, False otherwise
        """
        if not self._initialized:
            return False

        try:
            # Verify the token without checking expiration
            payload = await self._verify_token(token, verify_exp=False)

            if not payload:
                self._logger.warning('Token revocation failed: Invalid token')
                return False

            # Get token identifiers
            jti = payload.get('jti')
            user_id = payload.get('sub')

            if not jti:
                self._logger.warning('Token revocation failed: Token has no JTI')
                return False

            # Add to blacklist
            async with self._token_blacklist_lock:
                self._token_blacklist.add(jti)

            self._logger.info(
                'Token revoked successfully',
                extra={'jti': jti, 'user_id': user_id}
            )

            # Publish token revoked event
            await self._event_bus_manager.publish(
                event_type='security/token_revoked',
                source='security_manager',
                payload={'jti': jti, 'user_id': user_id}
            )

            return True

        except Exception as e:
            self._logger.error(f'Error revoking token: {str(e)}')
            return False

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a token.

        Args:
            token: The token to verify

        Returns:
            Token payload if valid, None otherwise
        """
        return await self._verify_token(token)

    async def has_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if a user has a specific permission.

        Args:
            user_id: User ID
            resource: Resource being accessed
            action: Action being performed

        Returns:
            True if the user has the permission, False otherwise
        """
        if not self._initialized:
            return False

        # Get user
        user = self._get_user_by_id(user_id)
        if not user or not user.active:
            return False

        # Get permission
        permission_id = f'{resource}.{action}'
        permission = self._permissions.get(permission_id)
        if not permission:
            return False

        # Check if user has a role with the permission
        for role in user.roles:
            if role in permission.roles:
                return True

        return False

    async def has_role(self, user_id: str, role: UserRole) -> bool:
        """Check if a user has a specific role.

        Args:
            user_id: User ID
            role: Role to check

        Returns:
            True if the user has the role, False otherwise
        """
        if not self._initialized:
            return False

        # Get user
        user = self._get_user_by_id(user_id)
        if not user or not user.active:
            return False

        # Check if user has the role
        return role in user.roles

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with user information if found, None otherwise
        """
        if not self._initialized:
            return None

        # Get user
        user = self._get_user_by_id(user_id)
        if not user:
            return None

        # Return user info
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': [role.value for role in user.roles],
            'active': user.active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'metadata': user.metadata
        }

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update a user.

        Args:
            user_id: User ID
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False otherwise

        Raises:
            SecurityError: If update fails
        """
        if not self._initialized:
            raise SecurityError('Security Manager not initialized')

        if self._use_memory_storage:
            # Get user
            user = self._get_user_by_id(user_id)
            if not user:
                raise SecurityError(f"User with ID '{user_id}' not found")

            # Update username
            if 'username' in updates and updates['username'] != user.username:
                new_username = updates['username']

                # Validate username
                if not self._is_valid_username(new_username):
                    raise SecurityError('Invalid username format')

                # Check if username already exists
                if (
                        new_username.lower() in self._username_to_id
                        and self._username_to_id[new_username.lower()] != user_id
                ):
                    raise SecurityError(f"Username '{new_username}' already exists")

                # Update username mapping
                if user.username.lower() in self._username_to_id:
                    del self._username_to_id[user.username.lower()]

                user.username = new_username
                self._username_to_id[new_username.lower()] = user_id

            # Update email
            if 'email' in updates and updates['email'] != user.email:
                new_email = updates['email']

                # Validate email
                if not self._is_valid_email(new_email):
                    raise SecurityError('Invalid email format')

                # Check if email already exists
                if (
                        new_email.lower() in self._email_to_id
                        and self._email_to_id[new_email.lower()] != user_id
                ):
                    raise SecurityError(f"Email '{new_email}' already exists")

                # Update email mapping
                if user.email.lower() in self._email_to_id:
                    del self._email_to_id[user.email.lower()]

                user.email = new_email
                self._email_to_id[new_email.lower()] = user_id

            # Update password
            if 'password' in updates:
                password = updates['password']

                # Validate password
                password_validation = self._validate_password(password)
                if not password_validation['valid']:
                    raise SecurityError(f"Invalid password: {password_validation['reason']}")

                # Hash password
                user.hashed_password = self._pwd_context.hash(password)

                # Revoke all tokens
                await self._revoke_user_tokens(user_id)

            # Update roles
            if 'roles' in updates:
                roles = []

                # Process roles
                for role in updates['roles']:
                    if isinstance(role, str):
                        try:
                            roles.append(UserRole(role))
                        except ValueError:
                            raise SecurityError(f'Invalid role: {role}')
                    elif isinstance(role, UserRole):
                        roles.append(role)
                    else:
                        raise SecurityError(f'Invalid role type: {type(role)}')

                user.roles = roles

            # Update active status
            if 'active' in updates:
                user.active = bool(updates['active'])

                # Revoke all tokens if user is deactivated
                if not user.active:
                    await self._revoke_user_tokens(user_id)

            # Update metadata
            if 'metadata' in updates:
                if updates['metadata'] is None:
                    user.metadata = {}
                else:
                    user.metadata.update(updates['metadata'])

            self._logger.info(
                f"Updated user '{user.username}'",
                extra={'user_id': user_id, 'updated_fields': list(updates.keys())}
            )

            # Publish user updated event
            await self._event_bus_manager.publish(
                event_type='security/user_updated',
                source='security_manager',
                payload={
                    'user_id': user_id,
                    'username': user.username,
                    'updated_fields': list(updates.keys())
                }
            )

            return True
        else:
            # Database-backed storage is not implemented yet
            self._logger.warning('Database-backed user updates not implemented yet')
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user.

        Args:
            user_id: User ID

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            SecurityError: If deletion fails
        """
        if not self._initialized:
            raise SecurityError('Security Manager not initialized')

        if self._use_memory_storage:
            # Get user
            user = self._get_user_by_id(user_id)
            if not user:
                raise SecurityError(f"User with ID '{user_id}' not found")

            # Remove username and email mappings
            if user.username.lower() in self._username_to_id:
                del self._username_to_id[user.username.lower()]

            if user.email.lower() in self._email_to_id:
                del self._email_to_id[user.email.lower()]

            # Remove user
            del self._users[user_id]

            # Revoke all tokens
            await self._revoke_user_tokens(user_id)

            self._logger.info(
                f"Deleted user '{user.username}'",
                extra={'user_id': user_id}
            )

            # Publish user deleted event
            await self._event_bus_manager.publish(
                event_type='security/user_deleted',
                source='security_manager',
                payload={'user_id': user_id, 'username': user.username}
            )

            return True
        else:
            # Database-backed storage is not implemented yet
            self._logger.warning('Database-backed user deletion not implemented yet')
            return False

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get information about all users.

        Returns:
            List of dictionaries with user information
        """
        if not self._initialized:
            return []

        result = []

        if self._use_memory_storage:
            # Get user info for all users
            for user in self._users.values():
                result.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'roles': [role.value for role in user.roles],
                    'active': user.active,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                })
        else:
            # Database-backed storage is not implemented yet
            self._logger.warning('Database-backed user listing not implemented yet')

        return result

    async def get_all_permissions(self) -> List[Dict[str, Any]]:
        """Get information about all permissions.

        Returns:
            List of dictionaries with permission information
        """
        if not self._initialized:
            return []

        result = []

        # Get permission info for all permissions
        for permission in self._permissions.values():
            result.append({
                'id': permission.id,
                'name': permission.name,
                'description': permission.description,
                'resource': permission.resource,
                'action': permission.action,
                'roles': [role.value for role in permission.roles]
            })

        return result

    def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        if self._use_memory_storage:
            return self._users.get(user_id)
        else:
            return None

    def _get_user_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """Get a user by username or email.

        Args:
            username_or_email: Username or email

        Returns:
            User if found, None otherwise
        """
        if self._use_memory_storage:
            # Try username
            user_id = self._username_to_id.get(username_or_email.lower())

            # Try email
            if not user_id:
                user_id = self._email_to_id.get(username_or_email.lower())

            # Get user
            if user_id:
                return self._users.get(user_id)

            return None
        else:
            return None

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if the password matches, False otherwise
        """
        return self._pwd_context.verify(plain_password, hashed_password)

    def _validate_password(self, password: str) -> Dict[str, Any]:
        """Validate a password against the password policy.

        Args:
            password: Password to validate

        Returns:
            Dictionary with validation result and reason
        """
        if not password:
            return {'valid': False, 'reason': 'Password cannot be empty'}

        # Check length
        min_length = self._password_policy.get('min_length', 8)
        if len(password) < min_length:
            return {'valid': False, 'reason': f'Password must be at least {min_length} characters long'}

        # Check uppercase
        if (
                self._password_policy.get('require_uppercase', True)
                and not any(c.isupper() for c in password)
        ):
            return {'valid': False, 'reason': 'Password must contain at least one uppercase letter'}

        # Check lowercase
        if (
                self._password_policy.get('require_lowercase', True)
                and not any(c.islower() for c in password)
        ):
            return {'valid': False, 'reason': 'Password must contain at least one lowercase letter'}

        # Check digit
        if (
                self._password_policy.get('require_digit', True)
                and not any(c.isdigit() for c in password)
        ):
            return {'valid': False, 'reason': 'Password must contain at least one digit'}

        # Check special character
        if self._password_policy.get('require_special', True):
            special_chars = '!@#$%^&*()_-+={}[]\\|:;"\'<>,.?/'
            if not any(c in special_chars for c in password):
                return {'valid': False, 'reason': 'Password must contain at least one special character'}

        return {'valid': True}

    def _is_valid_username(self, username: str) -> bool:
        """Validate a username.

        Args:
            username: Username to validate

        Returns:
            True if valid, False otherwise
        """
        if not username:
            return False

        if len(username) < 3 or len(username) > 32:
            return False

        username_pattern = r'^[a-zA-Z0-9._-]+$'
        return bool(re.match(username_pattern, username))

    def _is_valid_email(self, email: str) -> bool:
        """Validate an email address.

        Args:
            email: Email to validate

        Returns:
            True if valid, False otherwise
        """
        if not email:
            return False

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    async def _create_token(
            self,
            user_id: str,
            token_type: str,
            expires_delta: datetime.timedelta
    ) -> AuthToken:
        """Create a JWT token.

        Args:
            user_id: User ID
            token_type: Token type (access, refresh)
            expires_delta: Token expiration time

        Returns:
            Auth token object

        Raises:
            SecurityError: If token creation fails
        """
        if not self._jwt_secret:
            raise SecurityError('JWT secret not configured')

        # Create token payload
        issued_at = datetime.datetime.now(datetime.timezone.utc)
        expiration = issued_at + expires_delta
        jti = str(uuid.uuid4())

        payload = {
            'sub': user_id,
            'iat': issued_at.timestamp(),
            'exp': expiration.timestamp(),
            'jti': jti,
            'token_type': token_type
        }

        # Encode token
        token = jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

        # Create auth token
        auth_token = AuthToken(
            token=token,
            token_type=token_type,
            user_id=user_id,
            issued_at=issued_at,
            expires_at=expiration,
            jti=jti
        )

        # Store token
        async with self._active_tokens_lock:
            if user_id not in self._active_tokens:
                self._active_tokens[user_id] = []

            self._active_tokens[user_id].append(auth_token)

        return auth_token

    async def _verify_token(
            self,
            token: str,
            verify_exp: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Verify a JWT token.

        Args:
            token: Token to verify
            verify_exp: Whether to verify expiration

        Returns:
            Token payload if valid, None otherwise
        """
        if not self._jwt_secret:
            self._logger.error('JWT secret not configured')
            return None

        try:
            # Decode token
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
                options={'verify_exp': verify_exp}
            )

            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti:
                async with self._token_blacklist_lock:
                    if jti in self._token_blacklist:
                        self._logger.warning(
                            'Token validation failed: Token is blacklisted',
                            extra={'jti': jti}
                        )
                        return None

            return payload

        except jwt.ExpiredSignatureError:
            self._logger.warning('Token validation failed: Token has expired')
            return None
        except jwt.InvalidTokenError as e:
            self._logger.warning(f'Token validation failed: {str(e)}')
            return None
        except Exception as e:
            self._logger.error(f'Error verifying token: {str(e)}')
            return None

    async def _revoke_user_tokens(self, user_id: str) -> None:
        """Revoke all tokens for a user.

        Args:
            user_id: User ID
        """
        async with self._active_tokens_lock:
            # Get active tokens
            tokens = self._active_tokens.get(user_id, [])

            # Add tokens to blacklist
            async with self._token_blacklist_lock:
                for token in tokens:
                    self._token_blacklist.add(token.jti)

            # Remove tokens
            self._active_tokens.pop(user_id, None)

        self._logger.info(
            f'Revoked all tokens for user {user_id}',
            extra={'user_id': user_id}
        )

    async def _on_token_revoke_event(self, event: Any) -> None:
        """Handle token revocation events.

        Args:
            event: Token revocation event
        """
        payload = event.payload
        token = payload.get('token')

        if not token:
            self._logger.error(
                'Invalid token revocation event: Missing token',
                extra={'event_id': event.event_id}
            )
            return

        await self.revoke_token(token)

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: New value
        """
        if key == 'security.jwt.secret':
            # Update JWT secret
            self._jwt_secret = value
            self._logger.info('Updated JWT secret')

            # Revoke all tokens
            async with self._active_tokens_lock:
                for user_id in list(self._active_tokens.keys()):
                    await self._revoke_user_tokens(user_id)

        elif key == 'security.jwt.algorithm':
            # Update JWT algorithm
            self._jwt_algorithm = value
            self._logger.info(f'Updated JWT algorithm to {value}')

            # Revoke all tokens
            async with self._active_tokens_lock:
                for user_id in list(self._active_tokens.keys()):
                    await self._revoke_user_tokens(user_id)

        elif key == 'security.jwt.access_token_expire_minutes':
            # Update access token expiration
            self._access_token_expire_minutes = value
            self._logger.info(f'Updated access token expiration to {value} minutes')

        elif key == 'security.jwt.refresh_token_expire_days':
            # Update refresh token expiration
            self._refresh_token_expire_days = value
            self._logger.info(f'Updated refresh token expiration to {value} days')

        elif key.startswith('security.password_policy.'):
            # Update password policy
            policy_name = key.split('.')[-1]
            if policy_name in self._password_policy:
                self._password_policy[policy_name] = value
                self._logger.info(f'Updated password policy: {policy_name} = {value}')

    async def shutdown(self) -> None:
        """Shut down the security manager asynchronously.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Security Manager')

            # Unsubscribe from events
            await self._event_bus_manager.unsubscribe(subscriber_id='security_manager')

            # Unregister config listener
            await self._config_manager.unregister_listener('security', self._on_config_changed)

            # Clear data
            if self._use_memory_storage:
                self._users.clear()
                self._username_to_id.clear()
                self._email_to_id.clear()

            async with self._token_blacklist_lock:
                self._token_blacklist.clear()

            async with self._active_tokens_lock:
                self._active_tokens.clear()

            self._initialized = False
            self._healthy = False

            self._logger.info('Security Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Security Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down AsyncSecurityManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the security manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()

        if self._initialized:
            status.update({
                'storage': 'memory' if self._use_memory_storage else 'database',
                'users': {
                    'count': len(self._users) if self._use_memory_storage else 0
                },
                'permissions': {
                    'count': len(self._permissions)
                },
                'tokens': {
                    'active': sum(len(tokens) for tokens in self._active_tokens.values()),
                    'blacklisted': len(self._token_blacklist)
                },
                'jwt': {
                    'algorithm': self._jwt_algorithm,
                    'access_token_expire_minutes': self._access_token_expire_minutes,
                    'refresh_token_expire_days': self._refresh_token_expire_days
                }
            })

        return status