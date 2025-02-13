import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_drawing = mp.solutions.drawing_utils

# Initialize OpenCV
cap = cv2.VideoCapture(0)

# Get the webcam frame dimensions
ret, frame = cap.read()
if not ret: 
    print("Failed to get frame from webcam")
    exit()
    
height, width = frame.shape[:2]
# Create a blank white canvas with same dimensions as webcam frame
canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

drawing = False  # Flag to check if drawing is active
erasing = False  # Flag to check if erasing is active
prev_x, prev_y = None, None  # Previous coordinates
drawing_color = (0, 0, 255)  # Default red color
eraser_size = 20  # Size of eraser

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Flip for a better experience
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process hand detection
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on frame for visualization
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get finger landmarks
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            
            # Get base positions for comparison
            thumb_base = hand_landmarks.landmark[2]  # CMC joint of thumb
            index_base = hand_landmarks.landmark[5]
            
            h, w, _ = frame.shape
            x, y = int(index_tip.x * w), int(index_tip.y * h)
            
            # Calculate distance between thumb and index finger
            pinch_distance = np.sqrt(
                (thumb_tip.x - index_tip.x)**2 + 
                (thumb_tip.y - index_tip.y)**2
            )
            
            # Check if thumb and index fingers are up
            thumb_up = thumb_tip.y < thumb_base.y
            index_up = index_tip.y < index_base.y
            
            # Check for pinch pose (drawing)
            if pinch_distance < 0.05:  # Threshold for pinch detection
                if not drawing:  # Start a new line
                    prev_x, prev_y = x, y
                drawing = True
                erasing = False
            # Check for eraser pose (thumb and index up)
            elif thumb_up and index_up:
                drawing = False
                erasing = True
                if prev_x is not None and prev_y is not None:
                    cv2.circle(canvas, (x, y), eraser_size, (255, 255, 255), -1)
            else:
                drawing = False
                erasing = False
                prev_x, prev_y = None, None

            # Draw on the canvas
            if drawing and prev_x is not None and prev_y is not None:
                cv2.line(canvas, (prev_x, prev_y), (x, y), drawing_color, 2)
            
            prev_x, prev_y = x, y

    # Merge the canvas and webcam feed
    combined = cv2.addWeighted(frame, 0.6, canvas, 0.4, 0)

    # Add instructions
    cv2.putText(combined, "Pinch to draw", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(combined, "Raise thumb & index finger to erase", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Hand Drawing", combined)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Quit
        break
    elif key == ord('c'):  # Clear canvas
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

cap.release()
cv2.destroyAllWindows()
