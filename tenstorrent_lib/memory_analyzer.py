# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Memory Analyzer Module

Handles analysis of Tenstorrent-specific memory usage for processes.
"""

import os
from pathlib import Path
from typing import Dict, Any, List


class MemoryAnalyzer:
    """Analyzer for Tenstorrent device memory usage."""
    
    def get_tenstorrent_memory_usage(self, pid: str) -> Dict[str, Any]:
        """
        Get Tenstorrent-specific memory usage for a process.
        
        Args:
            pid: Process ID as string
            
        Returns:
            Dictionary containing Tenstorrent memory usage information
        """
        try:
            proc_dir = Path(f"/proc/{pid}")
            tt_memory = {
                'device_mappings': 0,
                'dma_mappings': 0, 
                'total_mapped': 0,
                'mapping_count': 0,
                'mapping_details': []
            }
            
            # Parse memory mappings from /proc/pid/maps
            maps_file = proc_dir / "maps"
            if maps_file.exists():
                maps_content = maps_file.read_text()
                
                for line in maps_content.splitlines():
                    # Look for Tenstorrent device mappings
                    if 'tenstorrent' in line.lower() or '/dev/tenstorrent' in line:
                        parts = line.split()
                        if len(parts) >= 6:
                            # Parse address range
                            addr_range = parts[0]
                            start_addr, end_addr = addr_range.split('-')
                            size = int(end_addr, 16) - int(start_addr, 16)
                            
                            permissions = parts[1]
                            offset = parts[2]
                            device_file = parts[5] if len(parts) > 5 else "unknown"
                            
                            mapping_info = {
                                'start': start_addr,
                                'end': end_addr,
                                'size': size,
                                'permissions': permissions,
                                'offset': offset,
                                'device': device_file
                            }
                            
                            tt_memory['mapping_details'].append(mapping_info)
                            tt_memory['mapping_count'] += 1
                            tt_memory['total_mapped'] += size
                            
                            # Categorize mapping type
                            if 'r' in permissions and 'w' in permissions:
                                tt_memory['device_mappings'] += size
                            elif 'r' in permissions:
                                tt_memory['dma_mappings'] += size
            
            # Check for additional Tenstorrent-related memory in smaps
            self._analyze_smaps(proc_dir, tt_memory)
            
            # Convert bytes to more readable units
            tt_memory['device_mappings_mb'] = tt_memory['device_mappings'] / (1024 * 1024)
            tt_memory['dma_mappings_mb'] = tt_memory['dma_mappings'] / (1024 * 1024)
            tt_memory['total_mapped_mb'] = tt_memory['total_mapped'] / (1024 * 1024)
            
            return tt_memory
            
        except (OSError, ValueError):
            return {
                'device_mappings': 0,
                'dma_mappings': 0,
                'total_mapped': 0,
                'mapping_count': 0,
                'device_mappings_mb': 0,
                'dma_mappings_mb': 0,
                'total_mapped_mb': 0,
                'mapping_details': []
            }
    
    def _analyze_smaps(self, proc_dir: Path, tt_memory: Dict[str, Any]) -> None:
        """Analyze smaps file for detailed Tenstorrent memory information."""
        smaps_file = proc_dir / "smaps"
        if not smaps_file.exists():
            return
            
        try:
            smaps_content = smaps_file.read_text()
            current_mapping = None
            
            for line in smaps_content.splitlines():
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    # New mapping header
                    if 'tenstorrent' in line.lower():
                        current_mapping = {'rss': 0, 'pss': 0, 'shared_clean': 0, 'shared_dirty': 0}
                elif current_mapping is not None:
                    # Memory details for Tenstorrent mapping
                    if line.startswith('Rss:'):
                        current_mapping['rss'] = int(line.split()[1])
                    elif line.startswith('Pss:'):
                        current_mapping['pss'] = int(line.split()[1])
                    elif line.startswith('Shared_Clean:'):
                        current_mapping['shared_clean'] = int(line.split()[1])
                    elif line.startswith('Shared_Dirty:'):
                        current_mapping['shared_dirty'] = int(line.split()[1])
                        # End of this mapping's details
                        tt_memory['rss_kb'] = tt_memory.get('rss_kb', 0) + current_mapping['rss']
                        tt_memory['pss_kb'] = tt_memory.get('pss_kb', 0) + current_mapping['pss']
                        current_mapping = None
        except (OSError, ValueError):
            pass
    
    def get_process_memory_summary(self, processes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary of memory usage across all processes.
        
        Args:
            processes: List of process dictionaries
            
        Returns:
            Dictionary containing memory usage summary
        """
        summary = {
            'total_system_memory_kb': 0,
            'total_tt_memory_mb': 0,
            'total_tt_mappings': 0,
            'total_processes': len(processes),
            'top_memory_users': []
        }
        
        # Calculate totals
        for proc in processes:
            # System memory
            if proc['memory'].get('VmRSS'):
                try:
                    rss_kb = int(proc['memory']['VmRSS'].split()[0])
                    summary['total_system_memory_kb'] += rss_kb
                except (ValueError, IndexError):
                    pass
            
            # Tenstorrent memory
            tt_mem = proc.get('tt_memory', {})
            summary['total_tt_memory_mb'] += tt_mem.get('total_mapped_mb', 0)
            summary['total_tt_mappings'] += tt_mem.get('mapping_count', 0)
        
        # Find top memory users
        sorted_by_tt_mem = sorted(
            processes, 
            key=lambda p: p.get('tt_memory', {}).get('total_mapped_mb', 0), 
            reverse=True
        )
        
        summary['top_memory_users'] = [
            {
                'pid': proc['pid'],
                'name': proc['name'],
                'tt_memory_mb': proc.get('tt_memory', {}).get('total_mapped_mb', 0),
                'mapping_count': proc.get('tt_memory', {}).get('mapping_count', 0)
            }
            for proc in sorted_by_tt_mem[:5]  # Top 5
            if proc.get('tt_memory', {}).get('total_mapped_mb', 0) > 0
        ]
        
        return summary
