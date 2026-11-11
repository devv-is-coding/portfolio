"""Logging setup and the request middleware.

Every log line carries the request id of the request it belongs to. The middleware
takes a valid incoming `X-Request-ID` (or generates one), returns it on every
response, writes one access log line per request and turns unexpected exceptions
into the shared 500 response. Request bodies, query strings, headers, passwords and
tokens are never logged.
"""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings
from app.core.errors import internal_error_response

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
TEXT_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
# Successful requests to these paths are logged at DEBUG instead of INFO.
_QUIET_PATHS = frozenset({"/health"})
# Structured fields the access log adds with `extra=`; JSON output includes them.
_ACCESS_FIELDS = ("method", "path", "status", "duration_ms", "user_id")

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("app.access")

_default_record_factory = logging.getLogRecordFactory()


def _record_with_request_id(*args: object, **kwargs: object) -> logging.LogRecord:
    """Every record gets `request_id`, whichever logger or handler it goes through."""
    record = _default_record_factory(*args, **kwargs)
    record.request_id = request_id_var.get() or "-"
    return record


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for field in _ACCESS_FIELDS:
            if hasattr(record, field):
                entry[field] = getattr(record, field)
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure the root logger. Safe to call more than once."""
    logging.setLogRecordFactory(_record_with_request_id)
    handler = logging.StreamHandler()
    formatter = JsonFormatter() if settings.log_format == "json" else logging.Formatter(TEXT_FORMAT)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level)
    # app.access (with request id, duration and user) replaces uvicorn's access log.
    logging.getLogger("uvicorn.access").disabled = True
    # HTTPX logs every outgoing request (ImageKit) at INFO; keep only its warnings.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _incoming_request_id(scope: Scope) -> str | None:
    for name, value in scope["headers"]:
        if name == b"x-request-id":
            candidate = value.decode("latin-1")
            return candidate if _VALID_REQUEST_ID.fullmatch(candidate) else None
    return None


class RequestContextMiddleware:
    """Pure ASGI middleware (no BaseHTTPMiddleware): request id, access log, 500s."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_request_id(scope) or uuid.uuid4().hex
        request_id_var.set(request_id)
        started = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message).append(REQUEST_ID_HEADER, request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception("Unhandled error on %s %s", scope["method"], scope["path"])
            if response_started:
                raise
            await internal_error_response()(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            # Docker's healthcheck hits /health every few seconds: keep passing checks
            # out of the INFO log; a failing one (503) still shows up.
            quiet = scope["path"] in _QUIET_PATHS and status < 400
            access_logger.log(
                logging.DEBUG if quiet else logging.INFO,
                "%s %s %s %.1fms",
                scope["method"],
                scope["path"],
                status,
                duration_ms,
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status,
                    "duration_ms": duration_ms,
                    # Set by get_current_user (app/dependencies.py) on authenticated requests.
                    "user_id": scope.get("state", {}).get("user_id"),
                },
            )
