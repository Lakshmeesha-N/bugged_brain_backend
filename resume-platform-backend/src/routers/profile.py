from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user
from src.schemas.profile import ProfileSchema
from src.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
@router.get("/")
def get_user_profile(user: dict = Depends(get_current_user)):
    profile = profile_service.get_profile(user["uid"])
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.put("")
@router.put("/")
def save_user_profile(
    profile_data: ProfileSchema,
    user: dict = Depends(get_current_user)
):
    data = profile_data.model_dump()
    return profile_service.save_profile(user["uid"], data)


@router.delete("")
@router.delete("/")
def delete_user_profile(user: dict = Depends(get_current_user)):
    profile_service.delete_profile(user["uid"])
    return {"deleted": True}
