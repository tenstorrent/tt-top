# Tenstorrent Device Monitor - `tt-top` utility

A python utility that shows process execution information on a WH/BH device at runtime.

This project has a data collection component and a UI component, creating a modular and reusable library structure.

## Installation

Clone the GitHub project directly.

```bash
git clone https://github.com/tenstorrent/tt-top
cd tt-top
```

## Usage

### Default
```bash
python tt-top.py
```

### Options
Custom interval (in seconds)
```bash
python tt-top.py -i 5
```

Run with a specific duration (in seconds)
```bash
python tt-top.py -d 30
```

Save history and exit
```bash
python tt-top.py --save
```


## Support

### Bug Reports & Feature Requests
- **GitHub Issues**: Report bugs and request features via [GitHub Issues](https://github.com/tenstorrent/tt-top/issues)
- **Response Time**: The team triages issues weekly, though response times may vary due to scheduling

### Questions & Discussion
- **Documentation Questions**: File as GitHub issues with the "documentation" label
- **Usage Questions**: File as GitHub issues with the "question" label

### Maintenance Status
This is a utility project with infrequent updates on an as-needed basis. We prioritize:
1. Critical bugs affecting core functionality
2. Security issues
3. Compatibility with new Tenstorrent hardware/software releases

## Architecture Overview

## Examples

Library Usage Examples: `library_usage_examples.py`

Demonstrates how to use the library for data collection without UI:

```bash
python library_usage_examples.py
```

### Library Structure (`tenstorrent_lib/`)

The data collection functionality has been extracted into a reusable library with the following modules:

- **`device_monitor.py`** - Handles Tenstorrent device utilization monitoring through PCIe performance counters
- **`process_scanner.py`** - Finds and analyzes processes using Tenstorrent devices
- **`memory_analyzer.py`** - Analyzes Tenstorrent-specific memory usage for processes
- **`data_collector.py`** - Coordinates data collection and provides unified snapshots
- **`utils.py`** - Common utility functions for formatting and system information

### UI Components (`ui/`)

The user interface functionality has been separated into modular components:

- **`terminal_ui.py`** - Basic terminal utilities and formatting
- **`input_handler.py`** - Keyboard input handling for interactive applications
- **`top_like_display.py`** - Top-like display rendering and formatting

### Basic Data Collection

```python
from tenstorrent_lib import DataCollector, find_tenstorrent_processes

# Simple process discovery
processes = find_tenstorrent_processes()
print(f"Found {len(processes)} processes using Tenstorrent devices")

# Complete monitoring snapshot
collector = DataCollector()
snapshot = collector.collect_snapshot()
print(f"Process count: {snapshot.process_count}")
print(f"Total TT memory: {snapshot.memory_summary['total_tt_memory_mb']}MB")
```

### Continuous Monitoring

```python
import time
from tenstorrent_lib import DataCollector

collector = DataCollector()

# Monitor for 60 seconds
for i in range(12):  # 12 iterations * 5 seconds = 60 seconds
    snapshot = collector.collect_snapshot()
    print(f"Snapshot {i+1}: {snapshot.process_count} processes")
    time.sleep(5)

# Save history
collector.save_history_to_file("monitoring_data.json")
```

### Custom UI Development

```python
from tenstorrent_lib import DataCollector
from ui import TerminalUI

collector = DataCollector()
terminal = TerminalUI()

# Create custom display
snapshot = collector.collect_snapshot()
terminal.clear_screen()
print("Custom Tenstorrent Monitor")
print(f"Processes: {snapshot.process_count}")
```

## File Organization

```
tt-top/
├── tenstorrent_lib/          # Data collection library
│   ├── __init__.py
│   ├── device_monitor.py
│   ├── process_scanner.py
│   ├── memory_analyzer.py
│   ├── data_collector.py
│   └── utils.py
├── ui/                       # UI components
│   ├── __init__.py
│   ├── terminal_ui.py
│   ├── input_handler.py
│   └── top_like_display.py
├── tt-top.py            # New main application
├── library_usage_examples.py # Library usage examples
└── README.md                # This file
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Tenstorrent, Inc.