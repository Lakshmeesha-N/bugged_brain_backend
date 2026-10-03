from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user
from src.services import template_service
from src.services.template_service import TemplateNotFound

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("")
@router.get("/")
def list_all_templates(user: dict = Depends(get_current_user)):
    return template_service.list_templates()


@router.get("/{template_id}")
def get_template(template_id: str, user: dict = Depends(get_current_user)):
    try:
        return template_service.get_template_fields(template_id)
    except TemplateNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
