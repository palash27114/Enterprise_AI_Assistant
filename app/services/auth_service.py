"""Authentication and OAuth business logic."""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select

from app.core.config import (
    EXPOSE_PASSWORD_RESET_URL,
    FRONTEND_URL,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_REDIRECT_URI,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    PASSWORD_RESET_EXPIRE_MINUTES,
)
from app.core.security import (
    create_access_token,
    generate_password_reset_token,
    generate_refresh_token,
    hash_password,
    hash_password_reset_token,
    hash_refresh_token,
    verify_password,
)
from app.db.models import PasswordResetToken, RefreshToken, User
from app.db.session import get_session

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised when authentication fails."""


def _issue_tokens(session, user: User) -> dict[str, Any]:
    """Create access and refresh tokens within the current database session."""
    access_token, expires_in = create_access_token(user.id, user.email)
    raw_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    session.add(
        RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=expires_at,
        )
    )

    return {
        "access_token": access_token,
        "refresh_token": raw_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": _user_to_dict(user),
    }


def _token_response_for_user_id(user_id: str) -> dict[str, Any]:
    """Build tokens for a persisted user ID."""
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise AuthError("User account not found.")
        return _issue_tokens(session, user)


def _user_to_dict(user: User) -> dict[str, Any]:
    """Serialize a user for API responses."""
    from app.services import employee_service

    employee = employee_service.get_employee_for_user(user)
    job_title = employee["job_title"] if employee else None
    access_role = employee["access_role"] if employee else None

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "provider": user.provider,
        "employee_id": user.employee_id or (employee["employee_id"] if employee else None),
        "job_title": job_title,
        "access_role": access_role,
        "access_role_label": employee_service.get_access_role_label(access_role or ""),
    }


def _store_refresh_token(user_id: str) -> str:
    """Persist a new refresh token and return the raw token."""
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise AuthError("User account not found.")
        tokens = _issue_tokens(session, user)
        return tokens["refresh_token"]


def register_user(email: str, password: str, full_name: str) -> dict[str, Any]:
    """Register a local email/password user."""
    normalized_email = email.strip().lower()

    with get_session() as session:
        existing = session.scalar(select(User).where(User.email == normalized_email))
        if existing:
            raise AuthError("An account with this email already exists.")

        user = User(
            id=str(uuid.uuid4()),
            email=normalized_email,
            full_name=full_name.strip(),
            hashed_password=hash_password(password),
            provider="local",
            provider_id=normalized_email,
        )
        session.add(user)
        session.flush()
        logger.info("Registered user: %s", user.email)
        return _issue_tokens(session, user)


def login_user(email: str, password: str) -> dict[str, Any]:
    """Authenticate a local user."""
    normalized_email = email.strip().lower()

    with get_session() as session:
        user = session.scalar(select(User).where(User.email == normalized_email))
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password.")
        if not user.is_active:
            raise AuthError("This account has been disabled.")

        logger.info("User logged in: %s", user.email)
        return _issue_tokens(session, user)


def refresh_session(refresh_token: str) -> dict[str, Any]:
    """Rotate refresh token and issue a new access token."""
    token_hash = hash_refresh_token(refresh_token)

    with get_session() as session:
        stored = session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
            )
        )
        if not stored or stored.expires_at <= datetime.now(timezone.utc):
            raise AuthError("Invalid or expired refresh token.")

        user = session.get(User, stored.user_id)
        if not user or not user.is_active:
            raise AuthError("User account is unavailable.")

        stored.revoked = True
        session.flush()
        logger.info("Refresh token rotated for user: %s", user.email)
        return _issue_tokens(session, user)


def logout_user(refresh_token: str) -> None:
    """Revoke a refresh token."""
    token_hash = hash_refresh_token(refresh_token)

    with get_session() as session:
        stored = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if stored:
            stored.revoked = True


def change_password(user_id: str, current_password: str, new_password: str) -> None:
    """Change password for a local email/password account."""
    if len(new_password) < 8:
        raise AuthError("New password must be at least 8 characters.")

    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise AuthError("User account not found.")
        if user.provider != "local":
            raise AuthError("Password change is only available for email/password accounts.")
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise AuthError("Current password is incorrect.")

        user.hashed_password = hash_password(new_password)
        session.flush()
        logger.info("Password changed for user: %s", user.email)


FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for that email, password reset instructions have been sent."
)


def request_password_reset(email: str) -> dict[str, Any]:
    """
    Create a one-time password reset token for a local account.

    Always returns the same message to avoid email enumeration.
    """
    normalized_email = email.strip().lower()
    reset_url: str | None = None

    with get_session() as session:
        user = session.scalar(select(User).where(User.email == normalized_email))
        if not user or user.provider != "local" or not user.hashed_password or not user.is_active:
            return {"message": FORGOT_PASSWORD_MESSAGE, "reset_url": None}

        for token in session.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used.is_(False),
            )
        ):
            token.used = True

        raw_token = generate_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
        session.add(
            PasswordResetToken(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token_hash=hash_password_reset_token(raw_token),
                expires_at=expires_at,
            )
        )
        session.flush()

        if EXPOSE_PASSWORD_RESET_URL:
            params = urlencode({"token": raw_token})
            reset_url = f"{FRONTEND_URL.rstrip('/')}/reset-password?{params}"
            logger.info("Password reset link for %s: %s", user.email, reset_url)
        else:
            logger.info("Password reset requested for %s", user.email)

    return {"message": FORGOT_PASSWORD_MESSAGE, "reset_url": reset_url}


def reset_password_with_token(token: str, new_password: str) -> None:
    """Set a new password using a valid one-time reset token."""
    if len(new_password) < 8:
        raise AuthError("New password must be at least 8 characters.")

    token_hash = hash_password_reset_token(token.strip())

    with get_session() as session:
        stored = session.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used.is_(False),
            )
        )
        if not stored or stored.expires_at <= datetime.now(timezone.utc):
            raise AuthError("Invalid or expired password reset link.")

        user = session.get(User, stored.user_id)
        if not user or not user.is_active or user.provider != "local":
            raise AuthError("Invalid or expired password reset link.")

        user.hashed_password = hash_password(new_password)
        stored.used = True

        for refresh in session.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked.is_(False),
            )
        ):
            refresh.revoked = True

        session.flush()
        logger.info("Password reset completed for user: %s", user.email)


def get_user_by_id(user_id: str) -> User | None:
    """Fetch an active user by ID."""
    with get_session() as session:
        user = session.get(User, user_id)
        if not user or not user.is_active:
            return None
        # Load scalar fields before detaching from the session.
        _ = (
            user.email,
            user.full_name,
            user.provider,
            user.is_active,
            user.employee_id,
            user.hashed_password,
        )
        session.expunge(user)
        return user


def get_user_profile(user_id: str) -> dict[str, Any]:
    """Return enriched profile data for API responses."""
    with get_session() as session:
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise AuthError("User account not found.")
        return _user_to_dict(user)


def get_or_create_oauth_user(
    email: str,
    full_name: str,
    provider: str,
    provider_id: str,
) -> str:
    """Find or create a user from an OAuth provider and return the user ID."""
    normalized_email = email.strip().lower()

    with get_session() as session:
        user = session.scalar(
            select(User).where(User.provider == provider, User.provider_id == provider_id)
        )
        if user:
            return user.id

        existing_email = session.scalar(select(User).where(User.email == normalized_email))
        if existing_email:
            existing_email.provider = provider
            existing_email.provider_id = provider_id
            if not existing_email.full_name:
                existing_email.full_name = full_name
            session.flush()
            return existing_email.id

        user = User(
            id=str(uuid.uuid4()),
            email=normalized_email,
            full_name=full_name.strip() or normalized_email,
            provider=provider,
            provider_id=provider_id,
        )
        session.add(user)
        session.flush()
        logger.info("Created OAuth user: %s via %s", user.email, provider)
        return user.id


def build_frontend_callback_url(tokens: dict[str, Any]) -> str:
    """Redirect authenticated users back to the frontend callback route."""
    params = urlencode(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": str(tokens["expires_in"]),
            "token_type": tokens["token_type"],
        }
    )
    return f"{FRONTEND_URL.rstrip('/')}/oauth/callback?{params}"


def get_google_login_url() -> str:
    """Return the Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID:
        raise AuthError("Google login is not configured.")

    state = secrets.token_urlsafe(16)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def handle_google_callback(code: str) -> dict[str, Any]:
    """Exchange Google OAuth code for application tokens."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise AuthError("Google login is not configured.")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        user_response.raise_for_status()
        profile = user_response.json()

    email = profile.get("email")
    if not email:
        raise AuthError("Google account did not return an email address.")

    user_id = get_or_create_oauth_user(
        email=email,
        full_name=profile.get("name", email),
        provider="google",
        provider_id=str(profile.get("sub")),
    )
    return _token_response_for_user_id(user_id)


def get_github_login_url() -> str:
    """Return the GitHub OAuth authorization URL."""
    if not GITHUB_CLIENT_ID:
        raise AuthError("GitHub login is not configured.")

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": secrets.token_urlsafe(16),
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


async def handle_github_callback(code: str) -> dict[str, Any]:
    """Exchange GitHub OAuth code for application tokens."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise AuthError("GitHub login is not configured.")

    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers=headers,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise AuthError("GitHub authentication failed.")

        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", **headers},
        )
        user_response.raise_for_status()
        profile = user_response.json()

        email = profile.get("email")
        if not email:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", **headers},
            )
            emails_response.raise_for_status()
            emails = emails_response.json()
            primary = next((item for item in emails if item.get("primary")), None)
            email = primary.get("email") if primary else (emails[0]["email"] if emails else None)

    if not email:
        raise AuthError("GitHub account did not return an email address.")

    user_id = get_or_create_oauth_user(
        email=email,
        full_name=profile.get("name") or profile.get("login") or email,
        provider="github",
        provider_id=str(profile.get("id")),
    )
    return _token_response_for_user_id(user_id)
