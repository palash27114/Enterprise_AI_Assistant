"""OpenAPI / Swagger metadata and tag definitions."""

from app.models.schemas import ValidationErrorResponse

OPENAPI_TAGS = [
    {
        "name": "Auth",
        "description": "Registration, login, OAuth, and token refresh endpoints.",
    },
    {
        "name": "Enterprise",
        "description": (
            "Enterprise action APIs used by the AI chatbot and external clients. "
            "Includes profile, tickets, reports, employee/customer lookup, queries, and workflows."
        ),
    },
    {
        "name": "Assistant",
        "description": (
            "Primary AI assistant endpoints. Submit questions for HR, IT, and policy "
            "answers, execute simulated enterprise actions, or create support tickets."
        ),
    },
    {
        "name": "Conversations",
        "description": "Per-user chat history — list and load past conversations.",
    },
    {
        "name": "Health",
        "description": "Service health and readiness checks.",
    },
]

OPENAPI_DESCRIPTION = "Enterprise AI Assistant API"

ASK_RESPONSES = {
    200: {
        "description": "Request processed successfully (AI answer, ticket created, or LLM fallback).",
        "content": {
            "application/json": {
                "examples": {
                    "ai_response": {
                        "summary": "AI-generated answer",
                        "value": {
                            "response": (
                                "Our leave policy provides employees with paid annual leave, "
                                "sick leave, and public holidays."
                            ),
                            "action": "ai_response",
                            "ticket_id": None,
                            "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                            "status": None,
                        },
                    },
                    "create_ticket": {
                        "summary": "Support ticket created",
                        "value": {
                            "response": "Support ticket created successfully.",
                            "action": "create_ticket",
                            "ticket_id": "INC-1001",
                            "conversation_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                            "status": "Open",
                        },
                    },
                    "llm_error": {
                        "summary": "LLM service unavailable",
                        "value": {
                            "response": "AI service unavailable. Please try again later.",
                            "action": "error",
                            "ticket_id": None,
                            "conversation_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                            "status": None,
                        },
                    },
                },
            },
        },
    },
    422: {
        "description": "Validation error — empty, whitespace-only, or overly long question.",
        "model": ValidationErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "empty_question": {
                        "summary": "Empty question",
                        "value": {"detail": "Question cannot be empty or whitespace only."},
                    },
                    "too_long": {
                        "summary": "Question exceeds limit",
                        "value": {"detail": "Question must not exceed 1000 characters."},
                    },
                },
            },
        },
    },
}

HEALTH_RESPONSES = {
    200: {
        "description": "Service and database are healthy.",
        "content": {
            "application/json": {
                "example": {"status": "ok", "database": "ok"},
            },
        },
    },
    503: {
        "description": "Service is running but the database is unavailable.",
        "content": {
            "application/json": {
                "example": {"status": "degraded", "database": "unavailable"},
            },
        },
    },
}
