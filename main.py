import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"  # Suppress TensorFlow INFO and WARNING logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Disable oneDNN custom ops

# Handle comtypes cache directory
import tempfile
comtypes_cache_dir = os.path.join(tempfile.gettempdir(), 'comtypes_cache')
os.environ['COMTYPES_CACHE'] = comtypes_cache_dir
try:
    if not os.path.exists(comtypes_cache_dir):
        os.makedirs(comtypes_cache_dir)
except Exception as e:
    print(f"Warning: Could not create comtypes cache directory: {e}")

import sys
sys.dont_write_bytecode = True

def check_dll_dependencies():
    """Check if required Visual C++ DLLs are present."""
    import ctypes
    import webbrowser
    from tkinter import messagebox
    
    required_dlls = [
        'msvcp140.dll',
        'msvcp140_1.dll',
        'msvcp140_2.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll'
    ]
    
    missing_dlls = []
    
    for dll in required_dlls:
        try:
            ctypes.CDLL(dll)
        except OSError:
            missing_dlls.append(dll)
    
    if missing_dlls:
        message = (
            "Some required system files are missing. These are part of the Microsoft "
            "Visual C++ Redistributable package.\n\n"
            "Would you like to download and install the required package now?\n\n"
            f"Missing files: {', '.join(missing_dlls)}"
        )
        
        if messagebox.askyesno("Missing Dependencies", message):
            # Open the Microsoft Visual C++ Redistributable download page
            webbrowser.open("https://aka.ms/vs/17/release/vc_redist.x64.exe")
            sys.exit(1)
        else:
            sys.exit(1)

# Check for required DLLs before importing other modules
check_dll_dependencies()

# Now the rest of your imports
import threading
import ctypes
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import Tk, filedialog, messagebox, Label, Frame, X, BOTTOM
from PIL import Image, ImageTk
from utils import focus_powerpoint_window, run_powerpoint, initialize_listener

# Add gesture management variables
last_gesture_time = 0
gesture_cooldown = 1.0  # 1 second cooldown between gestures
wrong_gesture_count = 0
max_wrong_gestures = 1

# Camera zoom settings
current_zoom_level = 0  # 0: Default, 1: 1x zoom, 2: 2x zoom

def reset_gesture_counter():
    global wrong_gesture_count
    wrong_gesture_count = 0

# Initialize mouse listener for focusing PowerPoint
initialize_listener()

# Tkinter GUI
root = Tk()
root.title("AIR TRACKER")
root.geometry("1350x700")
root.configure(bg="#a91f2d")

# Header
header_label = tk.Label(
    root,
    text="AIR TRACKER",
    font=("Georgia", 36, "italic", "bold"),
    bg="#a91f2d",
    fg="white"
)
header_label.pack(pady=10)

# Load and display the image
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(BASE_DIR, "media", "hand.png")
    original_image = Image.open(image_path)
    resized_image = original_image.resize((300, 300))
    my_image = ImageTk.PhotoImage(resized_image)
    image_label = Label(root, image=my_image, bg="#a91f2d")
    image_label.pack(pady=20)
except Exception as e:
    messagebox.showerror("Error", f"Could not load image: {e}")

# Set the icon on Windows
icon_path = os.path.join(BASE_DIR, "media", "hand.ico")
if os.name == 'nt':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"MyAppID")
    root.iconbitmap(icon_path)

# Add camera zoom control section
zoom_section = Frame(root, bg="#a91f2d")
zoom_section.pack(pady=10)

# Add descriptive text (left side)
zoom_description = tk.Label(
    zoom_section,
    text="How much you want to zoom in your camera:",
    font=("Georgia", 16, "italic"),
    bg="#a91f2d",
    fg="white"
)
zoom_description.pack(side=tk.LEFT, padx=(0, 10))

# Create a frame for zoom buttons (right side)
zoom_frame = Frame(zoom_section, bg="#a91f2d")
zoom_frame.pack(side=tk.LEFT)

def set_camera_zoom(zoom_level):
    """Sets the zoom level and updates button states."""
    root.current_zoom_level = zoom_level  # Store zoom level in root
    
    # Update button colors
    for btn, level in zoom_buttons:
        if level == zoom_level:
            btn.configure(fg_color="#ff7373", text_color="white")
        else:
            btn.configure(fg_color="white", text_color="#a91f2d")
    
    # Update zoom level in camera handler if it exists
    if hasattr(root, '_camera_handler') and root._camera_handler is not None:
        root._camera_handler.zoom_level = zoom_level
    
    # Update zoom level in any active camera overlay
    if hasattr(root, '_camera_overlay') and root._camera_overlay is not None:
        if hasattr(root._camera_overlay, 'camera_handler'):
            root._camera_overlay.camera_handler.zoom_level = zoom_level

# Create zoom control buttons
zoom_buttons = []
zoom_levels = [
    ("Default", 0),
    ("1x Zoom", 1),
    ("2x Zoom", 2)
]

for text, level in zoom_levels:
    btn = ctk.CTkButton(
        zoom_frame,
        text=text,
        command=lambda l=level: set_camera_zoom(l),
        font=("Georgia", 14, "italic"),  # Slightly smaller font
        fg_color="white",
        text_color="#a91f2d",
        hover_color="#ff7373",
        corner_radius=8,  # Slightly smaller corner radius
        width=90,  # Reduced width
        height=30  # Reduced height
    )
    btn.pack(side=tk.LEFT, padx=5)  # Reduced padding
    zoom_buttons.append((btn, level))

# Initialize zoom level
root.current_zoom_level = 0
set_camera_zoom(0)

def run_presentation():
    global wrong_gesture_count, last_gesture_time
    ppt_file = filedialog.askopenfilename(
        title="Select PowerPoint file",
        filetypes=[("PowerPoint Files", "*.pptx *.ppt")]
    )
    if ppt_file:
        try:
            if os.path.exists(ppt_file):
                root.iconify()
                # Reset gesture counter when starting new presentation
                reset_gesture_counter()
                
                def monitored_powerpoint():
                    global wrong_gesture_count, last_gesture_time
                    try:
                        run_powerpoint(ppt_file, root)
                    except Exception as e:
                        current_time = time.time()
                        if current_time - last_gesture_time >= gesture_cooldown:
                            last_gesture_time = current_time
                            wrong_gesture_count += 1
                            
                            if wrong_gesture_count >= max_wrong_gestures:
                                messagebox.showwarning(
                                    "Gesture Warning",
                                    "Too many incorrect gestures detected. Presentation will be reset."
                                )
                                root.deiconify()
                                reset_gesture_counter()
                                return
                            
                            if "RPC server is unavailable" in str(e):
                                messagebox.showwarning(
                                    "PowerPoint Error",
                                    "Lost connection to PowerPoint. The presentation will be closed.\n"
                                    "Please try opening the presentation again."
                                )
                                root.deiconify()
                            else:
                                messagebox.showerror("Error", f"An error occurred: {e}")
                
                threading.Thread(target=monitored_powerpoint, daemon=True).start()
            else:
                messagebox.showerror("File Not Found", f"The file could not be found: {ppt_file}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

# Footer with white background
footer_frame = Frame(root, bg="white", height=50, width=1400)
footer_frame.pack(side=BOTTOM, fill=X)

footer_label = tk.Label(
    footer_frame,
    text="Wave goodbye to clicks and embrace gestures.",
    font=("Georgia", 16, "italic"),
    bg="white",
    fg="#a91f2d"
)
footer_label.pack(pady=10)

# Rounded button below the image
def on_hover(event):
    upload_button.configure(fg_color="white", text_color="red")

def on_leave(event):
    upload_button.configure(fg_color="white", text_color="#a91f2d")

upload_button = ctk.CTkButton(
    root,
    text="Upload PowerPoint File",
    command=run_presentation,
    font=("Georgia", 20, "italic", "bold"),
    fg_color="white",
    text_color="#a91f2d",
    hover_color="#ff7373",
    corner_radius=20,
    width=200,
    height=50
)

upload_button.bind("<Enter>", on_hover)
upload_button.bind("<Leave>", on_leave)
upload_button.pack(pady=20)

root.mainloop()
