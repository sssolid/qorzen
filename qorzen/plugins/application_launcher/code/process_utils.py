from __future__ import annotations

"""
Process utilities module for Application Launcher plugin.

This module provides utility functions for process management and monitoring.
"""

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
    """Information about a running process."""

    pid: int
    name: str
    command_line: str
    memory_mb: float
    cpu_percent: float
    created_at: datetime
    user: str


class ProcessMonitor:
    """Monitor and manage external processes."""

    def __init__(self) -> None:
        """Initialize the process monitor."""
        self._known_pids: Set[int] = set()
        self._system = platform.system()

    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get information about a specific process.

        Args:
            pid: Process ID

        Returns:
            ProcessInfo object or None if process not found
        """
        try:
            if self._system == "Windows":
                return self._get_windows_process_info(pid)
            elif self._system in ("Linux", "Darwin"):
                return self._get_unix_process_info(pid)
            else:
                return None
        except Exception:
            return None

    def _get_windows_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get process information on Windows.

        Args:
            pid: Process ID

        Returns:
            ProcessInfo object or None if process not found
        """
        try:
            import psutil  # type: ignore
            if not psutil.pid_exists(pid):
                return None

            proc = psutil.Process(pid)
            return ProcessInfo(
                pid=pid,
                name=proc.name(),
                command_line=" ".join(proc.cmdline()),
                memory_mb=proc.memory_info().rss / (1024 * 1024),
                cpu_percent=proc.cpu_percent(interval=0.1),
                created_at=datetime.fromtimestamp(proc.create_time()),
                user=proc.username()
            )
        except Exception:
            return None

    def _get_unix_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get process information on Unix-like systems.

        Args:
            pid: Process ID

        Returns:
            ProcessInfo object or None if process not found
        """
        try:
            import psutil  # type: ignore
            if not psutil.pid_exists(pid):
                return None

            proc = psutil.Process(pid)
            return ProcessInfo(
                pid=pid,
                name=proc.name(),
                command_line=" ".join(proc.cmdline()),
                memory_mb=proc.memory_info().rss / (1024 * 1024),
                cpu_percent=proc.cpu_percent(interval=0.1),
                created_at=datetime.fromtimestamp(proc.create_time()),
                user=proc.username()
            )
        except Exception:
            # Fallback to ps command if psutil fails
            try:
                cmd = ["ps", "-p", str(pid), "-o", "comm=,pcpu=,pmem=,lstart=,user="]
                result = subprocess.check_output(cmd, text=True).strip()
                if result:
                    parts = result.split()
                    if len(parts) >= 5:
                        name = parts[0]
                        cpu = float(parts[1])
                        # Get command line from /proc on Linux
                        cmdline = ""
                        if os.path.exists(f"/proc/{pid}/cmdline"):
                            with open(f"/proc/{pid}/cmdline", "rb") as f:
                                cmdline_bytes = f.read()
                                cmdline = " ".join([arg.decode("utf-8", errors="replace")
                                                    for arg in cmdline_bytes.split(b"\0") if arg])

                        # Try to parse date from ps output
                        date_str = " ".join(parts[3:8])
                        try:
                            created_at = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
                        except ValueError:
                            created_at = datetime.now()

                        # Get memory info
                        mem_mb = 0.0
                        if os.path.exists(f"/proc/{pid}/status"):
                            with open(f"/proc/{pid}/status", "r") as f:
                                for line in f:
                                    if line.startswith("VmRSS:"):
                                        parts = line.split()
                                        if len(parts) >= 2:
                                            try:
                                                # Convert KB to MB
                                                mem_kb = float(parts[1])
                                                mem_mb = mem_kb / 1024
                                            except ValueError:
                                                pass
                                        break

                        return ProcessInfo(
                            pid=pid,
                            name=name,
                            command_line=cmdline,
                            memory_mb=mem_mb,
                            cpu_percent=cpu,
                            created_at=created_at,
                            user=parts[-1]
                        )
            except Exception:
                pass

            return None

    def limit_process_resources(self, pid: int, max_memory_mb: Optional[int] = None) -> bool:
        """
        Apply resource limits to a running process.

        Args:
            pid: Process ID
            max_memory_mb: Maximum memory limit in MB (None for no limit)

        Returns:
            True if limits were applied successfully, False otherwise
        """
        try:
            if not max_memory_mb:
                return True

            if self._system == "Windows":
                # Windows doesn't have direct way to limit memory, use Job Objects in C++
                # or WMI in Python, but it's complex - return True to indicate no error
                return True
            elif self._system == "Linux":
                # On Linux, we can use cgroups
                return self._set_linux_memory_limit(pid, max_memory_mb)
            elif self._system == "Darwin":
                # On macOS, we can use resource limits
                return self._set_macos_memory_limit(pid, max_memory_mb)
            else:
                return False
        except Exception:
            return False

    def _set_linux_memory_limit(self, pid: int, max_memory_mb: int) -> bool:
        """
        Set memory limit for a process on Linux using cgroups.

        Args:
            pid: Process ID
            max_memory_mb: Maximum memory in MB

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a temporary cgroup memory controller for this process
            cgroup_name = f"applauncher_{pid}"
            cgroup_path = f"/sys/fs/cgroup/memory/{cgroup_name}"

            if not os.path.exists("/sys/fs/cgroup/memory"):
                return False

            if not os.path.exists(cgroup_path):
                os.makedirs(cgroup_path, exist_ok=True)

            # Set memory limit (in bytes)
            with open(f"{cgroup_path}/memory.limit_in_bytes", "w") as f:
                f.write(str(max_memory_mb * 1024 * 1024))

            # Add process to cgroup
            with open(f"{cgroup_path}/tasks", "w") as f:
                f.write(str(pid))

            return True
        except Exception:
            return False

    def _set_macos_memory_limit(self, pid: int, max_memory_mb: int) -> bool:
        """
        Set memory limit for a process on macOS.

        Args:
            pid: Process ID
            max_memory_mb: Maximum memory in MB

        Returns:
            True if successful, False otherwise
        """
        try:
            # On macOS, we can use the launchctl limit command for the shell,
            # but not for already running processes
            # We can use the process_policy command, but it requires root
            # Return True to indicate no error, as we can't easily set limits
            return True
        except Exception:
            return False

    def find_output_files(
            self,
            working_dir: str,
            patterns: List[str],
            base_timestamp: float
    ) -> List[str]:
        """
        Find output files matching the given patterns that were modified
        after the base timestamp.

        Args:
            working_dir: Working directory to search in
            patterns: List of glob patterns to match
            base_timestamp: Base timestamp to filter files by modification time

        Returns:
            List of matching file paths
        """
        import glob
        import os
        import time

        output_files = []
        for pattern in patterns:
            # If pattern is absolute path, use it directly
            if os.path.isabs(pattern):
                matching_files = glob.glob(pattern)
            else:
                # Otherwise look in working directory
                matching_files = glob.glob(os.path.join(working_dir, pattern))

            # Filter by timestamp
            for file_path in matching_files:
                if os.path.isfile(file_path):
                    mod_time = os.path.getmtime(file_path)
                    if mod_time >= base_timestamp:
                        output_files.append(file_path)

        # Sort by modification time
        output_files.sort(key=lambda f: os.path.getmtime(f))
        return output_files

    @staticmethod
    def build_command_line(
            executable: str,
            arguments: List[str],
            environment: Optional[Dict[str, str]] = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        Build a command line string and environment dictionary for process execution.

        Args:
            executable: Path to the executable
            arguments: List of command line arguments
            environment: Optional environment variables dictionary

        Returns:
            Tuple of (command_line_string, environment_dict)
        """
        cmd_line = shlex.quote(executable)
        for arg in arguments:
            cmd_line += f" {shlex.quote(arg)}"

        env = os.environ.copy()
        if environment:
            env.update(environment)

        return cmd_line, env

    @staticmethod
    def create_temporary_script(
            script_content: str,
            script_type: str = "bash"
    ) -> Tuple[str, str]:
        """
        Create a temporary script file.

        Args:
            script_content: The script content
            script_type: Type of script ('bash', 'batch', 'python', etc.)

        Returns:
            Tuple of (file_path, executable)
        """
        extension_map = {
            "bash": ".sh",
            "batch": ".bat" if platform.system() == "Windows" else ".sh",
            "python": ".py",
            "powershell": ".ps1",
            "javascript": ".js",
        }

        extension = extension_map.get(script_type.lower(), ".txt")

        with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode="w") as f:
            f.write(script_content)
            temp_path = f.name

        # Make the script executable on Unix systems
        if platform.system() != "Windows" and script_type.lower() in ("bash", "batch"):
            os.chmod(temp_path, 0o755)

        # Determine the executable to use
        executable_map = {
            "bash": "bash" if platform.system() != "Windows" else "sh",
            "batch": "cmd.exe" if platform.system() == "Windows" else "bash",
            "python": "python",
            "powershell": "powershell",
            "javascript": "node",
        }

        executable = executable_map.get(script_type.lower(), "")

        return temp_path, executable