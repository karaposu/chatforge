# ContextManager & ContextLayer Usage Guide

## Overview

ContextManager and ContextLayer provide a structured approach to managing LLM context in applications with complex, multi-layered prompts. Instead of manually concatenating strings or using rigid template systems, this approach treats each piece of context as a first-class object with metadata.

## When to Use

### Good Fit

- **Multi-source context**: Applications that combine context from multiple sources (user state, environment, history, external data)
- **Conditional context**: When different modes or states require different context combinations
- **Dynamic prompts**: Context that changes per-request based on application state
- **Complex AI characters**: Personalities with behavioral parameters, constraints, and situational awareness
- **S2S (Speech-to-Speech) applications**: Real-time voice interactions requiring timed context injection
- **Interactive experiences**: Games, simulations, or assistants with rich situational context

### Not Needed

- Simple Q&A chatbots with static system prompts
- Single-purpose tools with fixed prompts
- Applications with < 3 context components

## Core Concepts

### ContextLayer

A single piece of context with metadata:

```python
from chatforge.services.context import ContextLayer, Layer

layer = ContextLayer(
    layer=Layer.STATE,           # Layer type (BASE, STATE, OVERRIDE, etc.)
    content="User is in lobby",  # The actual context string
    prefix="=== LOCATION ===",   # Header prepended to content
    default="Unknown location",  # Fallback if content is empty
    order=10,                    # Sort priority (lower = earlier in output)
)
```

### ContextManager

Orchestrates multiple layers:

```python
from chatforge.services.context import ContextManager

context_manager = ContextManager()
context_manager.add(layer1)
context_manager.add(layer2)
context_manager.add(layer3)

# Compile all layers into a single string (sorted by order)
compiled = context_manager.compile()
```

## Usage Patterns

### Pattern 1: Create → Add → Compile

The recommended pattern separates layer creation from adding:

```python
# 1. Create layers with descriptive names
cl_user_profile = ContextLayer(
    layer=Layer.STATE,
    content=user_profile_data,
    prefix="=== USER PROFILE ===",
    order=10,
)

cl_environment = ContextLayer(
    layer=Layer.STATE,
    content=environment_data,
    prefix="=== ENVIRONMENT ===",
    order=20,
)

cl_history = ContextLayer(
    layer=Layer.STATE,
    content=conversation_history,
    prefix="=== CONVERSATION HISTORY ===",
    order=30,
)

# 2. Add to manager
context_manager = ContextManager()
context_manager.add(cl_user_profile)
context_manager.add(cl_environment)
context_manager.add(cl_history)

# 3. Compile and use
compiled_context = context_manager.compile()
```

### Pattern 2: Conditional Layers

Add different layers based on application mode:

```python
# Core layers (always present)
context_manager.add(cl_user_profile)
context_manager.add(cl_environment)

# Mode-specific layers
if proactive_mode:
    cl_trigger = ContextLayer(
        layer=Layer.STATE,
        content=trigger_event,
        prefix="=== TRIGGER EVENT ===",
        order=50,
    )
    context_manager.add(cl_trigger)
else:
    cl_user_input = ContextLayer(
        layer=Layer.STATE,
        content=user_message,
        prefix="=== USER INPUT ===",
        order=50,
    )
    context_manager.add(cl_user_input)

# Feature flags
if enable_verbose_mode:
    cl_debug = ContextLayer(
        layer=Layer.STATE,
        content="Include detailed reasoning in response.",
        order=90,
    )
    context_manager.add(cl_debug)
```

### Pattern 3: SystemMessage + HumanMessage Split

For LLMs that support separate system/user messages:

```python
# Static system context (doesn't need ContextManager)
SYSTEM_PROMPT = """You are an AI assistant..."""

# Dynamic per-turn context (uses ContextManager)
context_manager = ContextManager()
context_manager.add(cl_user_state)
context_manager.add(cl_environment)
context_manager.add(cl_constraints)
context_manager.add(cl_instruction)

# Invoke with split messages
response = llm.invoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=context_manager.compile()),
])
```

### Pattern 4: Default Fallbacks

Use `default` for layers that need fallback content:

```python
cl_character = ContextLayer(
    layer=Layer.STATE,
    content=custom_character or "",  # May be empty
    prefix="=== CHARACTER ===",
    default=DEFAULT_CHARACTER_PROFILE,  # Used when content is empty
    order=10,
)
```

## Layer Properties

| Property | Type | Description |
|----------|------|-------------|
| `layer` | `Layer` | Layer type: `BASE`, `STATE`, `OVERRIDE`, `DERIVED`, `PROACTIVE` |
| `content` | `str` | The actual context string |
| `prefix` | `str` | Header text prepended to content (e.g., `"=== SECTION ==="`) |
| `default` | `str` | Fallback content when `content` is empty |
| `order` | `int` | Sort priority (lower values appear first) |
| `inject_at` | `InjectTiming` | For S2S: when to inject (`TURN_START`, `AFTER_RESPONSE`, etc.) |

## Order Strategy

Use consistent order ranges for different context categories:

```
Order Ranges:
├── 10-20:  Identity/Profile layers
├── 30-40:  Environment/State layers
├── 50-60:  Behavioral parameters
├── 70:     User input or trigger
├── 80:     Constraints
├── 85-95:  Optional modifiers (audio, language, etc.)
└── 100:    Final instruction
```

The `order` field determines final position regardless of when layers are added:

```python
# Added in random order...
context_manager.add(ContextLayer(content="C", order=30))
context_manager.add(ContextLayer(content="A", order=10))
context_manager.add(ContextLayer(content="B", order=20))

# ...but compiled in order:
context_manager.compile()  # → "A\n\nB\n\nC"
```

## S2S (Speech-to-Speech) Applications

> **Note**: S2S integration is planned but not yet tested. The API below is conceptual.

For real-time voice applications, ContextLayer supports timed injection via `inject_at`:

```python
from chatforge.services.context import InjectTiming

cl_turn_context = ContextLayer(
    layer=Layer.STATE,
    content=current_situation,
    inject_at=InjectTiming.TURN_START,  # When user starts speaking
    order=10,
)

cl_post_response = ContextLayer(
    layer=Layer.DERIVED,
    content=analysis_results,
    inject_at=InjectTiming.AFTER_RESPONSE,  # After AI responds
    order=10,
)

cl_proactive = ContextLayer(
    layer=Layer.PROACTIVE,
    content=alert_message,
    inject_at=InjectTiming.ASAP,  # Inject immediately
    order=10,
)
```

Available timings: `SESSION_START`, `TURN_START`, `AFTER_RESPONSE`, `SCHEDULED`, `ASAP`, `ON_EVENT`

Use `compile_for(timing)` to get layers for a specific moment:

```python
turn_context = context_manager.compile_for(InjectTiming.TURN_START)
post_context = context_manager.compile_for(InjectTiming.AFTER_RESPONSE)
```

For standard HTTP chat, `inject_at` is ignored—all layers compile together via `compile()`.

## Best Practices

### Naming Convention

Use `cl_` prefix for ContextLayer variables:

```python
cl_user_profile = ContextLayer(...)
cl_environment = ContextLayer(...)
cl_instruction = ContextLayer(...)
```

### Keep Static Content Out

Don't put truly static content in ContextManager:

```python
# Good - static system prompt stays separate
SYSTEM_PROMPT = "You are an AI assistant..."
response = llm.invoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=context_manager.compile()),
])

# Avoid - static content in manager adds complexity
context_manager.add(ContextLayer(layer=Layer.BASE, content=SYSTEM_PROMPT))
```

### Use Prefix for Structure

Prefixes help the LLM understand context sections:

```python
# Good - clear section markers
cl_history = ContextLayer(
    content=history_text,
    prefix="=== CONVERSATION HISTORY ===",
    order=30,
)

# Less clear - no prefix
cl_history = ContextLayer(
    content=history_text,
    order=30,
)
```

### Handle Empty Content

Use `default` or check content before adding:

```python
# Option 1: Use default
cl_optional = ContextLayer(
    content=maybe_empty or "",
    default="",  # Empty default means layer renders nothing
    order=50,
)

# Option 2: Conditional add
if optional_content:
    cl_optional = ContextLayer(content=optional_content, order=50)
    context_manager.add(cl_optional)
```

## Example: Complete Implementation

```python
from chatforge.services.context import ContextManager, ContextLayer, Layer
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = """You are an AI assistant in an interactive experience."""

def generate_response(
    user_profile: str,
    environment: str,
    conversation_history: str,
    user_input: str,
    language: str = None,
    verbose_mode: bool = False,
) -> str:
    # Create layers
    cl_profile = ContextLayer(
        layer=Layer.STATE,
        content=user_profile or "",
        prefix="=== USER PROFILE ===",
        order=10,
    )

    cl_environment = ContextLayer(
        layer=Layer.STATE,
        content=environment or "",
        prefix="=== ENVIRONMENT ===",
        order=20,
    )

    cl_history = ContextLayer(
        layer=Layer.STATE,
        content=conversation_history or "",
        prefix="=== CONVERSATION HISTORY ===",
        order=30,
    )

    cl_input = ContextLayer(
        layer=Layer.STATE,
        content=user_input,
        prefix="=== USER INPUT ===",
        order=50,
    )

    cl_instruction = ContextLayer(
        layer=Layer.STATE,
        content="Generate a helpful response based on the context above.",
        prefix="=== INSTRUCTION ===",
        order=100,
    )

    # Build context manager
    context_manager = ContextManager()
    context_manager.add(cl_profile)
    context_manager.add(cl_environment)
    context_manager.add(cl_history)
    context_manager.add(cl_input)

    # Conditional layers
    if language:
        cl_language = ContextLayer(
            layer=Layer.STATE,
            content=f"Respond in: {language}",
            prefix="=== LANGUAGE ===",
            order=90,
        )
        context_manager.add(cl_language)

    if verbose_mode:
        cl_verbose = ContextLayer(
            layer=Layer.STATE,
            content="Include detailed reasoning.",
            order=95,
        )
        context_manager.add(cl_verbose)

    context_manager.add(cl_instruction)

    # Invoke LLM
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context_manager.compile()),
    ])

    return response.content
```

## Summary

| Concept | Purpose |
|---------|---------|
| `ContextLayer` | Single context piece with metadata |
| `ContextManager` | Orchestrates multiple layers |
| `prefix` | Section header for clarity |
| `default` | Fallback when content empty |
| `order` | Sort priority (lower = first) |
| `compile()` | Merge all layers into string |
| `compile_for(timing)` | S2S: merge layers for specific timing |

The key insight is treating context as **structured data with metadata** rather than raw strings. This enables conditional assembly, consistent ordering, and clear separation of concerns.

## Context Builder Pattern

For applications with complex context requirements, separate context construction from LLM invocation using the Builder pattern.

### Why Use a Builder?

| Without Builder | With Builder |
|-----------------|--------------|
| Service serializes data to strings | Builder takes typed objects |
| LLM service has 15+ parameters | LLM service has 2-3 parameters |
| Context logic mixed with DB logic | Context logic isolated |
| Hard to test prompt structure | Can unit test builder alone |
| One-off context construction | Reusable across HTTP and S2S |

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Service Layer  │────▶│  Context Builder │────▶│ LLM Service │
│  (orchestration)│     │  (prompt logic)  │     │ (invocation)│
└─────────────────┘     └──────────────────┘     └─────────────┘
        │                        │                      │
   - Fetch from DB          - Create layers        - Get LLM
   - Call builder           - Handle modes         - Invoke with
   - Save response          - Return Manager         System + Human
```

### Builder Implementation

```python
# context_builders/my_character_context.py
class MyCharacterContextBuilder:
    """Builds ContextManager for a specific AI character."""

    def __init__(self, request: MyRequest, conversation: str = ""):
        self.request = request
        self.conversation = conversation

    def build(self) -> ContextManager:
        """Build and return ContextManager with all layers."""
        context_manager = ContextManager()

        # Core layers (always present)
        context_manager.add(self._build_profile_layer())
        context_manager.add(self._build_state_layer())
        context_manager.add(self._build_conversation_layer())

        # Mode-specific layers
        if self.request.proactive_trigger:
            context_manager.add(self._build_proactive_layer())
        else:
            context_manager.add(self._build_user_input_layer())

        # Optional layers
        if self.request.language:
            context_manager.add(self._build_language_layer())

        context_manager.add(self._build_instruction_layer())

        return context_manager

    def _build_profile_layer(self) -> ContextLayer:
        return ContextLayer(
            layer=Layer.STATE,
            content=self._format_profile(self.request.profile),
            prefix="=== CHARACTER PROFILE ===",
            default=DEFAULT_PROFILE,
            order=10,
        )

    # ... other layer builders ...
```

### LLM Service (Thin)

The LLM service becomes a thin wrapper focused only on invocation:

```python
# llm_service.py
class LLMService:
    def generate_with_context(
        self,
        system_prompt: str,
        context_manager: ContextManager,
        model: str = None,
    ) -> str:
        """Generate response using pre-built ContextManager."""
        llm = self._get_llm(model)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context_manager.compile()),
        ])
        return response.content
```

### Service Layer (Orchestration)

The service layer focuses on orchestration, not prompt engineering:

```python
# services/chat_service.py
class ChatService:
    def process_request(self):
        # 1. Fetch data
        conversation = self._fetch_conversation()

        # 2. Build context (builder handles all prompt logic)
        builder = MyCharacterContextBuilder(self.request, conversation)
        context_manager = builder.build()

        # 3. Generate response
        response = self.llm_service.generate_with_context(
            system_prompt=SYSTEM_PROMPT,
            context_manager=context_manager,
            model=self.request.model,
        )

        # 4. Save and return
        self._save_response(response)
        return response
```

### Benefits

1. **Testability**: Unit test the builder without mocking LLM calls
   ```python
   def test_proactive_mode_adds_trigger_layer():
       request = MyRequest(proactive_trigger="Say hello")
       builder = MyCharacterContextBuilder(request)
       ctx = builder.build()
       compiled = ctx.compile()
       assert "=== PROACTIVE TRIGGER ===" in compiled
   ```

2. **S2S Ready**: Builder returns `ContextManager`, not compiled string
   ```python
   # HTTP: compile everything
   compiled = context_manager.compile()

   # S2S: compile by timing
   turn_ctx = context_manager.compile_for(InjectTiming.TURN_START)
   ```

3. **Reusability**: Same builder for different entry points
   ```python
   # HTTP endpoint
   builder = MyCharacterContextBuilder(http_request, conversation)

   # WebSocket handler (future S2S)
   builder = MyCharacterContextBuilder(ws_request, conversation)
   ```

4. **Type Safety**: Builder takes typed objects, handles serialization internally
   ```python
   # Builder handles formatting
   def _format_profile(self, profile: ProfileModel) -> str:
       return json.dumps(profile.model_dump(), indent=2)
   ```

### When to Use a Builder

| Scenario | Use Builder? |
|----------|--------------|
| 3+ context sources | Yes |
| Conditional logic (modes, flags) | Yes |
| Multiple AI characters | Yes (one builder each) |
| Future S2S planned | Yes |
| Simple static prompt | No |
| Single-use context | No |
