"""LLM agent listing, health checks, and provider resolution."""

import logging
import time

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)

SUPPORTED_AGENTS = ("openai", "gemini")
HEALTH_CACHE_TTL_SECONDS = 120

AGENT_LABELS = {
    "openai": "OpenAI",
    "gemini": "Google Gemini",
}

_health_cache: dict[str, tuple[bool, float]] = {}


def get_available_agents(*, check_health: bool = True) -> list[dict[str, object]]:
    """Return configured AI agents and whether each is available and healthy."""
    agents = [
        {
            "id": "openai",
            "name": AGENT_LABELS["openai"],
            "model": OPENAI_MODEL,
            "available": bool(OPENAI_API_KEY),
            "is_default": LLM_PROVIDER == "openai",
            "healthy": False,
        },
        {
            "id": "gemini",
            "name": AGENT_LABELS["gemini"],
            "model": GEMINI_MODEL,
            "available": bool(GEMINI_API_KEY),
            "is_default": LLM_PROVIDER == "gemini",
            "healthy": False,
        },
    ]

    if not check_health:
        for agent in agents:
            agent["healthy"] = agent["available"]
        return agents

    for agent in agents:
        if agent["available"]:
            agent["healthy"] = probe_agent_health(str(agent["id"]))
        else:
            agent["healthy"] = False

    return agents


def probe_agent_health(agent_id: str, *, force: bool = False) -> bool:
    """
    Check whether an agent is likely usable.

    Uses API key presence by default to avoid burning LLM quota on every page load.
    """
    if agent_id == "openai":
        configured = bool(OPENAI_API_KEY)
    elif agent_id == "gemini":
        configured = bool(GEMINI_API_KEY)
    else:
        return False

    if not configured:
        _health_cache[agent_id] = (False, time.time())
        return False

    now = time.time()
    cached = _health_cache.get(agent_id)
    if not force and cached and now - cached[1] < HEALTH_CACHE_TTL_SECONDS:
        return cached[0]

    # Assume configured agents are healthy unless a recent request proved otherwise.
    healthy = True
    _health_cache[agent_id] = (healthy, now)
    return healthy


def mark_agent_unhealthy(agent_id: str) -> None:
    """Mark an agent unhealthy after a failed request (e.g. quota exceeded)."""
    _health_cache[agent_id] = (False, time.time())


def resolve_provider(agent: str | None) -> str:
    """Validate and resolve the requested agent provider."""
    from app.services.llm_service import LLMServiceError

    selected = (agent or LLM_PROVIDER).lower()

    if selected not in SUPPORTED_AGENTS:
        raise LLMServiceError("Invalid agent. Choose OpenAI or Google Gemini.")

    if selected == "openai" and not OPENAI_API_KEY:
        raise LLMServiceError("OpenAI is not configured. Add OPENAI_API_KEY to .env.")

    if selected == "gemini" and not GEMINI_API_KEY:
        raise LLMServiceError("Gemini is not configured. Add GEMINI_API_KEY to .env.")

    return selected


def pick_preferred_agent(agents: list[dict[str, object]]) -> str:
    """Choose the best default agent based on health and configuration."""
    healthy = [agent for agent in agents if agent.get("available") and agent.get("healthy")]
    if healthy:
        default = next((agent for agent in healthy if agent.get("is_default")), None)
        return str(default["id"] if default else healthy[0]["id"])

    available = [agent for agent in agents if agent.get("available")]
    if available:
        preferred = next((agent for agent in available if agent.get("is_default")), None)
        return str(preferred["id"] if preferred else available[0]["id"])

    return LLM_PROVIDER if LLM_PROVIDER in SUPPORTED_AGENTS else "openai"
