from unittest.mock import patch
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

with patch("firebase_admin.initialize_app"):
    from src.core.auth import get_current_user, require_admin

app = FastAPI()


@app.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return user


@app.get("/admin-only")
def admin_route(user: dict = Depends(require_admin)):
    return user


client = TestClient(app)


def test_no_auth_header():
    response = client.get("/protected")
    assert response.status_code in (401, 403)


@patch("src.core.auth.auth.verify_id_token")
def test_invalid_token(mock_verify):
    mock_verify.side_effect = Exception("Token expired")
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer invalid_token_123"}
    )
    assert response.status_code == 401
    assert "Invalid or expired authentication token" in response.json()["detail"]


@patch("src.core.auth.auth.verify_id_token")
def test_valid_token_non_admin(mock_verify):
    mock_verify.return_value = {"uid": "test123"}
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer valid_token_123"}
    )
    assert response.status_code == 200
    assert response.json() == {"uid": "test123", "admin": False}


@patch("src.core.auth.auth.verify_id_token")
def test_valid_token_admin(mock_verify):
    mock_verify.return_value = {"uid": "admin123", "admin": True}
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer valid_token_123"}
    )
    assert response.status_code == 200
    assert response.json() == {"uid": "admin123", "admin": True}


@patch("src.core.auth.auth.verify_id_token")
def test_require_admin_forbidden_for_regular_user(mock_verify):
    mock_verify.return_value = {"uid": "test123", "admin": False}
    response = client.get(
        "/admin-only",
        headers={"Authorization": "Bearer regular_token"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


@patch("src.core.auth.auth.verify_id_token")
def test_require_admin_success_for_admin_user(mock_verify):
    mock_verify.return_value = {"uid": "admin123", "admin": True}
    response = client.get(
        "/admin-only",
        headers={"Authorization": "Bearer admin_token"}
    )
    assert response.status_code == 200
    assert response.json() == {"uid": "admin123", "admin": True}
