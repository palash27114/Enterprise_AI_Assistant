"""Pydantic models for request and response validation."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ActionType = Literal[
    "ai_response",
    "create_ticket",
    "generate_report",
    "fetch_employee",
    "fetch_customer",
    "get_profile",
    "query_data",
    "trigger_workflow",
    "error",
]


class AskRequest(BaseModel):
    """Incoming question payload for POST /ask."""

    question: str = Field(
        ...,
        description="User question or support request (1–1000 characters, non-empty).",
        min_length=1,
        max_length=1000,
        examples=["What is the leave policy?"],
    )
    agent: Optional[Literal["openai", "gemini"]] = Field(
        default=None,
        description="Optional AI agent: `openai` or `gemini`. Uses server default if omitted.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"question": "What is the leave policy?"},
                {
                    "question": (
                        "My Outlook crashes every morning. Please create a support ticket."
                    ),
                },
            ],
        },
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Reject empty, whitespace-only, or overly long questions."""
        if not value or not value.strip():
            raise ValueError("Question cannot be empty or whitespace only.")
        if len(value) > 1000:
            raise ValueError("Question must not exceed 1000 characters.")
        return value.strip()


class AskResponse(BaseModel):
    """Unified response returned by POST /ask."""

    response: str = Field(
        ...,
        description="Assistant reply, ticket confirmation, or error fallback message.",
    )
    action: ActionType = Field(
        ...,
        description=(
            "Outcome of the request: `ai_response`, `create_ticket`, `generate_report`, "
            "`fetch_employee`, `fetch_customer`, `query_data`, `trigger_workflow`, or `error`."
        ),
    )
    ticket_id: Optional[str] = Field(
        default=None,
        description="Support ticket ID (e.g. INC-1001). Present only when action is `create_ticket`.",
        examples=["INC-1001"],
    )
    conversation_id: str = Field(
        ...,
        description=(
            "Unique conversation identifier. Pass back via the `X-Conversation-Id` "
            "header on subsequent requests to continue the same thread."
        ),
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    status: Optional[str] = Field(
        default=None,
        description="Ticket status. Present only when action is `create_ticket`.",
        examples=["Open"],
    )
    agent: Optional[str] = Field(
        default=None,
        description="AI agent used for the response (`openai` or `gemini`).",
        examples=["openai"],
    )
    data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Structured action payload for reports, lookups, queries, and workflows.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "response": (
                        "Our leave policy provides employees with paid annual leave, "
                        "sick leave, and public holidays."
                    ),
                    "action": "ai_response",
                    "ticket_id": None,
                    "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "status": None,
                },
                {
                    "response": "Support ticket created successfully.",
                    "action": "create_ticket",
                    "ticket_id": "INC-1001",
                    "conversation_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "status": "Open",
                },
                {
                    "response": "AI service unavailable. Please try again later.",
                    "action": "error",
                    "ticket_id": None,
                    "conversation_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                    "status": None,
                },
            ],
        },
    )


class HealthResponse(BaseModel):
    """Response returned by GET /health."""

    status: str = Field(
        ...,
        description="Service health indicator.",
        examples=["ok"],
    )
    database: str = Field(
        ...,
        description="Database connectivity status.",
        examples=["ok"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"status": "ok", "database": "ok"}],
        },
    )


class ValidationErrorResponse(BaseModel):
    """Response returned when request validation fails (HTTP 422)."""

    detail: str = Field(
        ...,
        description="Human-readable validation error message.",
        examples=["Question cannot be empty or whitespace only."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Question cannot be empty or whitespace only."},
                {"detail": "Question must not exceed 1000 characters."},
            ],
        },
    )


class RegisterRequest(BaseModel):
    """Payload for email/password registration."""

    email: str = Field(..., examples=["user@company.com"])
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255, examples=["Palash Joshi"])


class LoginRequest(BaseModel):
    """Payload for email/password login."""

    email: str = Field(..., examples=["user@company.com"])
    password: str = Field(..., min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    """Payload for refresh token rotation."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Payload for logout."""

    refresh_token: str


class UserResponse(BaseModel):
    """Authenticated user profile."""

    id: str
    email: str
    full_name: str
    provider: str


class TokenResponse(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class AgentInfo(BaseModel):
    """Configured AI agent."""

    id: str
    name: str
    model: str
    available: bool
    is_default: bool
    healthy: bool = False


class AgentListResponse(BaseModel):
    """Available AI agents."""

    default_agent: str
    agents: list[AgentInfo]


class ConversationMessage(BaseModel):
    """A single stored message."""

    role: str
    content: str


class ConversationSummary(BaseModel):
    """Conversation list item."""

    conversation_id: str
    title: str
    preview: str
    message_count: int
    updated_at: str


class ConversationDetailResponse(BaseModel):
    """Full conversation with messages."""

    conversation_id: str
    title: str
    updated_at: str
    messages: list[ConversationMessage]

