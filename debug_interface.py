import logging
import os
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

class DebugInterface:
    def __init__(self, root):
        self.root = root
        self.debug_window = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configures logging for the application."""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Single log file that gets overwritten
        log_file = os.path.join(logs_dir, 'airtracker.log')

        # Configure root logger with file handler only
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='w')  # 'w' mode overwrites the file
            ]
        )

        # Configure detailed debug logging
        debug_logger = logging.getLogger('comtypes')
        debug_logger.setLevel(logging.DEBUG)
        debug_logger.propagate = True

        # Configure PIL debug logging
        pil_logger = logging.getLogger('PIL')
        pil_logger.setLevel(logging.DEBUG)
        pil_logger.propagate = True

        # Disable logging to console
        logging.getLogger().handlers = [h for h in logging.getLogger().handlers if not isinstance(h, logging.StreamHandler)]

        self.logger = logging.getLogger('AirTracker')
        
    def create_debug_window(self):
        """Creates a debugging console window."""
        if self.debug_window:
            return
            
        self.debug_window = tk.Toplevel(self.root)
        self.debug_window.title("Debug Console")
        self.debug_window.geometry("800x400")
        
        # Create text area for logs
        self.log_text = scrolledtext.ScrolledText(
            self.debug_window,
            state='disabled',
            width=100,
            height=25
        )
        self.log_text.pack(pady=10)
        
        # Add handler to display logs in the window
        text_handler = TextHandler(self.log_text)
        self.logger.addHandler(text_handler)
        
    def log(self, message, level='info'):
        """Logs a message with specified level."""
        if level.lower() == 'debug':
            self.logger.debug(message)
        elif level.lower() == 'warning':
            self.logger.warning(message)
        elif level.lower() == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)

class TextHandler(logging.Handler):
    """Custom handler to display logs in Tkinter text widget."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.configure(state='disabled')
        self.text_widget.yview(tk.END)