from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RevokeTokenRequest,
    TokenRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse
from app.shared.exceptions import UnauthorizedException

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse, summary="Issue token pair")
async def issue_token(data: TokenRequest, db: AsyncSession = Depends(get_db)):
    """Issue access and refresh token pair using username/email or refresh_token grant."""
    auth_service = AuthService(db)

    # Handle refresh_token grant type via /token
    if (data.grant_type or "").lower() == "refresh_token":
        raw_refresh = data.refresh_token or data.password
        if not raw_refresh:
            raise UnauthorizedException("Refresh token is required for refresh_token grant")
        return await auth_service.refresh_tokens(raw_refresh)

    # Standard credentials grant
    identifier = data.identifier
    if not identifier or not data.password:
        raise UnauthorizedException("Username/email and password are required")

    user = await auth_service.authenticate(identifier, data.password)
    return await auth_service.issue_token_pair(user)


@router.post("/token/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh Access Token using Refresh Token with immediate rotation (RTR)."""
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(data.token_value)


@router.delete("/token", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke token / Logout")
async def delete_token(
    data: RevokeTokenRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token and terminate session (DELETE method)."""
    if data and data.token_value:
        await AuthService(db).revoke_token(data.token_value)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/token/revoke", response_model=MessageResponse, summary="Revoke token")
@router.post("/logout", response_model=MessageResponse, summary="Logout user")
async def logout(
    data: RevokeTokenRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token and terminate session (POST method)."""
    if data and data.token_value:
        await AuthService(db).revoke_token(data.token_value)
    return MessageResponse(message="Successfully logged out")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register user")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new customer user account."""
    auth_service = AuthService(db)
    return await auth_service.register(data)


@router.post("/password/forgot", response_model=MessageResponse, summary="Initiate password reset")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Initiate password reset flow for account email."""
    auth_service = AuthService(db)
    await auth_service.request_password_reset(data.email)
    return MessageResponse(message="Password reset instructions have been generated.")


@router.post("/password/reset", response_model=MessageResponse, summary="Reset password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Set new password using single-use reset token."""
    auth_service = AuthService(db)
    await auth_service.reset_password(data.token, data.new_password)
    return MessageResponse(message="Password has been successfully reset.")


# Backward compatibility aliases
@router.post("/login", response_model=TokenResponse, summary="Legacy login alias", deprecated=True)
async def login_legacy(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with email and password (legacy endpoint mapped to /token)."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate(data.identifier, data.password)
    return await auth_service.issue_token_pair(user)


@router.post("/refresh", response_model=TokenResponse, summary="Legacy refresh alias", deprecated=True)
async def refresh_legacy(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token (legacy endpoint mapped to /token/refresh)."""
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(data.token_value)
