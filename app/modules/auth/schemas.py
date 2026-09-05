import re
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_email_format(email: str) -> str:
    cleaned = email.strip()
    # RFC-like permissive email pattern that permits .local and internal TLDs
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
        raise ValueError("Invalid email format")
    return cleaned.lower()


class TokenRequest(BaseModel):
    """User authentication request supporting OAuth2 grant_type or standard email/password."""
    grant_type: str | None = Field(default="password", alias="grantType")
    username: str | None = None
    email: str | None = None
    password: str | None = None
    refresh_token: str | None = Field(default=None, alias="refreshToken")
    client_id: str | None = Field(default=None, alias="clientId")
    client_secret: str | None = Field(default=None, alias="clientSecret")

    model_config = {"populate_by_name": True}

    @property
    def identifier(self) -> str | None:
        return (self.username or self.email or "").strip() or None


class LoginRequest(BaseModel):
    """Legacy/convenience login payload."""
    email: str | None = None
    username: str | None = None
    password: str

    @property
    def identifier(self) -> str:
        ident = (self.username or self.email or "").strip()
        if not ident:
            raise ValueError("Username or email is required")
        return ident


class TokenResponse(BaseModel):
    """Token response conforming to RFC 6749 and standard 1.2."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str = "read write"


class RefreshTokenRequest(BaseModel):
    """Request payload for refreshing an access token."""
    refresh_token: str | None = Field(default=None, alias="refreshToken")
    token: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def token_value(self) -> str:
        val = self.refresh_token or self.token
        if not val or not val.strip():
            raise ValueError("Refresh token is required")
        return val.strip()


class RevokeTokenRequest(BaseModel):
    """Request payload for revoking a token / logging out."""
    refresh_token: str | None = Field(default=None, alias="refreshToken")
    token: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def token_value(self) -> str | None:
        val = self.refresh_token or self.token
        return val.strip() if val else None


class RegisterRequest(BaseModel):
    """User registration payload."""
    email: str
    password: str
    full_name: str
    workspace_id: int | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_format(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class ForgotPasswordRequest(BaseModel):
    """Request payload for initiating password reset."""
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_format(v)


class ResetPasswordRequest(BaseModel):
    """Request payload for setting a new password via reset token."""
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class MessageResponse(BaseModel):
    """Simple status/confirmation response."""
    message: str
