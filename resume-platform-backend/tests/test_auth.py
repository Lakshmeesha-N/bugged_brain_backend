from unittest.mock import patch
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

with patch("firebase_admin.initialize_app"):
    from src.core.auth import get_current_user

app = FastAPI()


@app.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
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
def test_valid_token(mock_verify):
    mock_verify.return_value = {"uid": "test123"}
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer valid_token_123"}
    )
    assert response.status_code == 200
    assert response.json() == {"uid": "test123"}
