

# **VRChat Screenshot Uploader**

This is a simple Python script that allows you to upload VRChat screenshots to a Discord channel using a webhook. The images have to be modified by [VRCX](https://github.com/pypy-vrc/VRCX) before being uploaded, as this adds metadata that is used to display information about the world and players in the Discord message.

## Usage

1. Install the required libraries using the '**install_dependencies.py**' script: `python install_dependencies.py`
2. Modify DISCORD_BOT_TOKEN in the **Upload to Discord.pyw** file with your actual Discord webhook URL (optional).
3. Start the application by double-clicking the **Upload to Discord.pyw** file.
4. Select the image you want to upload by clicking the "Browse" button and selecting the file.
5. Enter your Discord webhook URL in the "Webhook URL" field.
6. Click the "Upload Image" button.

## Note

-   The VRChat image must be modified by [VRCX](https://github.com/pypy-vrc/VRCX) to contain the necessary metadata.
-   If you don't want to copy your webhook each time you run it, you can replace the string `"https://discord.com/api/webhooks/your-webhook-url"` in the code with your actual webhook URL.

## Requirements

-   Python 3.6 or later
-   `requests` library
-   `pillow` library

These can be installed using the `install_dependencies.py` script.

**License**

This script is licensed under the MIT license. See the [LICENSE](https://github.com/Fynn9563/VRCX-Image-to-Discord-Uploader/blob/main/LICENSE) file for more information.
