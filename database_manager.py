# database_manager.py
import sqlite3
import logging
import os
from tkinter import messagebox

class DatabaseManager:
    """
    Manages database operations for webhooks.
    """
    def __init__(self, db_name):
        self.db_name = self.get_database_path(db_name)
        self.conn = None
        self.cursor = None
        self.connect()
        self.setup_database()

    def get_database_path(self, db_name):
        """
        Determines the full path to the database file in a user-writable directory.
        """
        # If db_name is an absolute path, return it as is
        if os.path.isabs(db_name):
            return db_name
        else:
            # Get the user's AppData directory
            appdata_dir = os.getenv('APPDATA')
            # Create a subdirectory for your application
            data_dir = os.path.join(appdata_dir, 'VRChat Photo Uploader')
            os.makedirs(data_dir, exist_ok=True)  # Create the directory if it doesn't exist
            # Return the full path to the database file
            return os.path.join(data_dir, db_name)

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            messagebox.showerror("Error", f"Database connection error: {e}")
            raise

    def setup_database(self):
        """
        Sets up the database table for storing webhooks.
        """
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error setting up database: {e}")
            messagebox.showerror("Error", f"Error setting up database: {e}")
            raise

    def insert_webhook(self, name, url):
        """
        Inserts a webhook into the database after validation.
        """
        try:
            self.cursor.execute("INSERT INTO webhooks (name, url) VALUES (?, ?)", (name, url))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error inserting webhook: {e}")
            messagebox.showerror("Error", f"Error inserting webhook: {e}")

    def delete_webhook(self, name):
        """
        Deletes a webhook from the database by name.
        """
        try:
            self.cursor.execute("DELETE FROM webhooks WHERE name = ?", (name,))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error deleting webhook: {e}")
            messagebox.showerror("Error", f"Error deleting webhook: {e}")

    def get_all_webhooks(self):
        """
        Retrieves all webhooks from the database.
        """
        try:
            self.cursor.execute("SELECT name, url FROM webhooks")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error retrieving webhooks: {e}")
            messagebox.showerror("Error", f"Error retrieving webhooks: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()