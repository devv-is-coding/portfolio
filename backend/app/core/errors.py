"""Application errors and the handlers that give every error the same JSON shape:

    {"error": {"code": "not_found", "message": "Project not found", "details": null}}

Services raise the AppError subclasses below; routers don't translate them. Errors
raised by FastAPI itself (validation, unknown routes) and database integrity errors
are converted to the same shape, and internal details never reach the client.
"""

import logging
from collections.abc import Iterable
from http import HTTPStatus
from typing import Any, ClassVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

# MariaDB error code for a duplicate value in a unique index.
_ER_DUP_ENTRY = 1062

# Codes for errors raised by FastAPI/Starlette themselves (unknown route, wrong method).
_HTTP_ERROR_CODES = {
    401: "unauthorized",
    404: "not_found",
    405: "method_not_allowed",
}


class AppError(Exception):
    """Base class: subclasses set the status code, code and default message."""

    status_code: ClassVar[int] = 500
    code: ClassVar[str] = "internal_error"
    default_message: ClassVar[str] = "Internal server error"
    default_headers: ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        message: str | None = None,
        *,
        details: list[ErrorDetail] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details
        self.headers = {**self.default_headers, **(headers or {})}
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Not found"


class ValidationFailedError(AppError):
    """Invalid input that schema validation can't catch (e.g. an unknown sort field).
    Same code and status as FastAPI's own validation errors."""

    status_code = 422
    code = "validation_error"
    default_message = "Invalid request"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "The request conflicts with existing data"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    default_message = "Not authenticated"
    default_headers: ClassVar[dict[str, str]] = {"WWW-Authenticate": "Bearer"}


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"
    default_message = "Too many requests, try again later"

    def __init__(self, message: str | None = None, *, retry_after: int) -> None:
        super().__init__(message, headers={"Retry-After": str(retry_after)})


class UpstreamError(AppError):
    """An external service (e.g. ImageKit) failed or answered unexpectedly."""

    status_code = 502
    code = "bad_gateway"
    default_message = "An external service failed, try again later"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "service_unavailable"
    default_message = "Service unavailable"


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(body.model_dump(mode="json"), status_code=status_code, headers=headers)


def internal_error_response() -> JSONResponse:
    """The 500 response: never a stack trace or exception text."""
    return error_response(500, AppError.code, AppError.default_message)


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses=` entries documenting the shared error shape."""
    return {
        code: {"model": ErrorResponse, "description": HTTPStatus(code).phrase}
        for code in status_codes
    }


async def _handle_app_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)  # registered for AppError only
    return error_response(
        exc.status_code, exc.code, exc.message, details=exc.details, headers=exc.headers
    )


async def _handle_http_exception(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # registered for HTTPException only
    message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
    code = _HTTP_ERROR_CODES.get(exc.status_code, "http_error")
    headers = dict(exc.headers) if exc.headers else None
    return error_response(exc.status_code, code, message, headers=headers)


def validation_details(errors: Iterable[Any]) -> list[ErrorDetail]:
    """Pydantic errors as ErrorDetail. The rejected input is never echoed back,
    so a mistyped password never appears in a response."""
    return [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
            type=error["type"],
        )
        for error in errors
    ]


async def _handle_validation_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # registered for it only
    return error_response(
        ValidationFailedError.status_code,
        ValidationFailedError.code,
        ValidationFailedError.default_message,
        details=validation_details(exc.errors()),
    )


async def _handle_integrity_error(request: Request, exc: Exception) -> JSONResponse:
    """A constraint the service didn't check first. 409, without leaking SQL."""
    assert isinstance(exc, IntegrityError)  # registered for it only
    logger.warning("Integrity error on %s %s: %s", request.method, request.url.path, exc.orig)
    error_code = exc.orig.args[0] if exc.orig is not None and exc.orig.args else None
    if error_code == _ER_DUP_ENTRY:
        return error_response(409, "conflict", "A record with these values already exists")
    return error_response(409, ConflictError.code, ConflictError.default_message)


async def _handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    # Logged by the server; the request middleware (app/core/logging.py) logs it
    # with the request id before this fallback is reached.
    return internal_error_response()


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(IntegrityError, _handle_integrity_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
