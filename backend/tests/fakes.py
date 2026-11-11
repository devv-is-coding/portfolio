"""In-memory stand-ins for external services, and small test helpers."""

import logging
from typing import cast
from urllib.parse import unquote

import httpx
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import Settings


class FakeRedis:
    """The few Redis commands the app uses. TTLs are stored, not counted down."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def incr(self, key: str) -> int:
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return key in self.values

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, -1)

    async def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            removed += self.values.pop(key, None) is not None
            self.ttls.pop(key, None)
        return removed


class BrokenRedis:
    """Every command fails, like a Redis server that is down."""

    def __getattr__(self, _name: str) -> object:
        async def fail(*_args: object, **_kwargs: object) -> None:
            raise RedisConnectionError("Redis is down")

        return fail


def as_redis(fake: FakeRedis | BrokenRedis) -> Redis:
    return cast(Redis, fake)


def field(record: logging.LogRecord, name: str) -> object:
    """A field added to the record at runtime (request_id, or `extra=` fields)."""
    return record.__dict__[name]


class FakeImageKit:
    """ImageKit's file REST API in memory, served through `httpx.MockTransport`."""

    def __init__(self) -> None:
        self.files: dict[str, dict[str, object]] = {}
        self.deleted: list[str] = []
        self.authorization_headers: list[str] = []
        self.requested_paths: list[str] = []

    def add_file(
        self, file_id: str, file_path: str, mime: str, size: int, width: int, height: int
    ) -> None:
        self.files[file_id] = {
            "fileId": file_id,
            "name": file_path.rsplit("/", 1)[-1],
            "filePath": file_path,
            "fileType": "image" if mime.startswith("image/") else "non-image",
            "mime": mime,
            "size": size,
            "width": width,
            "height": height,
        }

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        raw_path = request.url.raw_path.decode()
        self.requested_paths.append(raw_path)
        self.authorization_headers.append(request.headers.get("authorization", ""))
        parts = raw_path.split("/")  # ["", "v1", "files", "<id>", ("details")]
        file_id = unquote(parts[3]) if len(parts) > 3 else ""
        if request.method == "GET" and parts[4:] == ["details"]:
            file = self.files.get(file_id)
            if file is None:
                return httpx.Response(404, json={"message": "The requested file does not exist."})
            return httpx.Response(200, json=file)
        if request.method == "DELETE" and len(parts) == 4:
            self.deleted.append(file_id)
            if self.files.pop(file_id, None) is None:
                return httpx.Response(404, json={"message": "The requested file does not exist."})
            return httpx.Response(204)
        return httpx.Response(400, json={"message": f"unexpected {request.method} {raw_path}"})


class IsolatedSettings(Settings):
    """Settings from the values passed in and the defaults only: never `.env` or
    environment variables, so a developer's local config can't leak into tests."""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings,)
