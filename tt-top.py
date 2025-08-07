# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
"""
Tenstorrent Top-Like Monitor - Main Application

A top-like continuous monitoring application for Tenstorrent devices using the
separated library and UI components.
"""

import time
import signal
import argparse
from typing import Optional
from tenstorrent_lib import DataCollector
from ui import TopLikeDisplay, InputHandler


class TenstorrentTopApp:
    """Main application class for the Tenstorrent top-like monitor."""
    
    def __init__(self, interval: int = 3):
        self.interval = interval
        self.data_collector = DataCollector()
        self.display = TopLikeDisplay()
        self.input_handler = InputHandler()
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Setup input callbacks
        self.setup_input_callbacks()
    
    def setup_input_callbacks(self) -> None:
        """Setup keyboard input callbacks."""
        self.input_handler.register_callback('q', self.quit_app)
        self.input_handler.register_callback('h', self.toggle_help)
        self.input_handler.register_callback('?', self.toggle_help)
        self.input_handler.register_callback('c', lambda: self.set_sort('cpu_time'))
        self.input_handler.register_callback('m', lambda: self.set_sort('memory'))
        self.input_handler.register_callback('T', lambda: self.set_sort('tt_memory'))
        self.input_handler.register_callback('p', lambda: self.set_sort('pid'))
        self.input_handler.register_callback('t', lambda: self.set_sort('start_time'))
        self.input_handler.register_callback('a', lambda: self.set_sort('activity'))
        self.input_handler.register_callback('r', self.reverse_sort)
        self.input_handler.register_callback(' ', self.force_refresh)
    
    def quit_app(self) -> bool:
        """Quit the application."""
        self.running = False
        return False
    
    def toggle_help(self) -> bool:
        """Toggle help display."""
        self.display.toggle_help()
        return True
    
    def set_sort(self, column: str) -> bool:
        """Set sort column."""
        self.display.set_sort_options(column)
        return True
    
    def reverse_sort(self) -> bool:
        """Reverse sort order."""
        self.display.set_sort_options(self.display.sort_column, 
                                     not self.display.sort_reverse)
        return True
    
    def force_refresh(self) -> bool:
        """Force a refresh."""
        return True
    
    def signal_handler(self, signum, frame) -> None:
        """Handle termination signals."""
        self.running = False
    
    def run(self, duration_minutes: Optional[int] = None, 
            save_on_exit: bool = True) -> None:
        """
        Run the monitoring application.
        
        Args:
            duration_minutes: Duration to run in minutes (None for unlimited)
            save_on_exit: Whether to save history on exit
        """
        try:
            print("Starting Tenstorrent TOP-like monitor...")
            print("Press 'h' for help, 'q' to quit")
            time.sleep(2)
            
            # Setup terminal
            self.input_handler.setup_terminal()
            
            start_time = time.time()
            
            while self.running:
                # Collect data
                snapshot = self.data_collector.collect_snapshot()
                
                # Display data
                self.display.render_snapshot(snapshot)
                
                # Check duration limit
                if duration_minutes:
                    elapsed_minutes = (time.time() - start_time) / 60
                    if elapsed_minutes >= duration_minutes:
                        break
                
                # Handle input and wait
                self.handle_input_loop()
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup(save_on_exit)
    
    def handle_input_loop(self) -> None:
        """Handle input for the specified interval."""
        for _ in range(int(self.interval * 10)):  # Check input 10 times per second
            if not self.running:
                break
                
            char = self.input_handler.check_for_input()
            if char:
                # Special handling when help is displayed
                if self.display.show_help:
                    # Any key press exits help mode
                    self.display.toggle_help()
                else:
                    # Normal input handling
                    if not self.input_handler.handle_input(char):
                        self.running = False
                        break
            
            time.sleep(0.1)
    
    def cleanup(self, save_on_exit: bool) -> None:
        """Clean up resources."""
        self.input_handler.restore_terminal()
        self.display.terminal.clear_screen()
        self.display.terminal.show_cursor()
        
        print("Tenstorrent monitor stopped")
        
        if save_on_exit and self.data_collector.history:
            filename = f"tenstorrent_monitor_history_{int(time.time())}.json"
            if self.data_collector.save_history_to_file(filename):
                print(f"History saved to {filename}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='TOP-like Tenstorrent Device Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run with default 3-second interval
  %(prog)s -i 5               # Run with 5-second interval
  %(prog)s -d 30              # Run for 30 minutes
  %(prog)s --save             # Save history on exit
        """
    )
    
    parser.add_argument('-i', '--interval', type=int, default=3,
                       help='Monitoring interval in seconds (default: 3)')
    parser.add_argument('-d', '--duration', type=int,
                       help='Duration in minutes (default: unlimited)')
    parser.add_argument('--save', action='store_true',
                       help='Save history on exit (default: no save)')
    parser.add_argument('--version', action='version', version='tt-top 2.0.0')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.interval < 1:
        parser.error("Interval must be at least 1 second")
    if args.duration is not None and args.duration < 1:
        parser.error("Duration must be at least 1 minute")
    
    # Create and run application
    app = TenstorrentTopApp(interval=args.interval)
    app.run(duration_minutes=args.duration, save_on_exit=args.save)


if __name__ == "__main__":
    main()
