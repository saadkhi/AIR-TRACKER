import os
import cv2
from PIL import Image, ImageTk
from cvzone.HandTrackingModule import HandDetector
import pyautogui
import time
from tkinter import Label
import comtypes.client
import keras
from canvas_handler import CanvasHandler

# Set Keras backend to "jax"
os.environ["KERAS_BACKEND"] = "jax"

# Import Keras and load the model with error handling
try:
    model = keras.saving.load_model("hf://saaday5/hand_gesture_model")
except FileNotFoundError as e:
    print(f"Error loading model: {e}")

class CameraHandler:
    """Handles the camera feed and gesture detection."""

    def __init__(self, camera_label, master):
        self.camera_label = camera_label
        self.master = master
        self.detector = HandDetector(detectionCon=0.7, maxHands=1)
        self.cap = cv2.VideoCapture(0)
        self.width, self.height = 300, 200
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

    def start_camera(self):
        """Starts the camera feed and initializes gesture detection."""
        if not self.cap.isOpened():
            print("Error: Could not open video device.")
            return

        self.cap.set(3, self.width)  # Set width
        self.cap.set(4, self.height)  # Set height

        self.update_frame()

    def update_frame(self):
        """Captures frames from the camera and processes gestures."""
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            hands, img = self.detector.findHands(img)

            if hands:
                hand = hands[0]
                fingers_up = self.detector.fingersUp(hand)
                lm_index = hand['lmList'][8] 
                lmlist = hand['lmList']
                indexfinger = lmlist[8][0], lmlist[8][1]  # Index finger tip coordinates
                
                # Map camera coordinates to screen coordinates
                screen_x = int(self.screen_width * (indexfinger[0] / self.width))
                screen_y = int(self.screen_height * (indexfinger[1] / self.height))

                self.handle_gestures(fingers_up, screen_x, screen_y, indexfinger)

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)

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
            else:
                # If cooldown is active, do not toggle the canvas
                pass
        
        if fingers_up == [0, 1, 0, 0, 0]:  # Index finger up (drawing mode with pointer)
            self.canvas_handler.set_drawing_mode(True)
            if self.canvas_handler.canvas:
                x, y = screen_x, screen_y

                # Ensure pointer moves along while drawing
                self.canvas_handler.canvas.delete("pointer")
                self.canvas_handler.canvas.create_oval(
                    x - 5, y - 5, x + 5, y + 5,
                    fill=self.canvas_handler.current_color, outline="black", tags="pointer"
                )

                # 🚀 BLOCK DRAWING OVER BUTTONS!
                if self.canvas_handler.check_pointer_over_buttons(x, y):
                    self.canvas_handler.set_drawing_mode(False)
                    return  

                if self.last_x is not None and self.last_y is not None:
                    self.canvas_handler.canvas.create_line(
                        self.last_x, self.last_y, x, y, fill=self.canvas_handler.current_color, width=5, smooth=True
                    )

                self.last_x, self.last_y = x, y

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
        # Video control with thumb and index finger
        if fingers_up == [1, 1, 0, 0, 0] and not self.video_toggle_cooldown:
            print("Gesture detected: Toggle Video")
            self.click_video()
            self.video_playing = not self.video_playing
            self.video_toggle_cooldown = True
            self.camera_label.after(2000, self.reset_video_toggle_cooldown)

        # Enter key with last three fingers
        elif fingers_up == [0, 0, 1, 1, 1] and not self.enter_cooldown:  # Middle, ring, and pinky for enter
            print("Gesture detected: Press Enter")
            pyautogui.press('enter')
            self.enter_cooldown = True
            self.camera_label.after(1000, self.reset_enter_cooldown)

        # Slide navigation
        elif fingers_up == [1, 0, 0, 0, 0] and not self.slide_toggle_cooldown:  # Thumb only for previous
            print("Gesture detected: Move Slide Backward")
            self.move_slide_backward()
            self.slide_toggle_cooldown = True
            self.camera_label.after(1000, self.reset_slide_toggle_cooldown)
        elif fingers_up == [0, 0, 0, 0, 1] and not self.slide_toggle_cooldown:  # Pinky only for next
            print("Gesture detected: Move Slide Forward")
            self.move_slide_forward()
            self.slide_toggle_cooldown = True
            self.camera_label.after(1000, self.reset_slide_toggle_cooldown)

        # Zoom controls
        elif fingers_up == [0, 1, 1, 1, 0] and not self.zoom_in_cooldown:  # Three middle fingers for zoom in
            print("Gesture detected: Zoom In")
            self.trigger_zoom_in()
            self.zoom_in_cooldown = True
            self.camera_label.after(1500, self.reset_zoom_in_cooldown)
        elif fingers_up == [0, 1, 1, 1, 1] and not self.zoom_out_cooldown:  # Four fingers for zoom out
            print("Gesture detected: Zoom Out")
            self.trigger_zoom_out()
            self.zoom_out_cooldown = True
            self.camera_label.after(1500, self.reset_zoom_out_cooldown)

        # Close application with thumb and pinky up
        elif fingers_up == [1, 0, 0, 0, 1] and not self.close_cooldown:
            print("Gesture detected: Close Application")
            self.close_application()
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
        """Closes the application with quick cleanup."""
        try:
            # Force quit PowerPoint first to prevent any prompts
            os.system('taskkill /F /IM POWERPNT.EXE')
            
            # Release camera resources
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()

            # Immediate exit
            os._exit(0)
        except:
            # Force exit if any error occurs
            os._exit(0)

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

def start_camera(camera_label):
    """Starts the camera feed and initializes gesture detection."""
    camera_handler = CameraHandler(camera_label, camera_label.master)
    camera_handler.start_camera()