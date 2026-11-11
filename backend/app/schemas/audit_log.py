from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = Field(description="The admin; null for anonymous or CLI actions.")
    action: str = Field(examples=["project.update"])
    entity_type: str | None
    entity_id: int | None
    details: dict[str, JsonValue] | None = Field(
        description="What changed (`{field: {old, new}}`); secrets are redacted."
    )
    ip_address: str | None
    created_at: datetime
