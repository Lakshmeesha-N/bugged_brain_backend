from datetime import timedelta
import functools
import json
import google.auth
from google.auth.transport.requests import Request
from google.cloud import storage
from jinja2.sandbox import SandboxedEnvironment

from src.core.config import settings


class TemplateNotFound(Exception):
    """Raised when a resume template or required file cannot be found."""
    pass


@functools.lru_cache(maxsize=1)
def get_storage_client() -> storage.Client:
    return storage.Client(project=settings.GCP_PROJECT_ID)


def list_templates() -> list[dict]:
    client = get_storage_client()
    bucket = client.bucket(settings.TEMPLATES_BUCKET)
    blobs = list(bucket.list_blobs())

    template_ids = set()
    for blob in blobs:
        parts = blob.name.split("/")
        if len(parts) > 1 and parts[0]:
            template_ids.add(parts[0])

    templates = []
    for tid in sorted(template_ids):
        try:
            fields = get_template_fields(tid)
            url = get_preview_url(tid)
            templates.append({
                "id": tid,
                "name": fields.get("name", tid),
                "preview_url": url,
            })
        except Exception:
            continue

    return templates


def get_preview_url(template_id: str) -> str:
    client = get_storage_client()
    bucket = client.bucket(settings.TEMPLATES_BUCKET)
    blob = bucket.blob(f"{template_id}/preview.png")

    credentials, _ = google.auth.default()
    if hasattr(credentials, "refresh"):
        credentials.refresh(Request())

    service_account_email = getattr(credentials, "service_account_email", None)
    access_token = getattr(credentials, "token", None)

    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET",
        service_account_email=service_account_email,
        access_token=access_token,
    )


def get_template_fields(template_id: str) -> dict:
    client = get_storage_client()
    bucket = client.bucket(settings.TEMPLATES_BUCKET)
    blob = bucket.blob(f"{template_id}/fields.json")
    if not blob.exists():
        raise TemplateNotFound(f"Template fields not found for template_id: {template_id}")

    try:
        content = blob.download_as_text()
        return json.loads(content)
    except Exception as e:
        raise TemplateNotFound(f"Error reading fields.json for template_id: {template_id}: {str(e)}") from e


def get_template_source(template_id: str) -> str:
    client = get_storage_client()
    bucket = client.bucket(settings.TEMPLATES_BUCKET)
    blob = bucket.blob(f"{template_id}/template.jinja")
    if not blob.exists():
        raise TemplateNotFound(f"Template source not found for template_id: {template_id}")

    return blob.download_as_text()


def render_html(template_id: str, content: dict) -> str:
    source = get_template_source(template_id)
    env = SandboxedEnvironment(autoescape=True)
    template = env.from_string(source)
    return template.render(**content)
