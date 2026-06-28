"""LLM integration supporting OpenAI and Gemini providers."""

import logging
from typing import Any

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when the configured LLM provider fails."""


def _build_messages(history: list[dict[str, str]], question: str) -> list[dict[str, str]]:
    """Build chat messages including system prompt and conversation history."""
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


def _call_openai(messages: list[dict[str, str]]) -> str:
    """Call OpenAI Chat Completions API."""
    if not OPENAI_API_KEY:
        raise LLMServiceError("OPENAI_API_KEY is not configured.")

    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.3,
    )
    content = response.choices[0].message.content
    if not content:
        raise LLMServiceError("OpenAI returned an empty response.")
    return content.strip()


def _call_gemini(messages: list[dict[str, str]]) -> str:
    """Call Google Gemini generate_content API."""
    if not GEMINI_API_KEY:
        raise LLMServiceError("GEMINI_API_KEY is not configured.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents: list[Any] = []
    system_instruction = SYSTEM_PROMPT

    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "system":
            system_instruction = content
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append(types.Content(role=gemini_role, parts=[types.Part(text=content)]))

    if not contents:
        contents.append(types.Content(role="user", parts=[types.Part(text="Hello")]))

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
        ),
    )

    text = response.text
    if not text:
        raise LLMServiceError("Gemini returned an empty response.")
    return text.strip()


def generate_response(question: str, history: list[dict[str, str]]) -> str:
    """Generate an AI response using the configured LLM provider."""
    messages = _build_messages(history, question)
    provider = LLM_PROVIDER

    logger.info("LLM called: provider=%s", provider)

    try:
        if provider == "gemini":
            return _call_gemini(messages)
        return _call_openai(messages)
    except LLMServiceError:
        raise
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise LLMServiceError(str(exc)) from exc
