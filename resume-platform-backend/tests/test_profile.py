from unittest.mock import patch
from fastapi.testclient import TestClient

SAMPLE_PAYLOAD = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1234567890",
    "location": "New York, NY",
    "summary": "Full Stack Developer",
    "links": {
        "linkedin": "https://linkedin.com/in/janedoe",
        "github": "https://github.com/janedoe",
        "portfolio": "https://janedoe.dev",
        "other": None
    },
    "skills": ["Python", "FastAPI"],
    "projects": [
        {
            "title": "Resume AI",
            "description": "An AI platform",
            "tech_stack": ["FastAPI", "React"],
            "link": "https://github.com/janedoe/resume-ai"
        }
    ],
    "experience": [
        {
            "company": "Tech Corp",
            "role": "Software Engineer",
            "duration": "2 years",
            "description": "Built backend APIs"
        }
    ],
    "education": [
        {
            "institution": "University of Tech",
            "degree": "B.S. Computer Science",
            "year": "2024",
            "grade": "3.9 GPA"
        }
    ],
    "achievements": [
        {
            "title": "Hackathon Winner",
            "description": "1st place out of 50 teams",
            "year": "2023"
        }
    ],
    "certifications": [
        {
            "name": "GCP Cloud Architect",
            "issuer": "Google",
            "year": "2024"
        }
    ],
    "publications": [
        {
            "title": "Scalable Microservices",
            "venue": "Tech Journal",
            "year": "2024",
            "link": "https://example.com/paper"
        }
    ],
    "extracurriculars": [
        {
            "title": "Open Source Club",
            "role": "Lead",
            "description": "Organized workshops"
        }
    ],
    "languages": ["English", "Spanish"]
}


@patch("src.routers.profile.profile_service.save_profile")
def test_put_profile_saves_and_returns(mock_save, auth_client):
    mock_save.return_value = SAMPLE_PAYLOAD
    response = auth_client.put("/profile", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == SAMPLE_PAYLOAD
    mock_save.assert_called_once_with("test123", SAMPLE_PAYLOAD)


@patch("src.routers.profile.profile_service.get_profile")
def test_get_profile_returns_saved_data(mock_get, auth_client):
    mock_get.return_value = SAMPLE_PAYLOAD
    response = auth_client.get("/profile")
    assert response.status_code == 200
    assert response.json() == SAMPLE_PAYLOAD
    mock_get.assert_called_once_with("test123")


@patch("src.routers.profile.profile_service.get_profile")
def test_get_profile_not_found_returns_404(mock_get, auth_client):
    mock_get.return_value = None
    response = auth_client.get("/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"
    mock_get.assert_called_once_with("test123")


@patch("src.routers.profile.profile_service.delete_profile")
def test_delete_profile_returns_success(mock_delete, auth_client):
    mock_delete.return_value = None
    response = auth_client.delete("/profile")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    mock_delete.assert_called_once_with("test123")


def test_put_profile_invalid_body_missing_name_returns_422(auth_client):
    invalid_payload = {
        "email": "jane@example.com",
        "education": [
            {
                "institution": "University of Tech",
                "degree": "B.S.",
                "year": "2024"
            }
        ]
    }
    response = auth_client.put("/profile", json=invalid_payload)
    assert response.status_code == 422


def test_put_profile_invalid_body_empty_education_returns_422(auth_client):
    invalid_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "education": []
    }
    response = auth_client.put("/profile", json=invalid_payload)
    assert response.status_code == 422
