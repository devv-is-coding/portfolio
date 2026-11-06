"""Shared dependencies: the authenticated admin."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import SettingsDep
from app.core.database import SessionDep
from app.core.security import decode_access_token
from app.models import User

# auto_error=False: return our own 401 (with WWW-Authenticate) instead of FastAPI's 403.
bearer_scheme = HTTPBearer(auto_error=False, description="Access token from POST /auth/login")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    """The active admin the access token belongs to; 401 otherwise."""
    if credentials is None:
        raise _unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except jwt.InvalidTokenError as exc:
        raise _unauthorized() from exc
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
