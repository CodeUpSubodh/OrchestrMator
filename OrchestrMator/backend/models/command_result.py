from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.shared.database import Base
from backend.shared.base_model import TimestampMixin


class CommandResult(Base, TimestampMixin):
    __tablename__ = "command_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    node_result_id: Mapped[int] = mapped_column(
        ForeignKey("node_results.id")
    )

    command_id: Mapped[str] = mapped_column(
        String(100)
    )

    command_text: Mapped[str] = mapped_column(
        Text
    )

    output: Mapped[str] = mapped_column(
        Text
    )

    parsed_output: Mapped[dict] = mapped_column(
        JSONB
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )

    parser_used: Mapped[str] = mapped_column(
        String(100)
    )

    execution_time_ms: Mapped[int] = mapped_column(
        Integer
    )