from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.security import utc_now
from app.schemas.fields import BlankToNone, NotNull, RequiredText, WebUrl

Name = Annotated[RequiredText, Field(max_length=200, examples=["AWS Certified Developer"])]
Organization = Annotated[RequiredText, Field(max_length=200, examples=["Amazon Web Services"])]
CredentialId = Annotated[str | None, Field(max_length=150), BlankToNone]
ExpiresAt = Annotated[date | None, Field(description="Left out or null: doesn't expire.")]


class CertificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    issuing_organization: Organization
    credential_id: CredentialId = None
    credential_url: WebUrl | None = None
    issued_at: date | None = None
    expires_at: ExpiresAt = None


class CertificationUpdate(BaseModel):
    """Only the fields sent change; `null` clears optional fields."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[Name | None, NotNull] = None
    issuing_organization: Annotated[Organization | None, NotNull] = None
    credential_id: CredentialId = None
    credential_url: WebUrl | None = None
    issued_at: date | None = None
    expires_at: ExpiresAt = None


class CertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    issuing_organization: str
    credential_id: str | None
    credential_url: str | None
    issued_at: date | None
    expires_at: date | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    def is_expired(self) -> bool:
        """True once the expiry date (UTC) has passed; expired ones are still listed."""
        return self.expires_at is not None and self.expires_at < utc_now().date()
