"""GET /usage/me — returns the current user's plan and daily usage."""

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user
from src.core.config import settings
from src.services.usage_service import get_limit, get_plan, get_usage_today, resets_at

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/me")
def get_my_usage(user: dict = Depends(get_current_user)):
    uid = user["uid"]
    plan = get_plan(uid)
    limit = get_limit(plan)
    usage = get_usage_today(uid)
    tokens_used = usage["tokens_used"]
    remaining = max(0, limit - tokens_used)

    payload = {
        "plan": plan,
        "tokens_used": tokens_used,
        "limit": limit,
        "remaining": remaining,
        "requests": usage["requests"],
        "resets_at": resets_at(),
        "upgrade_url": settings.STRIPE_PAYMENT_LINK if plan == "free" else None,
    }
    return payload
