"""Pydantic models for request and response validation."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskRequest(BaseModel):
    """Incoming question payload for POST /ask."""

    question: str = Field(
        ...,
        description="User question or support request (1–1000 characters, non-empty).",
        min_length=1,
        max_length=1000,
        examples=["What is the leave policy?"],
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
    action: Literal["ai_response", "create_ticket", "error"] = Field(
        ...,
        description=(
            "Outcome of the request: `ai_response` for LLM answers, "
            "`create_ticket` for support tickets, `error` when the LLM is unavailable."
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
