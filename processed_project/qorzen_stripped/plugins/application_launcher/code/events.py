from __future__ import annotations
'\nEvents module for Application Launcher plugin.\n\nThis module defines the event types used by the Application Launcher plugin\nfor inter-component communication.\n'
from enum import Enum
from typing import Dict, Any, Optional
class AppLauncherEventType(str, Enum):
    APP_ADDED = 'application_launcher:app_added'
    APP_UPDATED = 'application_launcher:app_updated'
    APP_REMOVED = 'application_launcher:app_removed'
    APP_LAUNCHED = 'application_launcher:app_launched'
    APP_TERMINATED = 'application_launcher:app_terminated'
    APP_COMPLETED = 'application_launcher:app_completed'
    OUTPUT_DETECTED = 'application_launcher:output_detected'
    @classmethod
    def app_added(cls) -> str:
        return cls.APP_ADDED.value
    @classmethod
    def app_updated(cls) -> str:
        return cls.APP_UPDATED.value
    @classmethod
    def app_removed(cls) -> str:
        return cls.APP_REMOVED.value
    @classmethod
    def app_launched(cls) -> str:
        return cls.APP_LAUNCHED.value
    @classmethod
    def app_terminated(cls) -> str:
        return cls.APP_TERMINATED.value
    @classmethod
    def app_completed(cls) -> str:
        return cls.APP_COMPLETED.value
    @classmethod
    def output_detected(cls) -> str:
        return cls.OUTPUT_DETECTED.value
def create_app_added_event(app_id: str, app_name: str) -> Dict[str, Any]:
    return {'app_id': app_id, 'app_name': app_name, 'timestamp': __import__('time').time()}
def create_app_launched_event(app_id: str, app_name: str, command_line: str, working_dir: Optional[str]=None) -> Dict[str, Any]:
    return {'app_id': app_id, 'app_name': app_name, 'command_line': command_line, 'working_dir': working_dir, 'timestamp': __import__('time').time()}
def create_app_completed_event(app_id: str, app_name: str, exit_code: int, runtime_seconds: float, output_files: list) -> Dict[str, Any]:
    return {'app_id': app_id, 'app_name': app_name, 'exit_code': exit_code, 'success': exit_code == 0, 'runtime_seconds': runtime_seconds, 'output_files': output_files, 'timestamp': __import__('time').time()}