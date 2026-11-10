"""The one error shape every endpoint returns (see app/core/errors.py)."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """One problem with the request, e.g. a field that failed validation."""

    field: str | None = Field(
        default=None, description="Where the problem is, e.g. `body.email` or `query.page`."
    )
    message: str
    type: str | None = Field(default=None, description="Machine-readable kind, e.g. `missing`.")


class ErrorBody(BaseModel):
    code: str = Field(description="Stable machine-readable code, e.g. `not_found`.")
    message: str = Field(description="Human-readable summary, safe to show to users.")
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
