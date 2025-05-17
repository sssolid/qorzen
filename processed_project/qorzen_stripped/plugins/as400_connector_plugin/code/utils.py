from __future__ import annotations
'\nUtility functions for the AS400 Connector Plugin.\n\nThis module provides helper functions for working with AS400 connections,\nSQL queries, and other plugin-specific functionality.\n'
import os
import json
import re
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, cast
from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtGui import QColor
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, SavedQuery, QueryHistoryEntry, PluginSettings
def load_connections(file_manager: Any) -> Dict[str, AS400ConnectionConfig]:
    try:
        file_path = 'as400_connector_plugin/connections.json'
        try:
            file_info = file_manager.get_file_info(file_path, 'plugin_data')
            if not file_info:
                return {}
        except:
            return {}
        json_data = file_manager.read_text(file_path, 'plugin_data')
        data = json.loads(json_data)
        connections = {}
        for conn_data in data:
            try:
                if 'password' in conn_data and (not conn_data['password'].startswith('SecretStr')):
                    conn_data['password'] = conn_data['password']
                connection = AS400ConnectionConfig(**conn_data)
                connections[connection.id] = connection
            except Exception as e:
                continue
        return connections
    except Exception:
        return {}
def save_connections(connections: Dict[str, AS400ConnectionConfig], file_manager: Any) -> bool:
    try:
        file_path = 'as400_connector_plugin/connections.json'
        file_manager.ensure_directory('as400_connector_plugin', 'plugin_data')
        conn_list = []
        for conn in connections.values():
            conn_dict = conn.dict()
            if 'password' in conn_dict:
                conn_dict['password'] = conn.password.get_secret_value()
            conn_list.append(conn_dict)
        json_data = json.dumps(conn_list, indent=2)
        file_manager.write_text(file_path, json_data, 'plugin_data')
        return True
    except Exception:
        return False
def load_saved_queries(file_manager: Any) -> Dict[str, SavedQuery]:
    try:
        file_path = 'as400_connector_plugin/saved_queries.json'
        try:
            file_info = file_manager.get_file_info(file_path, 'plugin_data')
            if not file_info:
                return {}
        except:
            return {}
        json_data = file_manager.read_text(file_path, 'plugin_data')
        data = json.loads(json_data)
        queries = {}
        for query_data in data:
            try:
                if 'created_at' in query_data and isinstance(query_data['created_at'], str):
                    query_data['created_at'] = datetime.datetime.fromisoformat(query_data['created_at'])
                if 'updated_at' in query_data and isinstance(query_data['updated_at'], str):
                    query_data['updated_at'] = datetime.datetime.fromisoformat(query_data['updated_at'])
                query = SavedQuery(**query_data)
                queries[query.id] = query
            except Exception as e:
                continue
        return queries
    except Exception:
        return {}
def save_queries(queries: Dict[str, SavedQuery], file_manager: Any) -> bool:
    try:
        file_path = 'as400_connector_plugin/saved_queries.json'
        file_manager.ensure_directory('as400_connector_plugin', 'plugin_data')
        query_list = []
        for query in queries.values():
            query_dict = query.dict()
            if 'created_at' in query_dict and isinstance(query_dict['created_at'], datetime.datetime):
                query_dict['created_at'] = query_dict['created_at'].isoformat()
            if 'updated_at' in query_dict and isinstance(query_dict['updated_at'], datetime.datetime):
                query_dict['updated_at'] = query_dict['updated_at'].isoformat()
            query_list.append(query_dict)
        json_data = json.dumps(query_list, indent=2)
        file_manager.write_text(file_path, json_data, 'plugin_data')
        return True
    except Exception:
        return False
def load_query_history(file_manager: Any, limit: int=100) -> List[QueryHistoryEntry]:
    try:
        file_path = 'as400_connector_plugin/query_history.json'
        try:
            file_info = file_manager.get_file_info(file_path, 'plugin_data')
            if not file_info:
                return []
        except:
            return []
        json_data = file_manager.read_text(file_path, 'plugin_data')
        data = json.loads(json_data)
        history = []
        for entry_data in data:
            try:
                if 'executed_at' in entry_data and isinstance(entry_data['executed_at'], str):
                    entry_data['executed_at'] = datetime.datetime.fromisoformat(entry_data['executed_at'])
                entry = QueryHistoryEntry(**entry_data)
                history.append(entry)
            except Exception:
                continue
        history.sort(key=lambda x: x.executed_at, reverse=True)
        return history[:limit]
    except Exception:
        return []
def save_query_history(history: List[QueryHistoryEntry], file_manager: Any, limit: int=100) -> bool:
    try:
        file_path = 'as400_connector_plugin/query_history.json'
        file_manager.ensure_directory('as400_connector_plugin', 'plugin_data')
        sorted_history = sorted(history, key=lambda x: x.executed_at, reverse=True)[:limit]
        history_list = []
        for entry in sorted_history:
            entry_dict = entry.dict()
            if 'executed_at' in entry_dict and isinstance(entry_dict['executed_at'], datetime.datetime):
                entry_dict['executed_at'] = entry_dict['executed_at'].isoformat()
            history_list.append(entry_dict)
        json_data = json.dumps(history_list, indent=2)
        file_manager.write_text(file_path, json_data, 'plugin_data')
        return True
    except Exception:
        return False
def load_plugin_settings(config_manager: Any) -> PluginSettings:
    try:
        settings_dict = config_manager.get('plugins.as400_connector_plugin.settings', {})
        return PluginSettings(**settings_dict)
    except Exception:
        return PluginSettings()
def save_plugin_settings(settings: PluginSettings, config_manager: Any) -> bool:
    try:
        settings_dict = settings.dict()
        config_manager.set('plugins.as400_connector_plugin.settings', settings_dict)
        return True
    except Exception:
        return False
def format_value_for_display(value: Any) -> str:
    if value is None:
        return 'NULL'
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()
    if isinstance(value, bool):
        return str(value).upper()
    if isinstance(value, bytes):
        if len(value) > 20:
            return f'0x{value[:20].hex()}... ({len(value)} bytes)'
        else:
            return f'0x{value.hex()}'
    return str(value)
def detect_query_parameters(query: str) -> List[str]:
    param_names = re.findall(':(\\w+)', query)
    return list(dict.fromkeys(param_names))
def get_sql_keywords() -> List[str]:
    return ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE', 'ORDER', 'BY', 'GROUP', 'HAVING', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AS', 'UNION', 'ALL', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'IS', 'NULL', 'CREATE', 'TABLE', 'VIEW', 'INDEX', 'UNIQUE', 'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'DEFAULT', 'ALTER', 'ADD', 'DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'SET', 'INSERT', 'INTO', 'VALUES', 'EXISTS', 'INT', 'INTEGER', 'SMALLINT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL', 'CHAR', 'VARCHAR', 'TEXT', 'DATE', 'TIME', 'TIMESTAMP', 'DATETIME', 'BOOLEAN', 'BINARY', 'VARBINARY', 'BLOB', 'CLOB', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'IFNULL', 'CAST', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'SUBSTRING', 'LENGTH', 'CONCAT', 'REPLACE', 'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP', 'EXTRACT', 'TO_CHAR', 'TO_DATE', 'DATEADD', 'DATEDIFF', 'WITH', 'FETCH', 'FIRST', 'ROWS', 'ONLY', 'OPTIMIZE', 'FOR', 'RRN', 'LISTAGG', 'OVER', 'PARTITION', 'DENSE_RANK', 'ROW_NUMBER', 'RANK', 'SUBSTR', 'POSITION', 'LOCATE', 'VALUE', 'GET_CURRENT_CONNECTION', 'DAYS', 'MICROSECOND', 'QUARTER', 'RID', 'NODENAME', 'NODENUMBER']
def get_syntax_highlighting_colors() -> Dict[str, QColor]:
    return {'keyword': QColor(0, 128, 255), 'function': QColor(255, 128, 0), 'string': QColor(0, 170, 0), 'number': QColor(170, 0, 170), 'operator': QColor(170, 0, 0), 'comment': QColor(128, 128, 128), 'parameter': QColor(0, 170, 170), 'identifier': QColor(0, 0, 0), 'background': QColor(255, 255, 255), 'current_line': QColor(232, 242, 254)}
def guess_jar_locations() -> List[str]:
    potential_paths = []
    if os.name == 'nt':
        program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        for base in [program_files, program_files_x86]:
            potential_paths.extend([os.path.join(base, 'IBM', 'JTOpen', 'lib', 'jt400.jar'), os.path.join(base, 'IBM', 'Client Access', 'jt400.jar')])
        downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        potential_paths.append(os.path.join(downloads, 'jt400.jar'))
    else:
        potential_paths.extend(['/opt/jt400/lib/jt400.jar', '/usr/local/lib/jt400.jar', '/usr/lib/jt400.jar', os.path.join(os.path.expanduser('~'), 'lib', 'jt400.jar'), os.path.join(os.path.expanduser('~'), 'Downloads', 'jt400.jar')])
    project_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    potential_paths.extend([os.path.join(project_dir, 'lib', 'jt400.jar'), os.path.join(project_dir, 'jars', 'jt400.jar'), os.path.join(project_dir, 'external', 'jt400.jar')])
    return [path for path in potential_paths if os.path.exists(path)]
def format_execution_time(ms: int) -> str:
    if ms < 1000:
        return f'{ms} ms'
    elif ms < 60000:
        return f'{ms / 1000:.2f} sec'
    else:
        minutes = ms // 60000
        seconds = ms % 60000 / 1000
        return f'{minutes} min {seconds:.2f} sec'