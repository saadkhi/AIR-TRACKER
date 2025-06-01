import subprocess
import os
import sys
import logging
import comtypes.client
import cv2
import time
from comtypes import COMError

class PowerPointWrapper:
    """Wrapper for PowerPoint COM interface with error handling."""
    
    MAX_RETRIES = 3
    RPC_ERROR_CODE = -2147023174
    
    @staticmethod
    def start_presentation(ppt_file):
        """Starts a PowerPoint presentation."""
        logger = logging.getLogger('AirTracker')
        powerpoint = None
        
        for attempt in range(PowerPointWrapper.MAX_RETRIES):
            try:
                logger.debug(f"Attempt {attempt + 1} to start PowerPoint")
                powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
                powerpoint.Visible = 1
                
                logger.debug(f"Opening presentation: {ppt_file}")
                presentation = powerpoint.Presentations.Open(ppt_file)
                
                logger.debug("Setting up slideshow")
                slideshow = presentation.SlideShowSettings
                slideshow.Run()
                return True
                
            except COMError as e:
                if e.args[0] == PowerPointWrapper.RPC_ERROR_CODE:
                    logger.error(f"RPC server error (attempt {attempt + 1}): {e}")
                    if attempt < PowerPointWrapper.MAX_RETRIES - 1:
                        logger.info("Waiting before retry...")
                        time.sleep(2)  # Wait before retry
                        PowerPointWrapper.cleanup_powerpoint()
                        continue
                    else:
                        logger.error("Max retries reached. PowerPoint could not be started.")
                        return False
                else:
                    logger.error(f"COM error: {e}")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False
                
        return False

    @staticmethod
    def cleanup_powerpoint():
        """Safely cleanup PowerPoint processes with enhanced termination."""
        logger = logging.getLogger('AirTracker')
        try:
            # Try to close any open presentations first
            try:
                powerpoint = comtypes.client.GetActiveObject("PowerPoint.Application")
                powerpoint.Quit()
            except:
                pass

            # First attempt - normal termination
            subprocess.run(
                ["taskkill", "/IM", "POWERPNT.EXE"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(0.5)
            
            # Second attempt - force termination
            subprocess.run(
                ["taskkill", "/F", "/IM", "POWERPNT.EXE"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Final check - ensure PowerPoint is really closed
            time.sleep(0.5)
            try:
                subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq POWERPNT.EXE"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                if "POWERPNT.EXE" in output:
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "POWERPNT.EXE", "/T"],
                        check=False
                    )
            except:
                pass

            return True

        except Exception as e:
            logger.error(f"Error during PowerPoint cleanup: {e}")
            return False

class CameraWrapper:
    """Wrapper for camera operations."""
    
    @staticmethod
    def get_available_cameras():
        """Returns list of available camera indices."""
        available = []
        for i in range(3):  # Check first 3 indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
        
class SystemWrapper:
    """Wrapper for system operations."""
    
    @staticmethod
    def kill_process(process_name):
        """Forcefully kills a process by name."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", f"{process_name}.EXE"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except subprocess.CalledProcessError:
            return False