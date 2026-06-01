"""
Chatforge Storage Adapters - Implementations of repository interfaces.

Per-entity SQLAlchemy async repositories implementing the abstract
interfaces defined in chatforge.ports.storage.

Example:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from chatforge.ports.storage import Storage
    from chatforge.adapters.storage import (
        SQLAlchemyChatRepo,
        SQLAlchemyMessageRepo,
        SQLAlchemyProfilingRepo,
    )

    engine = create_async_engine("sqlite+aiosqlite:///./data/chatforge.db")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        storage = Storage(
            chats=SQLAlchemyChatRepo(session),
            messages=SQLAlchemyMessageRepo(session),
            profiling=SQLAlchemyProfilingRepo(session),
        )
        chat = await storage.chats.create_chat(user_id=1)
"""

from chatforge.adapters.storage.sqlalchemy import (
    SQLAlchemyChatRepo,
    SQLAlchemyMessageRepo,
    SQLAlchemyProfilingRepo,
)

__all__ = [
    "SQLAlchemyChatRepo",
    "SQLAlchemyMessageRepo",
    "SQLAlchemyProfilingRepo",
]
