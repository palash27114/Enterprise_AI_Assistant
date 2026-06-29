"""Authentication routes."""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_current_user
from app.core.config import FRONTEND_URL
from app.models.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _frontend_error_redirect(error_code: str) -> RedirectResponse:
    """Redirect OAuth failures back to the frontend."""
    params = urlencode({"error": error_code})
    return RedirectResponse(url=f"{FRONTEND_URL.rstrip('/')}/oauth/callback?{params}")


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register with email and password",
)
async def register(payload: RegisterRequest) -> TokenResponse:
    """Create a local account and return session tokens."""
    try:
        tokens = auth_service.register_user(payload.email, payload.password, payload.full_name)
        return TokenResponse(**tokens)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate with email/password and return session tokens."""
    try:
        tokens = auth_service.login_user(payload.email, payload.password)
        return TokenResponse(**tokens)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh(payload: RefreshRequest) -> TokenResponse:
    """Issue a new access token using a valid refresh token."""
    try:
        tokens = auth_service.refresh_session(payload.refresh_token)
        return TokenResponse(**tokens)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout", summary="Logout and revoke refresh token")
async def logout(payload: LogoutRequest) -> dict[str, str]:
    """Revoke the provided refresh token."""
    auth_service.logout_user(payload.refresh_token)
    return {"message": "Logged out successfully."}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def me(current_user=Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user's profile."""
    profile = auth_service.get_user_profile(current_user.id)
    return UserResponse(**profile)


@router.post(
    "/change-password",
    summary="Change account password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """Change password for a local email/password account."""
    try:
        auth_service.change_password(
            current_user.id,
            payload.current_password,
            payload.new_password,
        )
        return {"message": "Password updated successfully."}
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request a password reset link",
)
async def forgot_password(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Send password reset instructions for local email/password accounts."""
    result = auth_service.request_password_reset(payload.email)
    return ForgotPasswordResponse(**result)


@router.post(
    "/reset-password",
    summary="Reset password with a one-time token",
)
async def reset_password(payload: ResetPasswordRequest) -> dict[str, str]:
    """Set a new password using the token from the reset email link."""
    try:
        auth_service.reset_password_with_token(payload.token, payload.new_password)
        return {"message": "Password reset successfully. You can sign in with your new password."}
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/google/login", summary="Start Google OAuth login")
async def google_login():
    """Redirect the user to Google OAuth."""
    try:
        return RedirectResponse(url=auth_service.get_google_login_url())
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/google/callback", summary="Google OAuth callback")
async def google_callback(code: str | None = None, error: str | None = None):
    """Handle Google OAuth callback and redirect to frontend with tokens."""
    if error or not code:
        return _frontend_error_redirect("google_auth_failed")

    try:
        tokens = await auth_service.handle_google_callback(code)
        return RedirectResponse(url=auth_service.build_frontend_callback_url(tokens))
    except Exception as exc:
        logger.error("Google OAuth failed: %s", exc)
        return _frontend_error_redirect("google_auth_failed")


@router.get("/github/login", summary="Start GitHub OAuth login")
async def github_login():
    """Redirect the user to GitHub OAuth."""
    try:
        return RedirectResponse(url=auth_service.get_github_login_url())
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/github/callback", summary="GitHub OAuth callback")
async def github_callback(code: str | None = None, error: str | None = None):
    """Handle GitHub OAuth callback and redirect to frontend with tokens."""
    if error or not code:
        return _frontend_error_redirect("github_auth_failed")

    try:
        tokens = await auth_service.handle_github_callback(code)
        return RedirectResponse(url=auth_service.build_frontend_callback_url(tokens))
    except Exception as exc:
        logger.error("GitHub OAuth failed: %s", exc)
        return _frontend_error_redirect("github_auth_failed")
