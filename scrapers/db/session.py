from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime,timezone
from contextlib import asynccontextmanager
from scrapers import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=100,
    max_overflow=100,
    pool_timeout=60,
    pool_recycle=3600,
    pool_pre_ping=True,
)
async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


class TimestampMixin:
    created_at=Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at=Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
Base = declarative_base()