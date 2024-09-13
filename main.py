# main.py
import logging
from tkinter import Tk
from config_loader import load_config
from gui import AppState, ApplicationGUI

def main():
    config = load_config()

    # Setup logging based on configuration
    log_level = config.get('Logging', 'log_level', fallback='INFO').upper()
    logging.basicConfig(
        filename=config.get('Logging', 'log_file'),
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
