# VRChat Photo Uploader

Upload your VRChat photos to Discord with ease!

## Description

This tool allows users to select VRChat photos from their computer and upload them to a specified Discord webhook. If the photos contain metadata, it's extracted and used to create a rich message in Discord. Photos without metadata are uploaded without any accompanying message. If a photo is too large to be uploaded directly, the tool will automatically compress it to fit within Discord's size limits.

## Prerequisites

- **VRCX Metadata (Optional)**: For richer Discord messages, images should be modified by [VRCX](https://github.com/pypy-vrc/VRCX) to contain the necessary metadata. Ensure you're using VRCX to capture and save your VRChat photos if you want this feature.

## Features

- **Easy to Use**: Simple GUI for selecting photos and specifying a Discord webhook.
- **Metadata Extraction**: Extracts world and player information from VRChat photos when available.
- **Automatic Compression**: Automatically compresses photos that exceed Discord's size limits.
- **Webhook Management**: Save and manage multiple webhooks for different Discord channels.

## Installation

1. Ensure you have Python installed on your machine.
2. Clone this repository.
3. Run the `install_dependencies.py` script to install the required Python libraries:
   ```
   python install_dependencies.py
   ```
4. After the dependencies are installed, you can run the application by double-clicking on `Upload to Discord.pyw`.

## Usage

1. Open the tool.
2. Click "Browse" to select one or multiple VRChat photos.
3. Choose a saved webhook from the dropdown or add a new one.
4. Click "Upload Images" to start the upload process.
5. Monitor the progress bar and status messages to track the upload.

## Contributing

If you'd like to contribute, please fork the repository and make changes as you'd like. Pull requests are warmly welcome.

## License

This project is open-source and available under the [MIT License](https://github.com/Fynn9563/VRCX-Image-to-Discord-Uploader/blob/main/LICENSE).