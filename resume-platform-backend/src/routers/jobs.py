from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.core.auth import get_current_user
from src.schemas.job import JobDetail, JobSummary
from src.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=dict)
@router.get("/", response_model=dict)
def list_active_jobs(
    job_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    result = job_service.list_jobs(
        job_type=job_type,
        category=category,
        location=location,
        q=q,
        limit=limit,
        offset=offset,
        include_inactive=False,
    )
    items = []
    for item in result["items"]:
        items.append(
            JobSummary(
                id=item["id"],
                title=item["title"],
                company=item["company"],
                location=item["location"],
                job_type=item["job_type"],
                category=item["category"],
                created_at=str(item.get("created_at", "")),
                expires_at=str(item.get("expires_at")) if item.get("expires_at") else None,
                short_description=item.get("description", "")[:200],
            )
        )
    return {"items": [it.model_dump() for it in items], "total": result["total"]}


@router.get("/{job_id}", response_model=JobDetail)
def get_job_detail(job_id: str, user: dict = Depends(get_current_user)):
    job = job_service.get_job(job_id)
    if not job or not job.get("active", True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    expires_at = job.get("expires_at")
    if expires_at:
        today_str = date.today().isoformat()
        if str(expires_at)[:10] < today_str:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job has expired.")

    return JobDetail(
        id=job["id"],
        title=job["title"],
        company=job["company"],
        location=job["location"],
        job_type=job["job_type"],
        category=job["category"],
        created_at=str(job.get("created_at", "")),
        expires_at=str(job.get("expires_at")) if job.get("expires_at") else None,
        short_description=job.get("description", "")[:200],
        description=job.get("description", ""),
        apply_url=job.get("apply_url", ""),
    )
