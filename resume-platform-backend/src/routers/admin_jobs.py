from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from src.core.auth import require_admin
from src.schemas.job import AdminJob, JobCreate, JobUpdate
from src.services import job_service
from src.services.job_service import JobNotFound

router = APIRouter(prefix="/admin/jobs", tags=["admin-jobs"])


class SetActiveRequest(BaseModel):
    active: bool


@router.post("", response_model=dict)
@router.post("/", response_model=dict)
def create_new_job(job_data: JobCreate, user: dict = Depends(require_admin)):
    job_id = job_service.create_job(job_data.model_dump())
    return {"id": job_id}


@router.put("/{job_id}", response_model=AdminJob)
def update_existing_job(job_id: str, job_data: JobUpdate, user: dict = Depends(require_admin)):
    try:
        updated = job_service.update_job(job_id, job_data.model_dump(exclude_unset=True))
        return AdminJob(
            id=updated["id"],
            title=updated["title"],
            company=updated["company"],
            location=updated["location"],
            job_type=updated["job_type"],
            category=updated["category"],
            created_at=str(updated.get("created_at", "")),
            expires_at=str(updated.get("expires_at")) if updated.get("expires_at") else None,
            short_description=updated.get("description", "")[:200],
            description=updated.get("description", ""),
            apply_url=updated.get("apply_url", ""),
            active=updated.get("active", True),
            source=updated.get("source", "admin"),
        )
    except JobNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{job_id}/active", response_model=AdminJob)
def patch_job_active_status(job_id: str, body: SetActiveRequest, user: dict = Depends(require_admin)):
    try:
        updated = job_service.set_active(job_id, body.active)
        return AdminJob(
            id=updated["id"],
            title=updated["title"],
            company=updated["company"],
            location=updated["location"],
            job_type=updated["job_type"],
            category=updated["category"],
            created_at=str(updated.get("created_at", "")),
            expires_at=str(updated.get("expires_at")) if updated.get("expires_at") else None,
            short_description=updated.get("description", "")[:200],
            description=updated.get("description", ""),
            apply_url=updated.get("apply_url", ""),
            active=updated.get("active", True),
            source=updated.get("source", "admin"),
        )
    except JobNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{job_id}")
def delete_existing_job(job_id: str, user: dict = Depends(require_admin)):
    try:
        job_service.delete_job(job_id)
        return {"deleted": True}
    except JobNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=dict)
@router.get("/", response_model=dict)
def list_admin_jobs(
    job_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    user: dict = Depends(require_admin),
):
    result = job_service.list_jobs(
        job_type=job_type,
        category=category,
        location=location,
        q=q,
        limit=limit,
        offset=offset,
        include_inactive=True,
    )
    items = []
    for item in result["items"]:
        items.append(
            AdminJob(
                id=item["id"],
                title=item["title"],
                company=item["company"],
                location=item["location"],
                job_type=item["job_type"],
                category=item["category"],
                created_at=str(item.get("created_at", "")),
                expires_at=str(item.get("expires_at")) if item.get("expires_at") else None,
                short_description=item.get("description", "")[:200],
                description=item.get("description", ""),
                apply_url=item.get("apply_url", ""),
                active=item.get("active", True),
                source=item.get("source", "admin"),
            )
        )
    return {"items": [it.model_dump() for it in items], "total": result["total"]}
