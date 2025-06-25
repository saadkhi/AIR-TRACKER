import os
import cv2
from PIL import Image, ImageTk
import pyautogui
import time
from tkinter import Label
import comtypes.client
from canvas_handler import CanvasHandler
import tkinter.messagebox as messagebox
import numpy as np


class CameraHandler:
    """Handles the camera feed and gesture detection."""

    def __init__(self, camera_label, master):
        self.camera_label = camera_label
        self.master = master
        self.detector = None  # Delay HandDetector creation
        self.cap = None       # Delay camera creation
        self.video_toggle_cooldown = False
        self.slide_toggle_cooldown = False
        self.zoom_out_cooldown = False
        self.zoom_in_cooldown = False
        self.enter_cooldown = False
        self.close_cooldown = False
        self.video_playing = False
        self.is_pen_active = False
        self.is_highlighter_active = False
        self.drawing_active = False
        self.last_x, self.last_y = None, None
        self.screen_width, self.screen_height = pyautogui.size()
        self.drawing_positions = [[]]  # List to store drawing strokes
        self.canvas_handler = CanvasHandler(master, self) # Pass root to CanvasHandler
        self.current_tool = 'pen'  # Default tool
        self.gesture_error_count = 0
        self.max_gesture_errors = 5
        self.zoom_level = 0  # Default zoom level
        self.frame_width = None
        self.frame_height = None
    
    def set_drawing_color(self, color):
        """Sets the current drawing color."""
        self.canvas_handler.current_color = color

    def set_drawing_tool(self, tool):
        """Sets the current drawing tool."""
        self.current_tool = tool
        if tool == 'pen':
            self.is_pen_active = True
            self.is_highlighter_active = False
        elif tool == 'highlighter':
            self.is_pen_active = False
            self.is_highlighter_active = True
        elif tool == 'eraser':
            self.is_pen_active = False
            self.is_highlighter_active = False

    def set_zoom_level(self, level):
        """Sets the camera zoom level."""
        self.zoom_level = level
        if self.cap and self.cap.isOpened():
            if level == 1:  # 1x zoom
                self.cap.set(cv2.CAP_PROP_ZOOM, 100)  # Set to 100% zoom
            elif level == 2:  # 3x zoom
                self.cap.set(cv2.CAP_PROP_ZOOM, 300)  # Set to 300% zoom
            else:  # Default no zoom
                self.cap.set(cv2.CAP_PROP_ZOOM, 0)  # Reset zoom

    def apply_zoom(self, frame):
        """Applies zoom to the camera frame using ROI cropping method."""
        if self.zoom_level == 0:  # Default, no zoom
            return frame
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        if self.zoom_level == 1:  # 1x zoom - crop center 75% of the frame
            # Calculate crop coordinates (12.5% from each side)
            x1 = int(width * 0.125)
            y1 = int(height * 0.125)
            x2 = int(width * 0.875)
            y2 = int(height * 0.875)
        else:  # 2x zoom - crop center 60% of the frame (1/5 to 4/5)
            # Calculate crop coordinates (20% from each side)
            x1 = int(width / 4.5)
            y1 = int(height / 4.5)
            x2 = int(width * 3.5 / 4.5)
            y2 = int(height * 3.5 / 4.5)
        
        # Crop the frame to zoom region
        cropped_frame = frame[y1:y2, x1:x2]
        
        # Resize back to original size
        zoomed = cv2.resize(cropped_frame, (width, height), interpolation=cv2.INTER_LINEAR)
        
        return zoomed

    def start_camera(self):
        """Starts the camera feed and initializes gesture detection."""
        try:
            import cv2
            from cvzone.HandTrackingModule import HandDetector
            
            # Initialize detector
            self.detector = HandDetector(detectionCon=0.7, maxHands=1)
            
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Could not open video device. Please ensure your camera is connected and not in use by another application.")
                return
            
            # Get screen dimensions
            screen_width = self.master.winfo_screenwidth()
            
            # Set camera resolution based on screen size
            if screen_width >= 1920:  # 1080p and higher
                self.width, self.height = 1280, 720  # HD resolution
            else:  # Lower resolutions
                self.width, self.height = 640, 480
                
            # Try to set camera properties
            try:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                
                # Store original frame dimensions
                self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Get initial zoom level from master window if available
                if hasattr(self.master, 'current_zoom_level'):
                    self.zoom_level = self.master.current_zoom_level
                
                # Verify if the camera accepted our resolution settings
                actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                if abs(actual_width - self.width) > 50 or abs(actual_height - self.height) > 50:
                    print(f"Warning: Camera using different resolution. Requested: {self.width}x{self.height}, Got: {actual_width}x{actual_height}")
                
            except Exception as e:
                print(f"Warning: Could not set camera resolution: {e}")
                
            self.update_frame()
            
        except ImportError as e:
            messagebox.showerror("Import Error", f"Required module not found: {e}\nPlease ensure all dependencies are installed.")
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to initialize camera: {e}\nPlease check your camera connection and permissions.")

    def update_frame(self):
        """Captures frames from the camera and processes gestures."""
        if not self.cap or not self.cap.isOpened():
            return
            
        success, img = self.cap.read()
        if success:
            # Apply zoom if needed
            img = self.apply_zoom(img)
            
            # Flip the image horizontally for more intuitive interaction
            img = cv2.flip(img, 1)
            
            hands, img = self.detector.findHands(img)

            if hands:
                hand = hands[0]
                fingers_up = self.detector.fingersUp(hand)
                lm_index = hand['lmList'][8] 
                lmlist = hand['lmList']
                indexfinger = lmlist[8][0], lmlist[8][1]
                
                # Map camera coordinates to screen coordinates
                screen_x = int(self.screen_width * (indexfinger[0] / self.width))
                screen_y = int(self.screen_height * (indexfinger[1] / self.height))

                try:
                    self.handle_gestures(fingers_up, screen_x, screen_y, indexfinger)
                    self.gesture_error_count = 0
                except Exception as e:
                    self.gesture_error_count += 1
                    if self.gesture_error_count >= self.max_gesture_errors:
                        self.reset_camera()
                    print(f"Gesture detection error: {str(e)}")

            # Resize for display in the overlay window
            display_img = cv2.resize(img, (300, 200))
            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
                self.camera_label.img_tk = img_tk
                self.camera_label.config(image=img_tk)
                self.camera_label.after(30, self.update_frame)

    def handle_gestures(self, fingers_up, screen_x, screen_y, indexfinger):
        """Handles gestures based on finger configurations."""
        # Canvas activation/deactivation
        if fingers_up == [0, 1, 0, 0, 1]:  # Index and pinky fingers
            if not self.canvas_handler.canvas_cooldown:
                self.canvas_handler.toggle_canvas()
                self.canvas_handler.canvas_cooldown = True
                self.camera_label.after(2000, self.canvas_handler.reset_canvas_cooldown)
        
        if fingers_up == [0, 1, 0, 0, 0]:  # Index finger up (drawing mode)
            self.canvas_handler.set_drawing_mode(True)
            if self.canvas_handler.canvas:
                # Show pointer for all tools (pen, highlighter, eraser)
                pointer_size = 5  # Default size for pen
                if self.canvas_handler.current_tool == 'highlighter':
                    pointer_size = 15
                elif self.canvas_handler.current_tool == 'eraser':
                    pointer_size = 25
                
                self.canvas_handler.canvas.delete("pointer")
                self.canvas_handler.canvas.create_oval(
                    screen_x - pointer_size, screen_y - pointer_size, 
                    screen_x + pointer_size, screen_y + pointer_size,
                    fill=self.canvas_handler.current_color, 
                    outline="black", 
                    tags="pointer"
                )

                # Block drawing over buttons
                if self.canvas_handler.check_pointer_over_buttons(screen_x, screen_y):
                    self.canvas_handler.set_drawing_mode(False)
                    return  

                # Draw on canvas
                self.canvas_handler.draw_on_canvas(screen_x, screen_y)

        elif fingers_up == [0, 1, 1, 0, 0]:  # Index and middle finger up (Pointer Mode)
            self.canvas_handler.set_drawing_mode(False)  # Exit drawing mode
            if self.canvas_handler.canvas:
                self.canvas_handler.canvas.delete("pointer")
                self.canvas_handler.canvas.create_oval(
                    screen_x - 5, screen_y - 5, screen_x + 5, screen_y + 5,
                    fill=self.canvas_handler.current_color, outline="black", tags="pointer"
                )
                self.last_x, self.last_y = None, None  # Reset drawing positions

            # Check if the pointer is hovering over a button
            self.canvas_handler.check_pointer_over_buttons(screen_x, screen_y)

        # Other gesture handling code...
        if fingers_up == [1, 1, 0, 0, 0] and not self.video_toggle_cooldown:
            self.click_video()
            self.video_playing = not self.video_playing
            self.video_toggle_cooldown = True
            self.camera_label.after(2000, self.reset_video_toggle_cooldown)

        # Enter key with last three fingers
        # elif fingers_up == [0, 0, 1, 1, 1] and not self.enter_cooldown:  # Middle, ring, and pinky for enter
        #     pyautogui.press('enter')
        #     self.enter_cooldown = True
        #     self.camera_label.after(1000, self.reset_enter_cooldown)

        # Slide navigation
        elif fingers_up == [1, 0, 0, 0, 0] and not self.slide_toggle_cooldown:  # Thumb only for previous
            self.move_slide_backward()
            self.slide_toggle_cooldown = True
            self.camera_label.after(1000, self.reset_slide_toggle_cooldown)
        elif fingers_up == [0, 0, 0, 0, 1] and not self.slide_toggle_cooldown:  # Pinky only for next
            self.move_slide_forward()
            self.slide_toggle_cooldown = True
            self.camera_label.after(1000, self.reset_slide_toggle_cooldown)

        # Zoom controls
        # elif fingers_up == [0, 1, 1, 1, 0] and not self.zoom_in_cooldown:  # Three middle fingers for zoom in
        #     self.trigger_zoom_in()
        #     self.zoom_in_cooldown = True
        #     self.camera_label.after(1500, self.reset_zoom_in_cooldown)
        # elif fingers_up == [0, 1, 1, 1, 1] and not self.zoom_out_cooldown:  # Four fingers for zoom out
        #     self.trigger_zoom_out()
        #     self.zoom_out_cooldown = True
        #     self.camera_label.after(1500, self.reset_zoom_out_cooldown)

        # Close application with thumb and pinky up
        elif fingers_up == [1, 0, 0, 0, 1] and not self.close_cooldown:  # Thumb and pinky up
            self.close_application()  # Close PowerPoint and bring app back
            self.close_cooldown = True
            self.camera_label.after(2000, self.reset_close_cooldown)

    def handle_pen_mode(self, screen_x, screen_y):
        """Handles pen drawing mode."""
        if not self.is_pen_active:
            self.deactivate_highlighter()
            pyautogui.hotkey('ctrl', 'p')
            self.is_pen_active = True
            self.last_x, self.last_y = screen_x, screen_y  # Store initial point
            pyautogui.moveTo(screen_x, screen_y)  # Move cursor to start point
            time.sleep(0.1)  # Small delay to stabilize cursor movement

        self.drawing_active = True
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(screen_x, screen_y)  # Ensure drawing starts from initial point
        self.last_x, self.last_y = screen_x, screen_y

    def handle_highlighter_mode(self, screen_x, screen_y):
        """Handles highlighter drawing mode."""
        if not self.is_highlighter_active:
            self.deactivate_pen()
            pyautogui.hotkey('ctrl', 'i')
            self.is_highlighter_active = True
            self.last_x, self.last_y = screen_x, screen_y  # Store initial point
            pyautogui.moveTo(screen_x, screen_y)  # Move cursor to start point
            time.sleep(0.1)  # Small delay to stabilize cursor movement

        self.drawing_active = True
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(screen_x, screen_y)  # Ensure drawing starts from initial point
        self.last_x, self.last_y = screen_x, screen_y

    def deactivate_drawing_tools(self):
        """Deactivates all drawing tools."""
        if self.drawing_active:
            pyautogui.mouseUp(button='left')
        self.drawing_active = False
        self.is_pen_active = False
        self.is_highlighter_active = False
        self.last_x, self.last_y = None, None
    def deactivate_pen(self):
        """Deactivates pen tool."""
        if self.is_pen_active:
            pyautogui.mouseUp(button='left')
            self.is_pen_active = False

    def deactivate_highlighter(self):
        """Deactivates highlighter tool."""
        if self.is_highlighter_active:
            pyautogui.mouseUp(button='left')
            self.is_highlighter_active = False

    def click_video(self):
        """Simulates a mouse click to toggle video playback."""
        try:
            pyautogui.moveTo(self.screen_width // 2 + 50, self.screen_height // 2)
            time.sleep(1)
            pyautogui.moveTo(self.screen_width // 2, self.screen_height // 2)
            pyautogui.hotkey('alt', 'p')
        except Exception as e:
            print(f"Error toggling video: {e}")

    def move_slide_forward(self):
        """Simulates the 'right' arrow key to move forward in the presentation."""
        try:
            pyautogui.press('right')
        except Exception as e:
            print(f"Error moving forward: {e}")

    def move_slide_backward(self):
        """Simulates the 'left' arrow key to move backward in the presentation."""
        try:
            pyautogui.press('left')
        except Exception as e:
            print(f"Error moving backward: {e}")

    def trigger_zoom_out(self):
        """Simulates zoom-out action."""
        try:
            pyautogui.hotkey('ctrl', '-')
        except Exception as e:
            print(f"Error performing zoom-out: {e}")

    def trigger_zoom_in(self):
        """Simulates zoom-in action."""
        try:
            pyautogui.hotkey('ctrl', '+')
        except Exception as e:
            print(f"Error performing zoom-in: {e}")

    def close_application(self):
        """Closes the PowerPoint presentation and brings the app back to the foreground."""
        try:
            # Close the canvas if it exists and is active
            if hasattr(self, 'canvas_handler') and self.canvas_handler is not None:
                if self.canvas_handler.is_canvas_active:
                    self.canvas_handler.clear_canvas()
                    self.canvas_handler.is_canvas_active = False
            
            # Force quit PowerPoint to prevent any prompts
            os.system('taskkill /F /IM POWERPNT.EXE')
            
            # Release camera resources
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()

            # Bring the app back to the foreground
            self.master.deiconify()  # Ensure the app window is brought back
        except Exception as e:
            print(f"Error closing application: {e}")

    def reset_video_toggle_cooldown(self):
        self.video_toggle_cooldown = False

    def reset_slide_toggle_cooldown(self):
        self.slide_toggle_cooldown = False

    def reset_zoom_out_cooldown(self):
        self.zoom_out_cooldown = False

    def reset_zoom_in_cooldown(self):
        self.zoom_in_cooldown = False

    def reset_enter_cooldown(self):
        """Resets the enter key cooldown."""
        self.enter_cooldown = False

    def reset_close_cooldown(self):
        """Resets the close application cooldown."""
        self.close_cooldown = False

    def reset_camera(self):
        # Reset camera and gesture detection state
        self.gesture_error_count = 0
        if self.canvas_handler:
            self.canvas_handler.is_canvas_active = False
        # ...existing code...

def start_camera(camera_label):
    """Starts the camera feed and initializes gesture detection."""
    camera_handler = CameraHandler(camera_label, camera_label.master)
    camera_handler.start_camera()