import os
import threading
import ctypes
import customtkinter as ctk
import tkinter as tk
from tkinter import Tk, filedialog, messagebox, Label, Frame, X, BOTTOM
from PIL import Image, ImageTk
from utils import focus_powerpoint_window, run_powerpoint, initialize_listener

# Initialize mouse listener for focusing PowerPoint
initialize_listener()

# Tkinter GUI
root = Tk()
root.title("AIR TRACKER")
root.geometry("1350x700")
root.configure(bg="#a91f2d")

# Header
header_label = tk.Label(
    root,
    text="AIR TRACKER",
    font=("Georgia", 36, "italic", "bold"),
    bg="#a91f2d",
    fg="white"
)
header_label.pack(pady=10)

# Load and display the image
try:
    image_path = "media/hand.png"
    original_image = Image.open(image_path)
    resized_image = original_image.resize((300, 300))
    my_image = ImageTk.PhotoImage(resized_image)
    image_label = Label(root, image=my_image, bg="#a91f2d")
    image_label.pack(pady=20)
except Exception as e:
    messagebox.showerror("Error", f"Could not load image: {e}")

# Set the icon on Windows
icon_path = "media/hand.ico"
if os.name == 'nt':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"MyAppID")
    root.iconbitmap(icon_path)

def run_presentation():
    ppt_file = filedialog.askopenfilename(
        title="Select PowerPoint file",
        filetypes=[("PowerPoint Files", "*.pptx *.ppt")]
    )
    if ppt_file:
        try:
            if os.path.exists(ppt_file):
                root.iconify()
                threading.Thread(target=run_powerpoint, args=(ppt_file, root), daemon=True).start()
            else:
                messagebox.showerror("File Not Found", f"The file could not be found: {ppt_file}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

# Footer with white background
footer_frame = Frame(root, bg="white", height=50, width=1400)
footer_frame.pack(side=BOTTOM, fill=X)

footer_label = tk.Label(
    footer_frame,
    text="Wave goodbye to clicks and embrace gestures.",
    font=("Georgia", 16, "italic"),
    bg="white",
    fg="#a91f2d"
)
footer_label.pack(pady=10)

# Rounded button below the image
def on_hover(event):
    upload_button.configure(fg_color="white", text_color="red")

def on_leave(event):
    upload_button.configure(fg_color="white", text_color="#a91f2d")

upload_button = ctk.CTkButton(
    root,
    text="Upload PowerPoint File",
    command=run_presentation,
    font=("Arial", 20, "bold"),
    fg_color="white",
    text_color="#a91f2d",
    hover_color="#ff7373",
    corner_radius=20,
    width=200,
    height=50
)

upload_button.bind("<Enter>", on_hover)
upload_button.bind("<Leave>", on_leave)
upload_button.pack(pady=20)

root.mainloop()
