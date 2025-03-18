# AIR TRACKER

AIR TRACKER is an innovative application that enables gesture-based control for PowerPoint presentations and other functionalities. It uses computer vision and hand gesture recognition to provide a seamless, touch-free experience.

## Features

- **Gesture-Based Control**: Navigate slides, zoom in/out, and toggle video playback using hand gestures.
- **Virtual Canvas**: Draw, highlight, or erase on a virtual canvas overlay.
- **Camera Feed Overlay**: Display a live camera feed during presentations.
- **PowerPoint Integration**: Open, control, and close PowerPoint presentations programmatically.
- **Customizable Tools**: Switch between pen, highlighter, and eraser tools with ease.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/AIR-TRACKER.git
   cd AIR-TRACKER
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have a webcam connected for gesture detection.

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Use the GUI to upload a PowerPoint file and start the presentation.

3. Use the following gestures for control:
   - **Index and Pinky Fingers Up**: Toggle the virtual canvas.
   - **Thumb Up**: Move to the previous slide.
   - **Pinky Up**: Move to the next slide.
   - **Four Fingers Up**: Zoom out.
   - **Three Middle Fingers Up**: Zoom in.
   - **Thumb and Pinky Up**: Close the application.

4. Use the virtual canvas to draw, highlight, or erase using the tools provided.

## Project Structure

```
AIR-TRACKER/
├── main.py               # Main GUI application
├── utils.py              # Utility functions for PowerPoint control
├── new.py                # Gesture detection and camera handling
├── canvas_handler.py     # Virtual canvas overlay functionality
├── camera.py             # Camera feed and gesture processing
├── requirements.txt      # Project dependencies
├── media/                # Media assets (icons, images)
└── README.md             # Project documentation
```

## Requirements

- Python 3.8 or higher
- A webcam for gesture detection
- Windows OS (for PowerPoint integration)

## Dependencies

The project uses the following Python libraries:
- `customtkinter`
- `Pillow`
- `opencv-python`
- `cvzone`
- `mediapipe`
- `numpy`
- `keras`
- `pyautogui`
- `pynput`
- `comtypes`
- `pywin32`

Refer to `requirements.txt` for exact versions.

## Known Issues

- Ensure the PowerPoint file is valid and accessible.
- The application is optimized for Windows OS and may not work on other platforms.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- [Mediapipe](https://mediapipe.dev/) for hand tracking.
- [OpenCV](https://opencv.org/) for image processing.
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI.

Feel free to contribute to the project by submitting issues or pull requests!
