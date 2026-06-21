from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    user_id: int

    action: str

    resource_type: str

    resource_id: str

    ip_address: str

    user_agent: str

    success: bool

    details: dict[str, Any] | None = None

    timestamp: datetime