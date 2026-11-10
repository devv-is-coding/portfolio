from functools import lru_cache
from typing import Annotated, Literal, Self

from fastapi import Depends
from pydantic import SecretStr, model_validator
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
    cors_origins: list[str] = ["http://localhost:3000"]

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    # "json" (one JSON object per line) for production log collectors.
    log_format: Literal["text", "json"] = "text"

    db_host: str = "localhost"
    db_port: int = 3307
    db_name: str = "portfolio"
    db_user: str = "portfolio"
    db_password: SecretStr = SecretStr("portfolio")

    # Cache and Celery broker/result backend.
    redis_url: str = "redis://localhost:6380/0"

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
