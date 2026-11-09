
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# Read storage path from environment
STORAGE_PATH = os.getenv("STORAGE_PATH", "private_storage")

# Resolve storage path
storage_path = Path(STORAGE_PATH)

if not storage_path.is_absolute():
    storage_path = (PROJECT_ROOT / storage_path).resolve()

STORAGE_DIR = storage_path

# Create private storage directory if it doesn't exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
