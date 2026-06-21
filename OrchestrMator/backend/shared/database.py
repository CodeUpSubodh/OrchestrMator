from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase

from backend.shared.config import settings


engine = create_engine(
    settings.DATABASE_URL,

    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,

    echo=False
)


SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()