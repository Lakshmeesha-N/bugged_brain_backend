from pathlib import Path
from src.agents.ats_agent.state import AtsState
from src.llm import LLMError, generate_json

PROMPT_PATH = Path(__file__).resolve().parent / "prompt.md"

MAX_SCORES = {
    "keywords_match": 30,
    "sections_and_structure": 20,
    "formatting_readability": 15,
    "impact_and_achievements": 20,
    "clarity_and_length": 15,
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _get_system_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "You are an ATS resume reviewer."


async def analyze(state: AtsState) -> dict:
    resume_text = (state.get("resume_text") or "")[:15000]
    job_title = state.get("job_title") or "not provided"
    job_description = (state.get("job_description") or "not provided")[:6000]
    attempts = state.get("attempts", 0) + 1
    validation_error = state.get("validation_error")

    system_prompt = _get_system_prompt()

    user_prompt_parts = [
        f"--- RESUME TEXT ---\n{resume_text}\n",
        f"--- JOB TITLE ---\n{job_title}\n",
        f"--- JOB DESCRIPTION ---\n{job_description}\n",
    ]
    if validation_error:
        user_prompt_parts.append(f"--- PREVIOUS VALIDATION ERROR ---\n{validation_error}\nFix the JSON output to strictly match the requested schema.")

    user_prompt = "\n".join(user_prompt_parts)

    result = await generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    return {"result": result, "attempts": attempts, "validation_error": None}


async def validate(state: AtsState) -> dict:
    result = state.get("result", {})
    attempts = state.get("attempts", 1)

    try:
        if not isinstance(result, dict):
            raise ValueError("Result must be a JSON object.")

        required_keys = ["summary", "breakdown", "matched_keywords", "missing_keywords", "strengths", "improvements"]
        for k in required_keys:
            if k not in result:
                raise ValueError(f"Missing required key '{k}'.")

        if not isinstance(result["breakdown"], list):
            raise ValueError("'breakdown' must be a list of category scores.")

        breakdown_dict = {}
        for item in result["breakdown"]:
            cat = item.get("category")
            if cat in MAX_SCORES:
                raw_score = item.get("score", 0)
                try:
                    score_val = int(raw_score)
                except (ValueError, TypeError):
                    score_val = 0
                # Clamp score
                clamped_score = max(0, min(score_val, MAX_SCORES[cat]))
                item["score"] = clamped_score
                item["max"] = MAX_SCORES[cat]
                item["comment"] = str(item.get("comment", ""))
                breakdown_dict[cat] = item

        # Ensure all 5 categories are present
        normalized_breakdown = []
        for cat, max_val in MAX_SCORES.items():
            if cat in breakdown_dict:
                normalized_breakdown.append(breakdown_dict[cat])
            else:
                normalized_breakdown.append({
                    "category": cat,
                    "score": 0,
                    "max": max_val,
                    "comment": ""
                })
        result["breakdown"] = normalized_breakdown

        # Calculate overall score directly as sum of breakdown scores
        total_score = sum(item["score"] for item in normalized_breakdown)
        result["overall_score"] = max(0, min(total_score, 100))

        # Validate improvements
        raw_improvements = result.get("improvements", [])
        if not isinstance(raw_improvements, list):
            raw_improvements = []

        cleaned_improvements = []
        for imp in raw_improvements[:8]:
            priority = str(imp.get("priority", "medium")).lower()
            if priority not in PRIORITY_ORDER:
                priority = "medium"
            cleaned_improvements.append({
                "priority": priority,
                "section": str(imp.get("section", "")),
                "issue": str(imp.get("issue", "")),
                "suggestion": str(imp.get("suggestion", "")),
            })

        # Sort improvements high -> medium -> low
        cleaned_improvements.sort(key=lambda x: PRIORITY_ORDER.get(x["priority"], 1))
        result["improvements"] = cleaned_improvements

        # Clean strings / lists
        result["matched_keywords"] = [str(k) for k in result.get("matched_keywords", []) if isinstance(k, str)]
        result["missing_keywords"] = [str(k) for k in result.get("missing_keywords", []) if isinstance(k, str)]
        result["strengths"] = [str(s) for s in result.get("strengths", [])[:5] if isinstance(s, str)]

        return {"result": result}

    except Exception as e:
        error_msg = f"Validation failed: {str(e)}"
        if attempts < 2:
            return {"validation_error": error_msg}
        raise LLMError(error_msg) from e
