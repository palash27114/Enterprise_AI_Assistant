"""Intent routing between AI responses and business actions."""

import logging
import re

from app.core.config import TICKET_KEYWORDS

logger = logging.getLogger(__name__)

ActionIntent = str

WORKFLOW_PATTERNS = (
    r"\btrigger\b.*\bworkflow\b",
    r"\bstart\b.*\b(onboarding|offboarding|approval)\b",
    r"\b(run|execute|launch)\b.*\bworkflow\b",
    r"\bautomate\b.*\b(process|workflow|onboarding|offboarding)\b",
    r"\bworkflow\b.*\b(trigger|start|run|execute)\b",
)

REPORT_PATTERNS = (
    r"\bgenerate\b.*\breport\b",
    r"\bcreate\b.*\breport\b",
    r"\breport\b.*\b(for|on|about)\b",
    r"\b(show|get|fetch)\b.*\breport\b",
    r"\b(hr|sales|it|leave)\b.*\breport\b",
)

QUERY_PATTERNS = (
    r"\bquery\b.*\b(database|db|table|file|csv|records)\b",
    r"\b(search|lookup|select)\b.*\b(database|db|table|records|file)\b",
    r"\bfrom\b.*\b(employees|customers|tickets)\b.*\btable\b",
    r"\bread\b.*\b(csv|file|database)\b",
    r"\bsql\b",
)

EMPLOYEE_PATTERNS = (
    r"\b(fetch|get|lookup|find|show|retrieve)\b.*\bemployee\b",
    r"\bemployee\b.*\b(info|information|details|record|profile)\b",
    r"\bwho is\b.*\bemployee\b",
    r"\bemployee\b.*\b(named|called)\b",
)

CUSTOMER_PATTERNS = (
    r"\b(fetch|get|lookup|find|show|retrieve)\b.*\bcustomer\b",
    r"\bcustomer\b.*\b(info|information|details|record|profile|account)\b",
    r"\bclient\b.*\b(info|information|details|record|profile|account)\b",
    r"\b(fetch|get|lookup|find|show|retrieve)\b.*\b(client|account)\b",
)

PROFILE_PATTERNS = (
    r"\b(my|show|get|fetch)\b.*\bprofile\b",
    r"\bprofile\b.*\b(me|my|mine)\b",
    r"\bwho am i\b",
    r"\bmy account\b",
    r"\bmy details\b",
)


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase word tokens."""
    return set(re.findall(r"[a-zA-Z]+", text.lower()))


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    """Return True when text matches any regex pattern."""
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def detect_intent(question: str) -> ActionIntent:
    """
    Route the question to the most specific supported business action.

    Priority: profile > workflow > report > query > employee > customer > ticket > AI.
    """
    lowered = question.lower()

    if _matches_any(lowered, PROFILE_PATTERNS):
        logger.info("Detected intent: get_profile")
        return "get_profile"

    if _matches_any(lowered, WORKFLOW_PATTERNS):
        logger.info("Detected intent: trigger_workflow")
        return "trigger_workflow"

    if _matches_any(lowered, REPORT_PATTERNS):
        logger.info("Detected intent: generate_report")
        return "generate_report"

    if _matches_any(lowered, QUERY_PATTERNS):
        logger.info("Detected intent: query_data")
        return "query_data"

    if _matches_any(lowered, EMPLOYEE_PATTERNS) or (
        "employee" in lowered and any(word in lowered for word in ("fetch", "get", "lookup", "find", "show"))
    ):
        logger.info("Detected intent: fetch_employee")
        return "fetch_employee"

    if _matches_any(lowered, CUSTOMER_PATTERNS) or (
        any(word in lowered for word in ("customer", "client", "account"))
        and any(word in lowered for word in ("fetch", "get", "lookup", "find", "show"))
    ):
        logger.info("Detected intent: fetch_customer")
        return "fetch_customer"

    tokens = _tokenize(question)
    matched = TICKET_KEYWORDS.intersection(tokens)
    if matched:
        logger.info("Detected intent: create_ticket (keywords=%s)", sorted(matched))
        return "create_ticket"

    logger.info("Detected intent: ai_response")
    return "ai_response"


def is_action_intent(intent: ActionIntent) -> bool:
    """Return True when the intent should be handled without the LLM."""
    return intent != "ai_response"
