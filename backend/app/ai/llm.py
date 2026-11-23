"""Calls the language model. The only place that talks to it.

Gemini is reached through OpenRouter, which takes prepaid credit by card. Google Cloud
billing in Saudi Arabia goes through a reseller contract, which a student project cannot get.
"""

import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1"


class LLMNotConfiguredError(RuntimeError):
    """Raised when TAMAM_OPENROUTER_API_KEY is missing or rejected."""


class LLMUnavailableError(RuntimeError):
    """Raised when the model call fails after the client's own retries (timeout, 5xx)."""


class LLMQuotaExceededError(LLMUnavailableError):
    """Raised when the provider refuses for rate or credit limits; retrying soon will not help."""


@lru_cache
def _client(model: str):
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    if not settings.openrouter_api_key:
        raise LLMNotConfiguredError("Set TAMAM_OPENROUTER_API_KEY in backend/.env")
    return ChatOpenAI(
        model=model,
        api_key=settings.openrouter_api_key,
        base_url=OPENROUTER_URL,
        temperature=0,  # Policy answers should be repeatable, not creative.
        # Answering from given sources needs no extended reasoning. These models refuse to
        # turn it off; "minimal" gave the same answers in about 3 s with no reasoning tokens.
        extra_body={"reasoning": {"effort": "minimal"}},
        # Without a cap OpenRouter reserves credit for the model's 65k-token maximum.
        # The longest output, a procedure or a quiz as JSON, fits well within this.
        max_tokens=8192,
        # Healthy replies take 2-10 s; a model past 20 s has usually stalled, and waiting longer
        # only delays the fallback. Measured: one stalled call held a chat answer for minutes.
        timeout=20,
        # A model with a fallback after it gets one try, so a busy model hands over quickly;
        # the last model gets one retry.
        max_retries=1 if model == _models()[-1] else 0,
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
        ModelAuthenticationError,
        ModelConnectionError,
        ModelRateLimitError,
        ModelTimeoutError,
    )

    try:
        response = _client(model).invoke([("system", system), ("human", user)])
    except ModelAuthenticationError as error:
        raise LLMNotConfiguredError("TAMAM_OPENROUTER_API_KEY was rejected") from error
    except ModelRateLimitError as error:
        raise LLMQuotaExceededError(str(error)) from error
    except (ModelAPIError, ModelConnectionError, ModelTimeoutError) as error:
        raise LLMUnavailableError(str(error)) from error
    return response.text


def generate(system: str, user: str, fast: bool = False) -> str:
    """Sends the instructions and the user message, and returns the model's reply text.

    A model is sometimes refused for a while (high demand, or a rate limit), so when the
    main model fails the same request goes to the fallback model. `fast` tries the lighter
    model first, for short structured replies the employee waits on, such as a roadmap.
    """
    fast_model = get_settings().llm_fast_model if fast else ""
    models = list(dict.fromkeys([fast_model, *_models()] if fast_model else _models()))
    for model in models[:-1]:
        try:
            return _generate_with(model, system, user)
        except LLMUnavailableError as error:
            logger.warning("Model %s is unavailable, trying the next one: %s", model, error)
    return _generate_with(models[-1], system, user)
