from typing import Dict, Any


def post_enable(context: Dict[str, Any]) -> None:
    app_core = context.get('context').get("app_core")
    instance = context.get('plugin_instance')
    if not app_core or not hasattr(app_core, "_main_window"):
        return

    instance._main_window = app_core._main_window

    event_bus = context.get('context').get("event_bus")
    if event_bus:
        event_bus.publish(
            event_type="ui/ready",
            source=f"hook:initialdb",
            payload={"main_window": app_core._main_window}
        )

def post_disable(context: Dict[str, Any]) -> None:
    app_core = context.get('context').get("app_core")
    if not app_core or not hasattr(app_core, "_main_window"):
        return

    event_bus = context.get('context').get("event_bus")
    if event_bus:
        event_bus.publish(
            event_type="ui/ready",
            source=f"hook:initialdb",
            payload={"main_window": app_core._main_window}
        )