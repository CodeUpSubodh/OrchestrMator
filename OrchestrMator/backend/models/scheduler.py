from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.shared.database import Base
from backend.shared.base_model import TimestampMixin


class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)

    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id")
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    cron_expression: Mapped[str] = mapped_column(
        String(255)
    )

    one_time_execution_at: Mapped[datetime] = mapped_column(
        DateTime
    )

    input_data: Mapped[dict] = mapped_column(
        JSONB
    )

    next_execution_at: Mapped[datetime] = mapped_column(
        DateTime
    )

    is_recurring: Mapped[bool] = mapped_column(
        Boolean
    )

    active: Mapped[bool] = mapped_column(
        Boolean
    )