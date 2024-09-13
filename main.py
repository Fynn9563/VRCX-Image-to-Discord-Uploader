# main.py
import os
import logging
from tkinter import Tk
from config_loader import load_config
from gui import AppState, ApplicationGUI

def main():
    config = load_config()

    # Setup logging based on configuration
    log_level = config.get('Logging', 'log_level', fallback='INFO').upper()

    # Get the log file path from the config, defaulting to 'app.log' if not specified
    log_file = config.get('Logging', 'log_file', fallback='app.log')

    # If the log file path is not absolute, place it in a user-writable directory
    if not os.path.isabs(log_file):
        # Get the user's AppData directory
        appdata_dir = os.getenv('APPDATA')
        # Create a subdirectory for your application
        log_dir = os.path.join(appdata_dir, 'VRChat Photo Uploader')
        os.makedirs(log_dir, exist_ok=True)  # Create the directory if it doesn't exist
        # Set the full path to the log file
        log_file = os.path.join(log_dir, log_file)
    else:
        # If the path is absolute, ensure the directory exists
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    root = Tk()
    app_state = AppState(root, config)
    app_state.initialize()

    app_gui = ApplicationGUI(app_state)
    root.mainloop()

    # Close database connection on exit
    app_state.database_manager.close()

if __name__ == "__main__":
    main()