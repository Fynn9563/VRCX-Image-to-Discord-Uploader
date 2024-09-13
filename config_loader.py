# config_loader.py
import os
import sys
from configparser import ConfigParser
from tkinter import messagebox

def load_config(config_file='config.ini'):
    """
    Loads and validates the configuration file.
    """
    config = ConfigParser()
    if not os.path.exists(config_file):
        messagebox.showerror("Error", f"Configuration file '{config_file}' not found.")
        sys.exit(1)

    config.read(config_file)

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
            sys.exit(1)
        for option in required_options[section]:
            if not config.has_option(section, option):
                messagebox.showerror(
                    "Error", f"Missing option '{option}' in section '{section}' of configuration."
                )
                sys.exit(1)
    return config
