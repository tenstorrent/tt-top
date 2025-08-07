# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Utility Functions Module

Common utility functions for the Tenstorrent monitoring library.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Union


def get_process_start_time(pid: str) -> str:
    """
    Get process start time from /proc/pid/stat.
    
    Args:
        pid: Process ID as string
        
    Returns:
        Start time as formatted string or "unknown"
    """
    try:
        with open(f"/proc/{pid}/stat", 'r') as f:
            stat_fields = f.read().split()
            # Field 22 is starttime in clock ticks since boot
            starttime_ticks = int(stat_fields[21])
            
        # Get system boot time
        with open("/proc/stat", 'r') as f:
            for line in f:
                if line.startswith("btime "):
                    boot_time = int(line.split()[1])
                    break
            else:
                return "unknown"
        
        # Get clock ticks per second
        clock_ticks_per_sec = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
        
        # Calculate start time
        start_time = boot_time + (starttime_ticks / clock_ticks_per_sec)
        return datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
        
    except (OSError, ValueError, IndexError):
        return "unknown"


def get_process_cpu_time(pid: str) -> str:
    """
    Get process CPU time from /proc/pid/stat.
    
    Args:
        pid: Process ID as string
        
    Returns:
        CPU time as formatted string or "unknown"
    """
    try:
        with open(f"/proc/{pid}/stat", 'r') as f:
            stat_fields = f.read().split()
            # Fields 14 and 15 are utime and stime in clock ticks
            utime = int(stat_fields[13])
            stime = int(stat_fields[14])
            
        clock_ticks_per_sec = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
        total_cpu_seconds = (utime + stime) / clock_ticks_per_sec
        
        return f"{total_cpu_seconds:.2f}s"
        
    except (OSError, ValueError, IndexError):
        return "unknown"


def format_memory(mem_str: str) -> int:
    """
    Format memory string to MB.
    
    Args:
        mem_str: Memory string like "512000 kB"
        
    Returns:
        Memory in MB as integer
    """
    try:
        if mem_str == 'unknown' or not mem_str:
            return 0
        # Extract number from string like "512000 kB"
        mem_kb = int(mem_str.split()[0])
        return mem_kb // 1024  # Convert to MB
    except (ValueError, IndexError):
        return 0


def format_duration(start_time_str: str) -> str:
    """
    Calculate how long process has been running.
    
    Args:
        start_time_str: Start time as string in format "YYYY-MM-DD HH:MM:SS"
        
    Returns:
        Duration as formatted string "HH:MM:SS" or "MM:SS"
    """
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        duration = datetime.now() - start_time
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return "00:00"


def get_system_info() -> Dict[str, Any]:
    """
    Get system information like uptime, load average, and memory.
    
    Returns:
        Dictionary containing system information
    """
    try:
        # Get uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        
        # Get load average
        with open('/proc/loadavg', 'r') as f:
            load_avg = f.read().split()[:3]
        load_str = ', '.join(load_avg)
        
        # Get memory info
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith(('MemTotal:', 'MemFree:', 'MemAvailable:')):
                    key, value = line.split(':')
                    mem_info[key] = int(value.split()[0])  # Value in kB
        
        return {
            'uptime': uptime_str,
            'load_avg': load_str,
            'mem_total': mem_info.get('MemTotal', 0),
            'mem_free': mem_info.get('MemFree', 0),
            'mem_available': mem_info.get('MemAvailable', 0)
        }
    except (OSError, ValueError):
        return {
            'uptime': 'unknown',
            'load_avg': 'unknown',
            'mem_total': 0,
            'mem_free': 0,
            'mem_available': 0
        }


def calculate_cpu_percent(proc: Dict[str, Any], last_processes: Dict[str, Dict], 
                         current_time: float) -> float:
    """
    Calculate CPU percentage for a process.
    
    Args:
        proc: Process information dictionary
        last_processes: Dictionary of previous process states
        current_time: Current timestamp
        
    Returns:
        CPU percentage as float
    """
    try:
        pid = proc['pid']
        
        # Get current CPU time
        cpu_time_str = proc.get('cpu_time', '0.00s')
        cpu_time = float(cpu_time_str.replace('s', ''))
        
        if pid in last_processes:
            last_cpu_time = last_processes[pid].get('cpu_time', 0)
            last_time = last_processes[pid].get('timestamp', current_time)
            
            time_diff = current_time - last_time
            cpu_diff = cpu_time - last_cpu_time
            
            if time_diff > 0:
                cpu_percent = (cpu_diff / time_diff) * 100
                return min(cpu_percent, 100.0)  # Cap at 100%
        
        # Store current values for next calculation
        last_processes[pid] = {
            'cpu_time': cpu_time,
            'timestamp': current_time
        }
        
        return 0.0
    except (ValueError, KeyError):
        return 0.0


def format_bytes(bytes_value: Union[int, float], unit: str = "MB") -> str:
    """
    Format bytes to human readable format.
    
    Args:
        bytes_value: Number of bytes
        unit: Target unit ("B", "KB", "MB", "GB")
        
    Returns:
        Formatted string with unit
    """
    try:
        if unit == "B":
            return f"{bytes_value:.0f}B"
        elif unit == "KB":
            return f"{bytes_value / 1024:.1f}KB"
        elif unit == "MB":
            return f"{bytes_value / (1024 * 1024):.1f}MB"
        elif unit == "GB":
            return f"{bytes_value / (1024 * 1024 * 1024):.1f}GB"
        else:
            return f"{bytes_value:.0f}B"
    except (ValueError, TypeError):
        return "0B"


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        if isinstance(value, str):
            # Handle strings like "1234 kB"
            return int(value.split()[0])
        return int(value)
    except (ValueError, TypeError, IndexError):
        return default
