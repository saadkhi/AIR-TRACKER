import os
import time
import threading
import subprocess
import pythoncom
import comtypes.client
from pynput.mouse import Listener
from tkinter import messagebox, Toplevel, Label
from camera import start_camera
import win32gui
import win32con

overlay_window = None
powerpoint_lock = threading.Lock()

def safe_com_call(func, max_retries=10, delay=2, *args, **kwargs):  # Increased retries and delay
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except comtypes.COMError as e:
            print(f"COM call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise

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
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                break
            hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
    except Exception as e:
        print(f"Error focusing PowerPoint window: {e}")

def close_activation_dialog():
    try:
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and "Microsoft Office Activation Wizard" in win32gui.GetWindowText(hwnd):
                print(f"Found activation window. Attempting to close it.")
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception as e:
        print(f"Error while closing activation dialog: {e}")

def force_kill_powerpoint():
    """Forcefully kill all PowerPoint processes."""
    try:
        print("Forcefully killing all PowerPoint processes...")
        subprocess.run(["taskkill", "/F", "/IM", "POWERPNT.EXE"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("All PowerPoint processes terminated.")
    except subprocess.CalledProcessError as e:
        print(f"Error forcefully killing PowerPoint processes: {e}")

def restart_powerpoint():
    """Forcefully restart PowerPoint."""
    try:
        print("Restarting PowerPoint...")
        subprocess.run(["taskkill", "/F", "/IM", "POWERPNT.EXE"], check=True)
        time.sleep(2)  # Wait for PowerPoint to close
    except subprocess.CalledProcessError as e:
        print(f"Error restarting PowerPoint: {e}")

def wait_for_powerpoint_ready(powerpoint, timeout=60):  # Increased timeout to 60 seconds
    start_time = time.time()
    while True:
        try:
            if powerpoint.Presentations.Count >= 0:
                print("PowerPoint is ready.")
                break
        except comtypes.COMError:
            pass
        if time.time() - start_time > timeout:
            raise Exception("PowerPoint did not become ready in time.")
        time.sleep(1)

def run_powerpoint(ppt_file, root):
    global overlay_window
    powerpoint = None
    presentation = None

    try:
        pythoncom.CoInitialize()
        print("Initializing PowerPoint application...")
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        powerpoint.Visible = True
        wait_for_powerpoint_ready(powerpoint)
        close_activation_dialog()
        print(f"Opening PowerPoint file: {ppt_file}")
        formatted_ppt_file = ppt_file.replace("/", "\\")
        presentation = safe_com_call(powerpoint.Presentations.Open, max_retries=5, delay=1, FileName=formatted_ppt_file)
        if not presentation:
            raise Exception("Failed to open PowerPoint file. Please check the file path or format.")
        print("Starting slideshow...")
        safe_com_call(presentation.SlideShowSettings.Run)
        wait_for_powerpoint_ready(powerpoint)
        time.sleep(1)
        focus_powerpoint_window()
        if powerpoint.SlideShowWindows.Count == 0:
            raise Exception("Slideshow mode could not be started. Please ensure the PowerPoint file is valid.")
        print("Displaying camera overlay...")
        display_camera_overlay(root)

        # Monitor PowerPoint process
        while True:
            time.sleep(0.5)
            if powerpoint.SlideShowWindows.Count == 0:  # Check if slideshow is closed
                print("PowerPoint slideshow closed.")
                break

    except comtypes.COMError as e:
        print(f"COM Error: {e}")
        if "RPC server is unavailable" in str(e):
            print("PowerPoint COM object lost connection. Forcefully killing PowerPoint...")
            force_kill_powerpoint()
            messagebox.showwarning(
                "PowerPoint Error",
                "Lost connection to PowerPoint. The presentation will be closed.\n"
                "Please try opening the presentation again."
            )
    except Exception as e:
        print(f"Error running PowerPoint presentation: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
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
                force_kill_powerpoint()  # Force kill PowerPoint if quitting fails
        if overlay_window and overlay_window.winfo_exists():
            print("Destroying camera overlay window...")
            overlay_window.destroy()  # Ensure the camera overlay is closed
        pythoncom.CoUninitialize()

        # Bring the desktop app back to the foreground
        root.deiconify()  # Ensure the app window is brought back to the foreground

def display_camera_overlay(root):
    global overlay_window
    if overlay_window and overlay_window.winfo_exists():
        overlay_window.destroy()  # Destroy any existing overlay window
    overlay_window = Toplevel(root)
    overlay_window.title("Camera Feed Overlay")
    overlay_window.attributes('-topmost', True)
    overlay_window.geometry("300x200+1620+0")
    camera_label = Label(overlay_window)
    camera_label.pack()
    threading.Thread(target=start_camera, args=(camera_label,), daemon=True).start()
