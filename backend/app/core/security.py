"""Password hashing (pwdlib, argon2), access tokens (PyJWT) and refresh token helpers."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"

password_hasher = PasswordHash.recommended()

# Checked when the email is unknown, so a failed login takes the same time
# whether or not the account exists (no account discovery by timing).
_DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(16))


def utc_now() -> datetime:
    """Current time as naive UTC, the format stored in MariaDB DATETIME columns."""
    return datetime.now(UTC).replace(tzinfo=None)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Return (matches, new_hash). new_hash is set when the stored hash should be upgraded."""
    return password_hasher.verify_and_update(password, password_hash)


def verify_dummy_password(password: str) -> None:
    password_hasher.verify(password, _DUMMY_PASSWORD_HASH)


def create_access_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> int:
    """Return the user id.

    Raises jwt.InvalidTokenError when the token is invalid, expired or not an access token.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub"]},
    )
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise jwt.InvalidTokenError("Not an access token")
    try:
        return int(payload["sub"])
    except ValueError as exc:
        raise jwt.InvalidTokenError("Invalid subject") from exc


def generate_refresh_token() -> str:
    """An opaque random token (64 URL-safe characters). Only its hash is stored."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex (64 characters), the value in refresh_tokens.token_hash."""
    return hashlib.sha256(token.encode()).hexdigest()
