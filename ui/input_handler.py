# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Input Handler Module

Handles keyboard input for the top-like interface.
"""

import sys
import select
from typing import Optional, Callable

# Try to import the platform compatibility module
try:
    from tenstorrent_lib.platform_compat import TerminalManager
    COMPAT_AVAILABLE = True
except ImportError:
    # Fallback imports
    import termios
    import tty
    COMPAT_AVAILABLE = False


class InputHandler:
    """Handles keyboard input for interactive terminal applications."""
    
    def __init__(self):
        if COMPAT_AVAILABLE:
            self.terminal_manager = TerminalManager()
            self.old_settings = None
        else:
            self.terminal_manager = None
            self.old_settings = None
        self.input_callbacks = {}
        
    def setup_terminal(self) -> None:
        """Setup terminal for non-blocking input."""
        if COMPAT_AVAILABLE and self.terminal_manager:
            # Use the platform compatibility module
            self.terminal_manager.setup_raw_mode()
        else:
            # Fallback implementation
            try:
                self.old_settings = termios.tcgetattr(sys.stdin)
                if hasattr(tty, 'cbreak'):
                    tty.cbreak(sys.stdin.fileno())
                else:
                    # Fallback for systems without tty.cbreak
                    new_settings = termios.tcgetattr(sys.stdin)
                    new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
                    termios.tcsetattr(sys.stdin, termios.TCSANOW, new_settings)
            except (termios.error, OSError, AttributeError):
                pass  # Fallback for non-terminal environments
    
    def restore_terminal(self) -> None:
        """Restore terminal settings."""
        if COMPAT_AVAILABLE and self.terminal_manager:
            # Use the platform compatibility module
            self.terminal_manager.restore_terminal()
        else:
            # Fallback implementation
            if self.old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                except (termios.error, OSError, AttributeError):
                    pass
    
    def check_for_input(self) -> Optional[str]:
        """
        Check for keyboard input without blocking.
        
        Returns:
            Character pressed or None if no input
        """
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            try:
                char = sys.stdin.read(1)
                return char
            except (OSError, IOError):
                return None
        return None
    
    def register_callback(self, key: str, callback: Callable[[], bool]) -> None:
        """
        Register a callback for a specific key.
        
        Args:
            key: Key character to bind
            callback: Function to call when key is pressed, should return True to continue or False to quit
        """
        self.input_callbacks[key] = callback
    
    def handle_input(self, char: str) -> bool:
        """
        Handle keyboard input using registered callbacks.
        
        Args:
            char: Character that was pressed
            
        Returns:
            True to continue, False to quit
        """
        if char in self.input_callbacks:
            return self.input_callbacks[char]()
        return True  # Continue by default
    
    def get_default_bindings(self) -> dict:
        """
        Get default key bindings for top-like interface.
        
        Returns:
            Dictionary of default key bindings
        """
        return {
            'q': 'Quit',
            'h': 'Show/hide help',
            '?': 'Show/hide help',
            'c': 'Sort by CPU time',
            'm': 'Sort by system memory',
            'T': 'Sort by Tenstorrent memory',
            'p': 'Sort by PID',
            't': 'Sort by start time',
            'a': 'Sort by device activity',
            'r': 'Reverse sort order',
            ' ': 'Force refresh'
        }
