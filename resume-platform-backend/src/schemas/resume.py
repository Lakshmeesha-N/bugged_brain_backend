from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Answer(BaseModel):
    question: str
    answer: str


class GenerateRequest(BaseModel):
    template_id: str
    extra_info: Optional[str] = None
    answers: List[Answer] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    status: Literal["needs_info", "ready"]
    questions: Optional[List[str]] = None
    resume_id: Optional[str] = None
