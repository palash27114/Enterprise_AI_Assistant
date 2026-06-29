"""OpenAPI / Swagger metadata and tag definitions."""

from app.models.schemas import HealthResponse, ValidationErrorResponse

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
        "name": "Health",
        "description": "Service health and readiness checks.",
    },
]

OPENAPI_DESCRIPTION = """
## Enterprise AI Assistant API

REST API for an enterprise assistant that answers HR, IT, and company policy questions
and automatically creates support tickets for incident-related requests.

### How it works

1. **Validate** — Questions must be non-empty and at most 1000 characters.
2. **Remember** — Conversation history is stored and included in LLM prompts.
3. **Route** — Intent detection decides between AI Q&A and enterprise actions.
4. **Respond** — A structured JSON payload is returned with `action`, optional `data`, and `conversation_id`.

### Supported actions (simulated with mock data)

| Action | Example prompt |
|--------|----------------|
| `create_ticket` | "My laptop won't start, create a ticket" |
| `generate_report` | "Generate an HR headcount report" |
| `fetch_employee` | "Fetch employee info for Palash Joshi" |
| `fetch_customer` | "Get customer details for Acme Corporation" |
| `get_profile` | "Show my profile" |
| `query_data` | "Query the employees table" |
| `trigger_workflow` | "Trigger employee onboarding workflow" |
| `ai_response` | General HR/IT/policy questions |

### Conversation continuity

Each response includes a `conversation_id`. To continue a multi-turn conversation,
pass it back in the **`X-Conversation-Id`** request header on the next call to `POST /ask`.

### Ticket keywords

A support ticket is created when the question contains any of:
`ticket`, `issue`, `problem`, `incident`, `laptop`, `outlook`, `vpn`, `access`, `login`.

### LLM providers

Configure via environment variables: **OpenAI** (default) or **Google Gemini**.
See the project README for setup details.

### Enterprise REST APIs (Swagger)

The chatbot routes detected intents to the same handlers as these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Authenticated user profile |
| POST | `/tickets` | Create support ticket |
| POST | `/reports/generate` | Generate mock report |
| GET | `/employees`, `/employees/{id}` | Employee directory |
| GET | `/customers`, `/customers/{id}` | Customer accounts |
| POST | `/queries` | Query mock DB/file |
| GET | `/workflows` | List workflows |
| POST | `/workflows/trigger` | Trigger workflow |
"""

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
    },
    503: {
        "description": "Service is running but the database is unavailable.",
        "model": HealthResponse,
    },
}
