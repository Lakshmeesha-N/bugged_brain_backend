"""Tests for GET /usage/me and PUT /admin/users/{uid}/plan."""

import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.core.auth import get_current_user, require_admin

FAKE_USER = {"uid": "uid-test", "admin": False}
ADMIN_USER = {"uid": "uid-admin", "admin": True}


# ---------------------------------------------------------------------------
# GET /usage/me
# ---------------------------------------------------------------------------

class TestGetMyUsage:
    def test_returns_correct_numbers(self, auth_client):
        with patch("src.routers.usage.get_plan", return_value="free"), \
             patch("src.routers.usage.get_limit", return_value=50000), \
             patch("src.routers.usage.get_usage_today",
                   return_value={"tokens_used": 1000, "requests": 5}), \
             patch("src.routers.usage.resets_at", return_value=3600), \
             patch("src.routers.usage.settings") as s:
            s.STRIPE_PAYMENT_LINK = "https://stripe.example.com"

            resp = auth_client.get("/usage/me")
            assert resp.status_code == 200
            data = resp.json()
            assert data["plan"] == "free"
            assert data["tokens_used"] == 1000
            assert data["limit"] == 50000
            assert data["remaining"] == 49000
            assert data["requests"] == 5
            assert data["resets_at"] == 3600
            assert data["upgrade_url"] == "https://stripe.example.com"

    def test_remaining_never_below_zero(self, auth_client):
        with patch("src.routers.usage.get_plan", return_value="premium"), \
             patch("src.routers.usage.get_limit", return_value=500000), \
             patch("src.routers.usage.get_usage_today",
                   return_value={"tokens_used": 600000, "requests": 200}), \
             patch("src.routers.usage.resets_at", return_value=100), \
             patch("src.routers.usage.settings") as s:
            s.STRIPE_PAYMENT_LINK = ""

            resp = auth_client.get("/usage/me")
            assert resp.status_code == 200
            data = resp.json()
            assert data["remaining"] == 0
            assert data["upgrade_url"] is None

    def test_premium_user_no_upgrade_url(self, auth_client):
        with patch("src.routers.usage.get_plan", return_value="premium"), \
             patch("src.routers.usage.get_limit", return_value=500000), \
             patch("src.routers.usage.get_usage_today",
                   return_value={"tokens_used": 0, "requests": 0}), \
             patch("src.routers.usage.resets_at", return_value=3600), \
             patch("src.routers.usage.settings") as s:
            s.STRIPE_PAYMENT_LINK = "https://stripe.example.com"

            resp = auth_client.get("/usage/me")
            assert resp.status_code == 200
            assert resp.json()["upgrade_url"] is None


# ---------------------------------------------------------------------------
# PUT /admin/users/{uid}/plan
# ---------------------------------------------------------------------------

class TestAdminPlanEndpoint:
    def test_non_admin_gets_403(self):
        def fake_require_admin():
            raise HTTPException(status_code=403, detail="Admin access required")

        app.dependency_overrides[require_admin] = fake_require_admin
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.put(
            "/admin/users/uid-test/plan",
            json={"plan": "premium"},
        )
        assert resp.status_code == 403

    def test_admin_can_set_plan(self):
        app.dependency_overrides[require_admin] = lambda: ADMIN_USER
        client = TestClient(app, raise_server_exceptions=True)

        with patch("src.routers.admin_users.set_plan") as mock_set_plan:
            resp = client.put(
                "/admin/users/uid-target/plan",
                json={"plan": "premium"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["uid"] == "uid-target"
            assert data["plan"] == "premium"
            mock_set_plan.assert_called_once_with("uid-target", "premium")
