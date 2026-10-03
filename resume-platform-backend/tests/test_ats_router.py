import io
from unittest.mock import AsyncMock, MagicMock, patch
from docx import Document
from fastapi.testclient import TestClient


def create_sample_docx(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


MOCK_AGENT_RESULT = {
    "role_used": "Software Engineer",
    "summary": "Great match. Well structured.",
    "breakdown": [
        {"category": "keywords_match", "score": 25, "max": 30, "comment": "Good"},
        {"category": "sections_and_structure", "score": 18, "max": 20, "comment": "Clear"},
        {"category": "formatting_readability", "score": 14, "max": 15, "comment": "Readable"},
        {"category": "impact_and_achievements", "score": 16, "max": 20, "comment": "Strong"},
        {"category": "clarity_and_length", "score": 12, "max": 15, "comment": "Concise"},
    ],
    "overall_score": 85,
    "matched_keywords": ["python", "fastapi"],
    "missing_keywords": ["docker"],
    "strengths": ["Clear structure"],
    "improvements": [
        {"priority": "high", "section": "Experience", "issue": "Missing metrics", "suggestion": "Add numbers"}
    ]
}


def test_check_ats_unauthorized_without_token(unauthed_client):
    long_text = "This is a detailed and complete software engineering resume with lots of text exceeding one hundred characters easily."
    docx_bytes = create_sample_docx(long_text)
    response = unauthed_client.post(
        "/ats/check",
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code in (401, 403)


@patch("src.routers.ats.record_usage")
@patch("src.routers.ats.start_usage_tracking", return_value=MagicMock(tokens=0))
@patch("src.routers.ats.run_ats_agent", new_callable=AsyncMock)
def test_check_ats_success(mock_run_agent, mock_tracking, mock_record, authed_no_limit_client):
    mock_run_agent.return_value = MOCK_AGENT_RESULT
    long_text = "This is a detailed and complete software engineering resume with lots of text exceeding one hundred characters easily."
    docx_bytes = create_sample_docx(long_text)
    response = authed_no_limit_client.post(
        "/ats/check",
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"job_title": "Software Engineer", "job_description": "Python dev"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 85
    assert data["label"] == "Good"
    assert data["role_used"] == "Software Engineer"


def test_check_ats_unsupported_file_type(authed_no_limit_client):
    response = authed_no_limit_client.post(
        "/ats/check",
        files={"file": ("resume.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 415


def test_check_ats_file_too_large(authed_no_limit_client):
    oversized = b"a" * (5 * 1024 * 1024 + 100)
    response = authed_no_limit_client.post(
        "/ats/check",
        files={"file": ("resume.pdf", oversized, "application/pdf")}
    )
    assert response.status_code == 413


def test_check_ats_no_text_found(authed_no_limit_client):
    short_text = "Too short"
    docx_bytes = create_sample_docx(short_text)
    response = authed_no_limit_client.post(
        "/ats/check",
        files={"file": ("short.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 422
    assert "no readable text" in response.json()["detail"]
