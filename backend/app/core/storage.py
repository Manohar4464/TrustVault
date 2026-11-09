
import os
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

# Storage configuration
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()

# Local storage (development fallback)
STORAGE_PATH = os.getenv("STORAGE_PATH", "private_storage")
storage_path = Path(STORAGE_PATH)

if not storage_path.is_absolute():
    storage_path = (PROJECT_ROOT / storage_path).resolve()

STORAGE_DIR = storage_path

# R2 configuration
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_REGION = os.getenv("R2_REGION", "auto")

s3_client = None

if STORAGE_BACKEND == "r2":
    required_vars = [
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
    ]

    missing = [key for key in required_vars if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            f"Missing R2 environment variables: {', '.join(missing)}"
        )

    if not R2_ENDPOINT_URL:
        raise RuntimeError("R2_ENDPOINT_URL is required")

    s3_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name=R2_REGION,
    )

elif STORAGE_BACKEND == "local":
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

else:
    raise RuntimeError("STORAGE_BACKEND must be 'local' or 'r2'")


def save_encrypted_file(filename: str, data: bytes) -> None:
    """Save already-encrypted document bytes."""
    if STORAGE_BACKEND == "r2":
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
            Body=data,
            ContentType="application/octet-stream",
        )
    else:
        file_path = STORAGE_DIR / filename

        with file_path.open("xb") as encrypted_file:
            encrypted_file.write(data)


def read_encrypted_file(filename: str) -> bytes:
    """Read encrypted document bytes."""
    if STORAGE_BACKEND == "r2":
        response = s3_client.get_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
        )
        return response["Body"].read()

    file_path = (STORAGE_DIR / filename).resolve()

    if file_path.parent != STORAGE_DIR.resolve():
        raise ValueError("Invalid storage filename")

    return file_path.read_bytes()


def delete_encrypted_file(filename: str) -> None:
    """Delete encrypted document bytes."""
    if STORAGE_BACKEND == "r2":
        s3_client.delete_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
        )
    else:
        file_path = (STORAGE_DIR / filename).resolve()

        if file_path.parent != STORAGE_DIR.resolve():
            raise ValueError("Invalid storage filename")

        if file_path.exists():
            file_path.unlink()
