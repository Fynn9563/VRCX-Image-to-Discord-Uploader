import os
import json
import requests
import sqlite3
from tkinter import Tk, Button, Label, filedialog, messagebox, ttk, Entry, PhotoImage, TclError, Toplevel, IntVar, Checkbutton, Frame
from PIL import Image
import concurrent.futures
import tempfile
import logging
from configparser import ConfigParser

# Load configuration settings
config = ConfigParser()
config.read('config.ini')

# Global variables for tracking progress and the image queue
progress_bar = None
image_queue = []

# Setup logging
logging.basicConfig(filename=config.get('Logging', 'log_file'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite setup
DATABASE_NAME = config.get('Database', 'db_name')

# Database setup
def setup_database():
    """Sets up the database table for storing webhooks."""
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
    """Inserts a webhook into the database."""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO webhooks (name, url) VALUES (?, ?)", (name, url))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error inserting webhook: {e}")
        raise e

def get_all_webhooks():
    """Retrieves all webhooks from the database."""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, url FROM webhooks")
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error retrieving webhooks: {e}")
        raise e

# Webhook management
def add_webhook():
    """Adds a new webhook to the database based on user input and provides feedback."""
    name = webhook_name_entry.get()
    url = webhook_url_entry.get()
    if name and url.startswith('https://discord.com/api/webhooks/'):
        try:
            insert_webhook(name, url)
            update_webhook_combobox()
            add_webhook_window.destroy()
            messagebox.showinfo("Success", "Webhook added successfully!")
        except Exception as e:
            logging.error(f"Error adding webhook: {e}")
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", "Invalid name or webhook URL.")

def open_add_webhook_window():
    """
    Opens the "Manage Webhooks" window, allowing users to add or delete webhooks.
    """
    global add_webhook_window, webhook_name_entry, webhook_url_entry, existing_webhook_combobox
    
    # Create a new top-level window for managing webhooks
    add_webhook_window = Toplevel(root)
    add_webhook_window.title("Manage Webhooks")
    add_webhook_window.geometry("450x250")
    add_webhook_window.resizable(False, False)

    # Attempt to load a background image for the application window
    if background_image:
        background_label_add = Label(add_webhook_window, image=background_image)
        background_label_add.place(x=0, y=0, relwidth=1, relheight=2)

    # Create label and entry for naming the webhook
    webhook_name_label = Label(add_webhook_window, text="Webhook Name:", font=font_style)
    webhook_name_label.pack(padx=5, pady=5)
    webhook_name_entry = Entry(add_webhook_window, font=font_style, width=35)
    webhook_name_entry.pack(padx=5, pady=5)

    # Create label and entry for webhook's URL
    webhook_url_label = Label(add_webhook_window, text="Webhook URL:", font=font_style)
    webhook_url_label.pack(padx=5, pady=5)
    webhook_url_entry = Entry(add_webhook_window, font=font_style, width=35)
    webhook_url_entry.pack(padx=5, pady=5)

    # Create a frame for positioning the buttons
    button_frame = Frame(add_webhook_window)
    button_frame.pack(pady=10)

    # Add button for adding a new webhook
    add_webhook_btn = Button(button_frame, text="Add Webhook", command=add_webhook, font=font_style)
    add_webhook_btn.pack(side="left", padx=5)

    # Add button for deleting an existing webhook
    delete_webhook_btn = Button(button_frame, text="Delete Webhook", command=delete_webhook, font=font_style)
    delete_webhook_btn.pack(side="right", padx=5)
    
    # Label and combobox to show and select from existing webhooks
    existing_webhook_label = Label(add_webhook_window, text="Existing Webhooks:", font=font_style)
    existing_webhook_label.pack(padx=5, pady=5)
    existing_webhook_combobox = ttk.Combobox(add_webhook_window, values=[webhook[0] for webhook in get_all_webhooks()], font=font_style, state="readonly", width=30)
    existing_webhook_combobox.pack(padx=5, pady=5)
    
    # Run the main loop for this window
    add_webhook_window.mainloop()

def update_webhook_combobox():
    """Updates the dropdown list of webhooks."""
    webhooks = get_all_webhooks()
    webhook_combobox['values'] = [webhook[0] for webhook in webhooks]
    if webhooks:
        webhook_combobox.current(0)

def delete_webhook():
    """Deletes the selected webhook from the database."""
    selected_webhook_name = existing_webhook_combobox.get()
    if not selected_webhook_name:
        messagebox.showerror("Error", "Please select a webhook to delete.")
        return

    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM webhooks WHERE name = ?", (selected_webhook_name,))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error deleting webhook: {e}")
        messagebox.showerror("Error", str(e))
        return

    update_webhook_combobox()
    existing_webhook_combobox['values'] = [webhook[0] for webhook in get_all_webhooks()]

    messagebox.showinfo("Success", "Webhook deleted successfully!")

def extract_image_metadata(file_path):
    """Extracts image metadata to determine world name, world ID, and player names."""
    try:
        with Image.open(file_path) as img:
            description = img.info.get('Description')
            if not description:
                return None, None, None

            metadata = json.loads(description)
            world_name = metadata['world']['name']
            world_id = metadata['world']['id']
            players = metadata['players']
            player_names = [player['displayName'] for player in players]

            return world_name, world_id, player_names
    except Exception as e:
        logging.error(f"Error extracting metadata from {file_path}: {e}")
        return None, None, None

def create_payload(file_path):
    """Creates the payload message for the webhook."""
    timestamp = os.stat(file_path).st_ctime
    world_name, world_id, player_names = extract_image_metadata(file_path)

    if not world_name or not world_id or not player_names:
        if media_channel_var.get():
            thread_title = "Cool Image 😎"
            payload = {
                "thread_name": thread_title
            }
        else:
            payload = {}
        
        return payload

    world_vrchat_id_link = f"[**VRChat**](<https://vrchat.com/home/launch?worldId={world_id}>)"
    world_vrcx_id_link = f"[**VRCX**](<https://vrcx.azurewebsites.net/world/{world_id}>)"
    message_content = f"Photo taken at **{world_name}** (*{world_vrchat_id_link}*, *{world_vrcx_id_link}*) with **{', '.join(player_names)}** at <t:{int(timestamp)}:f>"
    thread_title = f"Photo taken at {world_name}"

    if len(thread_title) > 100:
        thread_title = thread_title[:97] + "..."

    if media_channel_var.get():
        payload = {
            "content": message_content,
            "thread_name": thread_title
        }
    else:
        payload = {
            "content": message_content
        }
    
    return payload

def compress_image(file_path, quality=85):
    """Compresses the image to a specific quality."""
    try:
        with Image.open(file_path) as img:
            # Create a temporary file for the compressed image
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            img.save(temp_file.name, "JPEG", quality=quality)
        return temp_file.name
    except Exception as e:
        logging.error(f"Error compressing image {file_path}: {e}")
        raise e

def upload_image(file_path, webhook_url):
    """Uploads the image to the specified webhook URL."""
    try:
        payload = create_payload(file_path)
        
        # If there's no payload, it means the image didn't have metadata.
        if not payload:
            payload = {}

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
        logging.info(f"Response for {os.path.basename(file_path)}: {response.status_code} - {response.text}")

        if response.status_code == 200:
            return True, f"Image {os.path.basename(file_path)} uploaded successfully"
        else:
            return False, f"Image {os.path.basename(file_path)} upload failed"

    except Exception as e:
        logging.error(f"Error uploading image {file_path}: {e}")
        return False, str(e)

failed_uploads = []
def on_image_uploaded(future):
    """Callback function after an image is uploaded."""
    global failed_uploads

    try:
        success, message = future.result()

        if success:
            logging.info(message)
        else:
            logging.error(message)
            failed_uploads.append(os.path.basename(message.split()[-3]))

        progress = 100 - (len(image_queue) * 100 // (len(image_queue) + 1))
        progress_bar['value'] = progress
        root.update()

    except Exception as e:
        logging.error(f"Error in on_image_uploaded: {e}")
        messagebox.showerror("Error", str(e))

    update_progress()

def update_progress():
    """Updates the progress bar based on the number of images uploaded."""
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
    
    if not webhook_url:
        logging.error(f"Webhook URL not found for '{selected_webhook_name}'")
        messagebox.showerror("Error", "Webhook URL not found.")
        return

    future = concurrent.futures.ThreadPoolExecutor().submit(upload_image, file_path, webhook_url)
    future.add_done_callback(on_image_uploaded)

def process_images():
    """Initiates the image uploading process."""
    global progress_bar

    try:
        selected_webhook_name = webhook_combobox.get()
        if not selected_webhook_name:
            messagebox.showerror("Error", "Please select a webhook.")
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
        logging.error(f"Error in process_images: {e}")
        messagebox.showerror("Error", str(e))

def browse_files():
    """Opens a file dialog for the user to select images."""
    file_paths = filedialog.askopenfilenames()
    file_path_textbox.delete(0, 'end')
    file_path_textbox.insert(0, ", ".join(file_paths))

# GUI initialization

# Initialize the main window
root = Tk()
root.title(config.get('Application', 'app_title'))
root.geometry(config.get('Application', 'window_size'))
root.resizable(False, False)

# Set the application icon if the file exists
icon_path = config.get('Application', 'icon_path')
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# Attempt to load a background image for the application window
background_image_file = config.get('Application', 'background_image')
try:
    background_image = PhotoImage(file=background_image_file)
    background_label = Label(root, image=background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
except TclError:
    background_image = None
    logging.warning(f"Background image '{background_image_file}' not found. Running without background image.")

# Set the font style for the labels and buttons
font_style = (config.get('Application', 'font_family'), config.getint('Application', 'font_size'))

# Create a custom style for the buttons
button_style = ttk.Style()
button_style.configure("Custom.TButton", font=font_style, padding=5)

# Initialize the webhook selection frame
webhook_frame = ttk.Frame(root)
webhook_frame.pack(side="top", padx=5, pady=5, fill="x")

# Label and dropdown for webhook selection
webhook_combobox_label = Label(webhook_frame, text="Select Webhook:", font=font_style)
webhook_combobox_label.grid(row=0, column=0, padx=5, pady=5)
webhook_combobox = ttk.Combobox(webhook_frame, values=[], font=font_style, state="readonly", width=30)
webhook_combobox.grid(row=0, column=1, padx=5, pady=5)

# Checkbox for specifying media channel option
media_channel_var = IntVar()
media_channel_tickbox = Checkbutton(root, text="Discord Media Channel", variable=media_channel_var, font=font_style)
media_channel_tickbox.pack(side="top", padx=5, pady=5)

# Button to add new webhook
add_webhook_button = Button(webhook_frame, text="Add/Delete Webhook", command=open_add_webhook_window, font=font_style)
add_webhook_button.grid(row=0, column=2, padx=5, pady=5)

# Label and textbox for entering file paths
file_path_label = Label(root, text="File Paths:", font=font_style)
file_path_textbox = Entry(root, width=50, font=font_style)
file_path_label.pack(side="top", padx=5, pady=5)
file_path_textbox.pack(side="top", padx=5, pady=5)

# Button to browse files
browse_button = Button(root, text="Browse", command=browse_files, font=font_style)
browse_button.pack(side="top", padx=5, pady=5)

# Button to upload selected images
upload_button = Button(root, text="Upload Images", command=process_images, font=font_style)
upload_button.pack(side="top", padx=5, pady=5)

# Label to show upload status
upload_status_label = Label(root, text="", fg="blue", font=font_style)
upload_status_label.pack(side="top", padx=5, pady=5)

setup_database()
update_webhook_combobox()

root.mainloop()