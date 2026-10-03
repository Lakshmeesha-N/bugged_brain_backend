from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.llm import LLMError, generate_json, generate_text, get_llm_client


def test_get_llm_client_singleton():
    client1 = get_llm_client()
    client2 = get_llm_client()
    assert client1 is client2


@pytest.mark.asyncio
async def test_generate_text():
    mock_response = MagicMock()
    mock_response.text = "Generated resume content"

    mock_generate = AsyncMock(return_value=mock_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        result = await generate_text("system prompt", "user prompt")
        assert result == "Generated resume content"


@pytest.mark.asyncio
async def test_generate_json_success():
    mock_response = MagicMock()
    mock_response.text = '{"title": "Software Engineer", "score": 95}'

    mock_generate = AsyncMock(return_value=mock_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        result = await generate_json("system prompt", "user prompt")
        assert result == {"title": "Software Engineer", "score": 95}
        assert mock_generate.call_count == 1


@pytest.mark.asyncio
async def test_generate_json_retry_on_invalid_json():
    # First response is invalid JSON, second response is valid JSON
    bad_response = MagicMock()
    bad_response.text = "invalid json text"

    good_response = MagicMock()
    good_response.text = '{"status": "recovered"}'

    mock_generate = AsyncMock(side_effect=[bad_response, good_response])
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        result = await generate_json("system prompt", "user prompt")
        assert result == {"status": "recovered"}
        assert mock_generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_json_raises_llm_error_after_second_failure():
    bad_response = MagicMock()
    bad_response.text = "not json at all"

    mock_generate = AsyncMock(return_value=bad_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        with pytest.raises(LLMError, match="Failed to parse valid JSON"):
            await generate_json("system prompt", "user prompt")
        assert mock_generate.call_count == 2
