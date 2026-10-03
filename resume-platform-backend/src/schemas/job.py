from datetime import date
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl

JobType = Literal["internship", "full_time", "part_time", "contract", "freelance"]


class JobCreate(BaseModel):
    title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    job_type: JobType
    category: str = Field(..., min_length=1)
    apply_url: HttpUrl
    expires_at: Optional[date] = None


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    company: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = Field(None, min_length=1)
    job_type: Optional[JobType] = None
    category: Optional[str] = Field(None, min_length=1)
    apply_url: Optional[HttpUrl] = None
    expires_at: Optional[date] = None


class JobSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str
    job_type: JobType
    category: str
    created_at: Any = None
    expires_at: Optional[str] = None
    short_description: str


class JobDetail(JobSummary):
    description: str
    apply_url: str


class AdminJob(JobDetail):
    active: bool
    source: str
