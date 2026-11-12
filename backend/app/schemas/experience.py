from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.fields import BlankToNone, DisplayOrder, NotNull, RequiredText

Company = Annotated[RequiredText, Field(max_length=200, examples=["Acme Inc."])]
Position = Annotated[RequiredText, Field(max_length=200, examples=["Backend developer"])]
EmploymentType = Annotated[
    str | None,
    Field(max_length=50, description="Free text, e.g. `full-time`, `contract`."),
    BlankToNone,
]
Location = Annotated[str | None, Field(max_length=150), BlankToNone]
Description = Annotated[str | None, Field(max_length=100_000, description="Markdown."), BlankToNone]
EndDate = Annotated[date | None, Field(description="Left out or null: the current job.")]


class ExperienceCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "company": "Acme Inc.",
                    "position": "Backend developer",
                    "employment_type": "full-time",
                    "location": "Remote",
                    "start_date": "2023-03-01",
                }
            ]
        },
    )

    company: Company
    position: Position
    employment_type: EmploymentType = None
    location: Location = None
    description: Description = None
    start_date: date
    end_date: EndDate = None
    display_order: DisplayOrder = Field(
        default=0, description="Orders jobs with the same start date."
    )


class ExperienceUpdate(BaseModel):
    """Only the fields sent change; `null` clears optional fields (`end_date`: current job)."""

    model_config = ConfigDict(extra="forbid")

    company: Annotated[Company | None, NotNull] = None
    position: Annotated[Position | None, NotNull] = None
    employment_type: EmploymentType = None
    location: Location = None
    description: Description = None
    start_date: Annotated[date | None, NotNull] = None
    end_date: EndDate = None
    display_order: Annotated[DisplayOrder | None, NotNull] = None


class ExperienceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    employment_type: str | None
    location: str | None
    description: str | None
    start_date: date
    end_date: date | None
    display_order: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    def is_current(self) -> bool:
        """True when there is no end date."""
        return self.end_date is None
