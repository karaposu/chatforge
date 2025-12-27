# ChatCore Constants: Organization and Tool Names

This document explains where constants should live in ChatCore, why tool names don't belong in the library, and how applications should manage tool references.

---

## The Constants Question

When extracting ChatCore from Ask-IT, we encountered constants in `backup_src/core/constants.py`:

```python
class _StrEnum(str, Enum):
    """Python 3.10 compatible StrEnum."""

class ToolNames(_StrEnum):
    CREATE_TICKET = "create_ticket"
    PREVIEW_TICKET = "preview_ticket"
    SEARCH_NOTION = "search_notion"
    ANALYZE_IMAGE = "analyze_image"

class GuardrailNames(_StrEnum):
    PII_DETECTION = "pii_detection"
    CONTENT_FILTER = "content_filter"
    SAFETY_GUARDRAIL = "safety_guardrail"

class TTLDefaults:
    IMAGE_ANALYSIS_CACHE_SECONDS = 1800
    CONVERSATION_TIMEOUT_SECONDS = 1800

class AgentDefaults:
    MAX_ITERATIONS = 10
    TIMEOUT_SECONDS = 25.0
    TEMPERATURE = 0.0
```

**Which of these belong in ChatCore?**

---

## Generic vs Application-Specific Constants

| Constant | Generic? | Belongs in ChatCore? | Reason |
|----------|----------|----------------------|--------|
| `_StrEnum` | ✅ Yes | ✅ Yes | Python 3.10 compatibility helper |
| `GuardrailNames` | ✅ Yes | ✅ Yes | ChatCore middleware names |
| `TTLDefaults` | ✅ Yes | ✅ Yes | Cache/timeout defaults |
| `AgentDefaults` | ✅ Yes | ✅ Yes | Agent configuration defaults |
| `ToolNames` | ❌ No | ❌ **NO** | Application-specific tool names |

### Why ToolNames Don't Belong in ChatCore

**ChatCore is domain-agnostic**. Tool names are domain-specific:

```python
# IT Support (Ask-IT)
class ToolNames(_StrEnum):
    CREATE_TICKET = "create_ticket"
    SEARCH_NOTION = "search_notion"

# E-commerce
class ToolNames(_StrEnum):
    SEARCH_PRODUCTS = "search_products"
    PLACE_ORDER = "place_order"
    CHECK_INVENTORY = "check_inventory"

# Customer Service
class ToolNames(_StrEnum):
    SEARCH_FAQ = "search_faq"
    CREATE_CASE = "create_case"
    TRANSFER_TO_HUMAN = "transfer_to_human"
```

Different applications have completely different tools. ChatCore can't know what tools your application will use.

---

## What Should Live in ChatCore

### `chatcore/constants.py`

```python
"""
ChatCore Constants.

Generic constants for agent configuration and library utilities.
Applications should define their own domain-specific constants.
"""

from enum import Enum


class _StrEnum(str, Enum):
    """
    Python 3.10 compatible StrEnum.

    StrEnum was added in Python 3.11. This provides backward compatibility
    for applications using Python 3.10.

    Usage:
        from chatcore.constants import _StrEnum

        class MyToolNames(_StrEnum):
            SEARCH = "search"
            CREATE = "create"
    """

    def __str__(self) -> str:
        return self.value


class AgentDefaults:
    """
    Default values for agent configuration.

    These are sensible defaults that applications can override
    via configuration or constructor arguments.
    """

    MAX_ITERATIONS: int = 10
    """Maximum ReACT loop iterations before stopping."""

    TIMEOUT_SECONDS: float = 25.0
    """Default timeout for agent operations."""

    TEMPERATURE: float = 0.0
    """Default LLM temperature (deterministic)."""

    MAX_RETRIES: int = 3
    """Maximum retries for failed operations."""


class TTLDefaults:
    """
    Default Time-To-Live values for caching.

    Applications can override these based on their needs.
    """

    CACHE_TTL_SECONDS: int = 1800  # 30 minutes
    """Default cache entry lifetime."""

    SESSION_TIMEOUT_SECONDS: int = 1800  # 30 minutes
    """Default session timeout."""

    IMAGE_CACHE_SECONDS: int = 1800  # 30 minutes
    """Default image analysis cache lifetime."""


class MiddlewareNames(_StrEnum):
    """
    Standard middleware names in ChatCore.

    These are the built-in middleware components.
    Applications can reference these to enable/disable specific middleware.
    """

    PII_DETECTION = "pii_detection"
    CONTENT_FILTER = "content_filter"
    SAFETY_GUARDRAIL = "safety_guardrail"
    INJECTION_GUARD = "injection_guard"


class ErrorMessages:
    """
    Standard error messages for common scenarios.

    Applications can customize these as needed.
    """

    TIMEOUT = "Request timed out. Please try again."
    TOOL_FAILED = "Unable to complete the requested action. Please try again."
    CONFIG_MISSING = "Required configuration is missing."
    INVALID_INPUT = "Invalid input provided."
```

---

## What Should Live in Applications

### `ask_it/constants.py`

```python
"""
Ask-IT Application Constants.

Domain-specific constants for the Ask-IT support agent.
"""

from chatcore.constants import _StrEnum


class ToolNames(_StrEnum):
    """
    Tool names for Ask-IT agent.

    IMPORTANT: These must match EXACTLY the `name` attribute in each tool class.
    """

    CREATE_TICKET = "create_ticket"
    PREVIEW_TICKET = "preview_ticket"
    SEARCH_NOTION = "search_notion"
    ANALYZE_IMAGE = "analyze_image"
    SUMMARIZE = "summarize_conversation"


class TicketPriority(_StrEnum):
    """Jira ticket priority levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class NotionDatabases(_StrEnum):
    """Notion database IDs."""

    KNOWLEDGE_BASE = "kb_database_id"
    RUNBOOKS = "runbooks_database_id"
```

---

## The Tool Names Problem: Constants vs Dependency Injection

### The Confusion

Tool names look like they should be dependency-injected, but they're actually just **constants for convenience**.

```python
# This is NOT dependency injection:
class ToolNames(_StrEnum):
    CREATE_TICKET = "create_ticket"

if tool_name == ToolNames.CREATE_TICKET:  # Just using a constant
    ...
```

### How Tool Names Actually Work

```
Flow of tool names:

1. Tool defines its name:
   ┌─────────────────────────┐
   │ class CreateTicketTool  │
   │   name = "create_ticket"│  ← Source of truth
   └─────────────────────────┘

2. Application creates enum (optional):
   ┌─────────────────────────┐
   │ class ToolNames:        │
   │   CREATE_TICKET = ...   │  ← Just a constant for YOUR code
   └─────────────────────────┘

3. Tool is injected into agent (DI):
   ┌─────────────────────────┐
   │ agent = ReActAgent(     │
   │   tools=[tool_instance] │  ← Dependency injection
   │ )                       │
   └─────────────────────────┘

4. Agent uses tool.name internally:
   ┌─────────────────────────┐
   │ for tool in self.tools: │
   │   if name == tool.name: │  ← Uses the tool's own name
   │     tool.run(...)       │
   └─────────────────────────┘
```

**The ToolNames enum is NOT part of dependency injection - it's just syntactic sugar to avoid magic strings in your application code.**

### What IS Dependency Injection

The **tool instances** are dependency-injected:

```python
# ✅ Dependency Injection
agent = ReActAgent(
    tools=[
        CreateTicketTool(jira_adapter=jira),    # DI: tool with adapter
        SearchNotionTool(notion_adapter=notion), # DI: tool with adapter
    ]
)

# ❌ NOT Dependency Injection
class ToolNames(_StrEnum):
    CREATE_TICKET = "create_ticket"  # Just a constant
```

---

## Best Practice: Tool Registry Pattern

If you want more sophisticated tool management with DI, use a registry:

### `chatcore/tools/registry.py`

```python
"""
Tool Registry - Dynamic tool management.

Provides a registry pattern for managing tools by name,
enabling runtime tool registration and lookup.
"""

from typing import Dict
from langchain_core.tools import BaseTool


class ToolRegistry:
    """
    Registry for managing tools by name.

    Allows applications to:
    - Register tools dynamically
    - Look up tools by name
    - Enable/disable tools at runtime
    - List available tools

    Example:
        registry = ToolRegistry()
        registry.register(CreateTicketTool())
        registry.register(SearchNotionTool())

        # Get tool by name
        tool = registry.get("create_ticket")

        # Get all tools for agent
        agent = ReActAgent(tools=registry.to_list())
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool by its name.

        Args:
            tool: Tool instance to register.

        Raises:
            ValueError: If a tool with this name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """
        Get tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name to remove.

        Returns:
            True if tool was removed, False if not found.
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def list_names(self) -> list[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())

    def to_list(self) -> list[BaseTool]:
        """
        Get all tools as a list.

        Returns:
            List of all registered tool instances.
        """
        return list(self._tools.values())

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()


def create_registry_from_list(tools: list[BaseTool]) -> ToolRegistry:
    """
    Create a registry from a list of tools.

    Args:
        tools: List of tool instances.

    Returns:
        ToolRegistry with all tools registered.

    Example:
        tools = [CreateTicketTool(), SearchNotionTool()]
        registry = create_registry_from_list(tools)
    """
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry
```

### Application Usage

```python
# ask_it/tools/factory.py

from chatcore.tools import ToolRegistry
from ask_it.tools import CreateTicketTool, SearchNotionTool
from ask_it.constants import ToolNames


def create_ask_it_tools(
    jira_adapter,
    notion_adapter,
    enabled_tools: set[str] | None = None
) -> ToolRegistry:
    """
    Factory to create Ask-IT tools with dependency injection.

    Args:
        jira_adapter: Injected Jira adapter dependency.
        notion_adapter: Injected Notion adapter dependency.
        enabled_tools: Set of tool names to enable (None = all).

    Returns:
        ToolRegistry with configured tools.
    """
    registry = ToolRegistry()

    # Define all available tools with their dependencies
    all_tools = {
        ToolNames.CREATE_TICKET: lambda: CreateTicketTool(jira=jira_adapter),
        ToolNames.SEARCH_NOTION: lambda: SearchNotionTool(notion=notion_adapter),
        ToolNames.ANALYZE_IMAGE: lambda: AnalyzeImageTool(),
    }

    # Register only enabled tools
    for name, factory in all_tools.items():
        if enabled_tools is None or name in enabled_tools:
            registry.register(factory())

    return registry


# Usage in main app:
registry = create_ask_it_tools(
    jira_adapter=jira,
    notion_adapter=notion,
    enabled_tools={ToolNames.CREATE_TICKET, ToolNames.SEARCH_NOTION}
)

agent = ReActAgent(tools=registry.to_list())
```

---

## Summary

### Constants Organization

| Location | What Lives There | Why |
|----------|------------------|-----|
| `chatcore/constants.py` | Generic defaults, `_StrEnum`, `MiddlewareNames` | Domain-agnostic utilities |
| `chatcore/tools/registry.py` | Tool registry pattern | Optional tool management |
| `ask_it/constants.py` | `ToolNames`, domain-specific enums | Application-specific |

### Key Principles

1. **ChatCore is domain-agnostic** - No application-specific constants
2. **Tool names are NOT DI** - They're just constants for convenience
3. **Tool instances ARE DI** - Passed to `ReActAgent(tools=[...])`
4. **Applications define their own ToolNames** - Using `_StrEnum` from ChatCore
5. **ToolRegistry is optional** - For advanced tool management

### Migration Checklist

When extracting constants from Ask-IT to ChatCore:

- ✅ Extract `_StrEnum` helper → ChatCore
- ✅ Extract `AgentDefaults` → ChatCore
- ✅ Extract `TTLDefaults` → ChatCore
- ✅ Rename `GuardrailNames` to `MiddlewareNames` → ChatCore
- ❌ **Leave `ToolNames` in Ask-IT** - Application-specific
- ✅ Add `ToolRegistry` to ChatCore → Optional utility

### Example: Multi-Domain Applications

ChatCore's design allows one library to power multiple domains:

```python
# IT Support agent
it_tools = [CreateTicketTool(), SearchNotionTool()]
it_agent = ReActAgent(tools=it_tools)

# E-commerce agent
ecommerce_tools = [SearchProductsTool(), PlaceOrderTool()]
ecommerce_agent = ReActAgent(tools=ecommerce_tools)

# Customer service agent
cs_tools = [SearchFAQTool(), TransferToHumanTool()]
cs_agent = ReActAgent(tools=cs_tools)
```

All powered by ChatCore, each with their own tool names.
