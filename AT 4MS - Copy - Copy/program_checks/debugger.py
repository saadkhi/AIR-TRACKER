import logging
import os
import tempfile
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

class DebugInterface:
    def __init__(self, root):
        self.root = root
        self.debug_window = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configures logging for the application with daily log files in temp directory."""
        # Create logs directory in system temp folder
        self.logs_dir = os.path.join(tempfile.gettempdir(), 'airtracker_logs')
        os.makedirs(self.logs_dir, exist_ok=True)

        # Create daily log file with timestamp
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.logs_dir, f'airtracker_{current_date}.log')

        # Configure root logger with file handler
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a')  # 'a' mode appends to the file
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
        
        # Log initial message with log file location
        self.logger.info(f"Log file created at: {log_file}")
        
    def get_logs_directory(self):
        """Returns the path to the temporary logs directory."""
        return self.logs_dir

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