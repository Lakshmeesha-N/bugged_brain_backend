"""FastAPI dependency for enforcing daily LLM token limits (PART 3)."""

from fastapi import Depends, HTTPException, status

from src.core.auth import get_current_user
from src.core.config import settings
from src.services.usage_service import LimitReached, check_limit, resets_at


def enforce_llm_limit(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: raise 429 if the user is at or over their daily token limit.

    Returns the user dict so routers can still use it normally.
    """
    try:
        check_limit(user["uid"])
    except LimitReached as exc:
        is_free = exc.plan == "free"
        if is_free:
            message = (
                "You have used your daily AI limit. "
                "Upgrade to premium to continue."
            )
        else:
            message = "You have reached today's limit. It resets at midnight."

        detail: dict = {
            "code": "limit_reached",
            "message": message,
            "plan": exc.plan,
            "used": exc.used,
            "limit": exc.limit,
            "resets_at": resets_at(),
        }
        if is_free:
            detail["upgrade_url"] = settings.STRIPE_PAYMENT_LINK
        else:
            detail["upgrade_url"] = None

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )

    return user
