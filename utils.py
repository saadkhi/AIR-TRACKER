import threading
import time
import subprocess
import comtypes
import pythoncom
import win32gui
import win32con
from tkinter import messagebox, Toplevel, Label
from pynput.mouse import Listener
from camera import CameraHandler

overlay_window = None

def safe_com_call(func, max_retries=3, delay=0.5, *args, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except comtypes.COMError as e:
            if "RPC server is unavailable" in str(e):
                # Suppress repeated RPC errors
                break
            time.sleep(delay)
    return None

def initialize_listener():
    def on_click(x, y, button, pressed):
        if pressed:
            focus_powerpoint_window()
    Listener(on_click=on_click).start()

def focus_powerpoint_window():
    try:
        hwnd = win32gui.FindWindow(None, None)
        while hwnd:
            if "PowerPoint Slide Show" in win32gui.GetWindowText(hwnd):
                win32gui.SetForegroundWindow(hwnd)
                break
            hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
    except Exception:
        pass  # Suppress focus errors

def close_activation_dialog():
    try:
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and "Microsoft Office Activation Wizard" in win32gui.GetWindowText(hwnd):
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        pass

def force_kill_powerpoint():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "POWERPNT.EXE"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        pass  # Suppress errors if process already closed

def wait_for_powerpoint_ready(powerpoint, timeout=10):
    start_time = time.time()
    while True:
        try:
            if powerpoint.Presentations.Count >= 0:
                return
        except comtypes.COMError:
            pass
        if time.time() - start_time > timeout:
            break
        time.sleep(0.5)

def run_powerpoint(ppt_file, root):
    global overlay_window
    powerpoint = None
    presentation = None

    try:
        pythoncom.CoInitialize()
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        powerpoint.Visible = True
        wait_for_powerpoint_ready(powerpoint)
        close_activation_dialog()
        formatted_ppt_file = ppt_file.replace("/", "\\")
        presentation = safe_com_call(powerpoint.Presentations.Open, max_retries=3, delay=0.5, FileName=formatted_ppt_file)
        if not presentation:
            raise Exception("Failed to open PowerPoint file. Please check the file path or format.")
        safe_com_call(presentation.SlideShowSettings.Run)
        wait_for_powerpoint_ready(powerpoint)
        time.sleep(0.5)
        focus_powerpoint_window()
        if powerpoint.SlideShowWindows.Count == 0:
            raise Exception("Slideshow mode could not be started. Please ensure the PowerPoint file is valid.")
        
        # Store current zoom level in root for camera overlay
        root.current_zoom_level = getattr(root, 'current_zoom_level', 0)
        
        display_camera_overlay(root)

        # Monitor PowerPoint process
        while True:
            time.sleep(0.2)
            if powerpoint.SlideShowWindows.Count == 0:
                break

    except comtypes.COMError as e:
        # Only show error if it's not the RPC server issue
        if "RPC server is unavailable" not in str(e) and "The remote procedure call failed" not in str(e):
            messagebox.showerror("PowerPoint Error", f"COM Error: {e}")
        # Otherwise, silently ignore or log if needed
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        # Immediately close overlay and restore main window
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.destroy()
        if presentation:
            try:
                safe_com_call(presentation.Close)
            except Exception:
                pass
        if powerpoint:
            try:
                safe_com_call(powerpoint.Quit)
            except Exception:
                pass
        force_kill_powerpoint()
        pythoncom.CoUninitialize()
        root.deiconify()  # Show main window immediately

def display_camera_overlay(root):
    """Displays the camera overlay window with dynamic positioning based on screen resolution."""
    global overlay_window
    
    # Close existing overlay if it exists
    if overlay_window and overlay_window.winfo_exists():
        overlay_window.destroy()
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Calculate camera window dimensions (maintain 3:2 aspect ratio)
    if screen_width >= 1920:  # 1080p and higher
        cam_width = 300
        cam_height = 200
    else:  # Lower resolutions
        cam_width = 240
        cam_height = 160
    
    # Calculate position (always top-right with padding)
    padding = 10
    x_position = screen_width - cam_width - padding
    y_position = padding
    
    # Create and configure overlay window
    overlay_window = Toplevel(root)
    overlay_window.title("Camera Feed")
    overlay_window.attributes('-topmost', True)
    
    # Remove window decorations for cleaner look
    overlay_window.overrideredirect(True)
    
    # Set window size and position
    geometry_string = f"{cam_width}x{cam_height}+{x_position}+{y_position}"
    overlay_window.geometry(geometry_string)
    
    # Add a close button
    close_button = Label(overlay_window, text="×", font=("Arial", 12), cursor="hand2")
    close_button.pack(side="right", anchor="ne", padx=5, pady=2)
    close_button.bind("<Button-1>", lambda e: overlay_window.destroy())
    
    # Create camera label
    camera_label = Label(overlay_window)
    camera_label.pack(expand=True, fill="both")
    
    # Make window draggable
    make_draggable(overlay_window)
    
    # Get current zoom level from main window
    current_zoom_level = getattr(root, 'current_zoom_level', 0)
    
    # Create camera handler and set zoom level
    camera_handler = CameraHandler(camera_label, root)
    camera_handler.zoom_level = current_zoom_level  # Set zoom level directly
    
    # Start camera in a separate thread
    threading.Thread(target=lambda: start_camera(camera_label, camera_handler), daemon=True).start()

def make_draggable(window):
    """Makes a window draggable by clicking and dragging anywhere on it."""
    def start_drag(event):
        window.x = event.x
        window.y = event.y

    def do_drag(event):
        deltax = event.x - window.x
        deltay = event.y - window.y
        x = window.winfo_x() + deltax
        y = window.winfo_y() + deltay
        window.geometry(f"+{x}+{y}")

    window.bind("<Button-1>", start_drag)
    window.bind("<B1-Motion>", do_drag)

def start_camera(camera_label, camera_handler=None):
    """Starts the camera feed and initializes gesture detection."""
    if camera_handler is None:
        camera_handler = CameraHandler(camera_label, camera_label.master)
    camera_handler.start_camera()
