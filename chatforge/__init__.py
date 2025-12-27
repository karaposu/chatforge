"""
Chatforge - A hexagonal architecture AI agent framework.

Chatforge provides a domain-agnostic, extensible framework for building
AI-powered chat agents using LangGraph and LangChain.

Core Components:
- Agent: ReACT agent engine using LangGraph
- Ports: Interfaces for external dependencies (hexagonal architecture)
- Adapters: Implementations of port interfaces
- Config: Configuration management with Pydantic
- Middleware: Security guardrails (PII, injection, safety)
- LLM: Multi-provider LLM factory

Quick Start:
    from chatforge import get_llm, ReActAgent, AsyncAwareTool

    # Simple LLM call
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    response = llm.invoke([{"role": "user", "content": "Hello!"}])

    # Create agent with tools
    agent = ReActAgent(
        tools=[my_search_tool, my_action_tool],
        system_prompt="You are a helpful assistant...",
    )
    response, trace_id = agent.process_message("Hello!", conversation_history=[])

For middleware:
    from chatforge.middleware import (
        SafetyGuardrail,
        PromptInjectionGuard,
        get_pii_middleware,
    )

For adapters:
    from chatforge.adapters import (
        InMemoryStorageAdapter,
        SQLiteStorageAdapter,
        NullMessagingAdapter,
    )
"""

from chatforge.services.agent import DEFAULT_SYSTEM_PROMPT, AgentState, ReActAgent
from chatforge.services.llm import get_llm, get_streaming_llm, get_vision_llm
from chatforge.services.agent.tools import AsyncAwareTool, create_tool

# Package metadata
__version__ = "0.1.0"
__author__ = "Chatforge Team"

__all__ = [
    # Agent
    "ReActAgent",
    "AgentState",
    "DEFAULT_SYSTEM_PROMPT",
    # LLM
    "get_llm",
    "get_streaming_llm",
    "get_vision_llm",
    # Tools
    "AsyncAwareTool",
    "create_tool",
    # Version
    "__version__",
]
