"""Shared dependencies: the client IP, the authenticated admin and the audit context."""

from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import SettingsDep
from app.core.database import SessionDep
from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.models import User
from app.repositories.users import UserRepository
from app.services.audit import AuditContext

# auto_error=False: raise our own 401 (shared error shape, WWW-Authenticate header)
# instead of FastAPI's default error.
bearer_scheme = HTTPBearer(auto_error=False, description="Access token from POST /auth/login")


def get_client_ip(request: Request) -> str | None:
    """The caller's IP as the server sees it. Behind a proxy this is the proxy's IP
    until trusted forwarded headers are configured (TODO.md, B12)."""
    return request.client.host if request.client else None


ClientIpDep = Annotated[str | None, Depends(get_client_ip)]


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    """The active admin the access token belongs to; 401 otherwise."""
    if credentials is None:
        raise UnauthorizedError
    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError from exc
    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError
    # Read by the access log (RequestContextMiddleware in app/core/logging.py).
    request.state.user_id = user.id
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_audit_context(user: CurrentUserDep, client_ip: ClientIpDep) -> AuditContext:
    """The acting admin and their IP, for audit entries of admin actions."""
    return AuditContext(user_id=user.id, ip_address=client_ip)


AuditContextDep = Annotated[AuditContext, Depends(get_audit_context)]
