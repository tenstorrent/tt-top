# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Tenstorrent Device Monitoring Library

This library provides comprehensive monitoring capabilities for Tenstorrent devices,
including process tracking, memory usage analysis, and device utilization metrics.
"""

from .device_monitor import TenstorrentDeviceMonitor
from .process_scanner import ProcessScanner, find_tenstorrent_processes
from .data_collector import DataCollector, MonitoringSnapshot
from .memory_analyzer import MemoryAnalyzer
from .utils import format_memory, format_duration, get_system_info
from .platform_compat import TerminalManager, check_system_compatibility

__version__ = "1.0.0"
__author__ = "Tenstorrent"

__all__ = [
    'TenstorrentDeviceMonitor',
    'ProcessScanner', 
    'find_tenstorrent_processes',
    'DataCollector',
    'MonitoringSnapshot',
    'MemoryAnalyzer',
    'format_memory',
    'format_duration', 
    'get_system_info',
    'TerminalManager',
    'check_system_compatibility'
]
