from typing import Any, Dict, Optional
from typing_extensions import TypedDict


class AtsState(TypedDict, total=False):
    resume_text: str
    job_title: Optional[str]
    job_description: Optional[str]
    result: Dict[str, Any]
    attempts: int
    validation_error: Optional[str]
