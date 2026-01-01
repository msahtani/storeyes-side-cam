#!/usr/bin/env python3
"""Upload MP4 recordings to S3 with timestamp-based naming and date folder structure."""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# ---------- CONFIGURATION ----------
RECORDINGS_DIR = Path("recordings")

# ---------- ENVIRONMENT VARIABLES ----------
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = os.getenv("S3_PREFIX", "").rstrip("/")


def get_birth_datetime(path: Path) -> datetime:
    """
    Get the birth datetime of a file.

    Args:
        path: Path to the file.

    Returns:
        The birth datetime (or ctime as fallback).
    """
    stat = path.stat()

    # Linux: try birth time first (Python 3.10+)
    if hasattr(stat, "st_birthtime"):
        return datetime.fromtimestamp(stat.st_birthtime)

    # Fallback (metadata change time)
    return datetime.fromtimestamp(stat.st_ctime)


def get_files_to_upload(recordings_dir: Path) -> list[Path]:
    """
    Get list of MP4 files to upload, excluding the newest one.

    Args:
        recordings_dir: Directory containing recording files.

    Returns:
        List of file paths to upload, sorted by modification time.
    """
    files = sorted(
        [
            f
            for f in recordings_dir.iterdir()
            if f.is_file() and f.suffix == ".mp4"
        ],
        key=lambda f: f.stat().st_mtime,
    )

    if len(files) < 2:
        return []

    # Exclude the newest file (still recording)
    return files[:-1]


def upload_file_to_s3(
    file_path: Path,
    s3_client: Any,
    bucket: str,
    prefix: str,
    recordings_dir: Path,
) -> bool:
    """
    Rename and upload a file to S3, then delete local copy.

    Args:
        file_path: Path to the file to upload.
        s3_client: Boto3 S3 client.
        bucket: S3 bucket name.
        prefix: S3 prefix/prefix path.
        recordings_dir: Directory containing recordings.

    Returns:
        True if upload successful, False otherwise.
    """
    try:
        birth_dt = get_birth_datetime(file_path)
        mp4_name = birth_dt.strftime("gcam_%d%m%Y_%H%M%S.mp4")
        mp4_path = recordings_dir / mp4_name

        file_path.rename(mp4_path)

        # Add date folder structure: YYYY-MM-DD/
        date_folder = birth_dt.strftime("%Y-%m-%d")
        if prefix:
            s3_key = f"{prefix}/{date_folder}/{mp4_name}"
        else:
            s3_key = f"{date_folder}/{mp4_name}"

        print(f"Uploading to S3: s3://{bucket}/{s3_key}")
        s3_client.upload_file(str(mp4_path), bucket, s3_key)

        # Cleanup only after success
        mp4_path.unlink()
        print(f"Deleted local file: {mp4_name}")
        return True

    except (BotoCoreError, ClientError) as e:
        print(f"S3 upload failed for {file_path.name}: {e}")
        return False


def main() -> None:
    """Main function to process and upload MP4 files."""
    if not all([AWS_REGION, S3_BUCKET]):
        raise RuntimeError("Missing required AWS env variables")

    s3_client = boto3.client("s3", region_name=AWS_REGION)

    files_to_process = get_files_to_upload(RECORDINGS_DIR)

    if not files_to_process:
        print("Not enough files to process")
        sys.exit(0)

    for mp4_file in files_to_process:
        upload_file_to_s3(
            mp4_file, s3_client, S3_BUCKET, S3_PREFIX, RECORDINGS_DIR
        )


if __name__ == "__main__":
    main()
