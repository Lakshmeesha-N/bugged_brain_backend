from unittest.mock import AsyncMock, patch
import pytest
from src.agents.resume_agent import run_resume_agent

SAMPLE_PROFILE = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "education": [{"institution": "Tech Univ", "degree": "B.S."}],
    "skills": ["Python"],
}

SAMPLE_FIELDS = {
    "id": "classic",
    "name": "Classic",
    "required": ["name", "email", "education"],
    "optional": ["phone", "skills", "projects", "experience"],
}


@pytest.mark.asyncio
@patch("src.agents.resume_agent.nodes.get_template_fields")
@patch("src.agents.resume_agent.nodes.generate_json")
async def test_agent_needs_info_passes_through(mock_generate, mock_get_fields):
    mock_get_fields.return_value = SAMPLE_FIELDS
    mock_generate.return_value = {
        "status": "needs_info",
        "questions": ["What is your graduation year?"]
    }

    result = await run_resume_agent("classic", SAMPLE_PROFILE)
    assert result["status"] == "needs_info"
    assert result["questions"] == ["What is your graduation year?"]


@pytest.mark.asyncio
@patch("src.agents.resume_agent.nodes.get_template_fields")
@patch("src.agents.resume_agent.nodes.generate_json")
async def test_agent_ready_passes_through(mock_generate, mock_get_fields):
    mock_get_fields.return_value = SAMPLE_FIELDS
    ready_content = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "education": [{"institution": "Tech Univ", "degree": "B.S."}],
        "skills": ["Python"]
    }
    mock_generate.return_value = {
        "status": "ready",
        "content": ready_content
    }

    result = await run_resume_agent("classic", SAMPLE_PROFILE)
    assert result["status"] == "ready"
    assert result["content"] == ready_content


@pytest.mark.asyncio
@patch("src.agents.resume_agent.nodes.get_template_fields")
@patch("src.agents.resume_agent.nodes.generate_json")
async def test_agent_missing_required_triggers_retry_then_succeeds(mock_generate, mock_get_fields):
    mock_get_fields.return_value = SAMPLE_FIELDS
    bad_content = {
        "name": "Jane Doe",
        # Missing required email and education
    }
    good_content = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "education": [{"institution": "Tech Univ", "degree": "B.S."}]
    }

    mock_generate.side_effect = [
        {"status": "ready", "content": bad_content},
        {"status": "ready", "content": good_content},
    ]

    result = await run_resume_agent("classic", SAMPLE_PROFILE)
    assert result["status"] == "ready"
    assert result["content"] == good_content
    assert mock_generate.call_count == 2


@pytest.mark.asyncio
@patch("src.agents.resume_agent.nodes.get_template_fields")
@patch("src.agents.resume_agent.nodes.generate_json")
async def test_agent_missing_required_triggers_retry_then_raises_error(mock_generate, mock_get_fields):
    mock_get_fields.return_value = SAMPLE_FIELDS
    bad_content = {
        "name": "Jane Doe",
        # Missing required email and education
    }

    mock_generate.return_value = {
        "status": "ready",
        "content": bad_content
    }

    with pytest.raises(ValueError, match="Missing required field"):
        await run_resume_agent("classic", SAMPLE_PROFILE)


@pytest.mark.asyncio
@patch("src.agents.resume_agent.nodes.get_template_fields")
@patch("src.agents.resume_agent.nodes.generate_json")
async def test_agent_unknown_content_keys_rejected(mock_generate, mock_get_fields):
    mock_get_fields.return_value = SAMPLE_FIELDS
    bad_content = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "education": [{"institution": "Tech Univ", "degree": "B.S."}],
        "unauthorized_field": "some data"
    }

    mock_generate.return_value = {
        "status": "ready",
        "content": bad_content
    }

    with pytest.raises(ValueError, match="unauthorized keys"):
        await run_resume_agent("classic", SAMPLE_PROFILE)
