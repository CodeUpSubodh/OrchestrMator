from datetime import datetime

from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from backend.shared.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    action: Mapped[str] = mapped_column(
        String(255)
    )

    resource_type: Mapped[str] = mapped_column(
        String(255)
    )

    resource_id: Mapped[str] = mapped_column(
        String(255)
    )

    ip_address: Mapped[str] = mapped_column(
        String(100)
    )

    user_agent: Mapped[str] = mapped_column(
        Text
    )

    success: Mapped[bool] = mapped_column(
        Boolean
    )

    details: Mapped[dict] = mapped_column(
        JSONB
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )