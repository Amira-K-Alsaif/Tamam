"""Calls the language model. The only place that talks to Gemini."""

import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(RuntimeError):
    """Raised when TAMAM_GOOGLE_API_KEY is missing."""


class LLMUnavailableError(RuntimeError):
    """Raised when the model call fails after the client's own retries (timeout, 5xx)."""


class LLMQuotaExceededError(LLMUnavailableError):
    """Raised when the provider refuses for rate or quota limits; retrying soon will not help."""


@lru_cache
def _client(model: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    settings = get_settings()
    if not settings.google_api_key:
        raise LLMNotConfiguredError("Set TAMAM_GOOGLE_API_KEY in backend/.env")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_api_key,
        temperature=0,  # Policy answers should be repeatable, not creative.
        # Answering from given sources needs no extended reasoning. Turning it off cut the
        # average answer time from about 24 s to 8 s with the same answers.
        thinking_budget=0,
        timeout=30,
        # A model with a fallback after it gets one try, so a busy model hands over quickly
        # and the worst-case wait stays what it was without a fallback.
        max_retries=2 if model == _models()[-1] else 0,
    )


def _models() -> list[str]:
    """The main model, then the fallback model when one is set."""
    settings = get_settings()
    models = [settings.llm_model]
    if settings.llm_fallback_model and settings.llm_fallback_model != settings.llm_model:
        models.append(settings.llm_fallback_model)
    return models


def _generate_with(model: str, system: str, user: str) -> str:
    from langchain_core.exceptions import (
        ModelAPIError,
        ModelConnectionError,
        ModelRateLimitError,
        ModelTimeoutError,
    )

    try:
        response = _client(model).invoke([("system", system), ("human", user)])
    except ModelRateLimitError as error:
        raise LLMQuotaExceededError(str(error)) from error
    except (ModelAPIError, ModelConnectionError, ModelTimeoutError) as error:
        raise LLMUnavailableError(str(error)) from error
    return response.text


def generate(system: str, user: str) -> str:
    """Sends the instructions and the user message, and returns the model's reply text.

    Gemini sometimes refuses a model for a while ("high demand", or its daily quota), so
    when the main model fails the same request goes to the fallback model.
    """
    models = _models()
    for model in models[:-1]:
        try:
            return _generate_with(model, system, user)
        except LLMUnavailableError as error:
            logger.warning("Model %s is unavailable, trying the next one: %s", model, error)
    return _generate_with(models[-1], system, user)
