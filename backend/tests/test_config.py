import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG_KEY = "a-production-secret-key-of-at-least-32-chars"


def test_short_jwt_secret_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None, jwt_secret_key="too-short")


def test_production_refuses_the_development_jwt_secret_key() -> None:
    with pytest.raises(ValidationError, match="must be set in production"):
        Settings(_env_file=None, environment="production")


def test_production_accepts_its_own_jwt_secret_key() -> None:
    settings = Settings(_env_file=None, environment="production", jwt_secret_key=STRONG_KEY)

    assert settings.jwt_secret_key.get_secret_value() == STRONG_KEY
