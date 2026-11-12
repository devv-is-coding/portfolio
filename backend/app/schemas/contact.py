from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.models.enums import ContactMessageStatus
from app.schemas.fields import BlankToNone, NotNull, RequiredText

# Name and subject go into email headers of the notification: one line only.
_ONE_LINE = StringConstraints(pattern=r"^[^\r\n]*$")

SenderName = Annotated[RequiredText, _ONE_LINE, Field(max_length=150)]
Subject = Annotated[str | None, _ONE_LINE, Field(max_length=255), BlankToNone]
Message = Annotated[RequiredText, Field(max_length=5000)]


class ContactMessageCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Grace Hopper",
                    "email": "grace@example.com",
                    "subject": "A project for you",
                    "message": "Hi! Do you have time for a small API next month?",
                }
            ]
        },
    )

    name: SenderName
    email: Annotated[EmailStr, Field(max_length=255)]
    subject: Subject = None
    message: Message
    website: str | None = Field(
        default=None,
        max_length=255,
        description="Spam trap: hide this field from people and leave it empty.",
    )


class ContactMessageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Annotated[ContactMessageStatus | None, NotNull] = None


class ContactMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    subject: str | None
    message: str
    status: ContactMessageStatus
    ip_address: str | None
    created_at: datetime
    updated_at: datetime
