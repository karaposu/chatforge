"""
Chatforge Adapters - Implementations of port interfaces.

Provides storage adapters and null/testing adapters.
"""

from chatforge.adapters.null import (
    NullKnowledgeAdapter,
    NullMessagingAdapter,
    NullTicketingAdapter,
)
from chatforge.adapters.storage import (
    InMemoryStorageAdapter,
    SQLiteStorageAdapter,
)
from chatforge.ports import NullTracingAdapter

__all__ = [
    # Storage
    "InMemoryStorageAdapter",
    "SQLiteStorageAdapter",
    # Null/Testing
    "NullMessagingAdapter",
    "NullKnowledgeAdapter",
    "NullTicketingAdapter",
    "NullTracingAdapter",
]
