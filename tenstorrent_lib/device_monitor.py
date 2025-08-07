# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Device Monitor Module

Handles Tenstorrent device utilization monitoring through PCIe performance counters.
"""

import os
from typing import Dict, Any, Optional


class TenstorrentDeviceMonitor:
    """Monitor Tenstorrent device utilization using PCIe performance counters."""
    
    def __init__(self):
        self.previous_counters = {}
        self.sysfs_base = "/sys/class/tenstorrent"
        
    def get_device_utilization(self, device_path: str) -> Dict[str, Any]:
        """
        Get device utilization from PCIe performance counters.
        
        Args:
            device_path: Path to the device (e.g., /dev/tenstorrent/0)
            
        Returns:
            Dictionary containing utilization metrics or error information
        """
        try:
            # Extract device number from path like /dev/tenstorrent/0
            device_num = os.path.basename(device_path)
            sysfs_path = f"{self.sysfs_base}/tenstorrent!{device_num}/pcie_perf_counters"
            
            if not os.path.exists(sysfs_path):
                return {"error": "sysfs not available"}
            
            counters = {}
            counter_files = [
                "mst_posted_wr_data_word_sent0",
                "mst_posted_wr_data_word_sent1", 
                "mst_rd_data_word_received0",
                "mst_rd_data_word_received1",
                "slv_posted_wr_data_word_received0",
                "slv_posted_wr_data_word_received1",
                "slv_rd_data_word_sent0",
                "slv_rd_data_word_sent1"
            ]
            
            # Read current counter values
            for counter in counter_files:
                counter_path = os.path.join(sysfs_path, counter)
                try:
                    with open(counter_path, 'r') as f:
                        counters[counter] = int(f.read().strip())
                except (OSError, ValueError):
                    counters[counter] = 0
            
            # Calculate deltas if we have previous readings
            device_key = f"device_{device_num}"
            if device_key in self.previous_counters:
                prev = self.previous_counters[device_key]
                deltas = {k: counters[k] - prev.get(k, 0) for k in counters}
                
                # Calculate total activity (sum of all deltas)
                total_activity = sum(abs(v) for v in deltas.values())
                utilization = {
                    "total_activity": total_activity,
                    "write_activity": deltas.get("mst_posted_wr_data_word_sent0", 0) + 
                                    deltas.get("mst_posted_wr_data_word_sent1", 0),
                    "read_activity": deltas.get("mst_rd_data_word_received0", 0) + 
                                   deltas.get("mst_rd_data_word_received1", 0),
                    "deltas": deltas,
                    "raw_counters": counters.copy()
                }
            else:
                utilization = {
                    "total_activity": "N/A (first reading)",
                    "write_activity": "N/A",
                    "read_activity": "N/A",
                    "deltas": {},
                    "raw_counters": counters.copy()
                }
            
            # Store current counters for next comparison
            self.previous_counters[device_key] = counters.copy()
            
            return utilization
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_devices(self) -> list:
        """Get list of all available Tenstorrent devices."""
        devices = []
        if os.path.exists("/dev/tenstorrent"):
            for device_name in os.listdir("/dev/tenstorrent"):
                device_path = f"/dev/tenstorrent/{device_name}"
                if os.path.exists(device_path):
                    devices.append(device_path)
        return sorted(devices)
    
    def get_all_device_utilization(self) -> Dict[str, Dict[str, Any]]:
        """Get utilization for all available devices."""
        device_utils = {}
        for device_path in self.get_all_devices():
            device_name = os.path.basename(device_path)
            device_utils[device_name] = self.get_device_utilization(device_path)
        return device_utils
    
    def reset_counters(self):
        """Reset stored counter values for fresh readings."""
        self.previous_counters.clear()
