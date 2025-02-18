import tkinter as tk
from PIL import Image, ImageTk
import pyautogui
import time

class CanvasHandler:
    def __init__(self, root, camera_handler):
        self.root = root
        self.camera_handler = camera_handler  # Store the CameraHandler instance
        self.canvas_window = None
        self.canvas = None
        self.is_canvas_active = False
        self.canvas_cooldown = False
        self.last_x, self.last_y = None, None
        self.current_color = 'black'  # Default drawing color
        self.cursor = None  # Cursor to show selected color
        self.color_buttons = []  # List to store color buttons

    def create_canvas_overlay(self):
        """Creates a full-screen canvas overlay with a color palette inside the canvas."""
        if self.canvas_window:
            return
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Create a full-screen transparent window
        self.canvas_window = tk.Toplevel(self.root)
        self.canvas_window.attributes('-fullscreen', True)
        self.canvas_window.attributes('-topmost', True)
        self.canvas_window.attributes('-transparentcolor', 'white')
        self.canvas_window.attributes('-alpha', 0.8)  # Set transparency level
        self.canvas_window.overrideredirect(True)

        # Debug print
        print("Canvas overlay window created")

        # Create a canvas to draw on (full screen)
        self.canvas = tk.Canvas(self.canvas_window, bg='grey', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Add color palette inside the canvas
        self.add_color_palette()

        # Bind mouse events
        self.canvas.bind("<B1-Motion>", self.draw_on_canvas)
        self.canvas.bind("<ButtonRelease-1>", self.reset_last_position)

        # Add a cursor to show the selected color
        self.cursor = self.canvas.create_oval(0, 0, 10, 10, fill=self.current_color, outline='black')

    def add_color_palette(self):
        """Adds a color palette inside the canvas."""
        colors = ['black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink']  # Define the colors for the palette

        button_size = 30
        padding = 5
        total_width = len(colors) * (button_size + padding) - padding  # Calculate total width of the palette
        screen_width = self.root.winfo_screenwidth()

        # Position the palette at the center top
        x_start = (screen_width - total_width) // 2
        y = 10  # Keep it at the top

        for color in colors:
            button = self.canvas.create_rectangle(
                x_start, y, x_start + button_size, y + button_size,
                fill=color,
                outline='black'
            )
            self.color_buttons.append((button, color))

            # Set color on click
            self.canvas.tag_bind(button, "<Button-1>", lambda event, c=color: self.set_color(c))

            # Hover effects
            self.canvas.tag_bind(button, "<Enter>", lambda event, btn=button, c=color: self.on_hover(btn, c))
            self.canvas.tag_bind(button, "<Leave>", lambda event, btn=button, c=color: self.on_leave(btn, c))

            x_start += button_size + padding  # Move to the next color position

    def on_hover(self, btn, color):
        """Handles hover effect for color buttons."""
        self.canvas.itemconfig(btn, fill="lightgray")  # Temporarily highlight the button
        self.canvas.config(cursor="crosshair")  # Change cursor shape
        self.root.config(cursor="crosshair")  

        # Update the cursor color dynamically
        self.canvas.itemconfig(self.cursor, fill=color)

        # Update the current drawing color temporarily
        self.current_color = color

    def on_leave(self, btn, color):
        """Handles leaving the hover effect for color buttons."""
        self.canvas.itemconfig(btn, fill=color)  # Restore original color
        self.canvas.config(cursor="arrow")  # Reset cursor
        self.root.config(cursor="arrow")

    def set_color(self, color):
        """Sets the current drawing color."""
        self.current_color = color
        self.canvas.itemconfig(self.cursor, fill=color)  # Update the cursor color

        # Notify CameraHandler about the color change
        if self.camera_handler:
            self.camera_handler.set_drawing_color(color)

    def set_eraser(self):
        """Sets the current tool to eraser (white color)."""
        self.current_color = 'white'  # Use white color as the eraser
        self.canvas.itemconfig(self.cursor, fill='white')  # Update the cursor to white

        # Notify CameraHandler about the color change
        if self.camera_handler:
            self.camera_handler.set_drawing_color('white') # Update the cursor to white

    def draw_on_canvas(self, event):
        """Draws on the canvas based on the current cursor position and selected color."""
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill=self.current_color, width=3, capstyle="round")
        self.last_x, self.last_y = x, y

        # Check if the pointer is over any color button
        self.check_pointer_over_buttons(x, y)

    def reset_last_position(self, event):
        """Resets the last drawing position."""
        self.last_x, self.last_y = None, None

    def check_pointer_over_buttons(self, x, y):
        """Checks if the pointer is over any color button and changes the color accordingly."""
        for button, color in self.color_buttons:
            # Get the coordinates of the button
            coords = self.canvas.coords(button)
            if coords:
                x1, y1, x2, y2 = coords
                if x1 <= x <= x2 and y1 <= y <= y2:
                    # Pointer is over the button, change the color
                    self.set_color(color)
                    break

    def toggle_canvas(self):
        """Toggles the canvas overlay on and off."""
        try:
            if self.canvas_cooldown:
                return

            if not self.is_canvas_active:
                print("Creating canvas overlay...")
                self.create_canvas_overlay()
                self.is_canvas_active = True
            else:
                print("Clearing canvas overlay...")
                self.clear_canvas()
                self.is_canvas_active = False

            self.canvas_cooldown = True
            self.root.after(2000, self.reset_canvas_cooldown)
        except Exception as e:
            print(f"Error toggling canvas: {e}")

    def clear_canvas(self):
        """Clears the canvas and destroys the overlay window."""
        if self.canvas and self.canvas.winfo_exists():  # Check if canvas exists
            self.canvas.delete("all")
        if self.canvas_window:
            self.canvas_window.destroy()
        self.canvas_window = None
        self.canvas = None  # Reset the canvas reference
        self.is_canvas_active = False   # Ensure the state is set to inactive

    def reset_canvas_cooldown(self):
        """Resets the canvas cooldown."""
        self.canvas_cooldown = False
