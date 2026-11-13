"""Calls the language model. The only place that talks to Gemini."""

from functools import lru_cache

from langchain_core.exceptions import ModelAPIError, ModelRateLimitError

from app.config import get_settings


class LLMNotConfiguredError(RuntimeError):
    """Raised when TAMAM_GOOGLE_API_KEY is missing."""


class LLMUnavailableError(RuntimeError):
    """Raised when the model cannot answer right now: quota used up or provider down."""


@lru_cache
def _client():
    from langchain_google_genai import ChatGoogleGenerativeAI

    settings = get_settings()
    if not settings.google_api_key:
        raise LLMNotConfiguredError("Set TAMAM_GOOGLE_API_KEY in backend/.env")
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,  # Policy answers should be repeatable, not creative.
        # Answering from given sources needs no extended reasoning. Turning it off cut the
        # average answer time from about 24 s to 8 s with the same answers.
        thinking_budget=0,
        timeout=30,
        max_retries=2,
    )


def generate(system: str, user: str) -> str:
    """Sends the instructions and the user message, and returns the model's reply text."""
    try:
        response = _client().invoke([("system", system), ("human", user)])
    except (ModelRateLimitError, ModelAPIError) as error:
        # The free tier allows a small number of requests per day; callers show a
        # "try again later" message instead of a server error.
        raise LLMUnavailableError(str(error)) from error
    return response.text
