from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.shared.database import Base
from backend.shared.base_model import TimestampMixin


class NodeResult(Base, TimestampMixin):
    __tablename__ = "node_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    execution_id: Mapped[int] = mapped_column(
        ForeignKey("executions.id")
    )

    node_name: Mapped[str] = mapped_column(
        String(255)
    )

    node_ip: Mapped[str] = mapped_column(
        String(100)
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )

    extracted_data: Mapped[dict] = mapped_column(
        JSONB
    )

    state_data: Mapped[dict] = mapped_column(
        JSONB
    )

    log_file_path: Mapped[str] = mapped_column(
        Text
    )

    error_message: Mapped[str] = mapped_column(
        Text
    )

    execution_priority: Mapped[int] = mapped_column(
        Integer
    )

    batch_id: Mapped[str] = mapped_column(
        String(100)
    )