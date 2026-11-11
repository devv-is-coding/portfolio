from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.fields import BlankToNone, NotNull, RequiredText

Institution = Annotated[RequiredText, Field(max_length=200, examples=["University of Tokyo"])]
OptionalName = Annotated[str | None, Field(max_length=200), BlankToNone]
# TEXT holds 65,535 bytes: 16,000 characters fit even at 4 bytes each.
Description = Annotated[str | None, Field(max_length=16_000, description="Markdown."), BlankToNone]


class EducationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: Institution
    degree: OptionalName = None
    field_of_study: OptionalName = None
    description: Description = None
    start_date: date | None = None
    end_date: date | None = Field(default=None, description="Left out or null: in progress.")


class EducationUpdate(BaseModel):
    """Only the fields sent change; `null` clears optional fields."""

    model_config = ConfigDict(extra="forbid")

    institution: Annotated[Institution | None, NotNull] = None
    degree: OptionalName = None
    field_of_study: OptionalName = None
    description: Description = None
    start_date: date | None = None
    end_date: date | None = None


class EducationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution: str
    degree: str | None
    field_of_study: str | None
    description: str | None
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime
