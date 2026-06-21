from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.shared.database import Base
from backend.shared.base_model import TimestampMixin


class Activity(Base, TimestampMixin):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255)
    )

    domain: Mapped[str] = mapped_column(
        String(100)
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    config: Mapped[dict] = mapped_column(
        JSONB
    )

    version: Mapped[str] = mapped_column(
        String(50)
    )

    git_commit_sha: Mapped[str] = mapped_column(
        String(64)
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )