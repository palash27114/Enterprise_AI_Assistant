"""Security helpers for password hashing and JWT tokens."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_SECRET_KEY,
)


class TokenError(Exception):
    """Raised when a token is invalid or expired."""


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Create a signed JWT access token."""
    expires_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expires_at,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires_minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired access token.") from exc

    if payload.get("type") != "access":
        raise TokenError("Invalid token type.")

    return payload


def generate_refresh_token() -> str:
    """Generate a secure opaque refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_password_reset_token() -> str:
    """Generate a secure opaque password reset token."""
    return secrets.token_urlsafe(48)


def hash_password_reset_token(token: str) -> str:
    """Hash a password reset token for database storage."""
    return hashlib.sha256(token.encode()).hexdigest()
