from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.config import SettingsDep
from app.core.database import SessionDep
from app.core.redis import RedisDep
from app.dependencies import CurrentUserDep
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth as auth_service
from app.services.login_rate_limit import LoginRateLimiter

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = "Incorrect email or password"
_INVALID_REFRESH_TOKEN = "Invalid refresh token"


def _token_response(tokens: auth_service.TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/login",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": _INVALID_CREDENTIALS},
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Too many failed logins"},
    },
)
async def login(
    body: LoginRequest,
    request: Request,
    session: SessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenResponse:
    """Exchange email and password for an access token and a refresh token."""
    limiter = LoginRateLimiter(redis, settings)
    client_ip = request.client.host if request.client else "unknown"
    retry_after = await limiter.retry_after(client_ip)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed logins, try again later",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        tokens = await auth_service.login(session, body.email, body.password, settings)
    except auth_service.InvalidCredentialsError as exc:
        await limiter.record_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_CREDENTIALS
        ) from exc
    await limiter.reset(client_ip)
    return _token_response(tokens)


@router.post(
    "/refresh",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": _INVALID_REFRESH_TOKEN}},
)
async def refresh(
    body: RefreshRequest, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    """Rotate a refresh token: the old one stops working, a new pair is returned.

    Reusing an old refresh token revokes every session of that admin.
    """
    try:
        tokens = await auth_service.refresh(session, body.refresh_token, settings)
    except auth_service.InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_REFRESH_TOKEN
        ) from exc
    return _token_response(tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, session: SessionDep) -> Response:
    """Revoke the refresh token. Always 204, also for unknown or already revoked tokens."""
    await auth_service.logout(session, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me")
async def me(user: CurrentUserDep) -> UserRead:
    """The admin the access token belongs to."""
    return UserRead.model_validate(user)
