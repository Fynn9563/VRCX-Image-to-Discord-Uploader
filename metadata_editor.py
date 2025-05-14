import io
import json
import os
import re
import datetime
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, PngImagePlugin

# Attempt to import pywin32 modules for Windows creation time update
try:
    import win32file
    import pywintypes
    import win32con
    def set_file_creation_time(path, creation_time):
        """Set the creation time of a file (Windows only)."""
        wintime = pywintypes.Time(creation_time)
        handle = win32file.CreateFile(
            path, win32con.GENERIC_WRITE, 0, None,
            win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None
        )
        win32file.SetFileTime(handle, wintime, None, None)
        handle.close()
except ImportError:
    set_file_creation_time = None

class PNGMetadataEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("PNG Metadata Editor")
        
        # Variables to store original file timestamps and creation time
        self.original_timestamps = None  # (atime, mtime)
        self.original_creation_time = None
        
        # Variable to store creation time string for display
        self.creation_date_var = tk.StringVar()
        
        # Create frames for organization
        load_frame = tk.LabelFrame(root, text="Load Existing Metadata")
        load_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        form_frame = tk.LabelFrame(root, text="Metadata Information")
        form_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        action_frame = tk.LabelFrame(root, text="Actions")
        action_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        # Load PNG for metadata extraction
        tk.Button(load_frame, text="Load PNG Metadata", command=self.load_png_metadata).grid(row=0, column=0, padx=5, pady=5)
        
        # Display creation date (if loaded)
        tk.Label(load_frame, text="Creation Date:").grid(row=0, column=1, sticky="w", padx=5)
        tk.Label(load_frame, textvariable=self.creation_date_var).grid(row=0, column=2, sticky="w", padx=5)
        
        # Raw JSON text area for loading JSON directly
        tk.Label(load_frame, text="Or Paste Raw JSON:").grid(row=1, column=0, sticky="w", padx=5)
        self.raw_json_text = scrolledtext.ScrolledText(load_frame, width=70, height=8)
        self.raw_json_text.grid(row=2, column=0, padx=5, pady=5, columnspan=3)
        tk.Button(load_frame, text="Load Raw JSON", command=self.load_raw_json).grid(row=3, column=0, padx=5, pady=5)
        
        # Form fields for metadata
        tk.Label(form_frame, text="Author Display Name:").grid(row=0, column=0, sticky="w", padx=5)
        self.author_displayName = tk.Entry(form_frame, width=40)
        self.author_displayName.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(form_frame, text="Author ID:").grid(row=1, column=0, sticky="w", padx=5)
        self.author_id = tk.Entry(form_frame, width=40)
        self.author_id.grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(form_frame, text="World Name:").grid(row=2, column=0, sticky="w", padx=5)
        self.world_name = tk.Entry(form_frame, width=40)
        self.world_name.grid(row=2, column=1, padx=5, pady=2)
        
        tk.Label(form_frame, text="World ID:").grid(row=3, column=0, sticky="w", padx=5)
        self.world_id = tk.Entry(form_frame, width=40)
        self.world_id.grid(row=3, column=1, padx=5, pady=2)
        
        tk.Label(form_frame, text="World Instance ID:").grid(row=4, column=0, sticky="w", padx=5)
        self.world_instanceId = tk.Entry(form_frame, width=40)
        self.world_instanceId.grid(row=4, column=1, padx=5, pady=2)
        
        tk.Label(form_frame, text="Players (one per line as: displayName, id):").grid(row=5, column=0, sticky="w", padx=5)
        self.players_text = scrolledtext.ScrolledText(form_frame, width=40, height=8)
        self.players_text.grid(row=5, column=1, padx=5, pady=2)
        
        # Action buttons
        tk.Button(action_frame, text="Select PNG for Embedding", command=self.select_png_for_embedding).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(action_frame, text="Embed Metadata into PNG", command=self.embed_metadata).grid(row=0, column=1, padx=5, pady=5)
        
        # Variable to hold the PNG image for embedding
        self.embed_png_path = None

    def load_png_metadata(self):
        """Load PNG metadata from an existing file, including creation date, and populate form fields."""
        file_path = filedialog.askopenfilename(title="Select PNG file", filetypes=[("PNG files", "*.png")])
        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                metadata_json = img.info.get("Description")
                if not metadata_json:
                    messagebox.showerror("Error", "No metadata found in the PNG file.")
                    return
                metadata = json.loads(metadata_json)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading PNG: {e}")
            return

        # Always get atime and mtime for later use
        try:
            stat = os.stat(file_path)
            self.original_timestamps = (stat.st_atime, stat.st_mtime)
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not load file timestamps: {e}")
            self.original_timestamps = None

        # Determine creation time from filename if possible
        creation_ts = None
        filename = os.path.basename(file_path)
        match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2}(?:\.\d+)?)", filename)
        if match:
            date_part = match.group(1)
            time_part = match.group(2).replace('-', ':')
            try:
                dt = datetime.datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    dt = datetime.datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt = None
            if dt:
                creation_ts = dt.timestamp()

        # Fallback to Windows creation time if filename parse failed
        if creation_ts is None:
            try:
                creation_ts = stat.st_ctime
            except Exception:
                creation_ts = None

        self.original_creation_time = creation_ts
        if creation_ts:
            creation_str = datetime.datetime.fromtimestamp(creation_ts).strftime("%Y-%m-%d %H:%M:%S")
            self.creation_date_var.set(creation_str)

        # Populate fields from metadata JSON
        if "author" in metadata:
            self.author_displayName.delete(0, tk.END)
            self.author_displayName.insert(0, metadata["author"].get("displayName", ""))
            self.author_id.delete(0, tk.END)
            self.author_id.insert(0, metadata["author"].get("id", ""))
        if "world" in metadata:
            self.world_name.delete(0, tk.END)
            self.world_name.insert(0, metadata["world"].get("name", ""))
            self.world_id.delete(0, tk.END)
            self.world_id.insert(0, metadata["world"].get("id", ""))
            self.world_instanceId.delete(0, tk.END)
            self.world_instanceId.insert(0, metadata["world"].get("instanceId", ""))
        if "players" in metadata:
            self.players_text.delete("1.0", tk.END)
            players_lines = [f"{p.get('displayName', '')}, {p.get('id', '')}" for p in metadata["players"]]
            self.players_text.insert(tk.END, "\n".join(players_lines))
        # Also populate the raw JSON area
        self.raw_json_text.delete("1.0", tk.END)
        self.raw_json_text.insert(tk.END, json.dumps(metadata, indent=2, ensure_ascii=False))
        messagebox.showinfo("Success", "Metadata and creation date loaded and form fields populated.")

    def load_raw_json(self):
        """Load JSON from the raw JSON text box into form fields."""
        raw = self.raw_json_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showerror("Error", "No raw JSON provided.")
            return
        try:
            metadata = json.loads(raw)
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing JSON: {e}")
            return
        # Populate fields
        if "author" in metadata:
            self.author_displayName.delete(0, tk.END)
            self.author_displayName.insert(0, metadata["author"].get("displayName", ""))
            self.author_id.delete(0, tk.END)
            self.author_id.insert(0, metadata["author"].get("id", ""))
        if "world" in metadata:
            self.world_name.delete(0, tk.END)
            self.world_name.insert(0, metadata["world"].get("name", ""))
            self.world_id.delete(0, tk.END)
            self.world_id.insert(0, metadata["world"].get("id", ""))
            self.world_instanceId.delete(0, tk.END)
            self.world_instanceId.insert(0, metadata["world"].get("instanceId", ""))
        if "players" in metadata:
            self.players_text.delete("1.0", tk.END)
            players_lines = [f"{p.get('displayName', '')}, {p.get('id', '')}" for p in metadata["players"]]
            self.players_text.insert(tk.END, "\n".join(players_lines))
        messagebox.showinfo("Success", "Raw JSON loaded into form fields.")

    def select_png_for_embedding(self):
        """Select a PNG file that will have metadata embedded."""
        file_path = filedialog.askopenfilename(title="Select PNG file for embedding", filetypes=[("PNG files", "*.png")])
        if not file_path:
            return
        self.embed_png_path = file_path
        messagebox.showinfo("File Selected", f"Selected PNG for embedding:\n{file_path}")

    def embed_metadata(self):
        """Build the metadata JSON from the form and embed it into the selected PNG.
        Also, use the original file’s timestamps (and creation time on Windows, if possible)."""
        if not self.embed_png_path:
            messagebox.showerror("Error", "No PNG file selected for embedding. Please click 'Select PNG for Embedding' first.")
            return
        author = {
            "displayName": self.author_displayName.get().strip(),
            "id": self.author_id.get().strip()
        }
        world = {
            "name": self.world_name.get().strip(),
            "id": self.world_id.get().strip(),
            "instanceId": self.world_instanceId.get().strip()
        }
        players = []
        players_raw = self.players_text.get("1.0", tk.END).strip()
        if players_raw:
            for line in players_raw.splitlines():
                parts = line.split(",")
                if len(parts) == 2:
                    players.append({
                        "displayName": parts[0].strip(),
                        "id": parts[1].strip()
                    })
        metadata_dict = {
            "application": "VRCX",
            "version": 1,
            "author": author,
            "world": world,
            "players": players
        }
        metadata_json = json.dumps(metadata_dict, indent=2, ensure_ascii=False)
        try:
            image = Image.open(self.embed_png_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error opening PNG file: {e}")
            return
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Description", metadata_json)
        base, ext = os.path.splitext(self.embed_png_path)
        save_path = base + "_Modified" + ext
        try:
            image.save(save_path, pnginfo=pnginfo)
            if self.original_timestamps:
                os.utime(save_path, self.original_timestamps)
            if set_file_creation_time and self.original_creation_time:
                set_file_creation_time(save_path, self.original_creation_time)
            messagebox.showinfo("Success", f"PNG saved with embedded metadata:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving PNG file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PNGMetadataEditor(root)
    root.mainloop()