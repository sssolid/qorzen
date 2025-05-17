import sys
import inspect
import logging
import traceback
from pathlib import Path
logging.basicConfig(level=logging.DEBUG, format='PLUGIN DEBUG - %(asctime)s - %(message)s', handlers=[logging.FileHandler('plugin_debug.log', mode='w'), logging.StreamHandler()])
logger = logging.getLogger('plugin_debugger')
logger.setLevel(logging.DEBUG)
logger.critical('=' * 80)
logger.critical('PLUGIN DEBUGGER INITIALIZING')
logger.critical('=' * 80)
operations = []
def log_operation(op_type, **kwargs):
    stack = traceback.extract_stack()
    relevant_stack = stack[:-2]
    stack_trace = ''.join(traceback.format_list(relevant_stack))
    logger.debug(f'OPERATION: {op_type}')
    for k, v in kwargs.items():
        logger.debug(f'  {k}: {v}')
    logger.debug(f'STACK TRACE:\n{stack_trace}')
    logger.debug('-' * 50)
    operations.append({'type': op_type, 'data': kwargs, 'stack': stack_trace})
def hook_plugin_manager():
    try:
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
            logger.error('Could not find plugin_manager module')
            return
        original_load = PluginManager.load_plugin
        original_unload = PluginManager.unload_plugin
        original_enable = PluginManager.enable_plugin
        original_disable = PluginManager.disable_plugin
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
        PluginManager.load_plugin = hooked_load
        PluginManager.unload_plugin = hooked_unload
        PluginManager.enable_plugin = hooked_enable
        PluginManager.disable_plugin = hooked_disable
        logger.critical('Successfully hooked plugin manager methods!')
    except Exception as e:
        logger.error(f'Error hooking plugin manager: {str(e)}')
        logger.error(traceback.format_exc())
def hook_lifecycle():
    try:
        lifecycle_manager = None
        try:
            from qorzen.plugin_system.lifecycle import LifecycleManager
            lifecycle_manager = sys.modules['qorzen.plugin_system.lifecycle']
        except ImportError:
            try:
                from processed_project.qorzen_stripped.plugin_system.lifecycle import LifecycleManager
                lifecycle_manager = sys.modules['processed_project.qorzen_stripped.plugin_system.lifecycle']
            except ImportError:
                logger.error('Could not find lifecycle_manager module')
                return
        if not lifecycle_manager:
            return
        original_set_state = LifecycleManager.set_plugin_state
        async def hooked_set_state(self, plugin_name, state):
            log_operation('set_plugin_state', plugin_name=plugin_name, state=str(state))
            return await original_set_state(self, plugin_name, state)
        LifecycleManager.set_plugin_state = hooked_set_state
        logger.critical('Successfully hooked lifecycle manager methods!')
    except Exception as e:
        logger.error(f'Error hooking lifecycle manager: {str(e)}')
        logger.error(traceback.format_exc())
def hook_state_manager():
    try:
        state_manager = None
        try:
            from qorzen.plugin_system.plugin_state_manager import PluginStateManager
            state_manager = sys.modules['qorzen.plugin_system.plugin_state_manager']
        except ImportError:
            try:
                from processed_project.qorzen_stripped.plugin_system.plugin_state_manager import PluginStateManager
                state_manager = sys.modules['processed_project.qorzen_stripped.plugin_system.plugin_state_manager']
            except ImportError:
                logger.error('Could not find plugin_state_manager module')
                return
        if not state_manager:
            return
        original_transition = PluginStateManager.transition
        async def hooked_transition(self, plugin_id, target_state, current_state=None):
            log_operation('state_transition', plugin_id=plugin_id, target_state=target_state, current_state=current_state)
            return await original_transition(self, plugin_id, target_state, current_state)
        PluginStateManager.transition = hooked_transition
        logger.critical('Successfully hooked state manager methods!')
    except Exception as e:
        logger.error(f'Error hooking state manager: {str(e)}')
        logger.error(traceback.format_exc())
hook_plugin_manager()
hook_lifecycle()
hook_state_manager()
logger.critical('=' * 80)
logger.critical('PLUGIN DEBUGGER INITIALIZED - CHECK plugin_debug.log FOR RESULTS')
logger.critical('=' * 80)