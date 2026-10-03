"""Tests for src/core/limits.py and that record_usage is called correctly."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.core.limits import enforce_llm_limit
from src.services.usage_service import LimitReached

FAKE_USER_FREE = {"uid": "uid-free", "admin": False}
FAKE_USER_PREMIUM = {"uid": "uid-premium", "admin": False}


# ---------------------------------------------------------------------------
# Unit tests for enforce_llm_limit dependency directly
# ---------------------------------------------------------------------------

class TestEnforceLlmLimit:
    def test_passes_under_limit(self):
        with patch("src.core.limits.check_limit"):
            result = enforce_llm_limit({"uid": "u1"})
            assert result == {"uid": "u1"}

    def test_free_user_over_limit_raises_429(self):
        exc = LimitReached(plan="free", used=50000, limit=50000)
        with patch("src.core.limits.check_limit", side_effect=exc), \
             patch("src.core.limits.resets_at", return_value=3600), \
             patch("src.core.limits.settings") as s:
            s.STRIPE_PAYMENT_LINK = "https://stripe.example.com"

            with pytest.raises(HTTPException) as exc_info:
                enforce_llm_limit({"uid": "u1"})

            assert exc_info.value.status_code == 429
            detail = exc_info.value.detail
            assert detail["code"] == "limit_reached"
            assert detail["plan"] == "free"
            assert detail["used"] == 50000
            assert detail["upgrade_url"] == "https://stripe.example.com"

    def test_premium_user_over_limit_upgrade_url_is_null(self):
        exc = LimitReached(plan="premium", used=500001, limit=500000)
        with patch("src.core.limits.check_limit", side_effect=exc), \
             patch("src.core.limits.resets_at", return_value=1800), \
             patch("src.core.limits.settings") as s:
            s.STRIPE_PAYMENT_LINK = "https://stripe.example.com"

            with pytest.raises(HTTPException) as exc_info:
                enforce_llm_limit({"uid": "u2"})

            detail = exc_info.value.detail
            assert detail["upgrade_url"] is None


# ---------------------------------------------------------------------------
# Integration: verify record_usage is called in resume /generate endpoint
# ---------------------------------------------------------------------------

class TestRecordUsageIntegration:
    def test_usage_recorded_after_success(self, authed_no_limit_client):
        mock_counter = MagicMock()
        mock_counter.tokens = 42

        with patch("src.routers.resume.start_usage_tracking", return_value=mock_counter), \
             patch("src.routers.resume.profile_service.get_profile", return_value={"name": "T"}), \
             patch("src.routers.resume.run_resume_agent",
                   new_callable=AsyncMock,
                   return_value={"status": "ready", "content": {}}), \
             patch("src.routers.resume.resume_service.save_resume", return_value="rid1"), \
             patch("src.routers.resume.record_usage") as mock_record:

            authed_no_limit_client.post(
                "/resume/generate",
                json={"template_id": "classic", "extra_info": "", "answers": []},
            )
            mock_record.assert_called_once_with("test123", 42)

    def test_usage_recorded_after_needs_info(self, authed_no_limit_client):
        mock_counter = MagicMock()
        mock_counter.tokens = 10

        with patch("src.routers.resume.start_usage_tracking", return_value=mock_counter), \
             patch("src.routers.resume.profile_service.get_profile", return_value={"name": "T"}), \
             patch("src.routers.resume.run_resume_agent",
                   new_callable=AsyncMock,
                   return_value={"status": "needs_info", "questions": ["q1"]}), \
             patch("src.routers.resume.record_usage") as mock_record:

            resp = authed_no_limit_client.post(
                "/resume/generate",
                json={"template_id": "classic", "extra_info": "", "answers": []},
            )
            assert resp.json()["status"] == "needs_info"
            mock_record.assert_called_once_with("test123", 10)

    def test_usage_recorded_after_agent_error(self, authed_no_limit_client):
        mock_counter = MagicMock()
        mock_counter.tokens = 5

        with patch("src.routers.resume.start_usage_tracking", return_value=mock_counter), \
             patch("src.routers.resume.profile_service.get_profile", return_value={"name": "T"}), \
             patch("src.routers.resume.run_resume_agent",
                   new_callable=AsyncMock,
                   side_effect=Exception("agent crash")), \
             patch("src.routers.resume.record_usage") as mock_record:

            authed_no_limit_client.post(
                "/resume/generate",
                json={"template_id": "classic", "extra_info": "", "answers": []},
            )
            mock_record.assert_called_once_with("test123", 5)
