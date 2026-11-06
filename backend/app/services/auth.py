"""Login, refresh token rotation, logout and admin accounts.

Each function commits its own work, so a failure that must still be recorded
(revoking every token after a reused refresh token) is committed before raising.
"""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
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


class InvalidCredentialsError(Exception):
    """Unknown email, wrong password or inactive account (deliberately not told apart)."""


class InvalidRefreshTokenError(Exception):
    """Unknown, expired, revoked or reused refresh token, or the user is inactive."""


class UserExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


async def login(session: AsyncSession, email: str, password: str, settings: Settings) -> TokenPair:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        verify_dummy_password(password)
        raise InvalidCredentialsError
    matches, new_hash = verify_password(password, user.password_hash)
    if not matches or not user.is_active:
        raise InvalidCredentialsError
    if new_hash is not None:
        user.password_hash = new_hash
    user.last_login_at = utc_now()
    tokens, _ = await _issue_tokens(session, user.id, settings)
    await session.commit()
    return tokens


async def refresh(session: AsyncSession, refresh_token: str, settings: Settings) -> TokenPair:
    """Rotate a refresh token: revoke it and issue a new pair.

    A refresh token that was already rotated or revoked means someone else has a
    copy, so every live token of that user is revoked and they must log in again.
    """
    now = utc_now()
    token = await session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
        .with_for_update()
    )
    if token is None:
        raise InvalidRefreshTokenError
    if token.revoked_at is not None:
        await _revoke_all(session, token.user_id)
        await session.commit()
        raise InvalidRefreshTokenError
    user = await session.get(User, token.user_id)
    if token.expires_at <= now or user is None or not user.is_active:
        raise InvalidRefreshTokenError

    tokens, replacement = await _issue_tokens(session, user.id, settings)
    token.revoked_at = now
    token.replaced_by_id = replacement.id
    await session.commit()
    return tokens


async def logout(session: AsyncSession, refresh_token: str) -> None:
    """Revoke one refresh token. Unknown or already revoked tokens are ignored."""
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token),
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=utc_now())
    )
    await session.commit()


async def create_admin(
    session: AsyncSession, email: str, password: str, *, reset_password: bool = False
) -> User:
    """Create an admin, or with reset_password change an existing admin's password.

    A reset also revokes every refresh token of that admin.
    """
    email = email.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    if reset_password:
        if user is None:
            raise UserNotFoundError(email)
        user.password_hash = hash_password(password)
        await _revoke_all(session, user.id)
    elif user is not None:
        raise UserExistsError(email)
    else:
        user = User(email=email, password_hash=hash_password(password))
        session.add(user)
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
    session.add(row)
    await session.flush()
    tokens = TokenPair(
        access_token=create_access_token(user_id, settings),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
    return tokens, row


async def _revoke_all(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )
