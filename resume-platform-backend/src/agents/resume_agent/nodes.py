import asyncio
import json
from pathlib import Path
from src.agents.resume_agent.state import ResumeState
from src.llm import generate_json
from src.services.template_service import get_template_fields

PROMPT_PATH = Path(__file__).resolve().parent / "prompt.md"


def _get_system_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "You are an expert Resume Agent."


async def load_template(state: ResumeState) -> dict:
    template_id = state.get("template_id", "classic")
    fields = await asyncio.to_thread(get_template_fields, template_id)
    return {"fields": fields, "attempts": 0}


async def generate(state: ResumeState) -> dict:
    profile = state.get("profile", {})
    extra_info = state.get("extra_info")
    answers = state.get("answers", [])
    fields = state.get("fields", {})
    attempts = state.get("attempts", 0) + 1
    validation_error = state.get("validation_error")

    system_prompt = _get_system_prompt()

    user_prompt_data = {
        "profile": profile,
        "extra_info": extra_info,
        "answers": answers,
        "template_fields": fields,
    }
    if validation_error:
        user_prompt_data["previous_validation_error"] = validation_error

    user_prompt = (
        "Generate a tailored resume in JSON format following the rules.\n"
        f"Input Data:\n{json.dumps(user_prompt_data, indent=2)}"
    )

    result = await generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    return {"result": result, "attempts": attempts, "validation_error": None}


async def validate(state: ResumeState) -> dict:
    result = state.get("result", {})
    fields = state.get("fields", {})
    attempts = state.get("attempts", 1)

    status = result.get("status")
    if status not in ("needs_info", "ready"):
        raise ValueError(f"Invalid status '{status}' in LLM result. Must be 'needs_info' or 'ready'.")

    if status == "needs_info":
        questions = result.get("questions")
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("needs_info result must have a non-empty list of questions.")
        if len(questions) > 5:
            result["questions"] = questions[:5]
        return {"result": result}

    # status == "ready"
    content = result.get("content")
    if not isinstance(content, dict):
        error_msg = "ready result must contain a 'content' object."
        if attempts < 2:
            return {"validation_error": error_msg}
        raise ValueError(error_msg)

    required_fields = set(fields.get("required", []))
    optional_fields = set(fields.get("optional", []))
    allowed_keys = required_fields | optional_fields

    # Check required fields
    for req in required_fields:
        val = content.get(req)
        if val is None or val == "" or (isinstance(val, list) and len(val) == 0):
            error_msg = f"Missing required field or empty value: '{req}'."
            if attempts < 2:
                return {"validation_error": error_msg}
            raise ValueError(error_msg)

    # Check unknown keys
    content_keys = set(content.keys())
    unknown_keys = content_keys - allowed_keys
    if unknown_keys:
        error_msg = f"Content contains unauthorized keys: {list(unknown_keys)}. Allowed keys are: {list(allowed_keys)}."
        if attempts < 2:
            return {"validation_error": error_msg}
        raise ValueError(error_msg)

    return {"result": result}
