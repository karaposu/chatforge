"""
LangGraph State Definition for Chatforge Agent.

This module defines the state types used by the LangGraph agent.

Usage:
    from chatforge.services.agent.state import AgentState

    state: AgentState = {
        "messages": [...],
        "user_id": "user123",
        ...
    }
"""

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """
    State object for LangGraph nodes.

    This TypedDict defines the state structure that can be passed
    through LangGraph nodes.

    Attributes:
        messages: List of LangChain message objects (required by ReACT agent)
        user_id: User identifier
        conversation_id: Conversation/session identifier
        metadata: Additional context (files, gathered info, etc.)
    """

    # Required by LangGraph ReACT agent
    messages: list[dict[str, str]]

    # Optional context
    user_id: str
    conversation_id: str
    metadata: dict[str, Any]
