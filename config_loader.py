# config_loader.py
import os
import sys
from configparser import ConfigParser
from tkinter import messagebox

def load_config():
    """
    Loads and validates the configuration file.
    If the configuration file doesn't exist, creates it with default values.
    """
    # Get the user's AppData directory
    appdata_dir = os.getenv('APPDATA')
    # Create a subdirectory for your application
    config_dir = os.path.join(appdata_dir, 'VRChat Photo Uploader')
    os.makedirs(config_dir, exist_ok=True)  # Ensure the directory exists

    # Define the full path to the config.ini file
    config_file_path = os.path.join(config_dir, 'config.ini')

    # Create a ConfigParser object
    config = ConfigParser()

    if not os.path.exists(config_file_path):
        # If config.ini doesn't exist, create it with default values
        create_default_config(config_file_path, config)
    else:
        # Read the existing config.ini
        config.read(config_file_path)

    # Validate the configuration
    if not validate_config(config):
        sys.exit(1)

    return config

def create_default_config(config_file_path, config):
    """
    Creates a default configuration file with standard settings.
    """
    # Define default configuration values
    config['Application'] = {
        'app_title': 'VRChat Photo Uploader',
        'window_size': '630x630',
        'icon_path': 'icon.ico',
        'background_image': 'background_image.png',
        'font_family': 'Helvetica Rounded',
        'font_size': '11'
    }
    config['Logging'] = {
        'log_file': 'app.log',
        'log_level': 'INFO'
    }
    config['Database'] = {
        'db_name': 'webhooks.db'
    }

    # Write the default configuration to config.ini
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)

def validate_config(config):
    """
    Validates the configuration, ensuring all required sections and options are present.
    """
    required_sections = ['Logging', 'Database', 'Application']
    required_options = {
        'Logging': ['log_file', 'log_level'],
        'Database': ['db_name'],
        'Application': [
            'app_title', 'window_size', 'font_family', 'font_size',
            'icon_path', 'background_image'
        ]
    }

    for section in required_sections:
        if not config.has_section(section):
            messagebox.showerror("Error", f"Missing section '{section}' in configuration.")
            return False
        for option in required_options[section]:
            if not config.has_option(section, option):
                messagebox.showerror(
                    "Error", f"Missing option '{option}' in section '{section}' of configuration."
                )
                return False
    return True