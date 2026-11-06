from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


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
