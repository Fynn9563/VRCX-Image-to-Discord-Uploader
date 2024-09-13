# uploader.py
import os
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

    def create_payload(self, file_path, timestamp):
        """
        Creates the payload message for the webhook.
        """
        world_name, world_id, player_names = extract_image_metadata(file_path)
        if not all([world_name, world_id, player_names]):
            # If metadata is missing or incomplete
            if self.app_state.media_channel_var.get():
                thread_title = "Image Upload"
                payload = {
                    "thread_name": thread_title
                }
            else:
                payload = {}
            return payload

        # Create message content with links
        world_vrchat_id_link = f"[**VRChat**](<https://vrchat.com/home/launch?worldId={world_id}>)"
        world_vrcx_id_link = f"[**VRCX**](<https://vrcx.azurewebsites.net/world/{world_id}>)"
        message_content = (
            f"Photo taken at **{world_name}** (*{world_vrchat_id_link}*, *{world_vrcx_id_link}*) "
            f"with **{', '.join(player_names)}** at <t:{int(timestamp)}:f>"
        )
        thread_title = f"Photo taken at {world_name}"

        if len(thread_title) > 100:
            thread_title = thread_title[:97] + "..."

        if self.app_state.media_channel_var.get():
            payload = {
                "content": message_content,
                "thread_name": thread_title
            }
        else:
            payload = {
                "content": message_content
            }

        return payload

    def upload_image(self, file_path):
        """
        Uploads the image to the specified webhook URL.
        """
        try:
            timestamp = os.stat(file_path).st_ctime
            payload = self.create_payload(file_path, timestamp)

            if not payload:
                payload = {}

            with open(file_path, 'rb') as f:
                image_data = f.read()

            files = {'file': (os.path.basename(file_path), image_data)}
            response = requests.post(self.webhook_url, data=payload, files=files)

            if response.status_code == 413:
                # If file is too large, compress it
                compressed_file_path = compress_image(file_path)
                with open(compressed_file_path, 'rb') as f:
                    image_data = f.read()
                files = {'file': (os.path.basename(file_path), image_data)}
                response = requests.post(self.webhook_url, data=payload, files=files)
                os.remove(compressed_file_path)

            logging.info(f"Response for {os.path.basename(file_path)}: {response.status_code} - {response.text}")

            if response.status_code == 200:
                self.result_queue.put((True, f"Image {os.path.basename(file_path)} uploaded successfully"))
            else:
                self.result_queue.put((False, f"Image {os.path.basename(file_path)} upload failed: {response.status_code}"))
        except Exception as e:
            logging.error(f"Error uploading image {file_path}: {e}")
            self.result_queue.put((False, str(e)))

    def start_uploads(self, image_queue):
        """
        Starts the upload process for all images in the queue.
        """
        for file_path in image_queue:
            thread = threading.Thread(target=self.upload_image, args=(file_path,), daemon=True)
            thread.start()

    def process_results(self, total_images):
        """
        Processes the results from the upload threads.
        """
        processed_images = 0
        while processed_images < total_images:
            try:
                success, message = self.result_queue.get(timeout=1)
                processed_images += 1
                progress = (processed_images / total_images) * 100
                self.app_state.progress_bar['value'] = progress
                self.app_state.root.update()

                if success:
                    logging.info(message)
                else:
                    logging.error(message)
                    self.app_state.failed_uploads.append(message)
            except queue.Empty:
                continue

        # Update upload status
        if self.app_state.failed_uploads:
            self.app_state.upload_status_label.config(
                text=f"{len(self.app_state.failed_uploads)} images failed to upload."
            )
        else:
            self.app_state.upload_status_label.config(text="All images uploaded successfully")
        self.app_state.upload_button.config(state='normal')
