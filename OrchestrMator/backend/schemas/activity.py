from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ActivityCreate(BaseModel):
    name: str
    domain: str
    description: str | None = None
    config: dict[str, Any]


class ActivityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str
    description: str | None
    config: dict[str, Any]
    version: str
    git_commit_sha: str
    is_active: bool
    created_at: datetime
    updated_at: datetime