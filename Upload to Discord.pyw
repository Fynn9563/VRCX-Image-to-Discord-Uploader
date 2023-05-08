import threading
import os
import json
import requests
from tkinter import Tk, Button, Label, filedialog, messagebox, ttk, Entry
from PIL import Image

# Replace YOUR_TOKEN_HERE with your actual Discord bot token
DISCORD_BOT_TOKEN = "YOUR_TOKEN_HERE"

progress_bar = None  # Global variable for progress bar

def extract_image_metadata(file_path):
    with Image.open(file_path) as img:
        description = img.info.get('Description')

        if not description:
            raise ValueError("The selected image has no metadata.")

        metadata = json.loads(description)
        world_name = metadata['world']['name']
        world_id = metadata['world']['id']
        players = metadata['players']
        player_names = [player['displayName'] for player in players]

        return world_name, world_id, player_names

def create_payload(file_path):
    timestamp = os.stat(file_path).st_ctime
    world_name, world_id, player_names = extract_image_metadata(file_path)

    payload = {
        "content": f"Photo taken at **{world_name}** *({world_id})* with **{', '.join(player_names)}** at <t:{int(timestamp)}:f>"
    }

    return payload

def upload_image_to_discord():
    global progress_bar  # Use global variable

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

        # Create payload
        payload = create_payload(file_path)

        # Destroy progress bar if it already exists
        if progress_bar:
            progress_bar.destroy()

        # Create progress bar
        progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        progress_bar.pack(side="top", padx=5, pady=5)


        # Start file upload in separate thread
        def upload_thread():
            try:
                # Read file before sending payload
                with open(file_path, 'rb') as f:
                    image_data = f.read()

                # Send payload to webhook with image attached
                files = {'file': (os.path.basename(file_path), image_data)}
                response = requests.post(webhook_url, data=payload, files=files, stream=True)

                # Update progress bar and elapsed time
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                progress = 0
                for chunk in response.iter_content(block_size):
                    progress += len(chunk)
                    if total_size > 0:
                        progress_bar['value'] = int(progress / total_size * 100)
                    root.update_idletasks()
                
                progress_bar['value'] = 100
                messagebox.showinfo("Success", "Image uploaded successfully")
            except Exception as e:
                progress_bar.destroy()
                messagebox.showerror("Error", str(e))
            finally:
                root.config(cursor="")
                upload_button.config(state="normal")

        t = threading.Thread(target=upload_thread)
        t.start()

        root.config(cursor="wait")
        upload_button.config(state="disabled")


    except Exception as e:
        messagebox.showerror("Error", str(e))

def browse_file():
    file_path = filedialog.askopenfilename()
    file_path_textbox.delete(0, 'end')
    file_path_textbox.insert(0, file_path)

root = Tk()
root.title("Upload Image to Discord")
root.geometry("400x250")
root.resizable(False, False)

# Create entry for file path
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
webhook_entry.insert(0, DISCORD_BOT_TOKEN)

# Create "Upload Image" button
upload_button = Button(root, text="Upload Image", command=upload_image_to_discord)
upload_button.pack(side="top", padx=5, pady=5)
root.mainloop()
