"""PUT /admin/users/{uid}/plan — admin-only plan management."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal

from src.core.auth import require_admin
from src.services.usage_service import set_plan

router = APIRouter(prefix="/admin/users", tags=["admin"])


class PlanUpdate(BaseModel):
    plan: Literal["free", "premium"]


@router.put("/{uid}/plan")
def update_user_plan(
    uid: str,
    body: PlanUpdate,
    _admin: dict = Depends(require_admin),
):
    """Set a user's plan to 'free' or 'premium'."""
    set_plan(uid, body.plan)
    return {"uid": uid, "plan": body.plan}
