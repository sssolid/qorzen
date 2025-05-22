from __future__ import annotations
'\nProcess utilities module for Application Launcher plugin.\n\nThis module provides utility functions for process management and monitoring.\n'
import os
import re
import platform
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any
@dataclass
class ProcessInfo:
    pid: int
    name: str
    command_line: str
    memory_mb: float
    cpu_percent: float
    created_at: datetime
    user: str
class ProcessMonitor:
    def __init__(self) -> None:
        self._known_pids: Set[int] = set()
        self._system = platform.system()
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        try:
            if self._system == 'Windows':
                return self._get_windows_process_info(pid)
            elif self._system in ('Linux', 'Darwin'):
                return self._get_unix_process_info(pid)
            else:
                return None
        except Exception:
            return None
    def _get_windows_process_info(self, pid: int) -> Optional[ProcessInfo]:
        try:
            import psutil
            if not psutil.pid_exists(pid):
                return None
            proc = psutil.Process(pid)
            return ProcessInfo(pid=pid, name=proc.name(), command_line=' '.join(proc.cmdline()), memory_mb=proc.memory_info().rss / (1024 * 1024), cpu_percent=proc.cpu_percent(interval=0.1), created_at=datetime.fromtimestamp(proc.create_time()), user=proc.username())
        except Exception:
            return None
    def _get_unix_process_info(self, pid: int) -> Optional[ProcessInfo]:
        try:
            import psutil
            if not psutil.pid_exists(pid):
                return None
            proc = psutil.Process(pid)
            return ProcessInfo(pid=pid, name=proc.name(), command_line=' '.join(proc.cmdline()), memory_mb=proc.memory_info().rss / (1024 * 1024), cpu_percent=proc.cpu_percent(interval=0.1), created_at=datetime.fromtimestamp(proc.create_time()), user=proc.username())
        except Exception:
            try:
                cmd = ['ps', '-p', str(pid), '-o', 'comm=,pcpu=,pmem=,lstart=,user=']
                result = subprocess.check_output(cmd, text=True).strip()
                if result:
                    parts = result.split()
                    if len(parts) >= 5:
                        name = parts[0]
                        cpu = float(parts[1])
                        cmdline = ''
                        if os.path.exists(f'/proc/{pid}/cmdline'):
                            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                                cmdline_bytes = f.read()
                                cmdline = ' '.join([arg.decode('utf-8', errors='replace') for arg in cmdline_bytes.split(b'\x00') if arg])
                        date_str = ' '.join(parts[3:8])
                        try:
                            created_at = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                        except ValueError:
                            created_at = datetime.now()
                        mem_mb = 0.0
                        if os.path.exists(f'/proc/{pid}/status'):
                            with open(f'/proc/{pid}/status', 'r') as f:
                                for line in f:
                                    if line.startswith('VmRSS:'):
                                        parts = line.split()
                                        if len(parts) >= 2:
                                            try:
                                                mem_kb = float(parts[1])
                                                mem_mb = mem_kb / 1024
                                            except ValueError:
                                                pass
                                        break
                        return ProcessInfo(pid=pid, name=name, command_line=cmdline, memory_mb=mem_mb, cpu_percent=cpu, created_at=created_at, user=parts[-1])
            except Exception:
                pass
            return None
    def limit_process_resources(self, pid: int, max_memory_mb: Optional[int]=None) -> bool:
        try:
            if not max_memory_mb:
                return True
            if self._system == 'Windows':
                return True
            elif self._system == 'Linux':
                return self._set_linux_memory_limit(pid, max_memory_mb)
            elif self._system == 'Darwin':
                return self._set_macos_memory_limit(pid, max_memory_mb)
            else:
                return False
        except Exception:
            return False
    def _set_linux_memory_limit(self, pid: int, max_memory_mb: int) -> bool:
        try:
            cgroup_name = f'applauncher_{pid}'
            cgroup_path = f'/sys/fs/cgroup/memory/{cgroup_name}'
            if not os.path.exists('/sys/fs/cgroup/memory'):
                return False
            if not os.path.exists(cgroup_path):
                os.makedirs(cgroup_path, exist_ok=True)
            with open(f'{cgroup_path}/memory.limit_in_bytes', 'w') as f:
                f.write(str(max_memory_mb * 1024 * 1024))
            with open(f'{cgroup_path}/tasks', 'w') as f:
                f.write(str(pid))
            return True
        except Exception:
            return False
    def _set_macos_memory_limit(self, pid: int, max_memory_mb: int) -> bool:
        try:
            return True
        except Exception:
            return False
    def find_output_files(self, working_dir: str, patterns: List[str], base_timestamp: float) -> List[str]:
        import glob
        import os
        import time
        output_files = []
        for pattern in patterns:
            if os.path.isabs(pattern):
                matching_files = glob.glob(pattern)
            else:
                matching_files = glob.glob(os.path.join(working_dir, pattern))
            for file_path in matching_files:
                if os.path.isfile(file_path):
                    mod_time = os.path.getmtime(file_path)
                    if mod_time >= base_timestamp:
                        output_files.append(file_path)
        output_files.sort(key=lambda f: os.path.getmtime(f))
        return output_files
    @staticmethod
    def build_command_line(executable: str, arguments: List[str], environment: Optional[Dict[str, str]]=None) -> Tuple[str, Dict[str, str]]:
        cmd_line = shlex.quote(executable)
        for arg in arguments:
            cmd_line += f' {shlex.quote(arg)}'
        env = os.environ.copy()
        if environment:
            env.update(environment)
        return (cmd_line, env)
    @staticmethod
    def create_temporary_script(script_content: str, script_type: str='bash') -> Tuple[str, str]:
        extension_map = {'bash': '.sh', 'batch': '.bat' if platform.system() == 'Windows' else '.sh', 'python': '.py', 'powershell': '.ps1', 'javascript': '.js'}
        extension = extension_map.get(script_type.lower(), '.txt')
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w') as f:
            f.write(script_content)
            temp_path = f.name
        if platform.system() != 'Windows' and script_type.lower() in ('bash', 'batch'):
            os.chmod(temp_path, 493)
        executable_map = {'bash': 'bash' if platform.system() != 'Windows' else 'sh', 'batch': 'cmd.exe' if platform.system() == 'Windows' else 'bash', 'python': 'python', 'powershell': 'powershell', 'javascript': 'node'}
        executable = executable_map.get(script_type.lower(), '')
        return (temp_path, executable)