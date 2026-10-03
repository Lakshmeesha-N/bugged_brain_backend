from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from src.agents.ats_agent import run_ats_agent
from src.core.limits import enforce_llm_limit
from src.llm import LLMError, start_usage_tracking
from src.schemas.ats import AtsResponse
from src.services.usage_service import record_usage
from src.utils.file_text import FileTooLarge, NoTextFound, UnsupportedFileType, extract_text

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/check", response_model=AtsResponse)
async def check_ats(
    file: UploadFile = File(...),
    job_title: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None),
    user: dict = Depends(enforce_llm_limit),
):
    uid = user["uid"]
    counter = start_usage_tracking()

    try:
        content_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}",
        )

    filename = file.filename or "uploaded_file"

    try:
        extracted_text = await run_in_threadpool(extract_text, filename, content_bytes)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))
    except FileTooLarge as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except NoTextFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The file has no readable text, please upload a text-based PDF or DOCX.",
        )

    agent_error: Exception | None = None
    agent_result: dict = {}
    try:
        agent_result = await run_ats_agent(
            resume_text=extracted_text,
            job_title=job_title,
            job_description=job_description,
        )
    except LLMError as e:
        agent_error = HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LLM Error: {str(e)}"
        )
    except Exception as e:
        agent_error = HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ATS Analysis error: {str(e)}"
        )
    finally:
        # Always record tokens spent, even on error
        await run_in_threadpool(record_usage, uid, counter.tokens)

    if agent_error is not None:
        raise agent_error

    overall_score = agent_result.get("overall_score", 0)
    label = AtsResponse.compute_label(overall_score)

    return AtsResponse(
        overall_score=overall_score,
        label=label,
        role_used=agent_result.get("role_used"),
        summary=agent_result.get("summary", ""),
        breakdown=agent_result.get("breakdown", []),
        matched_keywords=agent_result.get("matched_keywords", []),
        missing_keywords=agent_result.get("missing_keywords", []),
        strengths=agent_result.get("strengths", []),
        improvements=agent_result.get("improvements", []),
    )
