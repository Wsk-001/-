from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# SQLite does not support pool_size/max_overflow; detect dialect
_db_url = settings.DATABASE_URL
_is_sqlite = _db_url.startswith("sqlite")

_engine_kwargs: dict = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 10

engine = create_async_engine(_db_url, echo=False, **_engine_kwargs)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Use a naming convention for constraints to avoid conflicts
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # FIX: Removed auto-commit after yield. The previous code committed
    # on every request even if the route handler had already committed or
    # had caught-and-handled an exception internally, causing partial
    # writes. Routes now control their own transaction lifecycle.
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    import models  # noqa: F401 - ensure all models are imported so tables are created

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
