"""Updated test_llm.py — adds token-counting assertions (PART 5)."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.llm import LLMError, generate_json, generate_text, get_llm_client
from src.llm.usage import _current_counter, start_usage_tracking


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(text: str, total_token_count: int | None = None) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    meta = MagicMock()
    meta.total_token_count = total_token_count
    resp.usage_metadata = meta
    return resp


# ---------------------------------------------------------------------------
# Existing tests (preserved)
# ---------------------------------------------------------------------------

def test_get_llm_client_singleton():
    client1 = get_llm_client()
    client2 = get_llm_client()
    assert client1 is client2


@pytest.mark.asyncio
async def test_generate_text():
    mock_response = _make_response("Generated resume content", total_token_count=0)
    mock_generate = AsyncMock(return_value=mock_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        result = await generate_text("system prompt", "user prompt")
        assert result == "Generated resume content"


@pytest.mark.asyncio
async def test_generate_json_success():
    mock_response = _make_response('{"title": "Software Engineer", "score": 95}', 0)
    mock_generate = AsyncMock(return_value=mock_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        result = await generate_json("system prompt", "user prompt")
        assert result == {"title": "Software Engineer", "score": 95}
        assert mock_generate.call_count == 1


@pytest.mark.asyncio
async def test_generate_json_retry_on_invalid_json():
    bad_response = _make_response("invalid json text", 0)
    good_response = _make_response('{"status": "recovered"}', 0)
    mock_generate = AsyncMock(side_effect=[bad_response, good_response])
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        result = await generate_json("system prompt", "user prompt")
        assert result == {"status": "recovered"}
        assert mock_generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_json_raises_llm_error_after_second_failure():
    bad_response = _make_response("not json at all", 0)
    mock_generate = AsyncMock(return_value=bad_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        with pytest.raises(LLMError, match="Failed to parse valid JSON"):
            await generate_json("system prompt", "user prompt")
        assert mock_generate.call_count == 2


# ---------------------------------------------------------------------------
# New token-counting tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_json_adds_token_count():
    """generate_json adds tokens from usage_metadata to the active counter."""
    counter = start_usage_tracking()
    mock_response = _make_response('{"ok": true}', total_token_count=42)
    mock_generate = AsyncMock(return_value=mock_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        await generate_json("sys", "user")
    assert counter.tokens == 42


@pytest.mark.asyncio
async def test_generate_json_retry_adds_tokens_twice():
    """Each attempt (including the retry) must add its token count."""
    counter = start_usage_tracking()
    bad = _make_response("not json", total_token_count=10)
    good = _make_response('{"x": 1}', total_token_count=20)
    mock_generate = AsyncMock(side_effect=[bad, good])
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        await generate_json("sys", "user")
    assert counter.tokens == 30  # 10 + 20


@pytest.mark.asyncio
async def test_generate_json_missing_usage_metadata_counts_as_zero():
    """When usage_metadata or total_token_count is None, 0 is used."""
    counter = start_usage_tracking()
    resp = MagicMock()
    resp.text = '{"a": 1}'
    resp.usage_metadata = None          # no metadata object at all
    mock_generate = AsyncMock(return_value=resp)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        await generate_json("sys", "user")
    assert counter.tokens == 0


@pytest.mark.asyncio
async def test_generate_text_adds_token_count():
    counter = start_usage_tracking()
    mock_response = _make_response("Hello", total_token_count=15)
    mock_generate = AsyncMock(return_value=mock_response)
    with patch.object(get_llm_client().aio.models, "generate_content", mock_generate):
        await generate_text("sys", "user")
    assert counter.tokens == 15
