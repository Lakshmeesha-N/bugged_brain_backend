#!/usr/bin/env python3
"""
Upload all sample templates from sample_templates/ to Google Cloud Storage.

Usage:
    python scripts/upload_templates.py
"""

from pathlib import Path
from google.cloud import storage
from src.core.config import settings


def upload_templates():
    sample_dir = Path(__file__).resolve().parent.parent / "sample_templates"
    if not sample_dir.exists():
        print(f"Directory {sample_dir} does not exist.")
        return

    client = storage.Client(project=settings.GCP_PROJECT_ID)
    bucket = client.bucket(settings.TEMPLATES_BUCKET)

    for template_dir in sample_dir.iterdir():
        if template_dir.is_dir():
            template_id = template_dir.name
            print(f"Uploading template: {template_id}...")
            for file_path in template_dir.iterdir():
                if file_path.is_file():
                    blob_name = f"{template_id}/{file_path.name}"
                    blob = bucket.blob(blob_name)
                    blob.upload_from_filename(str(file_path))
                    print(f"  Uploaded {file_path.name} -> gs://{settings.TEMPLATES_BUCKET}/{blob_name}")

    print("Template upload complete!")


if __name__ == "__main__":
    upload_templates()
