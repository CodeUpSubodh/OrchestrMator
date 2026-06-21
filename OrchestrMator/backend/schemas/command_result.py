from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CommandResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    node_result_id: int

    command_id: str
    command_text: str

    output: str | None = None
    parsed_output: dict[str, Any] | None = None

    status: str
    parser_used: str
    execution_time_ms: int

    created_at: datetime
    updated_at: datetime