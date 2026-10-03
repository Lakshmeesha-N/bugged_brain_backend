from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.core.auth import get_current_user
from src.main import app

client = TestClient(app)


def override_get_current_user():
    return {"uid": "test123"}


app.dependency_overrides[get_current_user] = override_get_current_user


@patch("src.routers.resume.profile_service.get_profile")
def test_generate_missing_profile_returns_404(mock_get_profile):
    mock_get_profile.return_value = None
    response = client.post(
        "/resume/generate",
        json={"template_id": "classic", "extra_info": None, "answers": []}
    )
    assert response.status_code == 404
    assert "Profile not found" in response.json()["detail"]


@patch("src.routers.resume.resume_service.save_resume")
@patch("src.routers.resume.run_resume_agent", new_callable=AsyncMock)
@patch("src.routers.resume.profile_service.get_profile")
def test_generate_needs_info_saves_nothing(mock_get_profile, mock_run_agent, mock_save):
    mock_get_profile.return_value = {"name": "Jane"}
    mock_run_agent.return_value = {
        "status": "needs_info",
        "questions": ["What is your graduation year?"]
    }

    response = client.post(
        "/resume/generate",
        json={"template_id": "classic", "extra_info": None, "answers": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_info"
    assert data["questions"] == ["What is your graduation year?"]
    assert data["resume_id"] is None
    mock_save.assert_not_called()


@patch("src.routers.resume.resume_service.save_resume")
@patch("src.routers.resume.run_resume_agent", new_callable=AsyncMock)
@patch("src.routers.resume.profile_service.get_profile")
def test_generate_ready_saves_and_returns_id(mock_get_profile, mock_run_agent, mock_save):
    mock_get_profile.return_value = {"name": "Jane"}
    mock_run_agent.return_value = {
        "status": "ready",
        "content": {"name": "Jane Doe", "email": "jane@example.com"}
    }
    mock_save.return_value = "res_12345"

    response = client.post(
        "/resume/generate",
        json={"template_id": "classic", "extra_info": None, "answers": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["resume_id"] == "res_12345"
    assert data["questions"] is None
    mock_save.assert_called_once_with(
        "test123",
        "classic",
        {"name": "Jane Doe", "email": "jane@example.com"}
    )


@patch("src.routers.resume.html_to_pdf")
@patch("src.routers.resume.template_service.render_html")
@patch("src.routers.resume.resume_service.get_resume")
def test_get_resume_pdf_returns_bytes(mock_get_resume, mock_render_html, mock_pdf):
    mock_get_resume.return_value = {
        "template_id": "classic",
        "content": {"name": "Jane Doe"}
    }
    mock_render_html.return_value = "<html><body>Jane Doe</body></html>"
    mock_pdf.return_value = b"%PDF-1.4 Mock PDF binary content"

    response = client.get("/resume/res_12345/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
