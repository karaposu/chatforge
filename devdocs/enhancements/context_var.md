# Context Variables: Request-Scoped Data for Tools

This document explains context variables, why they're needed, their advantages, and how they fit into ChatCore's architecture.

---

## The Problem: Tools Need Request Context

### Scenario

A user sends a message through Slack:

```
User: alice@company.com (Slack user U12345)
Message: "Create a ticket for the printer issue"
```

The agent needs to create a Jira ticket **on behalf of Alice**, but the tool doesn't have access to her email:

```python
class CreateTicketTool(BaseTool):
    name = "create_ticket"

    def _run(self, description: str) -> str:
        # ❌ Problem: How do we know WHO is creating this ticket?
        # We need alice@company.com but it's not in the tool signature

        jira.create_issue(
            summary=description,
            reporter=???  # ← Where does this come from?
        )
```

### Why Tool Signature Can't Include Context

The LLM calls tools based on the user's message. If we add context to the signature:

```python
class CreateTicketTool(BaseTool):
    def _run(self, description: str, reporter_email: str) -> str:
        ...
```

The LLM would need to extract `reporter_email` from the conversation:

```
LLM reasoning:
"User said 'Create a ticket for the printer issue'"
"I need to call create_ticket(description='printer issue', reporter_email=???)"
"The user didn't mention their email... I'll have to guess or ask"
```

**The LLM can't know request-level metadata** like:
- User email
- User ID
- Session ID
- Channel/conversation ID
- Request timestamp
- Client IP address
- Authentication tokens

---

## Solution 1: Dependency Injection (Doesn't Work for Tools)

In typical DI, you'd inject dependencies into the constructor:

```python
# ✅ Works for adapters
class JiraAdapter:
    def __init__(self, api_token: str, user_email: str):
        self.api_token = api_token
        self.user_email = user_email

# ❌ Doesn't work for per-request data
# Tools are created once, not per-request
tool = CreateTicketTool(user_email="alice@company.com")  # Wrong!
```

**Problem**: Tools are instantiated once and reused across requests. You can't inject per-request data into the constructor.

---

## Solution 2: Global Variables (Thread-Unsafe)

```python
# ❌ BAD: Not thread-safe
current_user_email = None

def handle_request():
    global current_user_email
    current_user_email = "alice@company.com"
    agent.process_message("Create ticket")
    # If another request comes in here, it overwrites current_user_email!

class CreateTicketTool(BaseTool):
    def _run(self, description: str):
        return jira.create_issue(reporter=current_user_email)
```

**Problem**: Web servers handle multiple requests concurrently. Global variables are shared across all requests, causing race conditions.

---

## Solution 3: Context Variables (✅ Correct)

Python's `contextvars` provides **thread-safe, async-safe** request-scoped storage:

```python
import contextvars

# Define context variable
_reporter_email: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "reporter_email", default=None
)

# In request handler (each request gets isolated context)
async def handle_slack_message(event):
    user_email = await get_user_email(event['user'])
    _reporter_email.set(user_email)  # ← Sets for THIS request only

    response = agent.process_message(event['text'])
    # Context is automatically cleaned up after request

# In tool (reads from THIS request's context)
class CreateTicketTool(BaseTool):
    def _run(self, description: str):
        reporter = _reporter_email.get()  # ← Gets THIS request's email
        return jira.create_issue(reporter=reporter)
```

---

## How Context Variables Work

### Thread-Local Storage with Async Support

```
Request 1 (Thread/Task A):
┌─────────────────────────────────────┐
│ set_context("email", "alice@co.com")│
│ Context: {email: "alice@co.com"}    │
│   ↓                                 │
│ agent.process_message()             │
│   ↓                                 │
│ CreateTicketTool.run()              │
│   ↓                                 │
│ get_context("email") → "alice@..."  │
└─────────────────────────────────────┘

Request 2 (Thread/Task B) - running at the same time:
┌─────────────────────────────────────┐
│ set_context("email", "bob@co.com")  │
│ Context: {email: "bob@co.com"}      │
│   ↓                                 │
│ agent.process_message()             │
│   ↓                                 │
│ CreateTicketTool.run()              │
│   ↓                                 │
│ get_context("email") → "bob@..."    │
└─────────────────────────────────────┘

Each request has isolated context - no interference!
```

### Key Properties

| Feature | Description |
|---------|-------------|
| **Thread-safe** | Each thread has isolated context |
| **Async-safe** | Works with asyncio tasks |
| **Automatic cleanup** | Context cleared when request completes |
| **No explicit passing** | Tools access context without it being passed through call chain |
| **Type-safe** | Can use type hints with generics |

---

## Advantages of Context Variables

### 1. Clean Tool Signatures

```python
# ❌ Without context: Polluted signatures
class CreateTicketTool(BaseTool):
    def _run(
        self,
        description: str,
        reporter_email: str,     # ← LLM has to provide
        user_id: str,            # ← LLM has to provide
        channel_id: str,         # ← LLM has to provide
        request_timestamp: str,  # ← LLM has to provide
    ):
        pass

# ✅ With context: Clean signatures
class CreateTicketTool(BaseTool):
    def _run(self, description: str):
        # Context available automatically
        reporter = get_context("reporter_email")
        user_id = get_context("user_id")
        pass
```

### 2. Separation of Concerns

```python
# Application layer knows about the request
async def handle_slack_message(event):
    set_context("reporter_email", event['user_email'])
    set_context("channel_id", event['channel'])
    agent.process_message(event['text'])

# Tool layer doesn't need to know about Slack
class CreateTicketTool(BaseTool):
    def _run(self, description: str):
        # Just gets what it needs from context
        reporter = get_context("reporter_email")
```

### 3. No Explicit Passing Through Call Chain

```python
# ❌ Without context: Threading parameters through layers
def handle_request(user_email):
    process_message(message, user_email)

def process_message(message, user_email):
    agent.run(message, user_email)

def agent_run(message, user_email):
    tool.execute(message, user_email)

# ✅ With context: Set once, access anywhere
def handle_request(user_email):
    set_context("user_email", user_email)
    process_message(message)

def process_message(message):
    agent.run(message)

def agent_run(message):
    tool.execute(message)

def tool_execute(message):
    email = get_context("user_email")  # Available here
```

### 4. Request Tracing and Logging

```python
import logging

# Set request ID in context
set_context("request_id", "req_abc123")

# Logger can automatically include request ID
class ContextLogger(logging.Logger):
    def _log(self, level, msg, args, **kwargs):
        request_id = get_context("request_id", "none")
        msg = f"[{request_id}] {msg}"
        super()._log(level, msg, args, **kwargs)

logger.info("Processing ticket")
# Output: [req_abc123] Processing ticket
```

### 5. Middleware and Guardrails

```python
# Middleware can set context for downstream components
class AuthMiddleware:
    async def __call__(self, request):
        user = await authenticate(request)
        set_context("user_id", user.id)
        set_context("user_role", user.role)
        set_context("permissions", user.permissions)

        return await next_middleware(request)

# Tools can check permissions from context
class DeleteDataTool(BaseTool):
    def _run(self, data_id: str):
        permissions = get_context("permissions", [])
        if "delete" not in permissions:
            raise PermissionError("User not authorized to delete")

        # Proceed with deletion
```

---

## Does This Fit Into ChatCore?

### Arguments FOR Including in ChatCore

#### 1. Common Pattern Across All Applications

**Every** chat application needs request context:

```python
# IT Support
set_context("reporter_email", user.email)
set_context("slack_channel", channel_id)

# E-commerce
set_context("customer_id", customer.id)
set_context("shopping_cart", cart)
set_context("session_id", session.id)

# Customer Service
set_context("caller_phone", phone)
set_context("account_tier", tier)
set_context("case_id", case.id)

# HR Chatbot
set_context("employee_id", emp.id)
set_context("department", dept)
```

All use the same **pattern**, just different **keys/values**.

#### 2. Essential for Clean Architecture

Without context variables:
- Tool signatures become polluted
- Tight coupling between layers
- Request data threaded through entire call chain

#### 3. Critical for Tracing and Observability

```python
# ChatCore tracing can use context
from chatcore.context import get_context

class TracingPort:
    def start_trace(self):
        trace_id = generate_trace_id()
        set_context("trace_id", trace_id)
        return trace_id

    def log_event(self, event_name: str):
        trace_id = get_context("trace_id")
        # Send to observability platform
```

#### 4. Type-Safe Generic Implementation

ChatCore can provide type-safe base classes that applications extend:

```python
# ChatCore provides the machinery
from chatcore.context import ContextVar

# Applications define their context
class AppContext:
    user_id = ContextVar[str]("user_id")
    session_id = ContextVar[str]("session_id")
```

### Arguments AGAINST Including in ChatCore

#### 1. Not All Applications Need It

Simple use cases might not need request context:
- CLI chat tools (single user)
- Notebook experiments
- Testing/development

#### 2. Python Already Has `contextvars`

It's a standard library feature - do we need to wrap it?

**Counter**: Yes, because:
- Type-safe wrapper is valuable
- Centralized management pattern
- Integration with ChatCore tracing/logging

#### 3. Adds Complexity

More API surface area to maintain.

**Counter**: The implementation is simple (~100 lines) and the value is high.

---

## How ChatCore Should Support Context Variables

### Level 1: Minimal (Documentation Only)

ChatCore documents the pattern but doesn't provide implementation:

```markdown
## Request Context Pattern

For per-request data, use Python's contextvars:

\`\`\`python
import contextvars

user_email = contextvars.ContextVar("user_email")
user_email.set("alice@company.com")
\`\`\`
```

**Pros**: No maintenance burden
**Cons**: Every app reinvents the wheel, no type safety

### Level 2: Utility Classes (Recommended)

ChatCore provides generic `ContextVar` and `ContextManager` base classes:

```python
# chatcore/context.py

from chatcore.context import ContextVar, ContextManager

# Applications define their context
class MyAppContext(ContextManager):
    user_id = ContextVar[str]("user_id")
    session_id = ContextVar[str]("session_id")

context = MyAppContext()
```

**Pros**: Type-safe, reusable, optional
**Cons**: Small API to maintain

### Level 3: Built-in Standard Context (Not Recommended)

ChatCore defines standard context keys:

```python
# chatcore/context.py

# Pre-defined context variables
user_id = ContextVar[str]("user_id")
session_id = ContextVar[str]("session_id")
```

**Pros**: Consistency across applications
**Cons**: Opinionated, limits flexibility, not domain-agnostic

---

## Recommended Implementation for ChatCore

### `chatcore/context.py`

```python
"""
Request Context Management.

Provides utilities for managing per-request context data using
Python's contextvars for thread-safe, async-safe storage.

Tools can access request-level metadata (user ID, session ID, etc.)
without polluting tool signatures or threading data through layers.

Example:
    from chatcore.context import ContextVar

    # Define application context
    user_id = ContextVar[str]("user_id", default="")
    session_id = ContextVar[str]("session_id", default="")

    # In request handler
    user_id.set("user_123")
    session_id.set("session_abc")

    # In tools (deep in call stack)
    current_user = user_id.get()
"""

import contextvars
from typing import Any, Generic, TypeVar

T = TypeVar('T')


class ContextVar(Generic[T]):
    """
    Type-safe wrapper around contextvars.ContextVar.

    Provides a convenient API for defining and accessing
    request-scoped context variables.

    Attributes:
        name: Unique name for this context variable.
        default: Default value if not set.

    Example:
        # Define context variable
        user_email = ContextVar[str | None]("user_email", default=None)

        # Set value (in request handler)
        user_email.set("alice@company.com")

        # Get value (in tool)
        email = user_email.get()

        # Clear value
        user_email.clear()
    """

    def __init__(self, name: str, default: T | None = None):
        """
        Initialize context variable.

        Args:
            name: Unique identifier for this variable.
            default: Default value when not set.
        """
        self._var: contextvars.ContextVar[T] = contextvars.ContextVar(
            name, default=default
        )
        self.name = name
        self.default = default

    def set(self, value: T) -> None:
        """
        Set the context value for the current request.

        Args:
            value: Value to set.
        """
        self._var.set(value)

    def get(self) -> T:
        """
        Get the context value for the current request.

        Returns:
            Current value or default if not set.
        """
        return self._var.get()

    def clear(self) -> None:
        """Reset to default value."""
        if self.default is not None:
            self._var.set(self.default)

    def __repr__(self) -> str:
        return f"ContextVar(name={self.name!r}, default={self.default!r})"


class ContextManager:
    """
    Base class for managing multiple context variables.

    Subclass this to define your application's context schema
    as class attributes.

    Example:
        from chatcore.context import ContextManager, ContextVar

        class AppContext(ContextManager):
            user_id = ContextVar[str]("user_id", default="")
            session_id = ContextVar[str]("session_id", default="")
            trace_id = ContextVar[str | None]("trace_id", default=None)

        # Create instance
        ctx = AppContext()

        # Set values
        ctx.user_id.set("user_123")
        ctx.session_id.set("session_abc")

        # Get values
        user = ctx.user_id.get()

        # Clear all
        ctx.clear_all()
    """

    def clear_all(self) -> None:
        """Clear all context variables defined on this manager."""
        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                attr = getattr(self, attr_name)
                if isinstance(attr, ContextVar):
                    attr.clear()

    def to_dict(self) -> dict[str, Any]:
        """
        Get all context values as a dictionary.

        Returns:
            Dictionary of {name: value} for all context variables.
        """
        result = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                attr = getattr(self, attr_name)
                if isinstance(attr, ContextVar):
                    result[attr.name] = attr.get()
        return result
```

### Usage Example

```python
# ask_it/context.py

from chatcore.context import ContextManager, ContextVar


class AskITContext(ContextManager):
    """Ask-IT request context."""

    # User information
    user_id = ContextVar[str]("user_id", default="")
    user_email = ContextVar[str | None]("user_email", default=None)
    user_display_name = ContextVar[str]("user_display_name", default="")

    # Platform information
    platform = ContextVar[str]("platform", default="unknown")  # "slack", "api", etc.
    channel_id = ContextVar[str | None]("channel_id", default=None)

    # Request metadata
    request_id = ContextVar[str]("request_id", default="")
    timestamp = ContextVar[float]("timestamp", default=0.0)


# Singleton instance
context = AskITContext()


# In Slack handler
async def handle_message(event):
    context.user_id.set(event['user'])
    context.user_email.set(await get_user_email(event['user']))
    context.platform.set("slack")
    context.channel_id.set(event['channel'])
    context.request_id.set(generate_request_id())

    response = agent.process_message(event['text'])


# In CreateTicketTool
class CreateTicketTool(BaseTool):
    def _run(self, description: str):
        reporter = context.user_email.get()
        jira.create_issue(
            summary=description,
            reporter=reporter
        )
```

---

## Summary

### Why Context Variables Matter

| Problem | Solution |
|---------|----------|
| Tools need request metadata | Context variables provide it |
| Can't inject per-request data into tools | Context is thread-local, auto-isolated |
| Tool signatures get polluted | Context accessed without passing through signature |
| Global variables cause race conditions | Context variables are thread-safe |
| Tight coupling between layers | Context provides loose coupling |

### ChatCore Support Level

**Recommended: Level 2 (Utility Classes)**

```
ChatCore Provides:
├─ ContextVar[T] - Type-safe context variable wrapper
├─ ContextManager - Base class for context schemas
└─ Documentation and examples

Applications Provide:
├─ Specific context variable definitions
├─ Context schema (what keys/types)
└─ Integration with request handlers
```

### When to Use Context Variables

| Scenario | Use Context? |
|----------|--------------|
| User ID, session ID | ✅ Yes |
| Request tracing ID | ✅ Yes |
| Platform metadata (channel, etc.) | ✅ Yes |
| Authentication tokens | ✅ Yes |
| Tool configuration | ❌ No (use DI) |
| Static settings | ❌ No (use config) |

### Design Principles

1. **ChatCore is domain-agnostic** - Provides the pattern, not the keys
2. **Type-safe** - Use generics for type checking
3. **Optional** - Applications can use raw `contextvars` if they prefer
4. **Documented** - Clear examples of when/why to use
5. **Thread-safe** - Works with concurrent requests and async code
