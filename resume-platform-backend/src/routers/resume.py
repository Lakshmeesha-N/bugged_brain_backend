from fastapi import APIRouter, Depends, HTTPException, Response, status
from starlette.concurrency import run_in_threadpool

from src.agents.resume_agent import run_resume_agent
from src.core.limits import enforce_llm_limit
from src.llm import LLMError, start_usage_tracking
from src.schemas.resume import GenerateRequest, GenerateResponse
from src.services import profile_service, resume_service, template_service
from src.services.template_service import TemplateNotFound
from src.services.usage_service import record_usage
from src.utils.pdf import html_to_pdf

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_resume(
    req: GenerateRequest,
    user: dict = Depends(enforce_llm_limit),
):
    uid = user["uid"]
    counter = start_usage_tracking()

    profile = await run_in_threadpool(profile_service.get_profile, uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile before generating a resume.",
        )

    answers_dicts = [a.model_dump() for a in req.answers]

    agent_error: Exception | None = None
    result: dict = {}
    try:
        result = await run_resume_agent(
            template_id=req.template_id,
            profile=profile,
            extra_info=req.extra_info,
            answers=answers_dicts,
        )
    except TemplateNotFound as e:
        agent_error = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LLMError as e:
        agent_error = HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LLM Error: {str(e)}"
        )
    except Exception as e:
        agent_error = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    finally:
        # Always record — tokens were spent regardless of outcome
        await run_in_threadpool(record_usage, uid, counter.tokens)

    if agent_error is not None:
        raise agent_error

    if result.get("status") == "needs_info":
        return GenerateResponse(
            status="needs_info",
            questions=result.get("questions", []),
            resume_id=None,
        )

    # status == "ready"
    content = result.get("content", {})
    resume_id = await run_in_threadpool(
        resume_service.save_resume,
        uid,
        req.template_id,
        content,
    )
    return GenerateResponse(
        status="ready",
        questions=None,
        resume_id=resume_id,
    )


@router.get("/{resume_id}/pdf")
async def get_resume_pdf(
    resume_id: str,
    user: dict = Depends(enforce_llm_limit),
):
    uid = user["uid"]
    resume_doc = await run_in_threadpool(resume_service.get_resume, uid, resume_id)
    if not resume_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    template_id = resume_doc.get("template_id", "classic")
    content = resume_doc.get("content", {})

    try:
        html = await run_in_threadpool(template_service.render_html, template_id, content)
        pdf_bytes = await run_in_threadpool(html_to_pdf, html)
    except TemplateNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF rendering error: {str(e)}",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="resume.pdf"'},
    )


@router.get("")
@router.get("/")
def list_user_resumes(user: dict = Depends(enforce_llm_limit)):
    uid = user["uid"]
    return resume_service.list_resumes(uid)


@router.delete("/{resume_id}")
def delete_user_resume(resume_id: str, user: dict = Depends(enforce_llm_limit)):
    uid = user["uid"]
    resume_service.delete_resume(uid, resume_id)
    return {"deleted": True}
