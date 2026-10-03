from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class ResumeState(TypedDict, total=False):
    template_id: str
    profile: Dict[str, Any]
    job_title: Optional[str]
    job_description: Optional[str]
    extra_info: Optional[str]
    answers: List[Dict[str, str]]
    fields: Dict[str, Any]
    result: Dict[str, Any]
    attempts: int
    validation_error: Optional[str]
