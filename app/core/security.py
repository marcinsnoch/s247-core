from datetime import datetime, timedelta, timezone
import hashlib
import os
from typing import Any
import bcrypt
from jose import jwt

from app.core.config import settings

# Candidate locations for RSA public key
CANDIDATE_PUB_KEY_PATHS = [
    "/etc/rabbitmq/jwt_public_key.pem",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "s247-stack", "config", "rabbitmq", "jwt_keys", "public_key.pem"),
    os.path.join(os.getcwd(), "config", "rabbitmq", "jwt_keys", "public_key.pem"),
]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).digest()
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).digest()
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a JWT access token (HS256) for human users."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_rsa_public_key() -> str | None:
    """Resolve and read the RSA public key PEM for verifying machine tokens (RS256)."""
    for path in CANDIDATE_PUB_KEY_PATHS:
        normalized = os.path.normpath(path)
        if os.path.exists(normalized):
            with open(normalized, "r", encoding="utf-8") as f:
                return f.read()
    return None


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Supports both HS256 (users) and RS256 (machines/RabbitMQ)."""
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg == "RS256":
            pub_key = get_rsa_public_key()
            if not pub_key:
                return None
            return jwt.decode(token, pub_key, algorithms=["RS256"], audience="rabbitmq")
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        return None


def hash_token(raw_token: str) -> str:
    """Compute SHA256 digest of a token string for safe database lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Generate a high-entropy refresh token string, its hash, and UTC expiration datetime."""
    import secrets
    raw_token = secrets.token_urlsafe(64)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, token_hash, expires_at


def create_password_reset_token(user_id: int, email: str, expires_minutes: int = 15) -> str:
    """Generate a signed single-use JWT for password reset flows."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "password_reset",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> dict | None:
    """Verify and decode a password reset JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset" or "sub" not in payload:
            return None
        return payload
    except Exception:
        return None
