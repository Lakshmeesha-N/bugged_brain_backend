from unittest.mock import MagicMock, patch
import pytest
from src.services.template_service import (
    TemplateNotFound,
    get_template_fields,
    get_template_source,
    list_templates,
    render_html,
)

SAMPLE_FIELDS = {
    "id": "classic",
    "name": "Classic",
    "required": ["name", "email", "education"],
    "optional": ["skills", "projects"],
    "limits": {"projects": 3, "bullets_per_item": 3}
}

SAMPLE_JINJA = """
<h1>{{ name }}</h1>
<p>{{ email }}</p>
{% for edu in education %}
<div>{{ edu.institution }} - {{ edu.degree }}</div>
{% endfor %}
{% if skills %}
<p>{{ skills | join(', ') }}</p>
{% endif %}
"""


@patch("src.services.template_service.get_storage_client")
def test_get_template_fields_success(mock_get_client):
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_blob.download_as_text.return_value = '{"id": "classic", "name": "Classic", "required": ["name", "email", "education"]}'

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_get_client.return_value = mock_client

    fields = get_template_fields("classic")
    assert fields["id"] == "classic"
    assert fields["name"] == "Classic"


@patch("src.services.template_service.get_storage_client")
def test_get_template_fields_not_found(mock_get_client):
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_get_client.return_value = mock_client

    with pytest.raises(TemplateNotFound):
        get_template_fields("non_existent")


@patch("src.services.template_service.get_preview_url")
@patch("src.services.template_service.get_template_fields")
@patch("src.services.template_service.get_storage_client")
def test_list_templates(mock_get_client, mock_fields, mock_url):
    mock_blob1 = MagicMock()
    mock_blob1.name = "classic/fields.json"
    mock_blob2 = MagicMock()
    mock_blob2.name = "modern/fields.json"

    mock_bucket = MagicMock()
    mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]

    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_get_client.return_value = mock_client

    mock_fields.side_effect = lambda tid: {"name": tid.capitalize()}
    mock_url.side_effect = lambda tid: f"https://storage.googleapis.com/{tid}.png"

    templates = list_templates()
    assert len(templates) == 2
    assert templates[0]["id"] == "classic"
    assert templates[0]["name"] == "Classic"
    assert templates[0]["preview_url"] == "https://storage.googleapis.com/classic.png"


@patch("src.services.template_service.get_template_source")
def test_render_html_with_only_required_fields(mock_source):
    mock_source.return_value = SAMPLE_JINJA

    content = {
        "name": "John Doe",
        "email": "john@example.com",
        "education": [
            {"institution": "Tech Univ", "degree": "B.S. CS"}
        ]
    }

    html = render_html("classic", content)
    assert "John Doe" in html
    assert "john@example.com" in html
    assert "Tech Univ - B.S. CS" in html
