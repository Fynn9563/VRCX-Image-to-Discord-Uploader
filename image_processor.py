# image_processor.py
import os
import json
import logging
import tempfile
from PIL import Image

def extract_image_metadata(file_path):
    """
    Extracts image metadata to determine world name, world ID, and player names.
    """
    try:
        with Image.open(file_path) as img:
            description = img.info.get('Description')
            if not description:
                return None, None, None

            metadata = json.loads(description)
            world_info = metadata.get('world', {})
            world_name = world_info.get('name', 'Unknown World')
            world_id = world_info.get('id', 'Unknown ID')
            players = metadata.get('players', [])
            player_names = [player.get('displayName', 'Unknown') for player in players]

            return world_name, world_id, player_names
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error extracting metadata from {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing {file_path}: {e}")
    return None, None, None

def compress_image(file_path, quality=85):
    """
    Compresses the image to a specific quality.
    """
    try:
        with Image.open(file_path) as img:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                img.save(temp_file.name, "JPEG", quality=quality)
            return temp_file.name
    except Exception as e:
        logging.error(f"Error compressing image {file_path}: {e}")
        raise
