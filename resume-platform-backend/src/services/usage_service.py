"""Usage and plan service (PART 2).

All Firestore access lives here — no other file should touch the
`plans` or `usage` collections.

Collections
-----------
plans/{uid}
    plan: "free" | "premium"

usage/{uid}/days/{YYYY-MM-DD}   (date in USAGE_TIMEZONE)
    tokens_used: int
    requests:    int
    updated_at:  datetime (UTC)
"""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from google.cloud import firestore

from src.core.config import settings
from src.core.database import get_db

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class LimitReached(Exception):
    """Raised when a user has consumed their daily token quota."""

    def __init__(self, plan: str, used: int, limit: int) -> None:
        self.plan = plan
        self.used = used
        self.limit = limit
        super().__init__(f"Daily limit reached: {used}/{limit} tokens ({plan} plan)")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tz() -> ZoneInfo:
    return ZoneInfo(settings.USAGE_TIMEZONE)


def _today_key() -> str:
    """YYYY-MM-DD in the configured timezone."""
    return datetime.datetime.now(tz=_tz()).strftime("%Y-%m-%d")


def _seconds_until_midnight() -> int:
    """Seconds from now until midnight in USAGE_TIMEZONE (the next reset)."""
    tz = _tz()
    now = datetime.datetime.now(tz=tz)
    tomorrow = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return max(0, int((tomorrow - now).total_seconds()))


def _plan_ref(uid: str):
    return get_db().collection("plans").document(uid)


def _day_ref(uid: str, date_key: str):
    return (
        get_db()
        .collection("usage")
        .document(uid)
        .collection("days")
        .document(date_key)
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_plan(uid: str) -> str:
    """Return 'free' or 'premium'. Missing document → 'free'."""
    doc = _plan_ref(uid).get()
    if not doc.exists:
        return "free"
    return doc.to_dict().get("plan", "free")


def get_limit(plan: str) -> int:
    """Return the daily token limit for *plan*."""
    if plan == "premium":
        return settings.PREMIUM_DAILY_TOKEN_LIMIT
    return settings.FREE_DAILY_TOKEN_LIMIT


def get_usage_today(uid: str) -> dict:
    """Return {'tokens_used': int, 'requests': int} for today."""
    doc = _day_ref(uid, _today_key()).get()
    if not doc.exists:
        return {"tokens_used": 0, "requests": 0}
    data = doc.to_dict()
    return {
        "tokens_used": data.get("tokens_used", 0),
        "requests": data.get("requests", 0),
    }


def record_usage(uid: str, tokens: int) -> None:
    """Atomically increment tokens_used and requests for today.

    Skips the write entirely when *tokens* is 0 to avoid unnecessary writes.
    """
    if tokens == 0:
        return
    ref = _day_ref(uid, _today_key())
    ref.set(
        {
            "tokens_used": firestore.Increment(tokens),
            "requests": firestore.Increment(1),
            "updated_at": datetime.datetime.now(tz=datetime.timezone.utc),
        },
        merge=True,
    )


def check_limit(uid: str) -> None:
    """Raise LimitReached when the user is at or over their daily quota."""
    plan = get_plan(uid)
    limit = get_limit(plan)
    usage = get_usage_today(uid)
    used = usage["tokens_used"]
    if used >= limit:
        raise LimitReached(plan=plan, used=used, limit=limit)


def set_plan(uid: str, plan: str) -> None:
    """Overwrite the plan for *uid*."""
    _plan_ref(uid).set({"plan": plan}, merge=True)


def resets_at() -> int:
    """Seconds until the next midnight reset in USAGE_TIMEZONE."""
    return _seconds_until_midnight()
