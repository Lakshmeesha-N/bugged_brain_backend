from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class BreakdownItem(BaseModel):
    category: str
    score: int
    max: int
    comment: str = ""


class Improvement(BaseModel):
    priority: Literal["high", "medium", "low"]
    section: str
    issue: str
    suggestion: str


class AtsResponse(BaseModel):
    overall_score: int
    label: str
    role_used: Optional[str] = None
    summary: str
    breakdown: List[BreakdownItem]
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[Improvement] = Field(default_factory=list)

    @classmethod
    def compute_label(cls, score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 50:
            return "Fair"
        return "Needs work"
