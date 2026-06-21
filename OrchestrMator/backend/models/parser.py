from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.shared.database import Base
from backend.shared.base_model import TimestampMixin


class Parser(Base, TimestampMixin):
    __tablename__ = "parsers"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255)
    )

    domain: Mapped[str] = mapped_column(
        String(100)
    )

    parser_type: Mapped[str] = mapped_column(
        String(50)
    )

    code: Mapped[str] = mapped_column(
        Text
    )

    config: Mapped[dict] = mapped_column(
        JSONB
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )