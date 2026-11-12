"""Login, refresh token rotation, logout and admin accounts.

Each function commits its own work, so a failure that must still be recorded
(revoking every token after a reused refresh token, a failed login's audit entry)
is committed before raising. Every security event is written to the audit log;
passwords and tokens never are.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Never

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    utc_now,
    verify_dummy_password,
    verify_password,
)
from app.models import RefreshToken, User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.services import audit
from app.services.audit import AuditContext

# How long expired refresh tokens stay in the table before the daily cleanup deletes them.
REFRESH_TOKEN_RETENTION = timedelta(days=7)


class InvalidCredentialsError(UnauthorizedError):
    """Unknown email, wrong password or inactive account (deliberately not told apart)."""

    default_message = "Incorrect email or password"


class InvalidRefreshTokenError(UnauthorizedError):
    """Unknown, expired, revoked or reused refresh token, or the user is inactive."""

    default_message = "Invalid refresh token"


class UserExistsError(ConflictError):
    default_message = "A user with this email already exists"


class UserNotFoundError(NotFoundError):
    default_message = "No user with this email"


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


async def login(
    session: AsyncSession,
    email: str,
    password: str,
    settings: Settings,
    *,
    ip_address: str | None,
) -> TokenPair:
    user = await UserRepository(session).get_by_email(email)
    if user is None:
        verify_dummy_password(password)
        await _login_failed(session, None, email, "unknown_email", ip_address)
    matches, new_hash = verify_password(password, user.password_hash)
    if not matches:
        await _login_failed(session, user.id, email, "wrong_password", ip_address)
    if not user.is_active:
        await _login_failed(session, user.id, email, "inactive", ip_address)
    if new_hash is not None:
        user.password_hash = new_hash
    user.last_login_at = utc_now()
    tokens, _ = await _issue_tokens(session, user.id, settings)
    audit.record(session, AuditContext(user.id, ip_address), "auth.login")
    await session.commit()
    return tokens


async def _login_failed(
    session: AsyncSession, user_id: int | None, email: str, reason: str, ip_address: str | None
) -> Never:
    audit.record(
        session,
        AuditContext(user_id, ip_address),
        "auth.login_failed",
        details={"email": email, "reason": reason},
    )
    await session.commit()
    raise InvalidCredentialsError


async def refresh(
    session: AsyncSession, refresh_token: str, settings: Settings, *, ip_address: str | None
) -> TokenPair:
    """Rotate a refresh token: revoke it and issue a new pair.

    A refresh token that was already rotated or revoked means someone else has a
    copy, so every live token of that user is revoked and they must log in again.
    """
    now = utc_now()
    tokens_repo = RefreshTokenRepository(session)
    token = await tokens_repo.get_by_hash_for_update(hash_refresh_token(refresh_token))
    if token is None:
        raise InvalidRefreshTokenError
    if token.revoked_at is not None:
        await tokens_repo.revoke_all_for_user(token.user_id, now)
        audit.record(
            session,
            AuditContext(token.user_id, ip_address),
            "auth.refresh_reuse_detected",
            entity_type="refresh_token",
            entity_id=token.id,
        )
        await session.commit()
        raise InvalidRefreshTokenError
    user = await UserRepository(session).get(token.user_id)
    if token.expires_at <= now or user is None or not user.is_active:
        raise InvalidRefreshTokenError

    tokens, replacement = await _issue_tokens(session, user.id, settings)
    token.revoked_at = now
    token.replaced_by_id = replacement.id
    await session.commit()
    return tokens


async def logout(session: AsyncSession, refresh_token: str, *, ip_address: str | None) -> None:
    """Revoke one refresh token. Unknown or already revoked tokens are ignored."""
    token = await RefreshTokenRepository(session).get_by_hash_for_update(
        hash_refresh_token(refresh_token)
    )
    if token is not None and token.revoked_at is None:
        token.revoked_at = utc_now()
        audit.record(session, AuditContext(token.user_id, ip_address), "auth.logout")
    await session.commit()


async def cleanup_refresh_tokens(session: AsyncSession) -> int:
    """Delete refresh tokens that expired more than REFRESH_TOKEN_RETENTION ago.

    Revoked tokens are kept until then: presenting a revoked token is how a stolen
    one is detected (see `refresh`), so deleting it earlier would hide the theft.
    An expired token can't be used either way. Returns the number deleted.
    """
    deleted = await RefreshTokenRepository(session).delete_expired_before(
        utc_now() - REFRESH_TOKEN_RETENTION
    )
    await session.commit()
    return deleted


async def create_admin(
    session: AsyncSession, email: str, password: str, *, reset_password: bool = False
) -> User:
    """Create an admin, or with reset_password change an existing admin's password.

    A reset also revokes every refresh token of that admin. Run from the CLI, so the
    audit entry has no acting user or IP.
    """
    email = email.strip().lower()
    users = UserRepository(session)
    user = await users.get_by_email(email)
    if reset_password:
        if user is None:
            raise UserNotFoundError
        user.password_hash = hash_password(password)
        await RefreshTokenRepository(session).revoke_all_for_user(user.id, utc_now())
        action = "auth.password_reset"
    elif user is not None:
        raise UserExistsError
    else:
        user = User(email=email, password_hash=hash_password(password))
        users.add(user)
        await users.flush()
        action = "auth.admin_created"
    audit.record(session, AuditContext(None, None), action, entity_type="user", entity_id=user.id)
    await session.commit()
    return user


async def _issue_tokens(
    session: AsyncSession, user_id: int, settings: Settings
) -> tuple[TokenPair, RefreshToken]:
    refresh_token = generate_refresh_token()
    row = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
    )
    tokens_repo = RefreshTokenRepository(session)
    tokens_repo.add(row)
    await tokens_repo.flush()
    tokens = TokenPair(
        access_token=create_access_token(user_id, settings),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
    return tokens, row
