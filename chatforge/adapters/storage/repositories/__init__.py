"""
Backward-compatibility shim.

Repositories have moved to chatforge.adapters.storage.sqlalchemy.repositories.
"""

from chatforge.adapters.storage.sqlalchemy.repositories import (
    SQLAlchemyChatRepo,
    SQLAlchemyMessageRepo,
    SQLAlchemyProfilingRepo,
)

# Legacy aliases
ChatRepository = SQLAlchemyChatRepo
MessageRepository = SQLAlchemyMessageRepo
CPDE7Repository = SQLAlchemyProfilingRepo
