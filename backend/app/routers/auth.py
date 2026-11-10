from fastapi import APIRouter, Response, status

from app.core.config import SettingsDep
from app.core.database import SessionDep
from app.core.errors import RateLimitedError, error_responses
from app.core.redis import RedisDep
from app.dependencies import ClientIpDep, CurrentUserDep
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth as auth_service
from app.services.login_rate_limit import LoginRateLimiter

router = APIRouter(prefix="/auth", tags=["auth"], responses=error_responses(422))


def _token_response(tokens: auth_service.TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/login", responses=error_responses(401, 429))
async def login(
    body: LoginRequest,
    client_ip: ClientIpDep,
    session: SessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenResponse:
    """Exchange email and password for an access token and a refresh token.

    After too many failed logins from one IP, answers 429 with `Retry-After`.
    """
    limiter = LoginRateLimiter(redis, settings)
    limiter_key = client_ip or "unknown"
    retry_after = await limiter.retry_after(limiter_key)
    if retry_after is not None:
        raise RateLimitedError("Too many failed logins, try again later", retry_after=retry_after)
    try:
        tokens = await auth_service.login(
            session, body.email, body.password, settings, ip_address=client_ip
        )
    except auth_service.InvalidCredentialsError:
        await limiter.record_failure(limiter_key)
        raise
    await limiter.reset(limiter_key)
    return _token_response(tokens)


@router.post("/refresh", responses=error_responses(401))
async def refresh(
    body: RefreshRequest, client_ip: ClientIpDep, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    """Rotate a refresh token: the old one stops working, a new pair is returned.

    Reusing an old refresh token revokes every session of that admin.
    """
    tokens = await auth_service.refresh(session, body.refresh_token, settings, ip_address=client_ip)
    return _token_response(tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, client_ip: ClientIpDep, session: SessionDep) -> Response:
    """Revoke the refresh token. Always 204, also for unknown or already revoked tokens."""
    await auth_service.logout(session, body.refresh_token, ip_address=client_ip)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", responses=error_responses(401))
async def me(user: CurrentUserDep) -> UserRead:
    """The admin the access token belongs to."""
    return UserRead.model_validate(user)
