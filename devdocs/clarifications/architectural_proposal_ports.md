# Chatforge Architecture Proposal: LLMPort and AgentPort

**Date:** 2025-12-25
**Status:** Proposal
**Problem:** Chatforge lacks port abstractions for LLM and Agent interactions, causing tight coupling to LangChain

---

## Current Architecture (Without Ports)

```
Application Code
    ↓
chatforge.llm.get_llm() → BaseChatModel (LangChain interface)
    ↓
chatforge.adapters.agent.ReActAgent (hardcoded implementation)
    ↓
OpenAI/Anthropic/Bedrock via LangChain
```

**Problems:**
1. ❌ Tight coupling to LangChain's `BaseChatModel` interface
2. ❌ Can't easily mock LLM calls without LangChain mocks
3. ❌ Can't use non-LangChain LLM libraries
4. ❌ ReActAgent is the only pattern (no simple chat, no streaming-first)
5. ❌ Applications depend on concrete implementations, not abstractions

---

## Proposed Architecture (With Ports)

```
┌─────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                   │
│    - SiluetService (ChamberProtocolAI)              │
│    - CustomerSupportAgent                           │
│    - ChatAPI endpoints                              │
│    ↓ depends on                                      │
├─────────────────────────────────────────────────────┤
│  PORT INTERFACES (chatforge/ports/)                 │
│                                                      │
│  📝 LLMPort (Abstract LLM Interactions)             │
│    - invoke(messages) -> str                         │
│    - ainvoke(messages) -> str                        │
│    - stream(messages) -> Iterator[str]               │
│    - astream(messages) -> AsyncIterator[str]         │
│    - supports_vision() -> bool                       │
│    - supports_tools() -> bool                        │
│                                                      │
│  🤖 AgentPort (Abstract Agent Patterns)             │
│    - process_message(msg, history, context) -> str   │
│    - supports_tools() -> bool                        │
│    - add_tool(tool)                                  │
│    - set_system_prompt(prompt)                       │
│    ↓ implemented by                                  │
├─────────────────────────────────────────────────────┤
│  ADAPTERS (chatforge/adapters/)                     │
│                                                      │
│  LLM Adapters (implement LLMPort):                  │
│    - OpenAILLMAdapter                               │
│    - AnthropicLLMAdapter                            │
│    - BedrockLLMAdapter                              │
│    - LangChainLLMAdapter (wraps existing)           │
│    - MockLLMAdapter (for testing)                   │
│                                                      │
│  Agent Adapters (implement AgentPort):              │
│    - ReActAgentAdapter (tool-use pattern)           │
│    - SimpleChatAdapter (direct LLM, no tools)       │
│    - StreamingAgentAdapter (streaming-first)        │
│    - MockAgentAdapter (for testing)                 │
└─────────────────────────────────────────────────────┘
```

---

## 1. LLMPort Interface

**File:** `chatforge/ports/llm.py`

```python
"""
LLMPort - Abstract interface for LLM interactions.

Provides provider-agnostic interface for:
- Synchronous and asynchronous calls
- Streaming responses
- Vision capabilities
- Tool/function calling
"""

from abc import ABC, abstractmethod
from typing import Iterator, AsyncIterator, Any


class LLMMessage:
    """Standard message format for LLM interactions."""

    def __init__(
        self,
        role: str,  # "system" | "user" | "assistant"
        content: str | list[dict],  # Text or multimodal content
        name: str | None = None,
        tool_calls: list[dict] | None = None,
    ):
        self.role = role
        self.content = content
        self.name = name
        self.tool_calls = tool_calls


class LLMResponse:
    """Standard response format from LLM."""

    def __init__(
        self,
        content: str,
        model: str,
        usage: dict[str, int] | None = None,  # tokens used
        tool_calls: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.content = content
        self.model = model
        self.usage = usage
        self.tool_calls = tool_calls
        self.metadata = metadata or {}


class LLMPort(ABC):
    """
    Port interface for LLM interactions.

    Implementations provide access to different LLM providers
    (OpenAI, Anthropic, Bedrock, etc.) with a unified interface.

    Example:
        llm = get_llm_adapter(provider="openai", model="gpt-4o-mini")

        # Simple call
        response = await llm.ainvoke([
            LLMMessage(role="user", content="Hello!")
        ])

        # Streaming
        async for chunk in llm.astream([...]):
            print(chunk, end="", flush=True)
    """

    @abstractmethod
    def invoke(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """
        Synchronous LLM call.

        Args:
            messages: List of LLMMessage objects
            **kwargs: Provider-specific options (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    async def ainvoke(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Async LLM call."""
        pass

    @abstractmethod
    def stream(self, messages: list[LLMMessage], **kwargs) -> Iterator[str]:
        """
        Streaming LLM call (synchronous iterator).

        Yields:
            str: Text chunks as they arrive
        """
        pass

    @abstractmethod
    async def astream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        """Async streaming LLM call."""
        pass

    @abstractmethod
    def supports_vision(self) -> bool:
        """Whether this LLM supports vision (image inputs)."""
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this LLM supports tool/function calling."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier (e.g., 'gpt-4o-mini')."""
        pass

    @abstractmethod
    def get_provider(self) -> str:
        """Get the provider name (e.g., 'openai', 'anthropic')."""
        pass
```

---

## 2. AgentPort Interface

**File:** `chatforge/ports/agent.py`

```python
"""
AgentPort - Abstract interface for agent patterns.

Different agent patterns:
- SimpleChatAgent: Direct LLM calls, no tools
- ReActAgent: Tool-use with reasoning loop
- StreamingAgent: Streaming-first responses
"""

from abc import ABC, abstractmethod
from typing import Any


class AgentResponse:
    """Standard response from agent."""

    def __init__(
        self,
        content: str,
        tool_calls: list[dict] | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.content = content
        self.tool_calls = tool_calls
        self.trace_id = trace_id
        self.metadata = metadata or {}


class AgentPort(ABC):
    """
    Port interface for agent patterns.

    Agents process user messages and return responses.
    Different implementations provide different patterns:
    - SimpleChatAdapter: Direct LLM, no tools
    - ReActAgentAdapter: Tool use with reasoning
    - StreamingAgentAdapter: Streaming responses

    Example:
        agent = get_agent_adapter(
            type="simple_chat",
            llm=my_llm,
            system_prompt="You are a helpful assistant"
        )

        response = agent.process_message(
            user_message="What's the weather?",
            conversation_history=[...],
        )
    """

    @abstractmethod
    def process_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """
        Process user message and return response.

        Args:
            user_message: The user's input
            conversation_history: Previous messages [{"role": "user", "content": "..."}]
            context: Optional context (user_id, session_id, metadata, etc.)

        Returns:
            AgentResponse with content and metadata
        """
        pass

    @abstractmethod
    async def aprocess_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Async version of process_message."""
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this agent supports tool use."""
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this agent supports streaming responses."""
        pass

    @abstractmethod
    def set_system_prompt(self, prompt: str) -> None:
        """
        Update the system prompt.

        Important for dynamic prompts (e.g., ChamberProtocolAI's random word limits).
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get current system prompt."""
        pass
```

---

## 3. Example Adapters

### OpenAILLMAdapter

**File:** `chatforge/adapters/llm/openai_adapter.py`

```python
from openai import OpenAI, AsyncOpenAI
from chatforge.ports.llm import LLMPort, LLMMessage, LLMResponse


class OpenAILLMAdapter(LLMPort):
    """OpenAI implementation of LLMPort."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ):
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def ainvoke(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        # Convert LLMMessage to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await self.async_client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=openai_messages,
            temperature=kwargs.get("temperature", self.temperature),
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )

    def invoke(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        # Sync version
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=openai_messages,
            temperature=kwargs.get("temperature", self.temperature),
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )

    async def astream(self, messages: list[LLMMessage], **kwargs):
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        stream = await self.async_client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=openai_messages,
            temperature=kwargs.get("temperature", self.temperature),
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def stream(self, messages: list[LLMMessage], **kwargs):
        # Sync streaming
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        stream = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=openai_messages,
            temperature=kwargs.get("temperature", self.temperature),
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def supports_vision(self) -> bool:
        return self.model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]

    def supports_tools(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return self.model

    def get_provider(self) -> str:
        return "openai"
```

### SimpleChatAgentAdapter

**File:** `chatforge/adapters/agent/simple_chat_adapter.py`

```python
from chatforge.ports.agent import AgentPort, AgentResponse
from chatforge.ports.llm import LLMPort, LLMMessage


class SimpleChatAgentAdapter(AgentPort):
    """
    Simple chat agent - direct LLM calls without tools.

    Perfect for:
    - ChamberProtocolAI (game AI with dynamic prompts)
    - Simple Q&A bots
    - Conversational AI without tool use
    """

    def __init__(
        self,
        llm: LLMPort,
        system_prompt: str = "You are a helpful assistant.",
    ):
        self.llm = llm
        self._system_prompt = system_prompt

    async def aprocess_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        # Build messages
        messages = [LLMMessage(role="system", content=self._system_prompt)]

        # Add history
        if conversation_history:
            for msg in conversation_history:
                messages.append(
                    LLMMessage(role=msg["role"], content=msg["content"])
                )

        # Add current message
        messages.append(LLMMessage(role="user", content=user_message))

        # Call LLM
        response = await self.llm.ainvoke(messages)

        return AgentResponse(
            content=response.content,
            metadata={"model": response.model, "usage": response.usage},
        )

    def process_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        # Sync version
        messages = [LLMMessage(role="system", content=self._system_prompt)]

        if conversation_history:
            for msg in conversation_history:
                messages.append(
                    LLMMessage(role=msg["role"], content=msg["content"])
                )

        messages.append(LLMMessage(role="user", content=user_message))

        response = self.llm.invoke(messages)

        return AgentResponse(
            content=response.content,
            metadata={"model": response.model, "usage": response.usage},
        )

    def supports_tools(self) -> bool:
        return False

    def supports_streaming(self) -> bool:
        return True  # Can stream via LLMPort

    def set_system_prompt(self, prompt: str) -> None:
        """Update system prompt dynamically."""
        self._system_prompt = prompt

    def get_system_prompt(self) -> str:
        return self._system_prompt
```

---

## 4. Usage Examples

### Example 1: ChamberProtocolAI (Simple Chat with Dynamic Prompts)

```python
from chatforge.ports.llm import LLMPort
from chatforge.ports.agent import AgentPort
from chatforge.adapters.llm import get_llm_adapter
from chatforge.adapters.agent import SimpleChatAgentAdapter

class SiluetService:
    def __init__(self, agent: AgentPort, storage: StoragePort):
        self.agent = agent
        self.storage = storage

    async def process_request(self, request) -> str:
        # Build dynamic prompt with random word limit
        random_words = random.randint(2, 100)
        prompt = self._build_silüet_prompt(
            personality=request.personality,
            word_limit=random_words,
            emotion_tag=request.emotion_tag,
        )

        # Update agent's system prompt DYNAMICALLY
        self.agent.set_system_prompt(prompt)

        # Get history
        history = await self.storage.get_conversation(request.chat_id)

        # Process message
        response = await self.agent.aprocess_message(
            user_message=request.user_message,
            conversation_history=[
                {"role": msg.role, "content": msg.content}
                for msg in history
            ],
        )

        return response.content


# Initialization (dependency injection)
llm = get_llm_adapter(provider="anthropic", model="claude-3-5-sonnet-20241022")
agent = SimpleChatAgentAdapter(llm=llm, system_prompt="Default prompt")
storage = GlassmindStorageAdapter(...)

siluet_service = SiluetService(agent=agent, storage=storage)
```

### Example 2: Customer Support (ReAct Agent with Tools)

```python
from chatforge.adapters.agent import ReActAgentAdapter

# Create tools
search_tool = KnowledgeSearchTool(knowledge_base=kb)
ticket_tool = CreateTicketTool(ticketing_system=jira)

# Create ReAct agent
llm = get_llm_adapter(provider="openai", model="gpt-4o-mini")
agent = ReActAgentAdapter(
    llm=llm,
    tools=[search_tool, ticket_tool],
    system_prompt="You are a customer support agent..."
)

# Process message (agent decides when to use tools)
response = await agent.aprocess_message(
    user_message="I can't log in",
    conversation_history=[],
)
```

### Example 3: Testing with MockLLMAdapter

```python
from chatforge.adapters.llm import MockLLMAdapter

class MockLLMAdapter(LLMPort):
    """Mock LLM for testing."""

    def __init__(self, fixed_response: str = "Mock response"):
        self.fixed_response = fixed_response

    async def ainvoke(self, messages, **kwargs):
        return LLMResponse(
            content=self.fixed_response,
            model="mock-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )

    # ... other methods return mocked data


# In tests
def test_siluet_service():
    mock_llm = MockLLMAdapter(fixed_response="Test response")
    agent = SimpleChatAgentAdapter(llm=mock_llm)
    service = SiluetService(agent=agent, storage=mock_storage)

    response = await service.process_request(test_request)
    assert response == "Test response"
```

---

## 5. Factory Functions

**File:** `chatforge/factory.py`

```python
"""Factory functions for creating LLM and Agent adapters."""

from chatforge.ports.llm import LLMPort
from chatforge.ports.agent import AgentPort


def get_llm_adapter(
    provider: str,
    model: str | None = None,
    **kwargs,
) -> LLMPort:
    """
    Get LLM adapter for specified provider.

    Args:
        provider: "openai" | "anthropic" | "bedrock" | "langchain"
        model: Model name (provider-specific)
        **kwargs: Provider-specific options

    Returns:
        LLMPort implementation

    Example:
        llm = get_llm_adapter(provider="openai", model="gpt-4o-mini", temperature=0.7)
    """
    if provider == "openai":
        from chatforge.adapters.llm.openai_adapter import OpenAILLMAdapter
        return OpenAILLMAdapter(model=model, **kwargs)

    elif provider == "anthropic":
        from chatforge.adapters.llm.anthropic_adapter import AnthropicLLMAdapter
        return AnthropicLLMAdapter(model=model, **kwargs)

    elif provider == "bedrock":
        from chatforge.adapters.llm.bedrock_adapter import BedrockLLMAdapter
        return BedrockLLMAdapter(model=model, **kwargs)

    elif provider == "langchain":
        # Wrapper for existing LangChain models
        from chatforge.adapters.llm.langchain_adapter import LangChainLLMAdapter
        return LangChainLLMAdapter(model=kwargs.get("llm"))

    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_agent_adapter(
    type: str,
    llm: LLMPort,
    **kwargs,
) -> AgentPort:
    """
    Get agent adapter for specified type.

    Args:
        type: "simple_chat" | "react" | "streaming"
        llm: LLMPort instance
        **kwargs: Agent-specific options (system_prompt, tools, etc.)

    Returns:
        AgentPort implementation

    Example:
        agent = get_agent_adapter(
            type="simple_chat",
            llm=my_llm,
            system_prompt="You are..."
        )
    """
    if type == "simple_chat":
        from chatforge.adapters.agent.simple_chat_adapter import SimpleChatAgentAdapter
        return SimpleChatAgentAdapter(llm=llm, **kwargs)

    elif type == "react":
        from chatforge.adapters.agent.react_adapter import ReActAgentAdapter
        return ReActAgentAdapter(llm=llm, **kwargs)

    elif type == "streaming":
        from chatforge.adapters.agent.streaming_adapter import StreamingAgentAdapter
        return StreamingAgentAdapter(llm=llm, **kwargs)

    else:
        raise ValueError(f"Unknown agent type: {type}")
```

---

## 6. Migration Path

### Backward Compatibility

Keep existing API working while adding new ports:

```python
# chatforge/llm/factory.py (DEPRECATED)
def get_llm(*args, **kwargs):
    """DEPRECATED: Use get_llm_adapter() instead."""
    warnings.warn(
        "get_llm() is deprecated. Use get_llm_adapter() for port-based architecture.",
        DeprecationWarning,
    )
    # Return LangChain wrapper
    from chatforge.adapters.llm.langchain_adapter import LangChainLLMAdapter
    llm = _old_get_llm_implementation(*args, **kwargs)
    return LangChainLLMAdapter(llm=llm)
```

### Migration Steps

1. **Phase 1:** Add port interfaces (`LLMPort`, `AgentPort`)
2. **Phase 2:** Create adapters (`OpenAILLMAdapter`, `SimpleChatAgentAdapter`)
3. **Phase 3:** Add factory functions (`get_llm_adapter`, `get_agent_adapter`)
4. **Phase 4:** Deprecate old API (`get_llm()`, direct `ReActAgent` import)
5. **Phase 5:** Update documentation and examples

---

## 7. Benefits

### For Application Developers:

✅ **Provider Independence:** Switch between OpenAI/Anthropic/Bedrock without code changes
✅ **Easy Testing:** Mock LLM/agent with `MockLLMAdapter`
✅ **Clear Contracts:** Depend on `LLMPort`/`AgentPort`, not third-party interfaces
✅ **Multiple Patterns:** Choose simple chat, ReAct, streaming based on needs
✅ **Dynamic Behavior:** Change system prompts at runtime (ChamberProtocolAI use case)

### For Chatforge:

✅ **True Hexagonal Architecture:** Core = ports, implementations = adapters
✅ **Library Independence:** Not locked to LangChain
✅ **Extensibility:** Add new providers without changing core
✅ **Testability:** Every component mockable via ports

---

## 8. Comparison

### Before (Current):

```python
# Tightly coupled to LangChain
from langchain_openai import ChatOpenAI
from chatforge.adapters.agent import ReActAgent  # Only one pattern

llm = ChatOpenAI(model="gpt-4o-mini")  # LangChain class
agent = ReActAgent(llm=llm, tools=[...])  # Hardcoded ReAct pattern

# Can't change system prompt dynamically
# Can't use non-LangChain providers easily
# Can't mock without LangChain mocks
```

### After (With Ports):

```python
# Depends on ports, not implementations
from chatforge import get_llm_adapter, get_agent_adapter

llm = get_llm_adapter(provider="openai", model="gpt-4o-mini")
agent = get_agent_adapter(type="simple_chat", llm=llm)

# Can change system prompt anytime
agent.set_system_prompt("New prompt with 42 word limit")

# Easy to swap providers
llm = get_llm_adapter(provider="anthropic", model="claude-3-5-sonnet")

# Easy to mock
mock_llm = MockLLMAdapter(fixed_response="Test")
```

---

## Summary

This proposal adds **LLMPort** and **AgentPort** to chatforge, creating true hexagonal architecture where:

1. **Ports** = interfaces defining contracts
2. **Adapters** = implementations for different providers/patterns
3. **Applications** = depend on ports only

This solves ChamberProtocolAI's issues:
- ✅ Dynamic system prompts (`agent.set_system_prompt()`)
- ✅ Simple chat pattern (no ReAct overhead)
- ✅ Provider flexibility
- ✅ Easy testing with mocks

**Next Steps:**
1. Review and approve architecture
2. Implement `LLMPort` interface
3. Implement `AgentPort` interface
4. Create adapters for OpenAI, Anthropic
5. Create `SimpleChatAgentAdapter`
6. Deprecate old `get_llm()` API
