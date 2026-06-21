from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NodeResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: int
    node_name: str
    node_ip: str
    status: str

    extracted_data: dict[str, Any] | None = None
    state_data: dict[str, Any] | None = None

    log_file_path: str | None = None
    error_message: str | None = None

    execution_priority: int
    batch_id: str

    created_at: datetime
    updated_at: datetime