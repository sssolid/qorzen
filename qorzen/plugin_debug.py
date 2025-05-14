#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug script to find out why plugins are unloading.

This script adds extensive logging to the plugin system to detect
exactly what's causing plugins to unload.

TO USE:
1. Create a file called debug_hook.py in your project root
2. Copy this content into that file
3. Add this to the top of your main.py file:
   import debug_hook
4. Run the application with maximum logging enabled
5. Check the logs for "PLUGIN DEBUG" entries
"""

import sys
import inspect
import logging
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='PLUGIN DEBUG - %(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("plugin_debug.log", mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("plugin_debugger")
logger.setLevel(logging.DEBUG)

# Log startup
logger.critical("=" * 80)
logger.critical("PLUGIN DEBUGGER INITIALIZING")
logger.critical("=" * 80)

# Track all plugin-related operations
operations = []


def log_operation(op_type, **kwargs):
    """Log an operation with its stack trace"""
    stack = traceback.extract_stack()
    # Skip the last 2 frames (this function and its caller)
    relevant_stack = stack[:-2]
    stack_trace = ''.join(traceback.format_list(relevant_stack))

    # Log the operation
    logger.debug(f"OPERATION: {op_type}")
    for k, v in kwargs.items():
        logger.debug(f"  {k}: {v}")
    logger.debug(f"STACK TRACE:\n{stack_trace}")
    logger.debug("-" * 50)

    # Store the operation
    operations.append({
        'type': op_type,
        'data': kwargs,
        'stack': stack_trace
    })


# Create hooks for key plugin functions
def hook_plugin_manager():
    """Hook into the plugin manager to track operations"""
    try:
        # Find plugin_manager module - try several possible locations
        plugin_manager = None
        for path in sys.path:
            try:
                sys.path.insert(0, path)
                from qorzen.core.plugin_manager import PluginManager
                plugin_manager = sys.modules['qorzen.core.plugin_manager']
                break
            except ImportError:
                try:
                    from processed_project.qorzen_stripped.core.plugin_manager import PluginManager
                    plugin_manager = sys.modules['processed_project.qorzen_stripped.core.plugin_manager']
                    break
                except ImportError:
                    continue

        if not plugin_manager:
            logger.error("Could not find plugin_manager module")
            return

        # Hook key methods
        original_load = PluginManager.load_plugin
        original_unload = PluginManager.unload_plugin
        original_enable = PluginManager.enable_plugin
        original_disable = PluginManager.disable_plugin

        # Replace with hooked versions
        def hooked_load(self, plugin_id):
            log_operation('load_plugin', plugin_id=plugin_id)
            return original_load(self, plugin_id)

        def hooked_unload(self, plugin_id):
            log_operation('unload_plugin', plugin_id=plugin_id)
            return original_unload(self, plugin_id)

        def hooked_enable(self, plugin_id):
            log_operation('enable_plugin', plugin_id=plugin_id)
            return original_enable(self, plugin_id)

        def hooked_disable(self, plugin_id):
            log_operation('disable_plugin', plugin_id=plugin_id)
            return original_disable(self, plugin_id)

        # Apply the hooks
        PluginManager.load_plugin = hooked_load
        PluginManager.unload_plugin = hooked_unload
        PluginManager.enable_plugin = hooked_enable
        PluginManager.disable_plugin = hooked_disable

        logger.critical("Successfully hooked plugin manager methods!")
    except Exception as e:
        logger.error(f"Error hooking plugin manager: {str(e)}")
        logger.error(traceback.format_exc())


# Hook the plugin lifecycle
def hook_lifecycle():
    """Hook into the lifecycle manager"""
    try:
        # Try to import lifecycle manager
        lifecycle_manager = None
        try:
            from qorzen.plugin_system.lifecycle import LifecycleManager
            lifecycle_manager = sys.modules['qorzen.plugin_system.lifecycle']
        except ImportError:
            try:
                from processed_project.qorzen_stripped.plugin_system.lifecycle import LifecycleManager
                lifecycle_manager = sys.modules['processed_project.qorzen_stripped.plugin_system.lifecycle']
            except ImportError:
                logger.error("Could not find lifecycle_manager module")
                return

        if not lifecycle_manager:
            return

        # Hook set_plugin_state method
        original_set_state = LifecycleManager.set_plugin_state

        async def hooked_set_state(self, plugin_name, state):
            log_operation('set_plugin_state', plugin_name=plugin_name, state=str(state))
            return await original_set_state(self, plugin_name, state)

        LifecycleManager.set_plugin_state = hooked_set_state
        logger.critical("Successfully hooked lifecycle manager methods!")
    except Exception as e:
        logger.error(f"Error hooking lifecycle manager: {str(e)}")
        logger.error(traceback.format_exc())


# Hook state manager
def hook_state_manager():
    """Hook into the state manager"""
    try:
        # Try to import state manager
        state_manager = None
        try:
            from qorzen.plugin_system.plugin_state_manager import PluginStateManager
            state_manager = sys.modules['qorzen.plugin_system.plugin_state_manager']
        except ImportError:
            try:
                from processed_project.qorzen_stripped.plugin_system.plugin_state_manager import PluginStateManager
                state_manager = sys.modules['processed_project.qorzen_stripped.plugin_system.plugin_state_manager']
            except ImportError:
                logger.error("Could not find plugin_state_manager module")
                return

        if not state_manager:
            return

        # Hook transition method
        original_transition = PluginStateManager.transition

        async def hooked_transition(self, plugin_id, target_state, current_state=None):
            log_operation('state_transition', plugin_id=plugin_id, target_state=target_state,
                          current_state=current_state)
            return await original_transition(self, plugin_id, target_state, current_state)

        PluginStateManager.transition = hooked_transition
        logger.critical("Successfully hooked state manager methods!")
    except Exception as e:
        logger.error(f"Error hooking state manager: {str(e)}")
        logger.error(traceback.format_exc())


# Apply all hooks
hook_plugin_manager()
hook_lifecycle()
hook_state_manager()

logger.critical("=" * 80)
logger.critical("PLUGIN DEBUGGER INITIALIZED - CHECK plugin_debug.log FOR RESULTS")
logger.critical("=" * 80)