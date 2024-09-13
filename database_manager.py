# database_manager.py
import sqlite3
import logging
from tkinter import messagebox

class DatabaseManager:
    """
    Manages database operations for webhooks.
    """
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.setup_database()

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
