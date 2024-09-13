# VRChat Photo Uploader

Upload your VRChat photos to Discord with ease!

## Description

VRChat Photo Uploader is a tool that allows users to easily upload their VRChat photos to a specified Discord webhook. If the photos contain metadata (like world and player information), it's extracted and used to create a rich message in Discord. For photos without metadata, the tool simply uploads them without an accompanying message. If a photo exceeds Discord's size limits, the tool automatically compresses it to ensure successful uploads.

This tool is now packaged as an executable with an easy-to-use installer, so no Python installation is required!

## Features

- **Easy to Use**: Simple GUI for selecting photos and specifying a Discord webhook.
- **Metadata Extraction**: Extracts world and player information from VRChat photos when available.
- **Clickable World ID URLs**: Automatically generates clickable links for world IDs, allowing users to open corresponding VRChat worlds in their browser.
- **Automatic Compression**: Compresses photos that exceed Discord's file size limit.
- **Webhook Management**: Save and manage multiple Discord webhooks for easy reuse.
- **Discord Media Channel Option**: Includes a "Discord Media Channel" checkbox for uploads to Discord Media Channels, ensuring compatibility with Discord's media channel features.

## Installation

You no longer need to manually install Python or dependencies! Follow these steps to install the VRChat Photo Uploader:

1. **Download the Installer**:
   - Go to the **[Releases](https://github.com/Fynn9563/VRCX-Image-to-Discord-Uploader/releases)** section of the GitHub repository.
   - Download the latest version of the installer (`Setup.exe`).

2. **Run the Installer**:
   - Double-click on `Setup.exe` to install VRChat Photo Uploader on your computer.
   - Follow the prompts to complete the installation.

3. **Launch the Application**:
   - Once installed, you can find the VRChat Photo Uploader in your Start Menu or on your Desktop if you selected the option to create a shortcut.

## Usage

1. **Open the Tool**: Launch the VRChat Photo Uploader from your desktop or Start Menu.
2. **Browse Photos**: Click "Browse" to select one or multiple VRChat photos from your computer.
3. **Select Webhook**: Choose a saved webhook from the dropdown or add a new one by providing the webhook name and URL.
4. **Optional Media Channel Upload**: Check the "Discord Media Channel" box if you’re uploading to a Discord Media Channel.
5. **Upload Images**: Click "Upload Images" to start the upload process.
6. **Monitor Progress**: Watch the progress bar and status messages for feedback on the upload process.

## License

This project is licensed under the [MIT License](https://github.com/Fynn9563/VRCX-Image-to-Discord-Uploader/blob/main/LICENSE).

---