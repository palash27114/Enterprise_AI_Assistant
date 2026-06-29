"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_WORKERS = int(os.getenv("APP_WORKERS", "2"))
APP_RELOAD = os.getenv("APP_RELOAD", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

POSTGRES_USER = os.getenv("POSTGRES_USER", "assistant")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "assistant")
POSTGRES_DB = os.getenv("POSTGRES_DB", "enterprise_ai")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-a-long-random-secret")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    f"{BACKEND_URL.rstrip('/')}/auth/google/callback",
)

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv(
    "GITHUB_REDIRECT_URI",
    f"{BACKEND_URL.rstrip('/')}/auth/github/callback",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

ASSISTANT_SYSTEM_PROMPT = (
    "You are an enterprise AI assistant for HR, IT, and company operations.\n\n"
    "Default behavior: answer questions conversationally using your general knowledge "
    "about workplace topics, policies, and best practices.\n\n"
    "Only call a tool when the user needs LIVE data from company systems or wants a "
    "system action performed. Examples:\n"
    "- 'What is my name?' → get_profile\n"
    "- 'Look up Jane Doe in the employee directory' → lookup_employee\n"
    "- 'Generate an HR report' → generate_report\n"
    "- 'Create a ticket for my broken laptop' → create_support_ticket\n"
    "- 'Query the employees table' → query_enterprise_data\n"
    "- 'Start onboarding workflow' → trigger_workflow\n\n"
    "Do NOT call tools for general informational questions you can answer directly, "
    "such as explaining what a leave policy typically includes, how VPN works, or "
    "general career advice."
)

SYSTEM_PROMPT = ASSISTANT_SYSTEM_PROMPT

MAX_QUESTION_LENGTH = 1000

TICKET_KEYWORDS = frozenset(
    {
        "ticket",
        "issue",
        "problem",
        "incident",
        "laptop",
        "outlook",
        "vpn",
        "access",
        "login",
    }
)
