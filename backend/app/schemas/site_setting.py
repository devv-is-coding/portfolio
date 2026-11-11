import json
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue

KEY_MAX_LENGTH = 150
# Dotted lowercase segments: `site.name`, `seo.default_title`.
KEY_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$"
VALUE_MAX_JSON_LENGTH = 10_000


def _limit_size(value: JsonValue) -> JsonValue:
    if len(json.dumps(value, ensure_ascii=False)) > VALUE_MAX_JSON_LENGTH:
        raise ValueError(f"must be at most {VALUE_MAX_JSON_LENGTH} characters as JSON")
    return value


class SiteSettingWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Annotated[JsonValue, AfterValidator(_limit_size)] = Field(
        description="Any JSON value: string, number, boolean, list, object or null.",
        examples=["My portfolio"],
    )


class SiteSettingRead(BaseModel):
    key: str
    value: JsonValue
    is_public: bool = Field(description="Keys under `site.` and `seo.` are public.")
    created_at: datetime
    updated_at: datetime
