from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple
from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError


class PluginStateManager:
    """
    Helper class to manage plugin state transitions and avoid race conditions.
    This class acts as a state machine coordinator for plugins, ensuring that
    state transitions are atomic and consistent.
    """

    def __init__(self, plugin_manager: Any, logger: Optional[logging.Logger] = None):
        """
        Initialize the plugin state manager.

        Args:
            plugin_manager: Reference to the plugin manager instance
            logger: Optional logger instance for logging state transitions
        """
        self._plugin_manager = plugin_manager
        self._logger = logger or logging.getLogger("plugin_state_manager")
        self._state_locks: Dict[str, asyncio.Lock] = {}
        self._operation_locks: Dict[str, asyncio.Lock] = {}
        self._pending_operations: Dict[str, Set[str]] = {}
        self._active_transitions: Dict[str, str] = {}  # plugin_id -> transition_name

    async def transition(
            self,
            plugin_id: str,
            target_state: str,
            current_state: Optional[str] = None
    ) -> bool:
        """
        Safely transition a plugin to the target state, handling all intermediate states.

        Args:
            plugin_id: Unique identifier of the plugin
            target_state: The desired final state
            current_state: Optional current state if known; will be retrieved if not provided

        Returns:
            bool: True if transition succeeded, False otherwise
        """
        # Get or create lock for this plugin
        if plugin_id not in self._state_locks:
            self._state_locks[plugin_id] = asyncio.Lock()

        # Define transition name for logging
        transition_name = f"{plugin_id}-to-{target_state}"

        # Acquire lock to ensure exclusive access to this plugin's state
        async with self._state_locks[plugin_id]:
            # Check if plugin exists
            if not await self._plugin_exists(plugin_id):
                self._logger.warning(f"Cannot transition non-existent plugin: {plugin_id}")
                return False

            # Get current state if not provided
            if current_state is None:
                plugin_info = await self._get_plugin_info(plugin_id)
                if not plugin_info:
                    self._logger.warning(f"Failed to get state for plugin: {plugin_id}")
                    return False
                current_state = plugin_info.state

            # Log the transition attempt
            self._logger.debug(
                f"Attempting transition for plugin {plugin_id}: {current_state} -> {target_state}"
            )

            # Record active transition
            self._active_transitions[plugin_id] = transition_name

            try:
                # Handle transitions based on target state
                if target_state == "active":
                    return await self._transition_to_active(plugin_id, current_state)
                elif target_state == "inactive":
                    return await self._transition_to_inactive(plugin_id, current_state)
                elif target_state == "disabled":
                    return await self._transition_to_disabled(plugin_id, current_state)
                else:
                    self._logger.warning(f"Unsupported target state: {target_state}")
                    return False
            finally:
                # Clear active transition
                if plugin_id in self._active_transitions:
                    del self._active_transitions[plugin_id]

    async def _transition_to_active(self, plugin_id: str, current_state: str) -> bool:
        """
        Transition a plugin to the active state.

        This has been modified to avoid circular calls between plugin_manager and state_manager.
        """
        if current_state == 'active':
            return True

        # We only handle the load operation but avoid calling back to enable_plugin
        # to prevent a circular dependency
        if current_state in ('inactive', 'discovered'):
            return await self._exec_operation(plugin_id, 'load', lambda: self._plugin_manager.load_plugin(plugin_id))

        return False

    async def _transition_to_inactive(self, plugin_id: str, current_state: str) -> bool:
        """Handle transition to inactive state."""
        if current_state == "inactive":
            return True  # Already in target state

        if current_state in ("active", "loading"):
            return await self._exec_operation(plugin_id, "unload",
                                              lambda: self._plugin_manager.unload_plugin(plugin_id))

        # If it's discovered or disabled, nothing to do
        return True

    async def _transition_to_disabled(self, plugin_id: str, current_state: str) -> bool:
        """
        Transition a plugin to the disabled state.

        This has been modified to avoid circular calls between plugin_manager and state_manager.
        """
        if current_state == 'disabled':
            return True

        # First ensure the plugin is inactive
        if current_state in ('active', 'loading'):
            success = await self._transition_to_inactive(plugin_id, current_state)
            if not success:
                return False

        # We mark the plugin as disabled but don't call back to disable_plugin
        # to prevent a circular dependency
        plugin_info = await self._get_plugin_info(plugin_id)
        if plugin_info:
            from qorzen.core.plugin_manager import PluginState
            plugin_info.state = PluginState.DISABLED
            return True

        return False

    async def _exec_operation(self, plugin_id: str, operation: str, func: callable) -> bool:
        """Execute a plugin operation with proper tracking and error handling."""
        # Create operation lock if needed
        op_key = f"{plugin_id}-{operation}"
        if op_key not in self._operation_locks:
            self._operation_locks[op_key] = asyncio.Lock()

        # Add to pending operations
        if plugin_id not in self._pending_operations:
            self._pending_operations[plugin_id] = set()
        self._pending_operations[plugin_id].add(operation)

        # Execute with lock to prevent concurrent same operations
        async with self._operation_locks[op_key]:
            self._logger.debug(f"Executing operation {operation} on plugin {plugin_id}")
            try:
                result = await func()
                self._logger.debug(f"Operation {operation} on plugin {plugin_id} completed: {result}")
                return bool(result)
            except Exception as e:
                self._logger.error(
                    f"Operation {operation} on plugin {plugin_id} failed: {str(e)}",
                    exc_info=True
                )
                return False
            finally:
                # Remove from pending operations
                if plugin_id in self._pending_operations:
                    self._pending_operations[plugin_id].discard(operation)
                    if not self._pending_operations[plugin_id]:
                        del self._pending_operations[plugin_id]

    async def is_transitioning(self, plugin_id: str) -> bool:
        """
        Check if a plugin is currently in a state transition.

        Args:
            plugin_id: Unique identifier of the plugin

        Returns:
            bool: True if transitioning, False otherwise
        """
        return plugin_id in self._active_transitions

    async def get_active_transition(self, plugin_id: str) -> Optional[str]:
        """
        Get the name of the active transition for a plugin, if any.

        Args:
            plugin_id: Unique identifier of the plugin

        Returns:
            Optional[str]: Transition name or None if not transitioning
        """
        return self._active_transitions.get(plugin_id)

    async def get_pending_operations(self, plugin_id: str) -> Set[str]:
        """
        Get the set of pending operations for a plugin.

        Args:
            plugin_id: Unique identifier of the plugin

        Returns:
            Set[str]: Set of operation names
        """
        return self._pending_operations.get(plugin_id, set()).copy()

    async def _plugin_exists(self, plugin_id: str) -> bool:
        """Check if a plugin exists."""
        try:
            plugins = await self._plugin_manager.get_plugins()
            return plugin_id in plugins
        except Exception as e:
            self._logger.error(f"Error checking if plugin exists: {str(e)}")
            return False

    async def _get_plugin_info(self, plugin_id: str) -> Optional[Any]:
        """Get plugin info object."""
        try:
            return await self._plugin_manager.get_plugin_info(plugin_id)
        except Exception as e:
            self._logger.error(f"Error getting plugin info: {str(e)}")
            return None