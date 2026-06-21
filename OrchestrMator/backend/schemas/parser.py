from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ParserCreate(BaseModel):
    name: str
    domain: str
    parser_type: str
    code: str
    config: dict[str, Any]
    description: str | None = None


class ParserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str
    parser_type: str
    description: str | None
    is_active: bool

    created_at: datetime
    updated_at: datetime