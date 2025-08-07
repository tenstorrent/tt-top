# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Simple Library Usage Example

Demonstrates how to use the Tenstorrent monitoring library for data collection
without the UI components.
"""

import time
import json
from tenstorrent_lib import DataCollector, find_tenstorrent_processes


def simple_monitoring_example():
    """Example of simple monitoring using the library."""
    print("=== Simple Tenstorrent Monitoring Example ===\n")
    
    # Create data collector
    collector = DataCollector()
    
    # Collect a single snapshot
    print("Collecting snapshot...")
    snapshot = collector.collect_snapshot()
    
    print(f"Timestamp: {snapshot.timestamp}")
    print(f"Process count: {snapshot.process_count}")
    print(f"Devices found: {len(snapshot.device_utilization)}")
    
    # Show process information
    if snapshot.processes:
        print("\nProcesses using Tenstorrent devices:")
        for proc in snapshot.processes:
            tt_mem = proc.get('tt_memory', {}).get('total_mapped_mb', 0)
            print(f"  PID {proc['pid']}: {proc['name']} (TT Memory: {tt_mem:.1f}MB)")
    else:
        print("\nNo processes using Tenstorrent devices found")
    
    # Show device utilization
    print("\nDevice utilization:")
    for device, util in snapshot.device_utilization.items():
        if 'error' in util:
            print(f"  {device}: Error - {util['error']}")
        else:
            print(f"  {device}: Activity={util.get('total_activity', 'N/A')}")


def continuous_monitoring_example():
    """Example of continuous monitoring for a short period."""
    print("\n=== Continuous Monitoring Example ===\n")
    
    collector = DataCollector()
    duration = 10  # Monitor for 10 seconds
    interval = 2   # Every 2 seconds
    
    print(f"Monitoring for {duration} seconds (interval: {interval}s)...")
    
    start_time = time.time()
    while time.time() - start_time < duration:
        snapshot = collector.collect_snapshot()
        
        elapsed = time.time() - start_time
        print(f"[{elapsed:.1f}s] Processes: {snapshot.process_count}, "
              f"TT Memory: {snapshot.memory_summary.get('total_tt_memory_mb', 0):.1f}MB")
        
        time.sleep(interval)
    
    # Show history
    print(f"\nCollected {len(collector.history)} snapshots")
    
    # Save history
    filename = "example_history.json"
    if collector.save_history_to_file(filename):
        print(f"History saved to {filename}")


def process_analysis_example():
    """Example of detailed process analysis."""
    print("\n=== Process Analysis Example ===\n")
    
    # Use the standalone function
    processes = find_tenstorrent_processes()
    
    if not processes:
        print("No Tenstorrent processes found for analysis")
        return
    
    print(f"Found {len(processes)} processes using Tenstorrent devices\n")
    
    for proc in processes:
        print(f"Process: {proc['name']} (PID: {proc['pid']})")
        print(f"  User: {proc['username']}")
        print(f"  Command: {proc['cmdline'][:60]}...")
        print(f"  Start time: {proc['start_time']}")
        print(f"  CPU time: {proc['cpu_time']}")
        print(f"  Device: {proc.get('device', 'unknown')}")
        
        # Memory details
        mem = proc.get('memory', {})
        print(f"  System memory (RSS): {mem.get('VmRSS', 'unknown')}")
        
        # Tenstorrent memory details
        tt_mem = proc.get('tt_memory', {})
        if tt_mem.get('mapping_count', 0) > 0:
            print(f"  TT Memory: {tt_mem['total_mapped_mb']:.1f}MB "
                  f"({tt_mem['mapping_count']} mappings)")
            print(f"    Device mappings: {tt_mem['device_mappings_mb']:.1f}MB")
            print(f"    DMA mappings: {tt_mem['dma_mappings_mb']:.1f}MB")
        else:
            print("  TT Memory: No mappings found")
        
        print()


def data_export_example():
    """Example of data export functionality."""
    print("=== Data Export Example ===\n")
    
    collector = DataCollector()
    snapshot = collector.collect_snapshot()
    
    # Export as JSON
    json_data = snapshot.to_json()
    print("JSON export sample (first 200 chars):")
    print(json_data[:200] + "...")
    
    # Save to file
    with open("snapshot_export.json", "w") as f:
        f.write(json_data)
    print("\nSnapshot exported to snapshot_export.json")
    
    # Extract specific data
    print(f"\nSystem info extract:")
    print(f"  Uptime: {snapshot.system_info['uptime']}")
    print(f"  Load average: {snapshot.system_info['load_avg']}")
    print(f"  Memory: {snapshot.system_info['mem_total']//1024//1024}GB total")


def main():
    """Run all examples."""
    try:
        simple_monitoring_example()
        continuous_monitoring_example()
        process_analysis_example()
        data_export_example()
        
        print("\n=== All examples completed ===")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    main()
