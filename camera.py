import cv2
import threading
from PIL import Image, ImageTk
from cvzone.HandTrackingModule import HandDetector
import pyautogui
import time
import numpy as np
import tensorflow as tf
from tkinter import Label


# Initialize the hand detector
detector = HandDetector(detectionCon=0.7, maxHands=1)


# Flags for cooldowns and video state
video_toggle_cooldown = False
slide_toggle_cooldown = False
zoom_out_cooldown = False
enter_key_cooldown = False
video_playing = False


# Load the trained model
model = tf.keras.models.load_model('Hand_Gest_Model.keras')


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
    global video_toggle_cooldown, slide_toggle_cooldown, zoom_out_cooldown, enter_key_cooldown, video_playing
    width, height = 300, 200
    cap = cv2.VideoCapture(0)


    if not cap.isOpened():
        print("Error: Could not open video device.")
        return


    cap.set(3, width)
    cap.set(4, height)


    def update_frame():
        global video_toggle_cooldown, slide_toggle_cooldown, zoom_out_cooldown, enter_key_cooldown, video_playing


        success, img = cap.read()
        if success:
            img = cv2.flip(img, 1)
            hands, img = detector.findHands(img)


            if hands:
                hand = hands[0]
                fingers_up = detector.fingersUp(hand)
                print(f"Fingers detected: {fingers_up}")  # Debugging information


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

                # Enter key gesture: Index, middle, and ring fingers up (2-second cooldown)
                elif fingers_up == [0, 1, 1, 1, 0] and not enter_key_cooldown:
                    trigger_enter_key()
                    enter_key_cooldown = True
                    camera_label.after(2000, reset_enter_key_cooldown)  # 2-second cooldown

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            camera_label.img_tk = img_tk
            if camera_label.winfo_exists():
                camera_label.config(image=img_tk)

        camera_label.after(30, update_frame)

    update_frame()

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

def trigger_enter_key():
    """Simulates pressing the 'Enter' key."""
    try:
        pyautogui.press('enter')
    except Exception as e:
        print(f"Error pressing Enter key: {e}")

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

def reset_enter_key_cooldown():
    """Resets the cooldown for enter key."""
    global enter_key_cooldown
    enter_key_cooldown = False
