# AIR TRACKER: Gesture-Controlled PowerPoint

## Description

AIR TRACKER is a Python-based application that allows you to control PowerPoint presentations using hand gestures. It provides a user-friendly interface for uploading PowerPoint files and utilizes a camera feed to detect and interpret hand movements for actions like slide navigation, video control, and more.

## Features

*   **Gesture-Based Control:** Control your PowerPoint presentations with intuitive hand gestures.
*   **User-Friendly GUI:** Simple and visually appealing interface built with Tkinter and CustomTkinter.
*   **Real-time Camera Overlay:** Integrates a camera feed for real-time gesture detection.
*   **PowerPoint Automation:** Automates PowerPoint actions such as slide navigation and video playback.
*   **Customizable Gestures:** (Future Enhancement) Configure gestures to suit your preferences.

## Installation

1.  **Prerequisites:**
    *   Python 3.6 or higher
    *   pip package installer

2.  **Clone the repository:**

    ```bash
    git clone [repository URL]
    cd [repository directory]
    ```

3.  **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**

    ```bash
    python main.py
    ```

2.  **Upload PowerPoint File:** Click the "Upload PowerPoint File" button to select your presentation.

3.  **Gesture Control:** Once the presentation starts, use the defined hand gestures to control the slides and video playback.

## Dependencies

*   ctypes
*   customtkinter
*   tkinter
*   PIL (Pillow)
*   cvzone
*   pyautogui
*   comtypes
*   tensorflow
*   opencv-python

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bug fixes, feature requests, or improvements.

## License

[Choose a license - e.g., MIT License]

## Acknowledgements

*   This project utilizes the cvzone library for hand tracking.
*   CustomTkinter provides the modern UI elements.

## Future Enhancements

*   Implement zoom in/out functionality.
*   Add pen and pointer tools.
*   Allow users to customize gesture mappings.
*   Improve gesture recognition accuracy.
*   Add support for other presentation software.
