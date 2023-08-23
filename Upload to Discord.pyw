import os
import json
import requests
import sqlite3
from tkinter import Tk, Button, Label, filedialog, messagebox, ttk, Entry, PhotoImage, TclError, Toplevel
from PIL import Image
import concurrent.futures
import tempfile

# Global variables
progress_bar = None
image_queue = []

# SQLite setup
DATABASE_NAME = "webhooks.db"

def setup_database():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
        """)
        conn.commit()

def insert_webhook(name, url):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO webhooks (name, url) VALUES (?, ?)", (name, url))
        conn.commit()

def get_all_webhooks():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, url FROM webhooks")
        return cursor.fetchall()

def add_webhook():
    name = webhook_name_entry.get()
    url = webhook_url_entry.get()
    if name and url.startswith('https://discord.com/api/webhooks/'):
        insert_webhook(name, url)
        update_webhook_combobox()
        add_webhook_window.destroy()  # Close the add webhook window
        messagebox.showinfo("Success", "Webhook added successfully!")
    else:
        messagebox.showerror("Error", "Invalid name or webhook URL.")

def open_add_webhook_window():
    global add_webhook_window, webhook_name_entry, webhook_url_entry
    
    add_webhook_window = Toplevel(root)
    add_webhook_window.title("Add Webhook")
    add_webhook_window.geometry("300x200")
    add_webhook_window.resizable(False, False)

    # Set the background image for the new window
    if background_image:
        background_label_add = Label(add_webhook_window, image=background_image)
        background_label_add.place(x=0, y=0, relwidth=1, relheight=2)

    webhook_name_label = Label(add_webhook_window, text="Webhook Name:", font=font_style)
    webhook_name_entry = Entry(add_webhook_window, width=30, font=font_style)
    webhook_name_label.pack(side="top", padx=5, pady=5)
    webhook_name_entry.pack(side="top", padx=5, pady=5)

    webhook_url_label = Label(add_webhook_window, text="Webhook URL:", font=font_style)
    webhook_url_entry = Entry(add_webhook_window, width=30, font=font_style)
    webhook_url_label.pack(side="top", padx=5, pady=5)
    webhook_url_entry.pack(side="top", padx=5, pady=5)

    add_webhook_btn = Button(add_webhook_window, text="Add", command=add_webhook, font=font_style)
    add_webhook_btn.pack(side="top", padx=5, pady=10)

    add_webhook_window.mainloop()

def update_webhook_combobox():
    webhooks = get_all_webhooks()
    webhook_combobox['values'] = [webhook[0] for webhook in webhooks]
    if webhooks:
        webhook_combobox.current(0)

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

def compress_image(file_path, quality=85):
    with Image.open(file_path) as img:
        # Create a temporary file for the compressed image
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(temp_file.name, "JPEG", quality=quality)
    return temp_file.name
        
def upload_image(file_path, webhook_url):
    try:
        payload = create_payload(file_path)

        # Read file before sending payload
        with open(file_path, 'rb') as f:
            image_data = f.read()

        # Send payload to webhook with image attached
        files = {'file': (os.path.basename(file_path), image_data)}
        response = requests.post(webhook_url, data=payload, files=files)

        # If the upload fails due to size, compress the image and retry
        if response.status_code == 413:  # 413 is the status code for "Request entity too large"
            compressed_file_path = compress_image(file_path)
            with open(compressed_file_path, 'rb') as f:
                image_data = f.read()
            files = {'file': (os.path.basename(file_path), image_data)}
            response = requests.post(webhook_url, data=payload, files=files)
            os.remove(compressed_file_path)  # Delete the temporary compressed file after upload

        # Print the response content and status code to the console
        print(f"Response for {os.path.basename(file_path)}: {response.status_code} - {response.text}")

        if response.status_code == 200:
            return True, f"Image {os.path.basename(file_path)} uploaded successfully"
        else:
            return False, f"Image {os.path.basename(file_path)} upload failed"

    except Exception as e:
        return False, str(e)
        
failed_uploads = []
def on_image_uploaded(future):
    global failed_uploads

    try:
        success, message = future.result()

        if success:
            print(message)
        else:
            print(message)
            failed_uploads.append(os.path.basename(message.split()[-3]))

        progress = 100 - (len(image_queue) * 100 // (len(image_queue) + 1))
        progress_bar['value'] = progress
        root.update()

    except Exception as e:
        messagebox.showerror("Error", str(e))

    update_progress()

def update_progress():
    global progress_bar, failed_uploads

    if not image_queue:
        progress_bar['value'] = 100
        if len(failed_uploads) == 1:
            upload_status_label.config(text=f"{len(failed_uploads)} image failed to upload.")
        elif len(failed_uploads) > 1:
            upload_status_label.config(text=f"{len(failed_uploads)} images failed to upload.")
        else:
            upload_status_label.config(text="All images uploaded successfully")

        failed_uploads.clear()
        return

    file_path = image_queue.pop(0)
    selected_webhook_name = webhook_combobox.get()
    webhook_url = next((url for name, url in get_all_webhooks() if name == selected_webhook_name), None)
    
    future = concurrent.futures.ThreadPoolExecutor().submit(upload_image, file_path, webhook_url)
    future.add_done_callback(on_image_uploaded)

def process_images():
    global progress_bar

    try:
        selected_webhook_name = webhook_combobox.get()
        if not selected_webhook_name:
            messagebox.showerror("Error", "Please select a webhook.")
            return

        webhook_url = next((url for name, url in get_all_webhooks() if name == selected_webhook_name), None)
        if not webhook_url:
            messagebox.showerror("Error", "Webhook URL not found.")
            return

        if progress_bar:
            progress_bar.destroy()

        progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        progress_bar.pack(side="top", padx=5, pady=5)

        image_queue.clear()
        for file_path in file_path_textbox.get().split(', '):
            image_queue.append(file_path.strip())

        root.after(0, update_progress)
        upload_status_label.config(text="Uploading images...")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def browse_files():
    file_paths = filedialog.askopenfilenames()
    file_path_textbox.delete(0, 'end')
    file_path_textbox.insert(0, ", ".join(file_paths))

root = Tk()
root.title("VRChat Photo Uploader")
root.geometry("600x330")
root.resizable(False, False)

# Set the icon for the main window
icon_path = "icon.ico"  # Replace with the actual path to your icon file (ICO format)
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# Try to load the background image
background_image_file = "background_image.png"
try:
    background_image = PhotoImage(file=background_image_file)
    background_label = Label(root, image=background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
except TclError:
    background_image = None
    print(f"Background image '{background_image_file}' not found. Running without background image.")

# Change font for labels and buttons
font_style = ("Helvetica Rounded", 11)  # Replace with your desired font family and size

# Create a custom style for the buttons
button_style = ttk.Style()
button_style.configure("Custom.TButton", font=font_style, padding=5)

webhook_frame = ttk.Frame(root)
webhook_frame.pack(side="top", padx=5, pady=5, fill="x")

webhook_combobox_label = Label(webhook_frame, text="Select Webhook:", font=font_style)
webhook_combobox_label.grid(row=0, column=0, padx=5, pady=5)
webhook_combobox = ttk.Combobox(webhook_frame, values=[], font=font_style, state="readonly", width=30)
webhook_combobox.grid(row=0, column=1, padx=5, pady=5)

add_webhook_button = Button(webhook_frame, text="Add Webhook", command=open_add_webhook_window, font=font_style)
add_webhook_button.grid(row=0, column=2, padx=5, pady=5)

file_path_label = Label(root, text="File Paths:", font=font_style)
file_path_textbox = Entry(root, width=50, font=font_style)
file_path_label.pack(side="top", padx=5, pady=5)
file_path_textbox.pack(side="top", padx=5, pady=5)

browse_button = Button(root, text="Browse", command=browse_files, font=font_style)
browse_button.pack(side="top", padx=5, pady=5)

upload_button = Button(root, text="Upload Images", command=process_images, font=font_style)
upload_button.pack(side="top", padx=5, pady=5)

upload_status_label = Label(root, text="", fg="blue", font=font_style)
upload_status_label.pack(side="top", padx=5, pady=5)

setup_database()
update_webhook_combobox()

root.mainloop()
