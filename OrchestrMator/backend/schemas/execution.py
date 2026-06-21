from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ExecutionCreate(BaseModel):
    activity_id: int
    cr_id: str
    execution_mode: str
    input_data: dict[str, Any]
    max_parallelism: int = Field(ge=1, le=100)

    @field_validator("execution_mode")
    @classmethod
    def validate_mode(cls, value):
        allowed = ["manual", "scheduled", "api"]

        if value not in allowed:
            raise ValueError(
                f"execution_mode must be one of {allowed}"
            )

        return value


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    activity_id: int
    cr_id: str
    status: str
    execution_mode: str
    max_parallelism: int
    created_at: datetime
    updated_at: datetime