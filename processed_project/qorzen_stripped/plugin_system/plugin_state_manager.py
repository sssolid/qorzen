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
    def __init__(self, plugin_manager: Any, logger: Optional[logging.Logger]=None):
        self._plugin_manager = plugin_manager
        self._logger = logger or logging.getLogger('plugin_state_manager')
        self._state_locks: Dict[str, asyncio.Lock] = {}
        self._operation_locks: Dict[str, asyncio.Lock] = {}
        self._pending_operations: Dict[str, Set[str]] = {}
        self._active_transitions: Dict[str, str] = {}
    async def transition(self, plugin_id: str, target_state: str, current_state: Optional[str]=None) -> bool:
        if plugin_id not in self._state_locks:
            self._state_locks[plugin_id] = asyncio.Lock()
        transition_name = f'{plugin_id}-to-{target_state}'
        async with self._state_locks[plugin_id]:
            if not await self._plugin_exists(plugin_id):
                self._logger.warning(f'Cannot transition non-existent plugin: {plugin_id}')
                return False
            if current_state is None:
                plugin_info = await self._get_plugin_info(plugin_id)
                if not plugin_info:
                    self._logger.warning(f'Failed to get state for plugin: {plugin_id}')
                    return False
                current_state = plugin_info.state
            self._logger.debug(f'Attempting transition for plugin {plugin_id}: {current_state} -> {target_state}')
            self._active_transitions[plugin_id] = transition_name
            try:
                if target_state == 'active':
                    return await self._transition_to_active(plugin_id, current_state)
                elif target_state == 'inactive':
                    return await self._transition_to_inactive(plugin_id, current_state)
                elif target_state == 'disabled':
                    return await self._transition_to_disabled(plugin_id, current_state)
                else:
                    self._logger.warning(f'Unsupported target state: {target_state}')
                    return False
            finally:
                if plugin_id in self._active_transitions:
                    del self._active_transitions[plugin_id]
    async def _transition_to_active(self, plugin_id: str, current_state: str) -> bool:
        if current_state == 'active':
            return True
        if current_state in ('inactive', 'discovered'):
            return await self._exec_operation(plugin_id, 'load', lambda: self._plugin_manager.load_plugin(plugin_id))
        return False
    async def _transition_to_inactive(self, plugin_id: str, current_state: str) -> bool:
        if current_state == 'inactive':
            return True
        if current_state in ('active', 'loading'):
            return await self._exec_operation(plugin_id, 'unload', lambda: self._plugin_manager.unload_plugin(plugin_id))
        return True
    async def _transition_to_disabled(self, plugin_id: str, current_state: str) -> bool:
        if current_state == 'disabled':
            return True
        if current_state in ('active', 'loading'):
            success = await self._transition_to_inactive(plugin_id, current_state)
            if not success:
                return False
        plugin_info = await self._get_plugin_info(plugin_id)
        if plugin_info:
            from qorzen.core.plugin_manager import PluginState
            plugin_info.state = PluginState.DISABLED
            return True
        return False
    async def _exec_operation(self, plugin_id: str, operation: str, func: callable) -> bool:
        op_key = f'{plugin_id}-{operation}'
        if op_key not in self._operation_locks:
            self._operation_locks[op_key] = asyncio.Lock()
        if plugin_id not in self._pending_operations:
            self._pending_operations[plugin_id] = set()
        self._pending_operations[plugin_id].add(operation)
        async with self._operation_locks[op_key]:
            self._logger.debug(f'Executing operation {operation} on plugin {plugin_id}')
            try:
                result = await func()
                self._logger.debug(f'Operation {operation} on plugin {plugin_id} completed: {result}')
                return bool(result)
            except Exception as e:
                self._logger.error(f'Operation {operation} on plugin {plugin_id} failed: {str(e)}', exc_info=True)
                return False
            finally:
                if plugin_id in self._pending_operations:
                    self._pending_operations[plugin_id].discard(operation)
                    if not self._pending_operations[plugin_id]:
                        del self._pending_operations[plugin_id]
    async def is_transitioning(self, plugin_id: str) -> bool:
        return plugin_id in self._active_transitions
    async def get_active_transition(self, plugin_id: str) -> Optional[str]:
        return self._active_transitions.get(plugin_id)
    async def get_pending_operations(self, plugin_id: str) -> Set[str]:
        return self._pending_operations.get(plugin_id, set()).copy()
    async def _plugin_exists(self, plugin_id: str) -> bool:
        try:
            plugins = await self._plugin_manager.get_plugins()
            return plugin_id in plugins
        except Exception as e:
            self._logger.error(f'Error checking if plugin exists: {str(e)}')
            return False
    async def _get_plugin_info(self, plugin_id: str) -> Optional[Any]:
        try:
            return await self._plugin_manager.get_plugin_info(plugin_id)
        except Exception as e:
            self._logger.error(f'Error getting plugin info: {str(e)}')
            return None