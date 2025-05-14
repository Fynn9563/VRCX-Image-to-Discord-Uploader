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
        # store timestamps
        try:
            stat = os.stat(file_path)
            self.original_timestamps = (stat.st_atime, stat.st_mtime)
        except Exception as e:
            self.original_timestamps = None
            logging.warning(f"Could not read timestamps: {e}")
        # parse creation from filename first
        creation_ts = None
        base = os.path.basename(file_path)
        m = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2}(?:\.\d+)?)", base)
        if m:
            date, time = m.groups()
            tstr = time.replace('-', ':')
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.datetime.strptime(f"{date} {tstr}", fmt)
                    creation_ts = dt.timestamp()
                    break
                except ValueError:
                    continue
        if creation_ts is None:
            try:
                creation_ts = stat.st_ctime
            except Exception:
                creation_ts = None
        self.original_creation_time = creation_ts
        if creation_ts:
            self.creation_date_var.set(datetime.datetime.fromtimestamp(creation_ts).strftime("%Y-%m-%d %H:%M:%S"))
        # populate fields
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
            lines = [f"{p.get('displayName')}, {p.get('id')}" for p in metadata.get("players", [])]
            self.players_text.insert(tk.END, "\n".join(lines))
        self.raw_json_text.delete("1.0", tk.END)
        self.raw_json_text.insert(tk.END, json.dumps(metadata, indent=2, ensure_ascii=False))
        messagebox.showinfo("Success", "Loaded metadata and timestamps.")

    def load_raw_json(self):
        """Load JSON from the raw JSON text box into form fields."""
        raw = self.raw_json_text.get("1.0", tk.END).strip()
        if not raw:
            return messagebox.showerror("Error", "No raw JSON provided.")
        try:
            metadata = json.loads(raw)
        except Exception as e:
            return messagebox.showerror("Error", f"Invalid JSON: {e}")
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
            lines = [f"{p.get('displayName')}, {p.get('id')}" for p in metadata.get("players", [])]
            self.players_text.insert(tk.END, "\n".join(lines))
        messagebox.showinfo("Success", "Loaded raw JSON.")

    def select_png_for_embedding(self):
        file_path = filedialog.askopenfilename(title="Select PNG for embedding", filetypes=[("PNG files", "*.png")])
        if not file_path:
            return
        self.embed_png_path = file_path
        messagebox.showinfo("Selected", f"Embedding into: {file_path}")

    def embed_metadata(self):
        """Embed metadata and save output filename including date if missing."""
        if not self.embed_png_path:
            return messagebox.showerror("Error", "No file selected.")
        metadata = {
            "application": "VRCX",
            "version": 1,
            "author": {"displayName": self.author_displayName.get(), "id": self.author_id.get()},
            "world": {"name": self.world_name.get(), "id": self.world_id.get(), "instanceId": self.world_instanceId.get()},
            "players": [ {"displayName": p.split(',')[0].strip(), "id": p.split(',')[1].strip()} for p in self.players_text.get("1.0", tk.END).splitlines() if "," in p ]
        }
        data = json.dumps(metadata, indent=2, ensure_ascii=False)
        try:
            img = Image.open(self.embed_png_path)
        except Exception as e:
            return messagebox.showerror("Error", f"Open failed: {e}")
        info = PngImagePlugin.PngInfo()
        info.add_text("Description", data)
        base, ext = os.path.splitext(self.embed_png_path)
        name = os.path.basename(base)
        # add date if missing
        if not re.search(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}", name):
            ts = self.original_creation_time
            if ts:
                dt = datetime.datetime.fromtimestamp(ts)
                timestr = dt.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3] if dt.microsecond else dt.strftime("%Y-%m-%d_%H-%M-%S")
                base = f"{base}_{timestr}"
        out = f"{base}_Modified{ext}"
        try:
            img.save(out, pnginfo=info)
            if self.original_timestamps:
                os.utime(out, self.original_timestamps)
            if set_file_creation_time and self.original_creation_time:
                set_file_creation_time(out, self.original_creation_time)
            messagebox.showinfo("Done", f"Saved: {out}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    PNGMetadataEditor(root)
    root.mainloop()