from PIL import Image, ImageTk
import os
import logging
import re
import threading
from tkinter import (
    Tk, Button, Label, filedialog, messagebox, ttk, Entry, PhotoImage, Toplevel,
    IntVar, Checkbutton, Frame, TclError
)
from database_manager import DatabaseManager
from uploader import ImageUploader
from config_loader import load_config
from metadata_editor import PNGMetadataEditor

class AppState:
    """
    Manages the state of the application, including GUI components and data.
    """
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.progress_bar = None
        self.image_queue = []
        self.failed_uploads = []
        self.upload_status_label = None
        self.webhook_combobox = None
        self.webhook_name_entry = None
        self.webhook_url_entry = None
        self.existing_webhook_combobox = None
        self.add_webhook_window = None
        self.font_style = None
        self.background_image = None
        self.file_path_textbox = None
        self.media_channel_var = IntVar(master=self.root)
        self.database_manager = None
        self.webhooks = []
        self.upload_button = None
        self.original_bg_image = None  # Store the original background image

    def initialize(self):
        """
        Initializes the application state, including fonts and database.
        """
        self.font_style = (
            self.config.get('Application', 'font_family'),
            self.config.getint('Application', 'font_size')
        )
        self.database_manager = DatabaseManager(self.config.get('Database', 'db_name'))


class ApplicationGUI:
    """
    Builds and manages the GUI components.
    """
    def __init__(self, app_state):
        self.app_state = app_state
        self.root = app_state.root
        self.config = app_state.config
        self.setup_gui()

    def setup_gui(self):
        """
        Sets up the GUI components and layout.
        """
        self.root.title(self.config.get('Application', 'app_title'))
        self.root.geometry(self.config.get('Application', 'window_size'))
        self.root.resizable(True, True)

        icon_path = self.config.get('Application', 'icon_path')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        # Load and set up the background image
        background_image_file = self.config.get('Application', 'background_image')
        try:
            # Load the original image using PIL
            self.app_state.original_bg_image = Image.open(background_image_file)
            # Resize the image to the current window size
            resized_image = self.app_state.original_bg_image.resize(
                (self.root.winfo_width(), self.root.winfo_height()), Image.LANCZOS
            )
            self.app_state.background_image = ImageTk.PhotoImage(resized_image)
            # Create the background label
            self.background_label = Label(self.root, image=self.app_state.background_image)
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
            # Bind the resize event to the resize_background method
            self.root.bind('<Configure>', self.resize_background)
        except Exception as e:
            self.app_state.background_image = None
            logging.warning(
                f"Background image '{background_image_file}' not found or could not be loaded. "
                f"Running without background image. Error: {e}"
            )

        button_style = ttk.Style()
        button_style.configure("Custom.TButton", font=self.app_state.font_style, padding=5)

        # Set up widgets
        self.setup_widgets()
        self.update_webhook_combobox()

    def resize_background(self, event):
        """
        Resizes the background image to match the new window size.
        """
        # Check if the event is for the root window
        if event.widget == self.root:
            new_width = event.width
            new_height = event.height
            # Resize the original image to the new size
            resized_image = self.app_state.original_bg_image.resize(
                (new_width, new_height), Image.LANCZOS
            )
            self.app_state.background_image = ImageTk.PhotoImage(resized_image)
            # Update the background label with the new image
            self.background_label.config(image=self.app_state.background_image)
            # Keep a reference to prevent garbage collection
            self.background_label.image = self.app_state.background_image

    def setup_widgets(self):
        """
        Creates and places all GUI widgets.
        """
        webhook_frame = ttk.Frame(self.root)
        webhook_frame.pack(side="top", padx=5, pady=5, fill="x")

        webhook_combobox_label = Label(
            webhook_frame, text="Select Webhook:", font=self.app_state.font_style
        )
        webhook_combobox_label.grid(row=0, column=0, padx=5, pady=5)

        self.app_state.webhook_combobox = ttk.Combobox(
            webhook_frame, values=[], font=self.app_state.font_style, state="readonly", width=30
        )
        self.app_state.webhook_combobox.grid(row=0, column=1, padx=5, pady=5)

        add_webhook_button = Button(
            webhook_frame, text="Add/Delete Webhook",
            command=self.open_add_webhook_window, font=self.app_state.font_style
        )
        add_webhook_button.grid(row=0, column=2, padx=5, pady=5)

        # Edit Metadata button and checkbox side by side
        meta_media_frame = Frame(self.root)
        meta_media_frame.pack(side="top", fill="x", padx=5, pady=5)

        Button(meta_media_frame,
               text="Edit Metadata",
               font=self.app_state.font_style,
               command=lambda: PNGMetadataEditor(Toplevel(self.root))
        ).pack(side="left", padx=(0, 10))

        Checkbutton(meta_media_frame,
                    text="Discord Forum Channel",
                    variable=self.app_state.media_channel_var,
                    font=self.app_state.font_style
        ).pack(side="left")


        file_path_label = Label(self.root, text="File Paths:", font=self.app_state.font_style)
        self.app_state.file_path_textbox = Entry(self.root, width=50, font=self.app_state.font_style)
        file_path_label.pack(side="top", padx=5, pady=5)
        self.app_state.file_path_textbox.pack(side="top", padx=5, pady=5, fill='x')

        browse_button = Button(
            self.root, text="Browse", command=self.browse_files, font=self.app_state.font_style
        )
        browse_button.pack(side="top", padx=5, pady=5)
        
        self.app_state.upload_button = Button(
            self.root, text="Upload Images", command=self.process_images, font=self.app_state.font_style
        )
        self.app_state.upload_button.pack(side="top", padx=5, pady=5)


        self.app_state.upload_status_label = Label(
            self.root, text="", fg="blue", font=self.app_state.font_style
        )
        self.app_state.upload_status_label.pack(side="top", padx=5, pady=5)

    def update_webhook_combobox(self):
        """
        Updates the webhook combobox with the list of webhooks from the database.
        """
        webhooks = self.app_state.database_manager.get_all_webhooks()
        self.app_state.webhooks = webhooks
        self.app_state.webhook_combobox['values'] = [webhook[0] for webhook in webhooks]
        if webhooks:
            self.app_state.webhook_combobox.current(0)

    def open_add_webhook_window(self):
        """
        Opens the 'Manage Webhooks' window.
        """
        self.app_state.add_webhook_window = Toplevel(self.root)
        self.app_state.add_webhook_window.title("Manage Webhooks")
        self.app_state.add_webhook_window.geometry("450x250")
        self.app_state.add_webhook_window.resizable(False, False)

        if self.app_state.background_image:
            background_label_add = Label(
                self.app_state.add_webhook_window, image=self.app_state.background_image
            )
            background_label_add.place(x=0, y=0, relwidth=1, relheight=1)

        webhook_name_label = Label(
            self.app_state.add_webhook_window, text="Webhook Name:", font=self.app_state.font_style
        )
        webhook_name_label.pack(padx=5, pady=5)
        self.app_state.webhook_name_entry = Entry(
            self.app_state.add_webhook_window, font=self.app_state.font_style, width=35
        )
        self.app_state.webhook_name_entry.pack(padx=5, pady=5)

        webhook_url_label = Label(
            self.app_state.add_webhook_window, text="Webhook URL:", font=self.app_state.font_style
        )
        webhook_url_label.pack(padx=5, pady=5)
        self.app_state.webhook_url_entry = Entry(
            self.app_state.add_webhook_window, font=self.app_state.font_style, width=35
        )
        self.app_state.webhook_url_entry.pack(padx=5, pady=5)

        button_frame = Frame(self.app_state.add_webhook_window)
        button_frame.pack(pady=10)

        add_webhook_btn = Button(
            button_frame, text="Add Webhook", command=self.add_webhook, font=self.app_state.font_style
        )
        add_webhook_btn.pack(side="left", padx=5)

        delete_webhook_btn = Button(
            button_frame, text="Delete Webhook", command=self.delete_webhook, font=self.app_state.font_style
        )
        delete_webhook_btn.pack(side="right", padx=5)

        existing_webhook_label = Label(
            self.app_state.add_webhook_window, text="Existing Webhooks:", font=self.app_state.font_style
        )
        existing_webhook_label.pack(padx=5, pady=5)
        self.app_state.existing_webhook_combobox = ttk.Combobox(
            self.app_state.add_webhook_window,
            values=[webhook[0] for webhook in self.app_state.webhooks],
            font=self.app_state.font_style,
            state="readonly",
            width=30
        )
        self.app_state.existing_webhook_combobox.pack(padx=5, pady=5)

    def add_webhook(self):
        """
        Adds a new webhook to the database based on user input.
        """
        name = self.app_state.webhook_name_entry.get()
        url = self.app_state.webhook_url_entry.get()
        if name and self.is_valid_webhook_url(url):
            self.app_state.database_manager.insert_webhook(name, url)
            self.update_webhook_combobox()
            self.app_state.add_webhook_window.destroy()
            messagebox.showinfo("Success", "Webhook added successfully!")
        else:
            messagebox.showerror("Error", "Invalid name or webhook URL.")

    def delete_webhook(self):
        """
        Deletes the selected webhook from the database.
        """
        selected_webhook_name = self.app_state.existing_webhook_combobox.get()
        if not selected_webhook_name:
            messagebox.showerror("Error", "Please select a webhook to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion", f"Are you sure you want to delete the webhook '{selected_webhook_name}'?"
        )
        if not confirm:
            return

        self.app_state.database_manager.delete_webhook(selected_webhook_name)
        self.update_webhook_combobox()
        self.app_state.existing_webhook_combobox['values'] = [
            webhook[0] for webhook in self.app_state.webhooks
        ]
        messagebox.showinfo("Success", "Webhook deleted successfully!")

    def is_valid_webhook_url(self, url):
        """
        Validates the webhook URL using a regular expression.
        """
        pattern = r'^https://discord\.com/api/webhooks/\d+/\S+$'
        return re.match(pattern, url) is not None

    def browse_files(self):
        """
        Opens a file dialog for the user to select images.
        """
        file_paths = filedialog.askopenfilenames()
        self.app_state.file_path_textbox.delete(0, 'end')
        self.app_state.file_path_textbox.insert(0, ", ".join(file_paths))

    def process_images(self):
        """
        Initiates the image uploading process.
        """
        selected_webhook_name = self.app_state.webhook_combobox.get()
        if not selected_webhook_name:
            messagebox.showerror("Error", "Please select a webhook.")
            return

        webhook_url = next(
            (url for name, url in self.app_state.webhooks if name == selected_webhook_name), None
        )
        if not webhook_url:
            logging.error(f"Webhook URL not found for '{selected_webhook_name}'")
            messagebox.showerror("Error", "Webhook URL not found.")
            return

        file_paths = self.app_state.file_path_textbox.get().split(', ')
        self.app_state.image_queue = []
        for file_path in file_paths:
            file_path = file_path.strip()
            if not os.path.isfile(file_path):
                messagebox.showerror("Error", f"File not found: {file_path}")
                continue
            try:
                Image.open(file_path)
            except Exception:
                messagebox.showerror("Error", f"Invalid image file: {file_path}")
                continue
            self.app_state.image_queue.append(file_path)

        if not self.app_state.image_queue:
            messagebox.showinfo("No Images", "No valid images to upload.")
            return

        if self.app_state.progress_bar:
            self.app_state.progress_bar.destroy()

        # Initialize the progress bar
        self.app_state.progress_bar = ttk.Progressbar(
            self.root, orient="horizontal", length=200, mode="determinate"
        )
        self.app_state.progress_bar.pack(side="top", padx=5, pady=5, fill='x')
        self.app_state.progress_bar['value'] = 0

        self.app_state.upload_status_label.config(text="Uploading images...")
        self.app_state.upload_button.config(state='disabled')

        uploader = ImageUploader(webhook_url, self.app_state)
        uploader.start_uploads(self.app_state.image_queue)
        threading.Thread(
            target=uploader.process_results, args=(len(self.app_state.image_queue),), daemon=True
        ).start()
