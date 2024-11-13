import os
import io
import cv2
import numpy as np
from PIL import ImageGrab
import requests
import pyperclip
from pynput import keyboard
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Retrieve Imgur credentials
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
IMGUR_CLIENT_SECRET = os.getenv("IMGUR_CLIENT_SECRET")

if not IMGUR_CLIENT_ID or not IMGUR_CLIENT_SECRET:
    raise ValueError("Imgur Client ID or Secret not set in the .env file.")

IMGUR_UPLOAD_URL = "https://api.imgur.com/3/image"

# Global variables for area selection
start_x, start_y, end_x, end_y = None, None, None, None
is_selecting = False

# Function to capture a specific area
def capture_selected_area():
    global start_x, start_y, end_x, end_y
    if None in (start_x, start_y, end_x, end_y):
        print("Selection not complete!")
        return None
    bbox = (min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y))
    return ImageGrab.grab(bbox=bbox)

# Function to upload the image to Imgur
def upload_to_imgur(image):
    with io.BytesIO() as output:
        image.save(output, format="PNG")
        output.seek(0)
        headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
        files = {"image": output.getvalue()}
        try:
            response = requests.post(IMGUR_UPLOAD_URL, headers=headers, files=files)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return data["data"]["link"]
            else:
                print(f"Error from Imgur: {data}")
                return None
        except requests.RequestException as e:
            print(f"Error uploading to Imgur: {e}")
            return None

# Function to copy text to clipboard
def copy_to_clipboard(text):
    pyperclip.copy(text)
    print("URL copied to clipboard.")

# Mouse callback to handle area selection
def mouse_callback(event, x, y, flags, param):
    global start_x, start_y, end_x, end_y, is_selecting, screen_copy

    if event == cv2.EVENT_LBUTTONDOWN:  # Start selection
        start_x, start_y = x, y
        is_selecting = True

    elif event == cv2.EVENT_MOUSEMOVE and is_selecting:  # Highlight selection
        end_x, end_y = x, y
        temp_screen = screen_copy.copy()
        cv2.rectangle(temp_screen, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        cv2.imshow("Select Area", temp_screen)

    elif event == cv2.EVENT_LBUTTONUP:  # End selection
        end_x, end_y = x, y
        is_selecting = False
        cv2.destroyAllWindows()

# Function to trigger area selection and Imgur upload
def on_activate():
    global screen_copy

    print("Shortcut detected! Starting area selection.")

    # Capture the current screen for area selection
    screen = np.array(ImageGrab.grab())
    screen_copy = screen.copy()

    cv2.namedWindow("Select Area", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Select Area", mouse_callback)
    cv2.imshow("Select Area", screen_copy)
    cv2.waitKey(0)  # Wait until area selection is completed

    # Capture the selected area
    screenshot = capture_selected_area()
    if screenshot:
        print("Screenshot captured successfully.")
        imgur_url = upload_to_imgur(screenshot)
        if imgur_url:
            print(f"Image uploaded successfully: {imgur_url}")
            copy_to_clipboard(imgur_url)

    print("Exiting script...")
    os._exit(0)  # Ensure a clean exit after completion

# Keyboard listener for the shortcut (Ctrl+Alt+Space)
def main():
    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+<space>': on_activate}) as hotkey_listener:
        print("Listening for the shortcut Ctrl+Alt+Space...")
        hotkey_listener.join()

if __name__ == "__main__":
    main()
