from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import SecretStr

from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from tests.fakes import IsolatedSettings

SETTINGS = IsolatedSettings()


def _encode(payload: dict[str, object], key: str | None = None) -> str:
    secret = key or SETTINGS.jwt_secret_key.get_secret_value()
    return jwt.encode(payload, secret, JWT_ALGORITHM)


def test_password_hash_verifies_only_the_right_password() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2")
    assert verify_password("correct horse battery staple", password_hash)[0]
    assert not verify_password("wrong password", password_hash)[0]


def test_access_token_round_trip() -> None:
    assert decode_access_token(create_access_token(42, SETTINGS), SETTINGS) == 42


def test_expired_access_token_is_rejected() -> None:
    past = datetime.now(UTC) - timedelta(hours=1)
    token = _encode({"sub": "1", "type": "access", "iat": past, "exp": past})

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, SETTINGS)


def test_token_signed_with_another_key_is_rejected() -> None:
    token = create_access_token(1, SETTINGS)
    other = IsolatedSettings(jwt_secret_key=SecretStr("another-secret-key-that-is-long-enough!"))

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token, other)


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "1", "type": "refresh"},  # not an access token
        {"sub": "1"},  # no type
        {"sub": "abc", "type": "access"},  # subject isn't a user id
        {"type": "access"},  # no subject
    ],
)
def test_malformed_access_token_is_rejected(claims: dict[str, object]) -> None:
    now = datetime.now(UTC)
    token = _encode({**claims, "iat": now, "exp": now + timedelta(minutes=5)})

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, SETTINGS)


def test_refresh_tokens_are_random_and_hashed_to_64_hex_characters() -> None:
    token = generate_refresh_token()

    assert token != generate_refresh_token()
    assert len(hash_refresh_token(token)) == 64
    assert hash_refresh_token(token) == hash_refresh_token(token)
