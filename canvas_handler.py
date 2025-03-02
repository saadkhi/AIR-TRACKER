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
        self.current_tool = 'pen'  # Default tool
        self.cursor = None  # Cursor to show selected color
        self.color_buttons = []  # List to store color buttons
        self.tool_buttons = []  # List to store tool buttons
        self.canvas_x_offset = 0  # Initial offset, starts at 0
        self.canvas_shift_amount = 20  # Pixels to shift right each time
        self.is_drawing_mode = False  # New state variable to track drawing mode

    def set_drawing_mode(self, is_drawing):
        """Set the drawing mode."""
        self.is_drawing_mode = is_drawing
        if not is_drawing:
            self.last_x, self.last_y = None, None  # Reset drawing positions


    def create_canvas_overlay(self):
        """Creates a full-screen canvas overlay that shifts slightly to the right on reappearance."""
        if self.canvas_window:
            return

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Update X offset (shift to right each time)
        self.canvas_x_offset += self.canvas_shift_amount  
        if self.canvas_x_offset > 100:  # Prevent excessive shifting
            self.canvas_x_offset = 0  

        self.canvas_window = tk.Toplevel(self.root)
        self.canvas_window.geometry(f"{screen_width}x{screen_height}+{self.canvas_x_offset}+0")  
        self.canvas_window.attributes('-fullscreen', True)
        self.canvas_window.attributes('-topmost', True)
        self.canvas_window.attributes('-transparentcolor', 'white')
        self.canvas_window.attributes('-alpha', 0.8)
        self.canvas_window.overrideredirect(True)

        self.canvas = tk.Canvas(self.canvas_window, bg='grey', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.add_color_palette()
        self.add_tool_buttons()

        self.cursor = self.canvas.create_oval(0, 0, 20, 20, fill=self.current_color, outline='black')

    def add_color_palette(self):
        """Adds a color palette inside the canvas."""
        colors = ['black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink']  # Define the colors for the palette

        button_size = 40  # Reduced button size
        padding = 5  # Reduced padding between buttons
        total_width = len(colors) * (button_size + padding) - padding  # Calculate total width of the palette
        screen_width = self.root.winfo_screenwidth()

        # Position the palette at the center top
        x_start = (screen_width - total_width) // 2
        y = 40  # Slightly up from the top

        for color in colors:
            button = self.canvas.create_rectangle(
                x_start, y, x_start + button_size, y + button_size,
                fill=color,
                outline='black'  # Black boundary for color buttons
            )
            self.color_buttons.append((button, color))

            # Set color on click
            self.canvas.tag_bind(button, "<Button-1>", lambda event, c=color: self.set_color(c))

            # Hover effects
            self.canvas.tag_bind(button, "<Enter>", lambda event, btn=button, c=color: self.on_hover(btn, c))
            self.canvas.tag_bind(button, "<Leave>", lambda event, btn=button, c=color: self.on_leave(btn, c))

            x_start += button_size + padding  # Move to the next color position

    def add_tool_buttons(self):
        """Adds tool buttons (pen, highlighter, eraser) inside the canvas."""
        tools = [
            ('pen', r"media\pen.png"),
            ('highlighter', r"media\highlighter.png"),
            ('eraser', r"media\eraser.png")
        ]

        button_size = 40  # Reduced button size
        padding = 5  # Reduced padding between buttons
        total_width = (len(tools) + len(self.color_buttons)) * (button_size + padding) - padding  # Calculate total width of the tool buttons and color buttons
        screen_width = self.root.winfo_screenwidth()

        # Position the tool buttons and color buttons in the same line
        x_start = (screen_width - total_width) // 2
        y = 40  # Slightly up from the top

        # Add color buttons first
        for button, color in self.color_buttons:
            self.canvas.coords(button, x_start, y, x_start + button_size, y + button_size)
            x_start += button_size + padding

        # Add tool buttons
        for tool, image_path in tools:
            try:
                # Load the icon image
                icon_image = Image.open(image_path)
                icon_image = icon_image.resize((button_size, button_size), Image.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)

                # Create a rectangle around the tool button for the boundary
                boundary = self.canvas.create_rectangle(
                    x_start, y, x_start + button_size, y + button_size,
                    outline='black'  # Black boundary for tool buttons
                )

                # Create the button with the icon
                button = self.canvas.create_image(
                    x_start, y,
                    image=icon_photo,
                    anchor=tk.NW
                )
                self.tool_buttons.append((button, tool, icon_photo))

                # Set tool on click
                self.canvas.tag_bind(button, "<Button-1>", lambda event, t=tool: self.set_tool(t))

                # Hover effects
                self.canvas.tag_bind(button, "<Enter>", lambda event, btn=button, t=tool: self.on_tool_hover(btn, t))
                self.canvas.tag_bind(button, "<Leave>", lambda event, btn=button, t=tool: self.on_tool_leave(btn, t))

                x_start += button_size + padding  # Move to the next tool position
            except Exception as e:
                print(f"Error loading icon for {tool}: {e}")

    def set_tool(self, tool):
        """Sets the current tool (pen, highlighter, eraser)."""
        self.current_tool = tool
        if tool == 'eraser':
            self.current_color = 'grey'  # Use canvas background color as the eraser
            self.canvas.itemconfig(self.cursor, fill='grey')  # Update the cursor to grey
        elif tool == 'pen':
            self.current_color = 'black'  # Default pen color
            self.canvas.itemconfig(self.cursor, fill='black')  # Update the cursor to black
        elif tool == 'highlighter':
            self.current_color = '#39FF14'  # Neon green color for highlighter
            self.canvas.itemconfig(self.cursor, fill='#39FF14')  # Update the cursor to neon green

        # Notify CameraHandler about the tool change
        if self.camera_handler:
            self.camera_handler.set_drawing_tool(tool)

    def update_virtual_cursor(self):
        """Updates the virtual cursor's appearance based on the current tool."""
        if self.camera_handler:
            # Assuming the virtual cursor is represented by a circle on the canvas
            self.camera_handler.canvas_handler.canvas.itemconfig(self.camera_handler.canvas_handler.cursor, fill=self.current_color)
            self.camera_handler.set_drawing_color(self.current_color)
            self.camera_handler.set_drawing_tool(self.current_tool)

    def on_hover(self, btn, color):
        print(f"Hovering over: {btn}")  # Debugging
        self.canvas.itemconfig(btn, fill="lightgray")
        self.canvas.config(cursor="crosshair")
        self.root.config(cursor="crosshair")

        # Store the current pointer color before changing
        self.previous_color = self.canvas.itemcget(self.cursor, "fill")
        self.canvas.itemconfig(self.cursor, fill="grey")  # Change pointer to grey while hovering

    def on_leave(self, btn, color):
        print(f"Leaving: {btn}")  # Debugging
        self.canvas.itemconfig(btn, fill=color)
        self.canvas.config(cursor="arrow")
        self.root.config(cursor="arrow")

        # Restore the pointer to its previous color
        if hasattr(self, "previous_color"):
            self.canvas.itemconfig(self.cursor, fill=self.previous_color)


    def on_tool_hover(self, btn, tool):
        """Handles hover effect for tool buttons."""
        self.canvas.config(cursor="crosshair")  # Change cursor shape
        self.root.config(cursor="crosshair")

        # Update the cursor to reflect the selected tool
        if tool == 'eraser':
            self.canvas.itemconfig(self.cursor, fill='grey')
        elif tool == 'pen':
            self.canvas.itemconfig(self.cursor, fill='black')
        elif tool == 'highlighter':
            self.canvas.itemconfig(self.cursor, fill='#39FF14')
        
        

    def on_tool_leave(self, btn, tool):
        """Handles leaving the hover effect for tool buttons."""
        self.canvas.config(cursor="arrow")  # Reset cursor
        self.root.config(cursor="arrow")

    def set_color(self, color):
        """Sets the current drawing color."""
        self.current_color = color
        self.canvas.itemconfig(self.cursor, fill=color)  # Update the cursor color

        # Notify CameraHandler about the color change
        if self.camera_handler:
            self.camera_handler.set_drawing_color(color)
    def set_drawing_tool(self, tool):
        """Sets the current drawing tool."""
        if tool == 'pen':
            self.is_pen_active = True
            self.is_highlighter_active = False
        elif tool == 'highlighter':
            self.is_pen_active = False
            self.is_highlighter_active = True
        elif tool == 'eraser':
            self.is_pen_active = False
            self.is_highlighter_active = False

    def draw_on_canvas(self, event):
        """Draws on the canvas but blocks strokes over buttons."""
        if not self.is_drawing_mode:
            return

        x, y = event.x, event.y

        # 🚀 BLOCK DRAWING OVER BUTTONS!
        if self.check_pointer_over_buttons(x, y):
            return  # Stop drawing if pointer is over a button

        # Set different line widths based on the current tool
        if self.current_tool == 'pen':
            line_width = 3  # Default pen width
        elif self.current_tool == 'highlighter':
            line_width = 50  # Thicker line for highlighter
        elif self.current_tool == 'eraser':
            line_width = 50  # Thicker line for eraser
        else:
            line_width = 3  # Default width for other tools

        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill=self.current_color, width=line_width, capstyle="round")

        self.last_x, self.last_y = x, y



    def reset_last_position(self, event):
        """Resets the last drawing position."""
        self.last_x, self.last_y = None, None

    def check_pointer_over_buttons(self, x, y):
        """Checks if the pointer is over any color or tool button and changes the color or tool accordingly."""
        hovered = False  # Track if the pointer is over any button

        # Check color buttons
        for button, color in self.color_buttons:
            coords = self.canvas.coords(button)
            if coords and len(coords) == 4:
                x1, y1, x2, y2 = coords
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.set_color(color)
                    self.on_hover(button, color)
                    hovered = True  # Pointer is on a button
                else:
                    self.on_leave(button, color)  # Reset hover effect when leaving

        # Check tool buttons (pen, highlighter, eraser)
        for button, tool, _ in self.tool_buttons:
            coords = self.canvas.coords(button)
            if coords and len(coords) == 2:  # Image-based buttons have (x, y) coords
                x1, y1 = coords
                x2, y2 = x1 + 70, y1 + 70  # Assume button size is 70x70
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.set_tool(tool)
                    self.on_tool_hover(button, tool)  # Visual effect when hovering
                    hovered = True  # Pointer is on a button
                else:
                    self.on_tool_leave(button, tool)  # Reset hover effect when leaving

        # If the pointer is not over any button, reset cursor style
        if not hovered:
            self.canvas.config(cursor="arrow")
            self.root.config(cursor="arrow")
            self.root.config(cursor="arrow")

        return hovered  # Return whether the pointer is over a button

    def toggle_canvas(self):
        """Toggles the canvas overlay on and off without shifting position."""
        try:
            if self.canvas_cooldown:
                return

            if not self.is_canvas_active:
                print("Showing canvas overlay...")
                if self.canvas_window:
                    self.canvas_window.deiconify()  # Restore instead of recreating
                else:
                    self.create_canvas_overlay()
                self.is_canvas_active = True
            else:
                print("Hiding canvas overlay...")
                self.canvas_window.withdraw()  # Hide instead of destroying
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