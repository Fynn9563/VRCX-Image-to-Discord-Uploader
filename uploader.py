import os
import re
import requests
import logging
import threading
import queue
from image_processor import extract_image_metadata, compress_image

class ImageUploader:
    """
    Manages image uploads to Discord via webhooks.
    """
    def __init__(self, webhook_url, app_state):
        self.webhook_url = webhook_url
        self.app_state = app_state
        self.result_queue = queue.Queue()

    def _get_timestamp(self, file_path):
        """
        Extracts a timestamp from the filename in format YYYY-MM-DD_HH-MM-SS(.fff)_ then falls back to file creation time.
        """
        filename = os.path.basename(file_path)
        # match date and time segments
        match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2}(?:\.\d+)?)", filename)
        if match:
            date_part, time_part = match.groups()
            # normalize time part from hyphens to colons
            time_str = time_part.replace('-', ':')
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = __import__('datetime').datetime.strptime(f"{date_part} {time_str}", fmt)
                    break
                except ValueError:
                    continue
            if dt:
                return dt.timestamp()
        # fallback to creation time
        try:
            return os.stat(file_path).st_ctime
        except Exception as e:
            logging.warning(f"Could not get creation time for {file_path}: {e}")
            return None

    def create_payload(self, file_path, timestamp):
        """
        Creates the payload message for the webhook.
        """
        world_name, world_id, player_names = extract_image_metadata(file_path)
        if not all([world_name, world_id, player_names]):
            # If metadata is missing or incomplete
            if self.app_state.media_channel_var.get():
                thread_title = "Image Upload"
                return {"thread_name": thread_title}
            return {}

        # Create message content with links
        vrchat_link = f"[**VRChat**](<https://vrchat.com/home/launch?worldId={world_id}>)"
        vrcx_link = f"[**VRCX**](<https://vrcx.azurewebsites.net/world/{world_id}>)"
        content = (
            f"Photo taken at **{world_name}** (*{vrchat_link}*, *{vrcx_link}*) "
            f"with **{', '.join(player_names)}**"
        )
        if timestamp:
            content += f" at <t:{int(timestamp)}:f>"
        title = f"Photo taken at {world_name}"
        if len(title) > 100:
            title = title[:97] + "..."

        payload = {"content": content}
        if self.app_state.media_channel_var.get():
            payload["thread_name"] = title
        return payload

    def upload_image(self, file_path):
        """
        Uploads the image to the specified webhook URL.
        """
        try:
            timestamp = self._get_timestamp(file_path)
            payload = self.create_payload(file_path, timestamp) or {}

            with open(file_path, 'rb') as f:
                data = f.read()

            files = {'file': (os.path.basename(file_path), data)}
            response = requests.post(self.webhook_url, data=payload, files=files)

            if response.status_code == 413:
                # If file too large, compress and retry
                comp_path = compress_image(file_path)
                with open(comp_path, 'rb') as f2:
                    data2 = f2.read()
                files = {'file': (os.path.basename(comp_path), data2)}
                response = requests.post(self.webhook_url, data=payload, files=files)
                os.remove(comp_path)

            logging.info(f"Response for {os.path.basename(file_path)}: {response.status_code} - {response.text}")
            if response.status_code == 200:
                self.result_queue.put((True, f"Image uploaded: {file_path}"))
            else:
                self.result_queue.put((False, f"Upload failed ({response.status_code}): {file_path}"))
        except Exception as e:
            logging.error(f"Error uploading {file_path}: {e}")
            self.result_queue.put((False, str(e)))

    def start_uploads(self, image_queue):
        """
        Starts the upload process for all images in the queue.
        """
        for path in image_queue:
            threading.Thread(target=self.upload_image, args=(path,), daemon=True).start()

    def process_results(self, total_images):
        """
        Processes the results from the upload threads.
        """
        done = 0
        while done < total_images:
            try:
                success, msg = self.result_queue.get(timeout=1)
                done += 1
                prog = (done / total_images) * 100
                self.app_state.progress_bar['value'] = prog
                self.app_state.root.update()

                if success:
                    logging.info(msg)
                else:
                    logging.error(msg)
                    self.app_state.failed_uploads.append(msg)
            except queue.Empty:
                continue

        if self.app_state.failed_uploads:
            self.app_state.upload_status_label.config(
                text=f"{len(self.app_state.failed_uploads)} images failed to upload."
            )
        else:
            self.app_state.upload_status_label.config(text="All images uploaded successfully")
        self.app_state.upload_button.config(state='normal')