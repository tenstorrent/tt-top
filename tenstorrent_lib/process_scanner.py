# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Process Scanner Module

Handles finding and analyzing processes that use Tenstorrent devices.

Note: lsof is available on most systems but we use manual /proc scanning 
for better portability and control over the scanning process.
"""

import os
import glob
import pwd
from pathlib import Path
from typing import List, Dict, Any, Optional
from .memory_analyzer import MemoryAnalyzer
from .utils import get_process_start_time, get_process_cpu_time


class ProcessScanner:
    """Scanner for processes using Tenstorrent devices."""
    
    def __init__(self):
        self.memory_analyzer = MemoryAnalyzer()
    
    def get_process_info(self, pid: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed process information from /proc/pid.
        
        Args:
            pid: Process ID as string
            
        Returns:
            Dictionary with process information or None if process not accessible
        """
        try:
            proc_dir = Path(f"/proc/{pid}")
            
            # Get process name
            comm_file = proc_dir / "comm"
            process_name = comm_file.read_text().strip() if comm_file.exists() else "unknown"
            
            # Get command line
            cmdline_file = proc_dir / "cmdline"
            if cmdline_file.exists():
                cmdline = cmdline_file.read_text().replace('\0', ' ').strip()
            else:
                cmdline = "unknown"
            
            # Get process owner
            stat_info = proc_dir.stat()
            try:
                username = pwd.getpwuid(stat_info.st_uid).pw_name
            except KeyError:
                username = str(stat_info.st_uid)
            
            # Get memory info
            status_file = proc_dir / "status"
            memory_info = {}
            if status_file.exists():
                for line in status_file.read_text().splitlines():
                    if line.startswith(('VmSize:', 'VmRSS:', 'VmPeak:', 'VmHWM:')):
                        key, value = line.split(':', 1)
                        memory_info[key.strip()] = value.strip()
            
            # Get Tenstorrent-specific memory usage
            tt_memory = self.memory_analyzer.get_tenstorrent_memory_usage(pid)
            
            # Get start time and CPU time
            start_time = get_process_start_time(pid)
            cpu_time = get_process_cpu_time(pid)
            
            return {
                'pid': pid,
                'name': process_name,
                'cmdline': cmdline,
                'username': username,
                'memory': memory_info,
                'tt_memory': tt_memory,
                'start_time': start_time,
                'cpu_time': cpu_time
            }
        except (OSError, IOError):
            return None
    
    def find_processes_by_proc_scan(self) -> List[Dict[str, Any]]:
        """
        Find processes by scanning /proc/*/fd/ directories.
        
        This method provides reliable cross-platform detection without
        external dependencies like lsof.
        """
        processes = []
        for proc_dir in glob.glob('/proc/[0-9]*'):
            pid = os.path.basename(proc_dir)
            fd_dir = os.path.join(proc_dir, 'fd')
            
            try:
                # Check if any file descriptors point to tenstorrent devices
                for fd_link in os.listdir(fd_dir):
                    fd_path = os.path.join(fd_dir, fd_link)
                    try:
                        target = os.readlink(fd_path)
                        if 'tenstorrent' in target:
                            proc_info = self.get_process_info(pid)
                            if proc_info:
                                proc_info['device'] = target
                                proc_info['fd'] = fd_link
                                processes.append(proc_info)
                            break
                    except OSError:
                        continue
            except (OSError, PermissionError):
                continue
        return processes
    
    def find_all_processes(self) -> List[Dict[str, Any]]:
        """
        Find all processes using Tenstorrent devices.
        
        Uses /proc filesystem scanning for reliable detection.
        Note: lsof could be used as an alternative but we prefer
        direct /proc scanning for better control and portability.
        """
        return self.find_processes_by_proc_scan()


def find_tenstorrent_processes() -> List[Dict[str, Any]]:
    """
    Convenience function to find all Tenstorrent processes.
    
    Returns:
        List of dictionaries containing process information
    """
    scanner = ProcessScanner()
    return scanner.find_all_processes()
