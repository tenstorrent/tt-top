# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Data Collector Module

Coordinates data collection from all monitoring components and provides unified snapshots.
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from .device_monitor import TenstorrentDeviceMonitor
from .process_scanner import ProcessScanner
from .memory_analyzer import MemoryAnalyzer
from .utils import get_system_info


@dataclass
class MonitoringSnapshot:
    """Data class representing a monitoring snapshot."""
    timestamp: str
    process_count: int
    processes: List[Dict[str, Any]]
    device_utilization: Dict[str, Dict[str, Any]]
    system_info: Dict[str, Any]
    memory_summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert snapshot to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class DataCollector:
    """Main data collector that coordinates all monitoring components."""
    
    def __init__(self):
        self.device_monitor = TenstorrentDeviceMonitor()
        self.process_scanner = ProcessScanner()
        self.memory_analyzer = MemoryAnalyzer()
        self.history: List[MonitoringSnapshot] = []
        self.max_history_size = 1000  # Limit history to prevent memory issues
    
    def collect_snapshot(self) -> MonitoringSnapshot:
        """
        Collect a complete monitoring snapshot.
        
        Returns:
            MonitoringSnapshot containing all current data
        """
        timestamp = datetime.now()
        
        # Collect process data
        processes = self.process_scanner.find_all_processes()
        
        # Collect device utilization
        device_utilization = self.device_monitor.get_all_device_utilization()
        
        # Get system information
        system_info = get_system_info()
        
        # Get memory summary
        memory_summary = self.memory_analyzer.get_process_memory_summary(processes)
        
        snapshot = MonitoringSnapshot(
            timestamp=timestamp.isoformat(),
            process_count=len(processes),
            processes=processes,
            device_utilization=device_utilization,
            system_info=system_info,
            memory_summary=memory_summary
        )
        
        # Add to history
        self.add_to_history(snapshot)
        
        return snapshot
    
    def add_to_history(self, snapshot: MonitoringSnapshot) -> None:
        """
        Add snapshot to history with size management.
        
        Args:
            snapshot: Snapshot to add to history
        """
        self.history.append(snapshot)
        
        # Maintain history size limit
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
    
    def get_history(self, count: Optional[int] = None) -> List[MonitoringSnapshot]:
        """
        Get monitoring history.
        
        Args:
            count: Number of recent snapshots to return (None for all)
            
        Returns:
            List of monitoring snapshots
        """
        if count is None:
            return self.history.copy()
        return self.history[-count:] if count > 0 else []
    
    def clear_history(self) -> None:
        """Clear all monitoring history."""
        self.history.clear()
    
    def save_history_to_file(self, filename: str) -> bool:
        """
        Save monitoring history to JSON file.
        
        Args:
            filename: Path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert snapshots to serializable format
            serializable_history = [snapshot.to_dict() for snapshot in self.history]
            
            with open(filename, 'w') as f:
                json.dump(serializable_history, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False
    
    def load_history_from_file(self, filename: str) -> bool:
        """
        Load monitoring history from JSON file.
        
        Args:
            filename: Path to load file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'r') as f:
                history_data = json.load(f)
            
            # Convert back to MonitoringSnapshot objects
            self.history = []
            for snapshot_dict in history_data:
                snapshot = MonitoringSnapshot(**snapshot_dict)
                self.history.append(snapshot)
            
            return True
        except Exception as e:
            print(f"Error loading history: {e}")
            return False
    
    def get_process_trend(self, pid: str, metric: str, count: int = 10) -> List[Any]:
        """
        Get trend data for a specific process metric.
        
        Args:
            pid: Process ID to track
            metric: Metric name (e.g., 'tt_memory.total_mapped_mb')
            count: Number of recent data points to return
            
        Returns:
            List of metric values over time
        """
        trend_data = []
        recent_history = self.get_history(count)
        
        for snapshot in recent_history:
            for process in snapshot.processes:
                if process['pid'] == pid:
                    # Navigate nested metric path
                    value = process
                    for key in metric.split('.'):
                        value = value.get(key, 0)
                        if value == 0:
                            break
                    trend_data.append({
                        'timestamp': snapshot.timestamp,
                        'value': value
                    })
                    break
        
        return trend_data
    
    def get_device_trend(self, device_name: str, metric: str, count: int = 10) -> List[Any]:
        """
        Get trend data for a specific device metric.
        
        Args:
            device_name: Device name (e.g., '0', '1')
            metric: Metric name (e.g., 'total_activity')
            count: Number of recent data points to return
            
        Returns:
            List of metric values over time
        """
        trend_data = []
        recent_history = self.get_history(count)
        
        for snapshot in recent_history:
            device_util = snapshot.device_utilization.get(device_name, {})
            value = device_util.get(metric, 0)
            trend_data.append({
                'timestamp': snapshot.timestamp,
                'value': value
            })
        
        return trend_data
    
    def get_system_trend(self, metric: str, count: int = 10) -> List[Any]:
        """
        Get trend data for system metrics.
        
        Args:
            metric: System metric name (e.g., 'mem_free')
            count: Number of recent data points to return
            
        Returns:
            List of metric values over time
        """
        trend_data = []
        recent_history = self.get_history(count)
        
        for snapshot in recent_history:
            value = snapshot.system_info.get(metric, 0)
            trend_data.append({
                'timestamp': snapshot.timestamp,
                'value': value
            })
        
        return trend_data
    
    def reset_device_counters(self) -> None:
        """Reset device performance counters for fresh readings."""
        self.device_monitor.reset_counters()
    
    def set_max_history_size(self, size: int) -> None:
        """
        Set maximum history size.
        
        Args:
            size: Maximum number of snapshots to keep in history
        """
        self.max_history_size = max(1, size)
        
        # Trim current history if needed
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
