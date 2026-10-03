import functools
from google import genai
from src.core.config import settings


@functools.lru_cache(maxsize=1)
def get_llm_client() -> genai.Client:
    api_key = getattr(settings, "LLM_API_KEY", getattr(settings, "GEMINI_API_KEY", None))
    return genai.Client(api_key=api_key)
