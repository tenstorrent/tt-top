# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Top-Like Display Module

Handles the top-like display formatting and rendering for the Tenstorrent monitor.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, List
from tenstorrent_lib import MonitoringSnapshot
from tenstorrent_lib.utils import format_memory, format_duration, calculate_cpu_percent
from .terminal_ui import TerminalUI


class TopLikeDisplay:
    """Handles top-like display rendering."""
    
    def __init__(self):
        self.terminal = TerminalUI()
        self.sort_column = 'cpu_time'
        self.sort_reverse = True
        self.show_help = False
        self.last_processes = {}
        
    def set_sort_options(self, column: str, reverse: bool = None) -> None:
        """
        Set sorting options.
        
        Args:
            column: Column to sort by
            reverse: Sort in reverse order (None to toggle current)
        """
        self.sort_column = column
        if reverse is not None:
            self.sort_reverse = reverse
        else:
            self.sort_reverse = not self.sort_reverse
    
    def toggle_help(self) -> None:
        """Toggle help display."""
        self.show_help = not self.show_help
    
    def render_snapshot(self, snapshot: MonitoringSnapshot) -> None:
        """
        Render a complete monitoring snapshot.
        
        Args:
            snapshot: Monitoring snapshot to render
        """
        self.terminal.update_size()
        self.terminal.clear_screen()
        
        if self.show_help:
            self.render_help()
            return
        
        # Render header
        self.render_header(snapshot)
        
        # Render device summary
        self.render_device_summary(snapshot)
        
        # Render process table
        self.render_process_table(snapshot)
        
        # Render footer
        self.render_footer(snapshot)
    
    def render_header(self, snapshot: MonitoringSnapshot) -> None:
        """Render the top header section."""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Line 1: Time, uptime, load average
        print(f"tt-top - {current_time} up {snapshot.system_info['uptime']}, "
              f"load average: {snapshot.system_info['load_avg']}")
        
        # Line 2: Process summary
        print(f"Tenstorrent processes: {snapshot.process_count} total")
        
        # Line 3: CPU usage note
        print("CPU usage: monitoring Tenstorrent device processes only")
        
        # Line 4: Memory usage
        mem_total_gb = snapshot.system_info['mem_total'] / (1024 * 1024)
        mem_free_gb = snapshot.system_info['mem_free'] / (1024 * 1024)
        mem_used_gb = mem_total_gb - mem_free_gb
        print(f"Memory: {mem_total_gb:.1f}G total, {mem_free_gb:.1f}G free, {mem_used_gb:.1f}G used")
        
        # Line 5: Device summary
        device_count = len(snapshot.device_utilization)
        print(f"Devices: {device_count} Tenstorrent devices")
        
        print()  # Empty line
    
    def render_device_summary(self, snapshot: MonitoringSnapshot) -> None:
        """Render device utilization summary."""
        print("DEVICE UTILIZATION:")
        
        if not snapshot.device_utilization:
            print("  No device utilization data available")
        else:
            for device_name, util in sorted(snapshot.device_utilization.items()):
                if 'error' not in util:
                    total = util.get('total_activity', 'N/A')
                    write = util.get('write_activity', 'N/A')
                    read = util.get('read_activity', 'N/A')
                    print(f"  {device_name}: Total={total}, Write={write}, Read={read}")
                else:
                    print(f"  {device_name}: {util['error']}")
        print()
    
    def render_process_table(self, snapshot: MonitoringSnapshot) -> None:
        """Render the process table."""
        if not snapshot.processes:
            print("No processes using Tenstorrent devices")
            return
        
        # Sort processes
        sorted_processes = self.sort_processes(snapshot.processes, snapshot.device_utilization)
        
        # Print header
        self.render_process_header()
        
        # Calculate available lines
        available_lines = self.terminal.height - 15  # Reserve space for header and footer
        processes_to_show = min(len(sorted_processes), max(1, available_lines))
        
        # Render processes
        current_time = time.time()
        for proc in sorted_processes[:processes_to_show]:
            self.render_process_row(proc, snapshot, current_time)
        
        # Show remaining count
        remaining = len(sorted_processes) - processes_to_show
        if remaining > 0:
            print(f"... and {remaining} more processes")
    
    def render_process_header(self) -> None:
        """Render process table header."""
        header_cols = ['PID', 'USER', 'PR', '%CPU', '%MEM', 'TTMEM', 'TIME+', 'DEVICE', 'COMMAND']
        header_widths = [8, 10, 3, 6, 6, 8, 8, 8, 20]
        
        header = self.terminal.format_columns(header_cols, header_widths)
        print(self.terminal.bold_text(header))
    
    def render_process_row(self, proc: Dict[str, Any], snapshot: MonitoringSnapshot, 
                          current_time: float) -> None:
        """Render a single process row."""
        # Calculate metrics
        cpu_percent = calculate_cpu_percent(proc, self.last_processes, current_time)
        mem_mb = format_memory(proc['memory'].get('VmRSS', '0'))
        tt_mem_mb = proc.get('tt_memory', {}).get('total_mapped_mb', 0)
        
        # Calculate memory percentage
        system_mem_mb = snapshot.system_info['mem_total'] // 1024
        mem_percent = (mem_mb / system_mem_mb * 100) if system_mem_mb > 0 else 0
        
        # Format time and device
        time_running = format_duration(proc.get('start_time', '1970-01-01 00:00:00'))
        device_name = os.path.basename(proc.get('device', 'unknown'))
        
        # Format Tenstorrent memory
        tt_mem_str = f"{tt_mem_mb:.1f}MB" if tt_mem_mb > 0 else "0MB"
        
        # Truncate command
        cmd = proc.get('name', 'unknown')
        cmd = self.terminal.truncate_text(cmd, 20)
        
        # Format row
        cols = [
            proc['pid'],
            self.terminal.truncate_text(proc['username'], 10),
            '20',  # Priority (simplified)
            f"{cpu_percent:.1f}",
            f"{mem_percent:.1f}",
            tt_mem_str,
            time_running,
            device_name,
            cmd
        ]
        
        widths = [8, 10, 3, 6, 6, 8, 8, 8, 20]
        row = self.terminal.format_columns(cols, widths)
        print(row)
    
    def render_footer(self, snapshot: MonitoringSnapshot) -> None:
        """Render footer information."""
        # Sort info
        sort_info = f"Sorted by {self.sort_column} ({'desc' if self.sort_reverse else 'asc'}) - Press 'h' for help, 'q' to quit"
        print(f"\n{sort_info}")
        
        # Memory summary
        total_tt_memory = snapshot.memory_summary.get('total_tt_memory_mb', 0)
        total_tt_mappings = snapshot.memory_summary.get('total_tt_mappings', 0)
        
        if total_tt_memory > 0:
            print(f"Tenstorrent Memory: {total_tt_memory:.1f}MB total across {total_tt_mappings} mappings")
    
    def render_help(self) -> None:
        """Render help screen."""
        help_text = """
Help for Interactive Commands - tt-top version

  h,?   Show this help
  q     Quit
  
Sorting:
  c     Sort by CPU time
  m     Sort by system memory usage  
  T     Sort by Tenstorrent memory usage
  p     Sort by PID
  t     Sort by start time
  a     Sort by device activity
  r     Reverse sort order
  
  <Space>  Refresh display

Press any key to return to monitoring view...
        """
        print(help_text)
    
    def sort_processes(self, processes: List[Dict[str, Any]], 
                      device_utilization: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort processes based on current sort criteria."""
        def get_sort_key(proc):
            if self.sort_column == 'cpu_time':
                return calculate_cpu_percent(proc, self.last_processes, time.time())
            elif self.sort_column == 'memory':
                return format_memory(proc['memory'].get('VmRSS', '0'))
            elif self.sort_column == 'tt_memory':
                return proc.get('tt_memory', {}).get('total_mapped_mb', 0)
            elif self.sort_column == 'pid':
                return int(proc['pid'])
            elif self.sort_column == 'start_time':
                return proc.get('start_time', '1970-01-01 00:00:00')
            elif self.sort_column == 'activity':
                device_name = os.path.basename(proc.get('device', ''))
                util = device_utilization.get(device_name, {})
                activity = util.get('total_activity', 0)
                return activity if isinstance(activity, (int, float)) else 0
            return 0
        
        return sorted(processes, key=get_sort_key, reverse=self.sort_reverse)
