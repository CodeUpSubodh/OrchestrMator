from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class ScheduleCreate(BaseModel):
    activity_id: int

    cron_expression: str | None = None

    one_time_execution_at: datetime | None = None

    input_data: dict[str, Any]

    is_recurring: bool = False

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, value):
        if value is None:
            return value

        if len(value.split()) != 5:
            raise ValueError(
                "Invalid cron expression"
            )

        return value


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    activity_id: int

    user_id: int

    cron_expression: str | None

    one_time_execution_at: datetime | None

    next_execution_at: datetime | None

    is_recurring: bool

    active: bool

    created_at: datetime
    updated_at: datetime