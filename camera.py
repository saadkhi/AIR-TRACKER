import cv2
import threading
from PIL import Image, ImageTk
from cvzone.HandTrackingModule import HandDetector
import pyautogui
import time
import numpy as np
import tensorflow as tf
from tkinter import Label
from utils import zoom_in_slide  # Import the zoom in function

# Available backend options are: "jax", "torch", "tensorflow".
import os
os.environ["KERAS_BACKEND"] = "jax"

import keras
from huggingface_hub import hf_hub_download

# Download the model file from Hugging Face Hub
model_path = hf_hub_download(repo_id="saaday5/hand_gesture_model", filename="Hand_Gest_Model.keras")

# Load the trained model
model = keras.models.load_model(model_path)

# Initialize the hand detector
detector = HandDetector(detectionCon=0.7, maxHands=1)

# Flags for cooldowns and video state
video_toggle_cooldown = False
slide_toggle_cooldown = False
zoom_out_cooldown = False
enter_key_cooldown = False
video_playing = False

def preprocess_hand_image(hand_bbox, img):
    """Extracts and preprocesses the hand region for the model."""
    x, y, w, h = hand_bbox
    hand_img = img[y:y + h, x:x + w]
    hand_img = cv2.resize(hand_img, (64, 64))  # Assuming the model expects 64x64 input
    hand_img = cv2.cvtColor(hand_img, cv2.COLOR_BGR2RGB)
    hand_img = hand_img / 255.0  # Normalize to [0, 1]
    hand_img = np.expand_dims(hand_img, axis=0)  # Add batch dimension
    return hand_img

def process_gesture(gesture):
    """Processes the detected gesture and triggers corresponding actions."""
    if gesture == [1, 1, 0, 0, 0] and not video_toggle_cooldown:
        click_video()  # Toggle video playback
        video_playing = not video_playing  # Update playback state
        video_toggle_cooldown = True
        camera_label.after(2000, reset_video_toggle_cooldown)  # 2-second cooldown

    elif gesture == [1, 0, 0, 0, 0] and not slide_toggle_cooldown:  # Thumb up to move left
        move_slide_backward()
        slide_toggle_cooldown = True
        camera_label.after(1000, reset_slide_toggle_cooldown)  # 1-second cooldown

    elif gesture == [0, 0, 0, 0, 1] and not slide_toggle_cooldown:  # Pinky up to move right
        move_slide_forward()
        slide_toggle_cooldown = True
        camera_label.after(1000, reset_slide_toggle_cooldown)  # 1-second cooldown

    elif gesture == [0, 1, 1, 1, 1] and not zoom_out_cooldown:  # Zoom-out gesture: 4 fingers without thumb (3-second cooldown)
        trigger_zoom_out()
        zoom_out_cooldown = True
        camera_label.after(3000, reset_zoom_out_cooldown)  # 3-second cooldown

    elif gesture == [0, 1, 1, 1, 0] and not enter_key_cooldown:  # Enter key gesture: Index, middle, and ring fingers up (2-second cooldown)
        trigger_enter_key()
        enter_key_cooldown = True
        camera_label.after(2000, reset_enter_key_cooldown)  # 2-second cooldown

    elif gesture == [0, 0, 1, 1, 1]:  # Zoom-in gesture: Middle, ring, and pinky fingers up
        zoom_in_slide()

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
