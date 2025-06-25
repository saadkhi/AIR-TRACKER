import cv2
import threading
from PIL import Image, ImageTk
from cvzone.HandTrackingModule import HandDetector
import pyautogui
import time
import numpy as np
import keras
from tkinter import Label
import comtypes.client
import os
import mediapipe as mp  # Add this import

# Available backend options are: "jax", "torch", "tensorflow".
os.environ["KERAS_BACKEND"] = "jax"

# Initialize the hand detector
detector = HandDetector(detectionCon=0.7, maxHands=1)

# Flags for cooldowns and video state
video_toggle_cooldown = False
slide_toggle_cooldown = False
zoom_out_cooldown = False
zoom_in_cooldown = False  # Added zoom-in cooldown
enter_key_cooldown = False
close_ppt_cooldown = False  # Added close PPT cooldown
video_playing = False

# Load the trained model
try:
    model = keras.saving.load_model("hf://saaday5/hand_gesture_model")
except FileNotFoundError as e:
    print(f"Error loading model: {e}")
    model = None

# Initialize Mediapipe Hands object for hand tracking
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpdraw = mp.solutions.drawing_utils

# Define the folder where the color images are stored
folder = 'colors'
mylist = os.listdir(folder)
overlist = []
col = [0, 0, 255]  # Default color (red)

# Load images from the folder and append them to the list
for i in mylist:
    image = cv2.imread(f'{folder}/{i}')
    overlist.append(image)

# Set the initial header image from the first image in the list
header = overlist[0]

xp, yp = 0, 0

# Create a blank canvas to draw on
canvas = np.zeros((480, 640, 3), np.uint8)

# class GestureHandler:
#     def __init__(self):
#         self.is_pen_active = False
#         self.is_highlighter_active = False
#         self.drawing_active = False
#         self.last_x, self.last_y = None, None
#         self.screen_width, self.screen_height = pyautogui.size()
#         self.drawing_positions = []

#     def handle_pen_mode(self, screen_x, screen_y):
#         """Handles pen drawing mode."""
#         if not self.is_pen_active:
#             self.deactivate_highlighter()
#             pyautogui.hotkey('ctrl', 'p')
#             self.is_pen_active = True
#             self.last_x, self.last_y = None, None

#         self.drawing_active = True
#         pyautogui.mouseDown(button='left')

#         if self.last_x is not None and self.last_y is not None:
#             pyautogui.moveTo(screen_x, screen_y)
#         self.last_x, self.last_y = screen_x, screen_y

#     def handle_highlighter_mode(self, screen_x, screen_y):
#         """Handles highlighter drawing mode."""
#         if not self.is_highlighter_active:
#             self.deactivate_pen()
#             pyautogui.hotkey('ctrl', 'i')
#             self.is_highlighter_active = True
#             self.last_x, self.last_y = None, None

#         self.drawing_active = True
#         pyautogui.mouseDown(button='left')

#         if self.last_x is not None and self.last_y is not None:
#             pyautogui.moveTo(screen_x, screen_y)
#         self.last_x, self.last_y = screen_x, screen_y

#     def deactivate_drawing_tools(self):
#         """Deactivates all drawing tools."""
#         if self.drawing_active:
#             pyautogui.mouseUp(button='left')
#         self.drawing_active = False
#         self.is_pen_active = False
#         self.is_highlighter_active = False
#         self.last_x, self.last_y = None, None

#     def deactivate_pen(self):
#         """Deactivates pen tool."""
#         if self.is_pen_active:
#             pyautogui.mouseUp(button='left')
#             self.is_pen_active = False

#     def deactivate_highlighter(self):
#         """Deactivates highlighter tool."""
#         if self.is_highlighter_active:
#             pyautogui.mouseUp(button='left')
#             self.is_highlighter_active = False

def preprocess_hand_image(hand_bbox, img):
    """Extracts and preprocesses the hand region for the model."""
    x, y, w, h = hand_bbox
    hand_img = img[y:y + h, x:x + w]
    hand_img = cv2.resize(hand_img, (64, 64))  # Assuming the model expects 64x64 input
    hand_img = cv2.cvtColor(hand_img, cv2.COLOR_BGR2RGB)
    hand_img = hand_img / 255.0  # Normalize to [0, 1]
    hand_img = np.expand_dims(hand_img, axis=0)  # Add batch dimension
    return hand_img

def start_camera(camera_label: Label):
    """Starts the camera feed and gesture detection."""
    global video_toggle_cooldown, slide_toggle_cooldown, zoom_out_cooldown, zoom_in_cooldown, enter_key_cooldown, close_ppt_cooldown, video_playing
    width, height = 300, 200
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    cap.set(3, width)
    cap.set(4, height)

    # gesture_handler = GestureHandler()

    def update_frame():
        global video_toggle_cooldown, slide_toggle_cooldown, zoom_out_cooldown, zoom_in_cooldown, enter_key_cooldown, close_ppt_cooldown, video_playing

        success, img = cap.read()
        if success:
            img = cv2.flip(img, 1)
            hands, img = detector.findHands(img)

            if hands:
                hand = hands[0]
                fingers_up = detector.fingersUp(hand)
                print(f"Fingers detected: {fingers_up}")  # Debugging information

                # Get the screen coordinates of the hand
                lm_list = hand['lmList']
                screen_x, screen_y = pyautogui.size()
                screen_x = int(lm_list[8][0] / width * screen_x)
                screen_y = int(lm_list[8][1] / height * screen_y)

                # Play/pause toggle gesture with 2-second cooldown
                if fingers_up == [1, 1, 0, 0, 0] and not video_toggle_cooldown:
                    click_video()  # Toggle video playback
                    video_playing = not video_playing  # Update playback state
                    video_toggle_cooldown = True
                    camera_label.after(2000, reset_video_toggle_cooldown)  # 2-second cooldown

                # Slide navigation gestures
                elif fingers_up == [1, 0, 0, 0, 0]:  # Thumb up to move left
                    if not slide_toggle_cooldown:
                        move_slide_backward()
                        slide_toggle_cooldown = True
                        camera_label.after(1000, reset_slide_toggle_cooldown)  # 1-second cooldown

                elif fingers_up == [0, 0, 0, 0, 1]:  # Pinky up to move right
                    if not slide_toggle_cooldown:
                        move_slide_forward()
                        slide_toggle_cooldown = True
                        camera_label.after(1000, reset_slide_toggle_cooldown)  # 1-second cooldown

                # Zoom-out gesture: 4 fingers without thumb (3-second cooldown)
                elif fingers_up == [0, 1, 1, 1, 1] and not zoom_out_cooldown:
                    trigger_zoom_out()
                    zoom_out_cooldown = True
                    camera_label.after(3000, reset_zoom_out_cooldown)  # 3-second cooldown

                # Zoom-in gesture: 3 fingers (index, middle, ring) up (1-second cooldown)
                elif fingers_up == [0, 0, 1, 1, 1] and not zoom_in_cooldown:
                    trigger_zoom_in()
                    zoom_in_cooldown = True
                    camera_label.after(1000, reset_zoom_in_cooldown)  # 1-second cooldown

                # Enter key gesture: Index, middle, and ring fingers up (2-second cooldown)
                elif fingers_up == [0, 1, 1, 1, 0] and not enter_key_cooldown:
                    trigger_enter_key()
                    enter_key_cooldown = True
                    camera_label.after(2000, reset_enter_key_cooldown)  # 2-second cooldown

                # Close PPT gesture: Thumb and pinky up (2-second cooldown)
                elif fingers_up == [1, 0, 0, 0, 1] and not close_ppt_cooldown:
                    save_and_close_ppt()
                    close_ppt_cooldown = True
                    camera_label.after(2000, reset_close_ppt_cooldown)  # 2-second cooldown

                else:
                    # gesture_handler.deactivate_drawing_tools()
                    pass

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            camera_label.img_tk = img_tk
            if camera_label.winfo_exists():
                camera_label.config(image=img_tk)

        camera_label.after(30, update_frame)

    update_frame()

def handle_virtual_painter(img):
    """Handles the virtual painter functionality."""
    global xp, yp, col, header, canvas

    # Convert the frame to RGB color space for hand tracking
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Process the frame to detect hand landmarks
    results = hands.process(img_rgb)
    lanmark = []

    if results.multi_hand_landmarks:
        for hn in results.multi_hand_landmarks:
            for id, lm in enumerate(hn.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lanmark.append([id, cx, cy])
            mpdraw.draw_landmarks(img, hn, mpHands.HAND_CONNECTIONS)

    if len(lanmark) != 0:
        # Check if the hand is in "selection mode" or "drawing mode"
        x1, y1 = lanmark[8][1], lanmark[8][2]
        x2, y2 = lanmark[12][1], lanmark[12][2]

        if lanmark[8][2] < lanmark[6][2] and lanmark[12][2] < lanmark[10][2]:
            xp, yp = 0, 0
            print('Selection mode')

            # Detect the color chosen by the hand position
            if y1 < 100:
                if 71 < x1 < 142:
                    header = overlist[7]
                    col = (0, 0, 0)
                if 142 < x1 < 213:
                    header = overlist[6]
                    col = (226, 43, 138)
                # ... Other color conditions ...

            # Draw a rectangle representing the selected color
            cv2.rectangle(img, (x1, y1), (x2, y2), col, cv2.FILLED)

        elif lanmark[8][2] < lanmark[6][2]:
            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            # Draw lines on the canvas when in "drawing mode"
            if col == (0, 0, 0):
                cv2.line(img, (xp, yp), (x1, y1), col, 100, cv2.FILLED)
                cv2.line(canvas, (xp, yp), (x1, y1), col, 100, cv2.FILLED)
            cv2.line(img, (xp, yp), (x1, y1), col, 25, cv2.FILLED)
            cv2.line(canvas, (xp, yp), (x1, y1), col, 25, cv2.FILLED)
            print('Drawing mode')
            xp, yp = x1, y1

    # Resize the canvas to match the dimensions of img
    canvas = cv2.resize(canvas, (img.shape[1], img.shape[0]))

    # Prepare the canvas for blending with the frame
    imgGray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)

    # Use bitwise operations to blend the frame with the canvas
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, canvas)

    # Resize the header to match the width of img
    header_resized = cv2.resize(header, (img.shape[1], 100))

    # Add the header (color selection) at the top of the frame
    img[0:100, 0:img.shape[1]] = header_resized

    return img

def click_video():
    """Simulates a mouse click to toggle video playback."""
    try:
        screen_width, screen_height = pyautogui.size()
        pyautogui.moveTo(screen_width // 2 + 50, screen_height // 2)
        time.sleep(1)
        pyautogui.moveTo(screen_width // 2, screen_height // 2)
        pyautogui.hotkey('alt', 'p')
    except Exception as e:
        print(f"Error toggling video: {e}")

def move_slide_forward():
    """Simulates the 'right' arrow key to move forward in the presentation."""
    try:
        pyautogui.press('right')
    except Exception as e:
        print(f"Error moving forward: {e}")

def move_slide_backward():
    """Simulates the 'left' arrow key to move backward in the presentation."""
    try:
        pyautogui.press('left')
    except Exception as e:
        print(f"Error moving backward: {e}")

def trigger_zoom_out():
    """Simulates zoom-out action."""
    try:
        pyautogui.hotkey('ctrl', '-')
    except Exception as e:
        print(f"Error performing zoom-out: {e}")

def trigger_zoom_in():
    """Simulates zoom-in action."""
    try:
        pyautogui.hotkey('ctrl', '+')
    except Exception as e:
        print(f"Error performing zoom-in: {e}")

def trigger_enter_key():
    """Simulates pressing the 'Enter' key."""
    try:
        pyautogui.press('enter')
    except Exception as e:
        print(f"Error pressing Enter key: {e}")

def save_and_close_ppt():
    """Saves and closes the PowerPoint presentation and returns to the system screen."""
    try:
        powerpoint = comtypes.client.GetActiveObject("PowerPoint.Application")
        if powerpoint.Presentations.Count > 0:
            for presentation in powerpoint.Presentations:
                presentation.Save()
                presentation.Close()
        powerpoint.Quit()
        time.sleep(2)  # Add a delay before minimizing all windows
        pyautogui.hotkey('win', 'd')  # Minimize all windows to show the desktop
    except Exception as e:
        print(f"Error saving and closing PowerPoint: {e}")

def reset_video_toggle_cooldown():
    """Resets the cooldown for video toggle."""
    global video_toggle_cooldown
    video_toggle_cooldown = False

def reset_slide_toggle_cooldown():
    """Resets the cooldown for slide navigation."""
    global slide_toggle_cooldown
    slide_toggle_cooldown = False

def reset_zoom_out_cooldown():
    """Resets the cooldown for zoom out."""
    global zoom_out_cooldown
    zoom_out_cooldown = False

def reset_zoom_in_cooldown():
    """Resets the cooldown for zoom in."""
    global zoom_in_cooldown
    zoom_in_cooldown = False

def reset_enter_key_cooldown():
    """Resets the cooldown for enter key."""
    global enter_key_cooldown
    enter_key_cooldown = False

def reset_close_ppt_cooldown():
    """Resets the cooldown for closing the PowerPoint presentation."""
    global close_ppt_cooldown
    close_ppt_cooldown = False