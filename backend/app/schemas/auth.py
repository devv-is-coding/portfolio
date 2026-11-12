from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"email": "you@example.com", "password": "correct horse battery staple"}]
        },
    )

    email: EmailStr
    # Upper bound so huge bodies can't make argon2 do expensive work.
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    # Seconds until access_token expires.
    expires_in: int
