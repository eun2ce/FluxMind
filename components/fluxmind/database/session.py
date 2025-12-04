from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fluxmind.platform import get_settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

AsyncSessionMaker = async_sessionmaker[AsyncSession]


def _create_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.db_url,
        echo=False,
        future=True,
    )


_engine: AsyncEngine | None = None
_session_maker: AsyncSessionMaker | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_maker() -> AsyncSessionMaker:
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
        )
    return _session_maker


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
