from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.shared.database import Base
from backend.shared.base_model import TimestampMixin


class Execution(Base, TimestampMixin):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id")
    )

    cr_id: Mapped[str] = mapped_column(
        String(100)
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )

    execution_mode: Mapped[str] = mapped_column(
        String(50)
    )

    input_data: Mapped[dict] = mapped_column(
        JSONB
    )

    max_parallelism: Mapped[int] = mapped_column(
        Integer
    )

    trigger_source: Mapped[str] = mapped_column(
        String(100)
    )

    trigger_metadata: Mapped[dict] = mapped_column(
        JSONB
    )