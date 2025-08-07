# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Platform Compatibility Module

Handles platform-specific functionality and provides fallbacks for missing features.
"""

import sys
import os
import termios
import tty
from typing import Optional, Any


class TerminalManager:
    """Manages terminal settings in a cross-platform way."""
    
    def __init__(self):
        self.old_settings: Optional[Any] = None
        self.is_terminal = self._check_if_terminal()
    
    def _check_if_terminal(self) -> bool:
        """Check if we're running in a terminal."""
        try:
            return sys.stdin.isatty() and sys.stdout.isatty()
        except (AttributeError, OSError):
            return False
    
    def setup_raw_mode(self) -> bool:
        """
        Setup terminal for raw input mode.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_terminal:
            return False
        
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            
            # Try tty.cbreak first (preferred method)
            if hasattr(tty, 'cbreak'):
                tty.cbreak(sys.stdin.fileno())
            else:
                # Manual cbreak mode setup
                new_settings = list(self.old_settings)
                new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
                termios.tcsetattr(sys.stdin, termios.TCSANOW, new_settings)
            
            return True
            
        except (termios.error, OSError, AttributeError, ValueError):
            self.old_settings = None
            return False
    
    def restore_terminal(self) -> bool:
        """
        Restore terminal to original settings.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.old_settings:
            return False
        
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            self.old_settings = None
            return True
        except (termios.error, OSError, AttributeError, ValueError):
            return False
    
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return os.name == 'nt'
    
    def is_unix_like(self) -> bool:
        """Check if running on Unix-like system."""
        return os.name == 'posix'
    
    def get_platform_info(self) -> dict:
        """Get platform information."""
        return {
            'os_name': os.name,
            'platform': sys.platform,
            'is_terminal': self.is_terminal,
            'has_termios': 'termios' in sys.modules,
            'has_tty_cbreak': hasattr(tty, 'cbreak') if 'tty' in sys.modules else False
        }


def safe_import(module_name: str, fallback=None):
    """
    Safely import a module with fallback.
    
    Args:
        module_name: Name of module to import
        fallback: Fallback value if import fails
        
    Returns:
        Imported module or fallback value
    """
    try:
        return __import__(module_name)
    except ImportError:
        return fallback


def get_terminal_size_safe() -> tuple:
    """
    Get terminal size with fallbacks.
    
    Returns:
        Tuple of (width, height)
    """
    try:
        import shutil
        return shutil.get_terminal_size()
    except (ImportError, OSError):
        try:
            # Fallback using os.get_terminal_size
            size = os.get_terminal_size()
            return size.columns, size.lines
        except (AttributeError, OSError):
            # Final fallback
            return 80, 24


def clear_screen_safe():
    """Clear screen in a cross-platform way."""
    try:
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix-like
            os.system('clear')
    except OSError:
        # Fallback using ANSI escape codes
        print('\033[2J\033[H', end='')


def check_system_compatibility() -> dict:
    """
    Check system compatibility for the monitoring application.
    
    Returns:
        Dictionary with compatibility information
    """
    terminal_mgr = TerminalManager()
    
    compatibility = {
        'platform': terminal_mgr.get_platform_info(),
        'terminal_support': terminal_mgr.is_terminal,
        'raw_mode_support': terminal_mgr.setup_raw_mode(),
        'proc_filesystem': os.path.exists('/proc'),
        'sysfs_support': os.path.exists('/sys'),
        'tenstorrent_devices': os.path.exists('/dev/tenstorrent'),
        'lsof_available': False  # Note: lsof available but not used
    }
    
    # Restore terminal if we tested raw mode
    terminal_mgr.restore_terminal()
    
    # Check for lsof (for informational purposes only)
    try:
        import subprocess
        subprocess.run(['lsof', '--version'], 
                      capture_output=True, check=True)
        compatibility['lsof_available'] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return compatibility


def print_compatibility_report():
    """Print a detailed compatibility report."""
    print("Platform Compatibility Report")
    print("=" * 40)
    
    compat = check_system_compatibility()
    
    print(f"Platform: {compat['platform']['platform']}")
    print(f"OS Name: {compat['platform']['os_name']}")
    print(f"Terminal Support: {'✓' if compat['terminal_support'] else '✗'}")
    print(f"Raw Mode Support: {'✓' if compat['raw_mode_support'] else '✗'}")
    print(f"Proc Filesystem: {'✓' if compat['proc_filesystem'] else '✗'}")
    print(f"Sysfs Support: {'✓' if compat['sysfs_support'] else '✗'}")
    print(f"Tenstorrent Devices: {'✓' if compat['tenstorrent_devices'] else '✗'}")
    print(f"lsof Available: {'✓' if compat['lsof_available'] else '✗'} (not used - /proc scanning preferred)")
    
    # Recommendations
    print("\nRecommendations:")
    if not compat['terminal_support']:
        print("- Run in a proper terminal for interactive features")
    if not compat['raw_mode_support']:
        print("- Interactive keyboard input may not work properly")
    if not compat['proc_filesystem']:
        print("- Process monitoring will not work (Linux/Unix required)")
    if not compat['tenstorrent_devices']:
        print("- No Tenstorrent devices found")


if __name__ == "__main__":
    print_compatibility_report()
