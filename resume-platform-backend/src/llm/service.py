import asyncio
import json
from google.genai.types import GenerateContentConfig

from src.core.config import settings
from src.llm.client import get_llm_client


class LLMError(Exception):
    """Custom exception raised for LLM API and parsing errors."""
    pass


async def generate_text(system_prompt: str, user_prompt: str) -> str:
    client = get_llm_client()
    config = GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.3
    )
    model_name = getattr(settings, "LLM_MODEL", "gemini-2.5-flash")

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config
            ),
            timeout=60.0
        )
        return response.text
    except Exception as e:
        raise LLMError(f"Failed to generate text from LLM: {str(e)}") from e


async def generate_json(system_prompt: str, user_prompt: str) -> dict:
    client = get_llm_client()
    config = GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.3,
        response_mime_type="application/json"
    )
    model_name = getattr(settings, "LLM_MODEL", "gemini-2.5-flash")

    last_error = None
    for attempt in range(2):
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config
                ),
                timeout=60.0
            )
            raw_text = response.text or ""
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            last_error = e
            # Retry once on JSON decode error
            continue
        except Exception as e:
            raise LLMError(f"LLM API error during JSON generation: {str(e)}") from e

    raise LLMError(f"Failed to parse valid JSON from LLM response after retry: {str(last_error)}")
