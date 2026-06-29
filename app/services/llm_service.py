"""LLM integration with tool-calling for intelligent enterprise actions."""

import json
import logging
from typing import Any

from app.core.config import (
    ASSISTANT_SYSTEM_PROMPT,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from app.services.agent_service import resolve_provider
from app.services.assistant_tools import OPENAI_TOOLS, execute_tool, parse_openai_tool_arguments

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when the configured LLM provider fails."""


def _build_messages(history: list[dict[str, str]], question: str) -> list[dict[str, str]]:
    """Build chat messages including system prompt and conversation history."""
    messages: list[dict[str, str]] = [{"role": "system", "content": ASSISTANT_SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


def _normalize_action_result(result: dict[str, Any], provider: str) -> dict[str, Any]:
    """Normalize tool execution result for POST /ask."""
    return {
        "response": result["response"],
        "action": result["action"],
        "ticket_id": result.get("ticket_id"),
        "status": result.get("status"),
        "data": result.get("data"),
        "agent": provider,
    }


def _call_openai_plain(messages: list[dict[str, str]]) -> str:
    """Plain OpenAI completion without tools."""
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


def _call_gemini_plain(messages: list[dict[str, str]]) -> str:
    """Plain Gemini completion without tools."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    contents: list[Any] = []
    system_instruction = ASSISTANT_SYSTEM_PROMPT

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


def _call_openai_with_tools(
    messages: list[dict[str, str]],
    user: Any,
    question: str,
) -> dict[str, Any]:
    """Call OpenAI with enterprise tools; execute tool if the model requests one."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,  # type: ignore[arg-type]
        tools=OPENAI_TOOLS,
        tool_choice="auto",
        temperature=0.3,
    )
    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        arguments = parse_openai_tool_arguments(tool_call.function.arguments)
        result = execute_tool(tool_name, arguments, user, question)
        return _normalize_action_result(result, "openai")

    content = message.content
    if not content:
        raise LLMServiceError("OpenAI returned an empty response.")
    return {
        "response": content.strip(),
        "action": "ai_response",
        "ticket_id": None,
        "status": None,
        "data": None,
        "agent": "openai",
    }


def _gemini_function_declarations() -> list[Any]:
    """Build Gemini function declarations from OpenAI tool schemas."""
    from google.genai import types

    declarations = []
    for tool in OPENAI_TOOLS:
        fn = tool["function"]
        properties: dict[str, Any] = {}
        for key, value in fn.get("parameters", {}).get("properties", {}).items():
            prop: dict[str, Any] = {"type": value["type"].upper(), "description": value.get("description", "")}
            if "enum" in value:
                prop["enum"] = value["enum"]
            properties[key] = prop

        declarations.append(
            types.FunctionDeclaration(
                name=fn["name"],
                description=fn["description"],
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=fn.get("parameters", {}).get("required", []),
                ),
            )
        )
    return declarations


def _call_gemini_with_tools(
    messages: list[dict[str, str]],
    user: Any,
    question: str,
) -> dict[str, Any]:
    """Call Gemini with enterprise tools; execute tool if the model requests one."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents: list[Any] = []
    system_instruction = ASSISTANT_SYSTEM_PROMPT

    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "system":
            system_instruction = content
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append(types.Content(role=gemini_role, parts=[types.Part(text=content)]))

    if not contents:
        contents.append(types.Content(role="user", parts=[types.Part(text=question)]))

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(function_declarations=_gemini_function_declarations())],
            temperature=0.3,
        ),
    )

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                tool_name = part.function_call.name
                arguments = dict(part.function_call.args or {})
                result = execute_tool(tool_name, arguments, user, question)
                return _normalize_action_result(result, "gemini")

    text = response.text
    if not text:
        raise LLMServiceError("Gemini returned an empty response.")
    return {
        "response": text.strip(),
        "action": "ai_response",
        "ticket_id": None,
        "status": None,
        "data": None,
        "agent": "gemini",
    }


def _provider_error_message(provider: str, exc: Exception) -> str:
    """Map provider API failures to user-facing messages."""
    message = str(exc).lower()

    if provider == "openai":
        if "insufficient_quota" in message or "exceeded your current quota" in message:
            return (
                "OpenAI quota exceeded. Add billing at platform.openai.com "
                "or switch to Google Gemini using the agent selector above."
            )
        if "invalid_api_key" in message or "incorrect api key" in message:
            return "Invalid OpenAI API key. Check OPENAI_API_KEY in .env."
        return "OpenAI is unavailable. Please try again later."

    if "exceeded your current quota" in message or "resource_exhausted" in message:
        return (
            "Google Gemini quota exceeded. Check usage at ai.dev/rate-limit, "
            "enable billing in Google AI Studio, or try again later."
        )
    if "invalid" in message and "api key" in message:
        return "Invalid Gemini API key. Get a key from aistudio.google.com/apikey."
    return "Google Gemini is unavailable. Please try again later."


def _is_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "quota exceeded" in message
        or "insufficient_quota" in message
        or "resource_exhausted" in message
    )


def process_assistant_request(
    question: str,
    history: list[dict[str, str]],
    user: Any,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Process a user message: the LLM decides whether to answer directly or call an enterprise tool.
    Falls back to the alternate provider when the primary hits a quota error.
    """
    from app.services.agent_service import mark_agent_unhealthy

    messages = _build_messages(history, question)
    selected_provider = resolve_provider(provider)
    alternate = "gemini" if selected_provider == "openai" else "openai"

    logger.info("Assistant request: provider=%s", selected_provider)

    failures: list[str] = []

    for attempt_provider in (selected_provider, alternate):
        try:
            if attempt_provider == "gemini":
                if not GEMINI_API_KEY:
                    continue
                result = _call_gemini_with_tools(messages, user, question)
            else:
                if not OPENAI_API_KEY:
                    continue
                result = _call_openai_with_tools(messages, user, question)

            if attempt_provider != selected_provider:
                logger.info("Assistant fallback succeeded with provider=%s", attempt_provider)
            result["agent"] = attempt_provider
            return result
        except LLMServiceError as exc:
            if _is_quota_error(exc):
                mark_agent_unhealthy(attempt_provider)
            failures.append(str(exc))
            logger.warning("Provider %s failed: %s", attempt_provider, exc)
        except Exception as exc:
            if _is_quota_error(exc):
                mark_agent_unhealthy(attempt_provider)
            failures.append(_provider_error_message(attempt_provider, exc))
            logger.warning("Provider %s failed: %s", attempt_provider, exc)

    if len(failures) >= 2:
        raise LLMServiceError(
            "Both AI providers are unavailable right now. "
            + failures[0]
            + " "
            + failures[1]
            + " Try again later or add billing to your API account."
        )
    if failures:
        raise LLMServiceError(failures[0])

    raise LLMServiceError("AI service unavailable. Please try again later.")


def generate_response(
    question: str,
    history: list[dict[str, str]],
    provider: str | None = None,
) -> tuple[str, str]:
    """Generate a plain AI response without tool routing (used by health checks)."""
    messages = _build_messages(history, question)
    selected_provider = resolve_provider(provider)

    try:
        if selected_provider == "gemini":
            return _call_gemini_plain(messages), selected_provider
        return _call_openai_plain(messages), selected_provider
    except LLMServiceError:
        raise
    except Exception as exc:
        logger.error("LLM call failed (%s): %s", selected_provider, exc)
        raise LLMServiceError(_provider_error_message(selected_provider, exc)) from exc
