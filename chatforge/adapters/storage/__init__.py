"""
Chatforge Storage Adapters - Implementations of StoragePort.

Provides multiple storage backends:
- InMemoryStorageAdapter: Fast, non-persistent (testing, development)
- SQLiteStorageAdapter: File-based persistence (simple deployments)
- SQLAlchemyStorageAdapter: Full ORM support (PostgreSQL, MySQL, etc.)

Example:
    # Simple in-memory storage
    from chatforge.adapters.storage import InMemoryStorageAdapter
    storage = InMemoryStorageAdapter()

    # SQLite persistence
    from chatforge.adapters.storage import SQLiteStorageAdapter
    storage = SQLiteStorageAdapter("./data/chatforge.db")

    # PostgreSQL with SQLAlchemy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from chatforge.adapters.storage import SQLAlchemyStorageAdapter

    engine = create_engine("postgresql://user:pass@localhost/db")
    Session = sessionmaker(bind=engine)
    storage = SQLAlchemyStorageAdapter(engine, Session)
"""

from chatforge.adapters.storage.memory import InMemoryStorageAdapter
from chatforge.adapters.storage.sqlite import SQLiteStorageAdapter
from chatforge.adapters.storage.sqlalchemy import SQLAlchemyStorageAdapter

__all__ = [
    "InMemoryStorageAdapter",
    "SQLiteStorageAdapter",
    "SQLAlchemyStorageAdapter",
]
