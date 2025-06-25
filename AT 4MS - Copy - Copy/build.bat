@echo off
echo Building AIR-TRACKER with all dependencies...

REM Check if Visual C++ DLLs exist
if not exist "C:\Windows\System32\msvcp140.dll" (
    echo Warning: Visual C++ DLLs not found. The built application may require Visual C++ Redistributable on target systems.
    pause
)

REM Create build command with all dependencies
pyinstaller --name "AIR-TRACKER" ^
--onedir ^
--add-data "media;media" ^
--add-binary "C:\Windows\System32\msvcp140.dll;." ^
--add-binary "C:\Windows\System32\msvcp140_1.dll;." ^
--add-binary "C:\Windows\System32\msvcp140_2.dll;." ^
--add-binary "C:\Windows\System32\vcruntime140.dll;." ^
--add-binary "C:\Windows\System32\vcruntime140_1.dll;." ^
--hidden-import cv2 ^
--hidden-import cv2.data ^
--hidden-import mediapipe ^
--collect-data mediapipe ^
--hidden-import cvzone.HandTrackingModule ^
--hidden-import PIL ^
--hidden-import PIL.Image ^
--hidden-import PIL.ImageTk ^
--hidden-import numpy ^
--hidden-import pyautogui ^
--hidden-import comtypes ^
--hidden-import comtypes.client ^
--hidden-import comtypes.gen ^
--hidden-import comtypes.client._code_cache ^
--hidden-import customtkinter ^
--hidden-import tkinter ^
--hidden-import tkinter.messagebox ^
--hidden-import win32gui ^
--hidden-import win32con ^
--hidden-import pynput ^
--hidden-import pynput.mouse ^
--hidden-import tensorflow ^
--hidden-import tensorflow.python ^
--hidden-import tensorflow.python.platform ^
--collect-data cvzone ^
--collect-data comtypes ^
main.py

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo Build completed successfully!
echo The executable can be found in the dist/AIR-TRACKER directory.

REM Copy Visual C++ Redistributable installer
echo Downloading Visual C++ Redistributable installer...
powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'dist/AIR-TRACKER/vc_redist.x64.exe'}"

REM Create a README file
echo Creating README file...
echo AIR-TRACKER > "dist/AIR-TRACKER/README.txt"
echo =========== >> "dist/AIR-TRACKER/README.txt"
echo. >> "dist/AIR-TRACKER/README.txt"
echo Prerequisites: >> "dist/AIR-TRACKER/README.txt"
echo 1. Microsoft Visual C++ Redistributable for Visual Studio 2015-2019 >> "dist/AIR-TRACKER/README.txt"
echo    - If not installed, run vc_redist.x64.exe included in this package >> "dist/AIR-TRACKER/README.txt"
echo. >> "dist/AIR-TRACKER/README.txt"
echo Installation: >> "dist/AIR-TRACKER/README.txt"
echo 1. Run vc_redist.x64.exe if you haven't installed Visual C++ Redistributable >> "dist/AIR-TRACKER/README.txt"
echo 2. Run AIR-TRACKER.exe >> "dist/AIR-TRACKER/README.txt"

echo.
echo Build process complete! Press any key to exit.
pause 