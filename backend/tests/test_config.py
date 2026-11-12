from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from tests.fakes import IsolatedSettings

STRONG_KEY = "a-production-secret-key-of-at-least-32-chars"
IMAGEKIT: dict[str, Any] = {
    "imagekit_public_key": "public_test",
    "imagekit_private_key": "private_test",
    "imagekit_url_endpoint": "https://ik.imagekit.io/portfolio",
}


def _production(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "environment": "production",
        "jwt_secret_key": STRONG_KEY,
        "cors_origins": ["https://example.com"],
    }
    values |= IMAGEKIT | overrides
    return IsolatedSettings(**values)


def test_short_jwt_secret_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        IsolatedSettings(jwt_secret_key=SecretStr("too-short"))


def test_production_refuses_the_development_jwt_secret_key() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY must be set in production"):
        IsolatedSettings(environment="production", cors_origins=["https://example.com"], **IMAGEKIT)


def test_production_accepts_its_own_settings() -> None:
    settings = _production()

    assert settings.jwt_secret_key.get_secret_value() == STRONG_KEY


@pytest.mark.parametrize("missing", list(IMAGEKIT))
def test_production_requires_every_imagekit_setting(missing: str) -> None:
    with pytest.raises(ValidationError, match="must be set in production"):
        _production(**{missing: None})


def test_imagekit_is_optional_in_development() -> None:
    settings = IsolatedSettings()

    assert settings.imagekit_private_key is None


def test_imagekit_url_endpoint_must_be_https() -> None:
    with pytest.raises(ValidationError, match="must start with https://"):
        IsolatedSettings(imagekit_url_endpoint="http://ik.imagekit.io/portfolio")


@pytest.mark.parametrize(
    ("origins", "message"),
    [
        (["*"], "can't contain"),
        (["https://example.com/"], "no path"),
        (["https://example.com/app"], "no path"),
        (["example.com"], "no path"),
        (["ftp://example.com"], "no path"),
    ],
)
def test_cors_origins_must_be_exact_origins(origins: list[str], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        IsolatedSettings(cors_origins=origins)


def test_production_cors_origins_must_be_https() -> None:
    with pytest.raises(ValidationError, match="https:// origins in production"):
        _production(cors_origins=["https://example.com", "http://example.com"])

    assert _production().cors_origins == ["https://example.com"]
    assert IsolatedSettings(cors_origins=["http://localhost:3000"]).cors_origins


def test_pool_and_worker_sizes_have_safe_defaults() -> None:
    settings = IsolatedSettings()

    assert (settings.db_pool_size, settings.db_max_overflow) == (5, 10)
    assert settings.celery_worker_concurrency is None  # one per CPU core


@pytest.mark.parametrize(
    "invalid",
    [{"db_pool_size": 0}, {"db_max_overflow": -1}, {"celery_worker_concurrency": 0}],
)
def test_pool_and_worker_sizes_are_bounded(invalid: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        IsolatedSettings(**invalid)
