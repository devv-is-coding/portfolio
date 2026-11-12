from functools import lru_cache
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from fastapi import Depends
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

# Local development only. Production refuses to start with it (see Settings).
DEV_JWT_SECRET_KEY = "dev-only-insecure-jwt-secret-key-change-me"
MIN_JWT_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """App settings, read from environment variables (and backend/.env in development).

    Defaults match the local services from compose.yaml as seen from the host
    (MariaDB on 3307, Redis on 6380). Inside Docker, compose.yaml overrides the hosts
    and ports. Production must set every DB_* variable and REDIS_URL.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Portfolio API"
    environment: str = "development"
    # Exact origins (scheme://host[:port], no path); https:// only in production.
    cors_origins: list[str] = ["http://localhost:3000"]
    # Largest accepted request body. Files go to ImageKit directly, never through the API;
    # the biggest JSON body is a blog post (up to 200,000 characters of Markdown).
    max_request_body_bytes: int = 1_048_576

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    # "json" (one JSON object per line) for production log collectors.
    log_format: Literal["text", "json"] = "text"

    db_host: str = "localhost"
    db_port: int = 3307
    db_name: str = "portfolio"
    db_user: str = "portfolio"
    db_password: SecretStr = SecretStr("portfolio")
    # Connections per API process: up to pool_size kept open, max_overflow more under load.
    # Keep WEB_CONCURRENCY x (DB_POOL_SIZE + DB_MAX_OVERFLOW) below MariaDB's
    # max_connections (151 by default), with room for the worker and migrations.
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)

    # Cache and Celery broker/result backend.
    redis_url: str = "redis://localhost:6380/0"
    # Celery worker processes; unset uses one per CPU core.
    celery_worker_concurrency: int | None = Field(default=None, ge=1)

    # Sentry is enabled only when a DSN is set.
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.1

    # Signs access tokens (HS256). Production must set its own random value.
    jwt_secret_key: SecretStr = SecretStr(DEV_JWT_SECRET_KEY)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    # Failed logins allowed per client IP within the window, then 429 until it ends.
    login_max_attempts: int = 5
    login_window_seconds: int = 900
    # Contact form messages allowed per client IP within the window.
    contact_max_messages: int = 5
    contact_window_seconds: int = 3600

    # Email about new contact messages (SMTP, e.g. Gmail with an app password).
    # Optional: without SMTP_HOST and CONTACT_NOTIFY_EMAIL nothing is sent.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    # True: STARTTLS on the port (587). False: implicit TLS (465).
    smtp_starttls: bool = True
    smtp_from: str | None = None
    contact_notify_email: str | None = None

    # ImageKit (media files). Optional locally: media endpoints answer 503 without them.
    # Production refuses to start unless all three are set.
    imagekit_public_key: str | None = None
    imagekit_private_key: SecretStr | None = None
    imagekit_url_endpoint: str | None = None

    @model_validator(mode="after")
    def _check_imagekit(self) -> Self:
        if self.imagekit_url_endpoint and not self.imagekit_url_endpoint.startswith("https://"):
            raise ValueError("IMAGEKIT_URL_ENDPOINT must start with https://")
        configured = (
            self.imagekit_public_key,
            self.imagekit_private_key,
            self.imagekit_url_endpoint,
        )
        if self.environment == "production" and not all(configured):
            raise ValueError(
                "IMAGEKIT_PUBLIC_KEY, IMAGEKIT_PRIVATE_KEY and IMAGEKIT_URL_ENDPOINT "
                "must be set in production"
            )
        return self

    @model_validator(mode="after")
    def _check_cors_origins(self) -> Self:
        for origin in self.cors_origins:
            if origin == "*":
                raise ValueError('CORS_ORIGINS can\'t contain "*": the API allows credentials')
            # An origin never has a path: "https://example.com/" would match no request.
            parts = urlsplit(origin)
            has_path = bool(parts.path or parts.query or parts.fragment)
            if parts.scheme not in ("http", "https") or not parts.netloc or has_path:
                raise ValueError(
                    f"CORS_ORIGINS entry {origin!r} must be scheme://host[:port] with no path"
                )
            if self.environment == "production" and parts.scheme != "https":
                raise ValueError("CORS_ORIGINS must be https:// origins in production")
        return self

    @model_validator(mode="after")
    def _check_jwt_secret_key(self) -> Self:
        key = self.jwt_secret_key.get_secret_value()
        if len(key) < MIN_JWT_SECRET_KEY_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_KEY_LENGTH} characters"
            )
        if self.environment == "production" and key == DEV_JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set in production")
        return self

    @property
    def database_url(self) -> URL:
        """Async SQLAlchemy URL for MariaDB (asyncmy driver). Password is escaped safely."""
        return URL.create(
            drivername="mysql+asyncmy",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
