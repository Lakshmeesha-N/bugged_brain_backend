"""Tests for src/services/usage_service.py (mock Firestore)."""

import datetime
import pytest
from unittest.mock import MagicMock, patch, call
from zoneinfo import ZoneInfo

from src.services.usage_service import (
    LimitReached,
    check_limit,
    get_limit,
    get_plan,
    get_usage_today,
    record_usage,
    resets_at,
    set_plan,
    _today_key,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _mock_doc(exists: bool, data: dict | None = None):
    doc = MagicMock()
    doc.exists = exists
    doc.to_dict.return_value = data or {}
    return doc


def _mock_db():
    """Return a mock Firestore client that intercepts collection/document chains."""
    db = MagicMock()
    return db


# ---------------------------------------------------------------------------
# get_plan
# ---------------------------------------------------------------------------

class TestGetPlan:
    def test_missing_document_returns_free(self):
        doc = _mock_doc(exists=False)
        with patch("src.services.usage_service.get_db") as mock_get_db:
            mock_get_db.return_value.collection.return_value.document.return_value.get.return_value = doc
            assert get_plan("uid1") == "free"

    def test_premium_plan_returned(self):
        doc = _mock_doc(exists=True, data={"plan": "premium"})
        with patch("src.services.usage_service.get_db") as mock_get_db:
            mock_get_db.return_value.collection.return_value.document.return_value.get.return_value = doc
            assert get_plan("uid1") == "premium"

    def test_free_plan_returned(self):
        doc = _mock_doc(exists=True, data={"plan": "free"})
        with patch("src.services.usage_service.get_db") as mock_get_db:
            mock_get_db.return_value.collection.return_value.document.return_value.get.return_value = doc
            assert get_plan("uid1") == "free"


# ---------------------------------------------------------------------------
# get_limit
# ---------------------------------------------------------------------------

class TestGetLimit:
    def test_free_limit(self):
        with patch("src.services.usage_service.settings") as s:
            s.FREE_DAILY_TOKEN_LIMIT = 50000
            s.PREMIUM_DAILY_TOKEN_LIMIT = 500000
            assert get_limit("free") == 50000

    def test_premium_limit(self):
        with patch("src.services.usage_service.settings") as s:
            s.FREE_DAILY_TOKEN_LIMIT = 50000
            s.PREMIUM_DAILY_TOKEN_LIMIT = 500000
            assert get_limit("premium") == 500000


# ---------------------------------------------------------------------------
# record_usage
# ---------------------------------------------------------------------------

class TestRecordUsage:
    def test_uses_increment(self):
        with patch("src.services.usage_service.get_db") as mock_get_db, \
             patch("src.services.usage_service.firestore") as mock_firestore:
            mock_firestore.Increment.side_effect = lambda x: f"INC({x})"
            ref = MagicMock()
            (mock_get_db.return_value
             .collection.return_value
             .document.return_value
             .collection.return_value
             .document.return_value) = ref

            record_usage("uid1", 100)

            ref.set.assert_called_once()
            args, kwargs = ref.set.call_args
            data = args[0]
            assert data["tokens_used"] == "INC(100)"
            assert data["requests"] == "INC(1)"
            assert kwargs.get("merge") is True

    def test_skips_write_when_tokens_zero(self):
        with patch("src.services.usage_service.get_db") as mock_get_db:
            record_usage("uid1", 0)
            mock_get_db.assert_not_called()


# ---------------------------------------------------------------------------
# check_limit
# ---------------------------------------------------------------------------

class TestCheckLimit:
    def _setup(self, plan: str, tokens_used: int):
        """Patch get_plan and get_usage_today for check_limit tests."""
        patcher_plan = patch("src.services.usage_service.get_plan", return_value=plan)
        patcher_usage = patch(
            "src.services.usage_service.get_usage_today",
            return_value={"tokens_used": tokens_used, "requests": 1},
        )
        patcher_settings = patch("src.services.usage_service.settings")
        return patcher_plan, patcher_usage, patcher_settings

    def test_passes_below_limit(self):
        with patch("src.services.usage_service.get_plan", return_value="free"), \
             patch("src.services.usage_service.get_usage_today",
                   return_value={"tokens_used": 100, "requests": 1}), \
             patch("src.services.usage_service.settings") as s:
            s.FREE_DAILY_TOKEN_LIMIT = 50000
            s.PREMIUM_DAILY_TOKEN_LIMIT = 500000
            check_limit("uid1")  # must not raise

    def test_raises_at_limit(self):
        with patch("src.services.usage_service.get_plan", return_value="free"), \
             patch("src.services.usage_service.get_usage_today",
                   return_value={"tokens_used": 50000, "requests": 10}), \
             patch("src.services.usage_service.settings") as s:
            s.FREE_DAILY_TOKEN_LIMIT = 50000
            s.PREMIUM_DAILY_TOKEN_LIMIT = 500000
            with pytest.raises(LimitReached) as exc_info:
                check_limit("uid1")
            assert exc_info.value.plan == "free"
            assert exc_info.value.used == 50000
            assert exc_info.value.limit == 50000

    def test_raises_above_limit(self):
        with patch("src.services.usage_service.get_plan", return_value="premium"), \
             patch("src.services.usage_service.get_usage_today",
                   return_value={"tokens_used": 600000, "requests": 100}), \
             patch("src.services.usage_service.settings") as s:
            s.FREE_DAILY_TOKEN_LIMIT = 50000
            s.PREMIUM_DAILY_TOKEN_LIMIT = 500000
            with pytest.raises(LimitReached):
                check_limit("uid1")


# ---------------------------------------------------------------------------
# _today_key uses USAGE_TIMEZONE
# ---------------------------------------------------------------------------

class TestTodayKey:
    def test_date_key_uses_usage_timezone(self):
        with patch("src.services.usage_service.settings") as s:
            s.USAGE_TIMEZONE = "Asia/Kolkata"
            key = _today_key()
            tz = ZoneInfo("Asia/Kolkata")
            expected = datetime.datetime.now(tz=tz).strftime("%Y-%m-%d")
            assert key == expected
