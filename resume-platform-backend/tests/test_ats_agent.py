from unittest.mock import patch
import pytest
from src.agents.ats_agent import run_ats_agent
from src.llm import LLMError


@pytest.mark.asyncio
@patch("src.agents.ats_agent.nodes.generate_json")
async def test_ats_agent_overall_score_computed_and_improvements_sorted(mock_generate):
    mock_llm_output = {
        "role_used": "Software Engineer",
        "summary": "Solid resume. Good keywords.",
        "breakdown": [
            {"category": "keywords_match", "score": 25, "max": 30, "comment": "Good"},
            {"category": "sections_and_structure", "score": 18, "max": 20, "comment": "Clear"},
            {"category": "formatting_readability", "score": 14, "max": 15, "comment": "Readable"},
            {"category": "impact_and_achievements", "score": 16, "max": 20, "comment": "Strong"},
            {"category": "clarity_and_length", "score": 12, "max": 15, "comment": "Concise"},
        ],
        "matched_keywords": ["python", "fastapi"],
        "missing_keywords": ["docker"],
        "strengths": ["Clear structure"],
        "improvements": [
            {"priority": "low", "section": "Formatting", "issue": "Fonts", "suggestion": "Fix font"},
            {"priority": "high", "section": "Experience", "issue": "Missing metrics", "suggestion": "Add numbers"},
            {"priority": "medium", "section": "Skills", "issue": "Order", "suggestion": "Reorder"},
        ]
    }
    mock_generate.return_value = mock_llm_output

    result = await run_ats_agent(
        resume_text="Some resume text",
        job_title="Software Engineer",
        job_description="Looking for python dev"
    )

    # 25 + 18 + 14 + 16 + 12 = 85
    assert result["overall_score"] == 85
    assert len(result["improvements"]) == 3
    # Check priority sorting: high -> medium -> low
    assert result["improvements"][0]["priority"] == "high"
    assert result["improvements"][1]["priority"] == "medium"
    assert result["improvements"][2]["priority"] == "low"


@pytest.mark.asyncio
@patch("src.agents.ats_agent.nodes.generate_json")
async def test_ats_agent_scores_are_clamped(mock_generate):
    mock_llm_output = {
        "role_used": None,
        "summary": "Overview.",
        "breakdown": [
            {"category": "keywords_match", "score": 999, "max": 30},
            {"category": "sections_and_structure", "score": -50, "max": 20},
            {"category": "formatting_readability", "score": 15, "max": 15},
            {"category": "impact_and_achievements", "score": 20, "max": 20},
            {"category": "clarity_and_length", "score": 15, "max": 15},
        ],
        "matched_keywords": [],
        "missing_keywords": [],
        "strengths": [],
        "improvements": []
    }
    mock_generate.return_value = mock_llm_output

    result = await run_ats_agent(resume_text="Some resume text")

    # Clamped scores: 30 + 0 + 15 + 20 + 15 = 80
    assert result["overall_score"] == 80


@pytest.mark.asyncio
@patch("src.agents.ats_agent.nodes.generate_json")
async def test_ats_agent_retry_on_invalid_output_then_succeeds(mock_generate):
    bad_output = {"bad_key": "missing required keys"}
    good_output = {
        "role_used": None,
        "summary": "Summary.",
        "breakdown": [
            {"category": "keywords_match", "score": 20, "max": 30},
            {"category": "sections_and_structure", "score": 15, "max": 20},
            {"category": "formatting_readability", "score": 10, "max": 15},
            {"category": "impact_and_achievements", "score": 15, "max": 20},
            {"category": "clarity_and_length", "score": 10, "max": 15},
        ],
        "matched_keywords": [],
        "missing_keywords": [],
        "strengths": [],
        "improvements": []
    }

    mock_generate.side_effect = [bad_output, good_output]

    result = await run_ats_agent(resume_text="Some resume text")
    assert result["overall_score"] == 70
    assert mock_generate.call_count == 2


@pytest.mark.asyncio
@patch("src.agents.ats_agent.nodes.generate_json")
async def test_ats_agent_raises_llm_error_after_second_invalid_output(mock_generate):
    bad_output = {"bad_key": "missing required keys"}
    mock_generate.return_value = bad_output

    with pytest.raises(LLMError):
        await run_ats_agent(resume_text="Some resume text")
    assert mock_generate.call_count == 2
