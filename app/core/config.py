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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

SYSTEM_PROMPT = (
    "You are an enterprise AI assistant that answers HR, IT and company policy "
    "questions professionally."
)

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
