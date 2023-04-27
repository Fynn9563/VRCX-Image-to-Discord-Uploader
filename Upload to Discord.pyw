from tkinter import Tk, Button, Label, filedialog, messagebox, ttk, Entry
import sys
import os
import json
import datetime
import importlib
import requests
from PIL import Image

def upload_image_to_discord():
    try:
        # Get file path from file dialog
        file_path = file_path_textbox.get()

        # Check if file was selected
        if not file_path:
            return

        # Get webhook URL from user input
        webhook_url = webhook_entry.get()

        # Check if webhook URL is valid
        if not webhook_url.startswith('https://discord.com/api/webhooks/'):
            messagebox.showerror("Error", "Invalid webhook URL.")
            return
		
        # Create progress bar
        progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="indeterminate")
        progress_bar.pack()

        # Start progress bar
        progress_bar.start()

        # Extract image data
        with open(file_path, 'rb') as f:
            image_data = f.read()

        # Extract image description
        with Image.open(file_path) as img:
            description = img.info.get('Description')

            # Check if image has metadata
            if not description:
                messagebox.showerror("Error", "The selected image has no metadata.")
                progress_bar.stop()
                progress_bar.pack_forget()
                return

        # Extract world name and display names from description
        world_name = 'unknown'
        player_names = []
        if description:
            try:
                desc = json.loads(description)
                world_name = desc['world']['name']
                world_id = desc['world']['id']
                players = desc['players']
                player_names = [player['displayName'] for player in players]
            except KeyError:
                pass

        # Get file creation time
        timestamp = os.stat(file_path).st_ctime
        
        # Create payload
        payload = {
            "content": f"Photo taken at **{world_name}** *({world_id})* with **{', '.join(player_names)}** at <t:{int(timestamp)}:f>"
        }

        # Send payload to webhook with image attached
        files = {'file': (file_path, image_data)}
        response = requests.post(webhook_url, data=payload, files=files)

        # Stop progress bar
        progress_bar.stop()
        progress_bar.pack_forget()

        # Check for successful response
        if response.status_code != 200:
            messagebox.showerror("Error", f"Error: {response.status_code} - {response.text}")
            return

        messagebox.showinfo("Success", "Image uploaded successfully")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def browse_file():
    file_path = filedialog.askopenfilename()
    file_path_textbox.delete(0, 'end')
    file_path_textbox.insert(0, file_path)

root = Tk()
root.title("Upload Image to Discord")
root.geometry("400x200")
root.resizable(False, False)

# Create entry widget for file path
file_path_label = Label(root, text="File Path:")
file_path_textbox = Entry(root, width=50)
file_path_label.pack(side="top", padx=5, pady=5)
file_path_textbox.pack(side="top", padx=5, pady=5)

# Create "Browse" button for selecting file
browse_button = Button(root, text="Browse", command=browse_file)
browse_button.pack(side="top", padx=5, pady=5)

# Create entry widget for webhook URL
webhook_label = Label(root, text="Webhook URL:")
webhook_entry = Entry(root, width=50)
webhook_label.pack(side="top", padx=5, pady=5)
webhook_entry.pack(side="top", padx=5, pady=10)
webhook_entry.insert(0, "https://discord.com/api/webhooks/915459012168937503/zf8HeiluYhaVhny70Guqriq9eWhJsU6wlVDylDM8-NVZYCiGsPb0zTfU0oN3yeZHx_Nk")

# Create "Upload Image" button
upload_button = Button(root, text="Upload Image", command=upload_image_to_discord)
upload_button.pack(side="top", padx=5, pady=5)
root.mainloop()
