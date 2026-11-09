import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Read storage path from .env
STORAGE_PATH = os.getenv("STORAGE_PATH", "../private_storage")

# Resolve storage path independently of the terminal directory
STORAGE_DIR = (PROJECT_ROOT / "backend" / STORAGE_PATH).resolve()

# Create private storage directory if it doesn't exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)