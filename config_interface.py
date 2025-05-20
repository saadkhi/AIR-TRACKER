import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, Tk

DEFAULT_CONFIG = {
    "gestures": {
    "next_slide": [0, 0, 0, 0, 1],
    "prev_slide": [1, 0, 0, 0, 0],
    "toggle_video": [1, 1, 0, 0, 0],
    "toggle_canvas": [0, 1, 0, 0, 1],
    "drawing_mode": [0, 1, 0, 0, 0],
    "pointer_mode": [0, 1, 1, 0, 0]
},
"cooldowns": {
    "slide_navigation": 800,
    "video_toggle": 800,
    "enter_key": 300,
    "zoom_controls": 500,
    "canvas_toggle": 1000,
    "close_app": 1000
},
    "gesture_limits": {
        "max_attempts": 5,  # Max wrong gestures before cooldown
        "cooldown_period": 3000,  # Cooldown period in milliseconds
        "reset_interval": 5000  # Time to reset wrong gesture counter
    },
    "canvas": {
        "default_color": "black",
        "default_tool": "pen",
        "opacity": 0.8
    },
    "camera": {
        "width": 300,
        "height": 200,
        "device_index": 0
    }
}
class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Loads configuration from file or creates default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_CONFIG
        return DEFAULT_CONFIG
        
    def save_config(self):
        """Saves current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except:
            return False
            
    def get(self, key, default=None):
        """Gets a configuration value."""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except:
            return default
            
    def set(self, key, value):
        """Sets a configuration value."""
        keys = key.split('.')
        current = self.config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

class ConfigWindow:
    """GUI for configuration settings."""
    
    def __init__(self, root, config_manager):
        self.root = root
        self.config = config_manager
        self.window = None
        
    def show(self):
        """Displays the configuration window."""
        if self.window:
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.root)
        self.window.title("Configuration Settings")
        
        # Create notebook for different sections
        notebook = ttk.Notebook(self.window)
        
        # Gestures Tab
        gestures_frame = ttk.Frame(notebook)
        self._setup_gestures_tab(gestures_frame)
        notebook.add(gestures_frame, text="Gestures")
        
        # Canvas Tab
        canvas_frame = ttk.Frame(notebook)
        self._setup_canvas_tab(canvas_frame)
        notebook.add(canvas_frame, text="Canvas")
        
        # Camera Tab
        camera_frame = ttk.Frame(notebook)
        self._setup_camera_tab(camera_frame)
        notebook.add(camera_frame, text="Camera")
        
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Save button
        save_btn = ttk.Button(
            self.window,
            text="Save Configuration",
            command=self._save_config
        )
        save_btn.pack(pady=10)
        
    def _setup_gestures_tab(self, frame):
        """Sets up the gestures configuration tab."""
        # Implementation for gesture configuration UI
        pass
        
    def _setup_canvas_tab(self, frame):
        """Sets up the canvas configuration tab."""
        # Implementation for canvas configuration UI
        pass
        
    def _setup_camera_tab(self, frame):
        """Sets up the camera configuration tab."""
        # Implementation for camera configuration UI
        pass
        
    def _save_config(self):
        """Saves the current configuration."""
        if self.config.save_config():
            messagebox.showinfo("Success", "Configuration saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save configuration")