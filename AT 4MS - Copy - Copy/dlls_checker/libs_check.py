import os
import sys
import tempfile
import ctypes
import webbrowser
import logging
from tkinter import messagebox, Tk

# === STEP 1: Configure Environment Variables ===
# These environment variables modify how TensorFlow and other libraries behave.

# Suppress TensorFlow INFO and WARNING messages (only show errors)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"

# Disable Intel oneDNN optimizations if they cause instability or unwanted performance tuning
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# === STEP 2: Setup comtypes Cache Directory ===
# This is used by libraries that depend on COM (e.g., pyttsx3 or pywinauto).
# Prevents clutter and issues by redirecting the COM cache to a known location.

comtypes_cache_dir = os.path.join(tempfile.gettempdir(), 'comtypes_cache')
os.environ['COMTYPES_CACHE'] = comtypes_cache_dir

try:
    if not os.path.exists(comtypes_cache_dir):
        os.makedirs(comtypes_cache_dir)
except Exception as e:
    print(f"[WARNING] Failed to create comtypes cache directory: {e}")

# === STEP 3: Prevent .pyc File Generation ===
# Helps in cleaner folder structures, especially for compiled or production builds.
sys.dont_write_bytecode = True

# === STEP 4: Setup Logging ===
# Optional but highly recommended for debugging and deployment.
log_file = os.path.join(tempfile.gettempdir(), "dependency_check.log")
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# === STEP 5: Check Required DLL Dependencies ===
def check_dll_dependencies():
    """
    Checks for the presence of critical Microsoft Visual C++ Redistributable DLLs.
    If any are missing, notifies the user via GUI and logs the missing files.
    """
    required_dlls = [
        'msvcp140.dll',
        'msvcp140_1.dll',
        'msvcp140_2.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll'
    ]
    
    missing_dlls = []

    for dll in required_dlls:
        try:
            # Try loading the DLL
            ctypes.CDLL(dll)
            logging.info(f"Found DLL: {dll}")
        except OSError:
            logging.error(f"Missing DLL: {dll}")
            missing_dlls.append(dll)
    
    if missing_dlls:
        # Initialize a hidden Tkinter root window for messagebox
        root = Tk()
        root.withdraw()

        # Prepare the GUI message
        message = (
            "Some required system files (DLLs) are missing. These files are part of the "
            "Microsoft Visual C++ Redistributable package needed to run this application.\n\n"
            f"Missing files:\n{', '.join(missing_dlls)}\n\n"
            "Would you like to download and install the required package now?"
        )

        # Show messagebox prompt
        user_choice = messagebox.askyesno("Missing Dependencies", message)

        if user_choice:
            logging.info("User chose to download the Visual C++ Redistributable.")
            webbrowser.open("https://aka.ms/vs/17/release/vc_redist.x64.exe")
        else:
            logging.info("User declined to download dependencies.")

        logging.warning("Exiting application due to missing DLLs.")
        sys.exit(1)

    else:
        print("[✓] All required Visual C++ DLLs are present.")
        logging.info("All required DLLs found. Application ready.")


# === STEP 6: Main Entry Point ===
# Ensures the script runs only when executed directly, not on import.

if __name__ == "__main__":
    print("[*] Checking system environment and dependencies...")
    logging.info("Starting DLL dependency check.")
    
    check_dll_dependencies()

    # Additional startup logic for your app can go here
    print("[*] System ready. You may proceed with application logic.")
    logging.info("Dependency check completed. Proceeding to application.")
