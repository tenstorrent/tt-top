# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Terminal UI Module

Basic terminal utilities for the Tenstorrent monitor interface.
"""

import os
import shutil
from typing import Tuple


class TerminalUI:
    """Basic terminal UI utilities."""
    
    def __init__(self):
        self.width = 80
        self.height = 24
        self.update_size()
    
    def update_size(self) -> None:
        """Update terminal size."""
        try:
            self.width, self.height = shutil.get_terminal_size()
        except (OSError, AttributeError):
            self.width, self.height = 80, 24
    
    def get_size(self) -> Tuple[int, int]:
        """
        Get current terminal size.
        
        Returns:
            Tuple of (width, height)
        """
        self.update_size()
        return self.width, self.height
    
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('clear')
    
    def move_cursor(self, row: int, col: int) -> None:
        """
        Move cursor to specific position.
        
        Args:
            row: Row number (1-based)
            col: Column number (1-based)
        """
        print(f"\033[{row};{col}H", end='')
    
    def hide_cursor(self) -> None:
        """Hide the cursor."""
        print("\033[?25l", end='')
    
    def show_cursor(self) -> None:
        """Show the cursor."""
        print("\033[?25h", end='')
    
    def set_color(self, color_code: str) -> None:
        """
        Set text color using ANSI codes.
        
        Args:
            color_code: ANSI color code (e.g., '31' for red)
        """
        print(f"\033[{color_code}m", end='')
    
    def reset_color(self) -> None:
        """Reset text color to default."""
        print("\033[0m", end='')
    
    def bold_text(self, text: str) -> str:
        """
        Make text bold.
        
        Args:
            text: Text to make bold
            
        Returns:
            Bold formatted text
        """
        return f"\033[1m{text}\033[0m"
    
    def colored_text(self, text: str, color_code: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to color
            color_code: ANSI color code
            
        Returns:
            Colored text
        """
        return f"\033[{color_code}m{text}\033[0m"
    
    def truncate_text(self, text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to fit within max length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length including suffix
            suffix: Suffix to append if text is truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        if max_length <= len(suffix):
            return suffix[:max_length]
        
        return text[:max_length - len(suffix)] + suffix
    
    def center_text(self, text: str, width: int) -> str:
        """
        Center text within given width.
        
        Args:
            text: Text to center
            width: Total width
            
        Returns:
            Centered text
        """
        if len(text) >= width:
            return text[:width]
        
        padding = width - len(text)
        left_pad = padding // 2
        right_pad = padding - left_pad
        
        return ' ' * left_pad + text + ' ' * right_pad
    
    def format_columns(self, columns: list, widths: list, separator: str = " ") -> str:
        """
        Format text in columns.
        
        Args:
            columns: List of column texts
            widths: List of column widths
            separator: Separator between columns
            
        Returns:
            Formatted row text
        """
        formatted_cols = []
        
        for i, (text, width) in enumerate(zip(columns, widths)):
            if i < len(columns) - 1:  # Not the last column
                formatted_cols.append(f"{str(text):<{width}}")
            else:  # Last column, no width restriction
                formatted_cols.append(str(text))
        
        return separator.join(formatted_cols)
    
    @staticmethod
    def get_color_codes() -> dict:
        """
        Get dictionary of common ANSI color codes.
        
        Returns:
            Dictionary mapping color names to ANSI codes
        """
        return {
            'reset': '0',
            'bold': '1',
            'dim': '2',
            'underline': '4',
            'blink': '5',
            'reverse': '7',
            'black': '30',
            'red': '31',
            'green': '32',
            'yellow': '33',
            'blue': '34',
            'magenta': '35',
            'cyan': '36',
            'white': '37',
            'bg_black': '40',
            'bg_red': '41',
            'bg_green': '42',
            'bg_yellow': '43',
            'bg_blue': '44',
            'bg_magenta': '45',
            'bg_cyan': '46',
            'bg_white': '47'
        }
