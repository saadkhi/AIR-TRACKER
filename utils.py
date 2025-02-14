import os
import comtypes.client
import time
import threading
import pythoncom
from pynput.mouse import Listener
from tkinter import messagebox, Toplevel, Label
from camera import start_camera
import win32gui
import win32con
import subprocess

overlay_window = None
powerpoint_lock = threading.Lock()


def safe_com_call(func, max_retries=5, delay=1, *args, **kwargs):
    """
    Safely call a COM method with retry logic to handle situations where the application is busy.
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except comtypes.COMError as e:
            if attempt < max_retries - 1:
                print(f"COM call failed (attempt {attempt + 1}), retrying...")
                time.sleep(delay)
            else:
                print(f"COM call failed after {max_retries} attempts.")
                raise e


def initialize_listener():
    """
    Starts a mouse listener to focus PowerPoint on mouse clicks.
    """
    def on_click(x, y, button, pressed):
        if pressed:
            focus_powerpoint_window()

    listener = Listener(on_click=on_click)
    listener.start()


def focus_powerpoint_window():
    """
    Focuses on the PowerPoint window when it's running.
    """
    try:
        hwnd = win32gui.FindWindow(None, None)
        while hwnd:
            window_title = win32gui.GetWindowText(hwnd)
            if "PowerPoint Slide Show" in window_title:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                break
            hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
    except Exception as e:
        print(f"Error focusing PowerPoint window: {e}")


def close_activation_dialog():
    """
    Attempts to find and close the Office activation dialog.
    """
    try:
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if "Microsoft Office Activation Wizard" in window_title:
                    print(f"Found activation window: {window_title}. Attempting to close it.")
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception as e:
        print(f"Error while closing activation dialog: {e}")


def force_kill_powerpoint():
    """
    Forcefully kills all running PowerPoint processes.
    """
    try:
        print("Forcefully killing all PowerPoint processes...")
        subprocess.run(["taskkill", "/F", "/IM", "POWERPNT.EXE"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("All PowerPoint processes terminated.")
    except subprocess.CalledProcessError as e:
        print(f"Error forcefully killing PowerPoint processes: {e}")


def wait_for_powerpoint_ready(powerpoint, timeout=30):
    """
    Waits for PowerPoint to be ready, with a timeout.
    """
    start_time = time.time()
    while True:
        try:
            # Try accessing a COM property to check if PowerPoint is ready
            if powerpoint.Presentations.Count >= 0:
                print("PowerPoint is ready.")
                break
        except comtypes.COMError:
            # PowerPoint is still busy, wait and retry
            pass

        # Check if timeout is reached
        if time.time() - start_time > timeout:
            raise Exception("PowerPoint did not become ready in time.")
        time.sleep(1)


def run_powerpoint(ppt_file, root):
    """
    Runs the PowerPoint presentation with proper thread and COM handling.
    """
    global overlay_window
    powerpoint = None
    presentation = None

    try:
        pythoncom.CoInitialize()

        # Create PowerPoint Application
        print("Initializing PowerPoint application...")
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        powerpoint.Visible = True

        # Wait for PowerPoint to be ready
        wait_for_powerpoint_ready(powerpoint)

        # Close activation dialog if it exists
        close_activation_dialog()

        # Open the PowerPoint file
        print(f"Opening PowerPoint file: {ppt_file}")
        formatted_ppt_file = ppt_file.replace("/", "\\")
        presentation = safe_com_call(
            powerpoint.Presentations.Open,
            max_retries=5, delay=1, FileName=formatted_ppt_file
        )

        if not presentation:
            raise Exception("Failed to open PowerPoint file. Please check the file path or format.")

        # Start the slideshow
        print("Starting slideshow...")
        safe_com_call(presentation.SlideShowSettings.Run)

        # Wait to ensure slideshow starts
        wait_for_powerpoint_ready(powerpoint)

        # Focus PowerPoint window
        time.sleep(1)
        focus_powerpoint_window()

        # Ensure the slideshow starts
        if powerpoint.SlideShowWindows.Count == 0:
            raise Exception("Slideshow mode could not be started. Please ensure the PowerPoint file is valid.")

        print("Displaying camera overlay...")
        display_camera_overlay(root)

        # Monitor the slideshow
        while powerpoint.SlideShowWindows.Count > 0:
            time.sleep(0.5)

    except Exception as e:
        print(f"Error running PowerPoint presentation: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        # Safely close the PowerPoint presentation if it exists
        print("Closing PowerPoint presentation...")
        if presentation:
            try:
                safe_com_call(presentation.Close, max_retries=5, delay=1)
            except Exception as e:
                print(f"Error closing PowerPoint presentation: {e}")
        if powerpoint:
            try:
                safe_com_call(powerpoint.Quit, max_retries=5, delay=1)
            except Exception as e:
                print(f"Error quitting PowerPoint application: {e}")
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.destroy()
        pythoncom.CoUninitialize()


def display_camera_overlay(root):
    """
    Displays the camera overlay window with a live camera feed.
    """
    global overlay_window
    
    # If there's an existing overlay window, destroy it first
    if overlay_window and overlay_window.winfo_exists():
        overlay_window.destroy()
    
    overlay_window = Toplevel(root)
    overlay_window.title("Camera Feed Overlay")
    overlay_window.attributes('-topmost', True)
    overlay_window.geometry("300x200+1620+0")  # Adjusted to top-right corner

    camera_label = Label(overlay_window)
    camera_label.pack()

    threading.Thread(target=start_camera, args=(camera_label,), daemon=True).start()
