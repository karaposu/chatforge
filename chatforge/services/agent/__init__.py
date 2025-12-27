"""
Chatforge Agent - ReACT agent engine.

This module provides the core ReACT (Reason-Act-Observe) agent
implementation using LangGraph.

Usage:
    from chatforge.services.agent import ReActAgent, AgentState

    agent = ReActAgent(
        tools=[my_tool],
        system_prompt="You are a helpful assistant...",
    )

    response, trace_id = agent.process_message(
        "Hello!",
        conversation_history=[],
    )
"""

from chatforge.services.agent.engine import DEFAULT_SYSTEM_PROMPT, ReActAgent
from chatforge.services.agent.state import AgentState

__all__ = [
    "ReActAgent",
    "AgentState",
    "DEFAULT_SYSTEM_PROMPT",
]
