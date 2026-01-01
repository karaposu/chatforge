"""Realtime voice API adapters."""

from .openai import OpenAIRealtimeAdapter
from .mock import MockRealtimeAdapter

__all__ = [
    "OpenAIRealtimeAdapter",
    "MockRealtimeAdapter",
]
