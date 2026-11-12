"""HTTP caching (pure ASGI): ETags and 304s for public reads, no-store for the rest.

Public GET responses (200) get a weak ETag and `Cache-Control: public, no-cache`:
browsers, the Next.js server and CDNs may keep them but must revalidate, so content
is never stale, and an unchanged one costs a 304 without a body. Admin, auth and
health responses get `no-store` (tokens and private data are never cached).
"""

import hashlib

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

PUBLIC_CACHE_CONTROL = "public, no-cache"
NO_STORE = "no-store"
# Never cached: private data and tokens, and health checks that must hit the server.
NO_STORE_PREFIXES = ("/admin", "/auth", "/health")
# Not sent with a 304: it has no body.
_BODY_HEADERS = ("content-length", "content-type")


def etag_for(body: bytes) -> str:
    """Weak, because gzip may change the bytes on the way; the content is the same."""
    return f'W/"{hashlib.blake2b(body, digest_size=16).hexdigest()}"'


def _matches(if_none_match: str, etag: str) -> bool:
    """Weak comparison (RFC 9110): `W/` prefixes are ignored; `*` matches anything."""
    opaque = etag.removeprefix("W/")
    candidates = (tag.strip().removeprefix("W/") for tag in if_none_match.split(","))
    return any(tag in ("*", opaque) for tag in candidates)


class HttpCacheMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope["path"].startswith(NO_STORE_PREFIXES):
            await self.app(scope, receive, _with_no_store(send))
            return
        if scope["method"] != "GET":
            await self.app(scope, receive, send)
            return
        await self._cacheable(scope, receive, send)

    async def _cacheable(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Hold a 200 response until its body is complete, then add the ETag (or
        answer 304). Other statuses pass through untouched."""
        start: Message | None = None
        chunks: list[bytes] = []
        if_none_match = Headers(scope=scope).get("if-none-match")

        async def buffering_send(message: Message) -> None:
            nonlocal start
            if message["type"] == "http.response.start" and message["status"] == 200:
                start = message
                return
            if start is None:
                await send(message)
                return
            chunks.append(message.get("body", b""))
            if message.get("more_body", False):
                return
            body = b"".join(chunks)
            etag = etag_for(body)
            headers = MutableHeaders(scope=start)
            headers["ETag"] = etag
            headers.setdefault("Cache-Control", PUBLIC_CACHE_CONTROL)
            if if_none_match is not None and _matches(if_none_match, etag):
                for name in _BODY_HEADERS:
                    del headers[name]
                await send({**start, "status": 304})
                await send({"type": "http.response.body", "body": b""})
                return
            await send(start)
            await send({"type": "http.response.body", "body": body})

        await self.app(scope, receive, buffering_send)


def _with_no_store(send: Send) -> Send:
    async def send_no_store(message: Message) -> None:
        if message["type"] == "http.response.start":
            MutableHeaders(scope=message).setdefault("Cache-Control", NO_STORE)
        await send(message)

    return send_no_store
