"""HTTP hardening middleware (pure ASGI): security headers and a request body limit."""

from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response

# The API serves JSON, never pages to frame or content to sniff. (No Content-Security-
# Policy: the public Swagger UI at /docs loads its scripts from a CDN.)
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}
# One year, production only: once a browser sees it, it refuses plain HTTP to this host.
HSTS_HEADER = ("Strict-Transport-Security", "max-age=31536000")

PAYLOAD_TOO_LARGE = 413
PAYLOAD_TOO_LARGE_MESSAGE = "Request body too large"


class SecurityHeadersMiddleware:
    """Adds the security headers to every response that doesn't set them itself."""

    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app = app
        self.headers = dict(SECURITY_HEADERS)
        if hsts:
            self.headers[HSTS_HEADER[0]] = HSTS_HEADER[1]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in self.headers.items():
                    headers.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)


class BodySizeLimitMiddleware:
    """413 for request bodies over `max_bytes`.

    A declared Content-Length over the limit is refused before the app runs. Bodies
    without one (chunked) are counted while the app reads them; going over raises a
    413 HTTPException, which FastAPI passes on to the shared error handler.
    """

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = Headers(scope=scope).get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            response = error_response(
                PAYLOAD_TOO_LARGE, "payload_too_large", PAYLOAD_TOO_LARGE_MESSAGE
            )
            await response(scope, receive, send)
            return

        received = 0

        async def receive_with_limit() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(PAYLOAD_TOO_LARGE, PAYLOAD_TOO_LARGE_MESSAGE)
            return message

        await self.app(scope, receive_with_limit, send)
