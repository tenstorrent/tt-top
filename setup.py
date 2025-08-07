# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Setup Script for Tenstorrent Monitor

This script helps set up the Python path and dependencies for the refactored
Tenstorrent monitoring system.
"""

import os
import sys
import subprocess
from pathlib import Path


def add_to_python_path():
    """Add the current directory to Python path for imports."""
    current_dir = Path(__file__).parent.absolute()
    
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
        print(f"Added {current_dir} to Python path")
    
    return current_dir


def check_dependencies():
    """Check if required system dependencies are available."""
    dependencies = {
        'lsof': 'lsof command for process scanning',
        '/proc': 'procfs for system information',
        '/sys/class/tenstorrent': 'Tenstorrent sysfs interface'
    }
    
    print("Checking dependencies...")
    
    for dep, description in dependencies.items():
        if dep.startswith('/'):
            # Check filesystem path
            if os.path.exists(dep):
                print(f"✓ {dep} - {description}")
            else:
                print(f"⚠ {dep} - {description} (not found)")
        else:
            # Check command availability
            try:
                subprocess.run([dep, '--version'], 
                             capture_output=True, check=True)
                print(f"✓ {dep} - {description}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"⚠ {dep} - {description} (not found)")


def create_launcher_script(install_dir):
    """Create a launcher script for the application."""
    launcher_content = f"""#!/bin/bash
# Tenstorrent Top Launcher Script

# Set Python path
export PYTHONPATH="{install_dir}:$PYTHONPATH"

# Run the application
python3 "{install_dir}/tt-top.py" "$@"
"""
    
    launcher_path = install_dir / "tt-top"
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    # Make executable
    os.chmod(launcher_path, 0o755)
    print(f"Created launcher script: {launcher_path}")
    print("You can run it with: ./tt-top")


def run_tests():
    """Run basic tests to verify the setup."""
    print("\nRunning basic tests...")
    
    try:
        # Test library imports
        print("Testing library imports...")
        from tenstorrent_lib import DataCollector, find_tenstorrent_processes
        print("✓ tenstorrent_lib imports successful")
        
        from ui import TerminalUI, TopLikeDisplay, InputHandler
        print("✓ ui components import successful")
        
        # Test basic functionality
        print("Testing basic functionality...")
        processes = find_tenstorrent_processes()
        print(f"✓ Process scanning works (found {len(processes)} processes)")
        
        collector = DataCollector()
        snapshot = collector.collect_snapshot()
        print(f"✓ Data collection works (snapshot with {snapshot.process_count} processes)")
        
        print("✓ All tests passed!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False
    
    return True


def show_usage_examples():
    """Show usage examples."""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    examples = [
        ("Run the top-like monitor:", "python3 tt-top.py"),
        ("Run with 5-second interval:", "python3 tt-top.py -i 5"),
        ("Run for 30 minutes:", "python3 tt-top.py -d 30"),
        ("Run library examples:", "python3 library_usage_examples.py"),
        ("Use the launcher script:", "./tt-top"),
    ]
    
    for description, command in examples:
        print(f"\n{description}")
        print(f"  {command}")
    
    print(f"\nFor more information, see README_REFACTORED.md")


def main():
    """Main setup function."""
    print("Tenstorrent Monitor Setup")
    print("="*40)
    
    # Add to Python path
    install_dir = add_to_python_path()
    
    # Check dependencies
    check_dependencies()
    
    # Create launcher script
    create_launcher_script(install_dir)
    
    # Run tests
    if run_tests():
        print("\n✓ Setup completed successfully!")
        show_usage_examples()
    else:
        print("\n✗ Setup completed with errors. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
