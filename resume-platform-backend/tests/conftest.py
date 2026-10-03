import os
import pytest
from fastapi.testclient import TestClient

# Set dummy environment variables for tests before Settings is instantiated
os.environ.setdefault("GCP_PROJECT_ID", "test-project-id")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("TEMPLATES_BUCKET", "test-bucket")
os.environ.setdefault("FREE_DAILY_TOKEN_LIMIT", "50000")
os.environ.setdefault("PREMIUM_DAILY_TOKEN_LIMIT", "500000")
os.environ.setdefault("STRIPE_PAYMENT_LINK", "")
os.environ.setdefault("USAGE_TIMEZONE", "Asia/Kolkata")


FAKE_USER = {"uid": "test123", "admin": False}


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """Ensure dependency overrides are clean before and after every test."""
    from src.main import app
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client():
    """TestClient with get_current_user overridden to return FAKE_USER."""
    from src.main import app
    from src.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def authed_no_limit_client():
    """TestClient with both get_current_user and enforce_llm_limit overridden."""
    from src.main import app
    from src.core.auth import get_current_user
    from src.core.limits import enforce_llm_limit
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    app.dependency_overrides[enforce_llm_limit] = lambda: FAKE_USER
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def unauthed_client():
    """TestClient with NO overrides — real auth applies."""
    from src.main import app
    return TestClient(app, raise_server_exceptions=False)
