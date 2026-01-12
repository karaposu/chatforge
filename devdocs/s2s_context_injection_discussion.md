# S2S Context Injection: The Universal Challenge

## The Problem Statement

**Every application that uses Speech-to-Speech (S2S) with rich context faces the same fundamental mismatch:**

```
Text API:    Request → [Full Context + Message] → Response → Done
                       ↑ Context injected fresh each time

S2S API:     Session Start → [Context in system_prompt] → Conversation Loop...
                              ↑ Context FROZEN at session start
```

This document examines this problem across two real applications and shows how LDCI (Layered Dynamic Context Injection) addresses it.

---

## Case Study 1: Chamber Protocol (Siluet)

### Application
A psychological thriller game where an AI character (Siluet) guides players through puzzle rooms. The AI's value comes from deep context-awareness.

### Context Structure (~8KB per request)
```
player_progress:
  - current_loop, total_loops
  - rooms_completed, puzzles_solved
  - extracted_information (personality analysis, triggers, fears)

room_context:
  - room_name, room_type
  - available_objects (with detailed descriptions)
  - active_puzzle, puzzle_solution (SECRET)
  - time_in_room

visual_context:
  - currently_looking_at (changes every few seconds)
  - last_10_seconds_viewed

ai_character_response_parameters:
  - puzzle_secrets_disclosure_level
  - conversational_intent
  - emotional_state
  - conversation_power_distribution
```

### The S2S Challenge
- **visual_context** changes constantly as player looks around
- AI needs to know what painting you're looking at when you ask "What is this?"
- Disclosure levels change based on puzzle progress
- Room transitions require complete context replacement

### Current Text API Behavior
Each request bundles EVERYTHING. The game client has full control over exactly what context the AI sees. Testing is easy: load `art_room/1.json`, send message, verify response.

---

## Case Study 2: KANKA (Social Architect)

### Application
A voice-first AI companion that builds a "personal memory graph" of users over time, then facilitates introductions between people with genuine shared experiences.

### Context Structure (grows over time)
```
user_profile:
  - personality_traits (inferred)
  - communication_style
  - trust_level (can degrade if user breaks promises)

memory_graph:
  - anecdotes (stories user has shared)
  - routines (daily patterns)
  - moods (emotional history)
  - preferences (learned over time)
  - connections (other users, consent status)

social_context:
  - pending_introductions
  - community_events (matching user's style)
  - recent_interactions_with_others
```

### The S2S Challenge
- Voice is the PRIMARY interface (not a secondary modality)
- Memory graph grows DURING the conversation as user shares anecdotes
- AI must remember what was said 5 minutes ago AND 5 days ago
- Trust/personality inference happens in real-time
- Context size grows unbounded over user lifetime

### Unique KANKA Requirements
- **Bi-directional context**: Not just injecting context, but EXTRACTING new context from conversation
- **Long-term memory**: Can't fit entire memory graph in system_prompt
- **Real-time personality modeling**: AI's understanding of user evolves mid-session

---

## The Common Problem: Session-Based Context Freeze

Both applications suffer from the same architectural tension:

| Aspect | Text API | S2S API |
|--------|----------|---------|
| Context timing | Per-request | Per-session |
| Context mutability | Full replacement each time | Expensive to update |
| Testing | Easy (inject any context) | Hard (session already started) |
| Dynamic state | Natural fit | Requires workarounds |

### Why This Matters

**Without dynamic context injection, S2S AI becomes a generic chatbot.**

- Siluet can't know what painting you're looking at
- KANKA can't remember the anecdote you shared 2 minutes ago
- Both lose their core value proposition

---

## OpenAI Realtime API: Available Mechanisms

| Mechanism | Latency | Token Cost | Persistence | Use Case |
|-----------|---------|------------|-------------|----------|
| `session.update` (system_prompt) | ~300ms | High (counted every turn) | Session-wide | Base character, major changes |
| `add_text_item()` | ~30ms | Lower (one-time) | Accumulates in history | Dynamic updates |
| `send_text()` | ~30ms | Lower | Accumulates + triggers response | User text input |
| Tool calls | Variable | Variable | Stateless | Query external systems |

### The Key Insight

**`add_text_item()` is the secret weapon.**

It allows injecting context WITHOUT:
- The ~300ms latency of session.update
- The high token cost of system_prompt repetition
- Triggering an AI response

---

## Solution: LDCI (Layered Dynamic Context Injection)

LDCI provides a structured approach to context injection that works for both HTTP and S2S.

### The 5 Layers

| Layer | Purpose | S2S Timing |
|-------|---------|------------|
| L1 Base | AI identity, rules | Session start (system_prompt) |
| L2 State | Current situation | Turn start (add_text_item) |
| L3 Override | Full replacement | On-demand (session.update) |
| L4 Derived | Background insights | After response (add_text_item) |
| L5 Proactive | App-triggered AI speech | ASAP (add_text_item + create_response) |

### How It Maps to S2S

```python
from chatforge.services.context import (
    ContextManager, ContextLayer, Layer, InjectTiming
)

# Create context manager (same for HTTP and S2S)
context = ContextManager()

# L1: Base context - inject at session start
context.add(ContextLayer(
    layer=Layer.BASE,
    content=SILUET_PROFILE + GAME_RULES,
    inject_at=InjectTiming.SESSION_START
))

# L2: Room context - inject each turn
context.add(ContextLayer(
    layer=Layer.STATE,
    content=room_context,
    inject_at=InjectTiming.TURN_START,
    order=10
))

# L2: Visual context - inject each turn (changes constantly)
context.add(ContextLayer(
    layer=Layer.STATE,
    content=f"Player is looking at: {currently_looking_at}",
    inject_at=InjectTiming.TURN_START,
    order=20
))

# Connect with L1
await port.connect(VoiceSessionConfig(
    system_prompt=context.get_base()  # L1 only
))

# Event loop - inject context at right moments
async for event in port.events():
    if event.type == "speech_started":
        # Inject L2 state layers BEFORE user speech is processed
        text = context.compile_for(InjectTiming.TURN_START)
        if text:
            await port.add_text_item(text)

    if event.type == "response_done":
        # Could inject L4 derived insights here
        text = context.compile_for(InjectTiming.AFTER_RESPONSE)
        if text:
            await port.add_text_item(text)

    # Handle visual context updates (from game)
    if event.type == "visual_context_changed":
        context.clear_state()
        context.add(ContextLayer(
            layer=Layer.STATE,
            content=f"Player is looking at: {event.data}",
            inject_at=InjectTiming.TURN_START,
            order=20
        ))
```

### The Key Moment: SPEECH_STARTED

When the user starts speaking, LDCI injects current state:

```
User starts speaking → SPEECH_STARTED event
                            ↓
                    context.compile_for(TURN_START)
                            ↓
                    "[Room: Art Gallery] [Looking at: Broken Mirror]"
                            ↓
                    port.add_text_item(text)
                            ↓
                    User's speech is processed WITH fresh context
```

This ensures the AI knows what the user is looking at when they ask "What is this?"

---

## Context Extraction: The KANKA Pattern

KANKA has a unique requirement: **extracting** context from conversation, not just injecting it.

### The Problem

During a voice session, user shares:
> "I went to this amazing coffee shop yesterday, the one near the park with the blue awning..."

KANKA needs to:
1. Recognize this as an anecdote worth remembering
2. Extract structured data (location, description, sentiment)
3. Update the memory graph
4. Make this available for future context injection

### Solution: Tool-Based Extraction

Tools are a port concern (not LDCI), but work alongside context injection:

```python
MEMORY_TOOLS = [
    ToolDefinition(
        name="remember_anecdote",
        description="Store an anecdote the user shared",
        parameters={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "location": {"type": "string"},
                "people": {"type": "array", "items": {"type": "string"}},
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            }
        }
    )
]

# Handle tool calls
async for event in port.events():
    if event.type == "tool_call":
        if event.data["name"] == "remember_anecdote":
            # Store in memory graph
            await memory_graph.add_anecdote(event.data["arguments"])

            # Later, this can become L4 derived context
            context.add(ContextLayer(
                layer=Layer.DERIVED,
                content=f"User recently mentioned: {event.data['arguments']['summary']}",
                inject_at=InjectTiming.AFTER_RESPONSE
            ))
```

---

## HTTP vs S2S: Same ContextManager, Different Timing

### HTTP Pattern (Chamber Protocol current)

```python
context = ContextManager()

# Add all layers
context.add(ContextLayer(layer=Layer.BASE, content=system_prompt))
context.add(ContextLayer(layer=Layer.STATE, content=room_context))
context.add(ContextLayer(layer=Layer.STATE, content=visual_context))

# Compile ALL layers (timing ignored)
compiled = context.compile(audio_tags=True)

# Build request
response = llm.invoke([
    SystemMessage(content=context.get_base()),
    *history,
    HumanMessage(content=compiled + "\n" + user_input)
])
```

### S2S Pattern (Chamber Protocol future)

```python
context = ContextManager()

# Same layers, but with timing
context.add(ContextLayer(
    layer=Layer.BASE,
    content=system_prompt,
    inject_at=InjectTiming.SESSION_START
))
context.add(ContextLayer(
    layer=Layer.STATE,
    content=room_context,
    inject_at=InjectTiming.TURN_START
))
context.add(ContextLayer(
    layer=Layer.STATE,
    content=visual_context,
    inject_at=InjectTiming.TURN_START
))

# Connect with L1
await port.connect(system_prompt=context.get_base())

# Inject L2 at turn start
async for event in port.events():
    if event.type == "speech_started":
        await port.add_text_item(context.compile_for(InjectTiming.TURN_START))
```

**Same ContextManager API. Different injection timing.**

---

## Testing Considerations

### The Testing Pattern

LDCI makes S2S testing easier by providing explicit context control:

```python
async def test_siluet_wrong_painting_response():
    context = ContextManager()

    # Load test scenario
    context.add(ContextLayer(
        layer=Layer.BASE,
        content=load_json("test_cases/base_context.json")
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=load_json("test_cases/art_room_wrong_painting.json")
    ))

    # Connect with full context
    await port.connect(system_prompt=context.get_base())
    await port.add_text_item(context.compile())

    # Send test utterance
    await port.send_text("What am I looking at?")

    # Verify response
    response = await wait_for_response()
    assert "wrong" in response.lower() or "not the one" in response.lower()
```

### L3 Override for Testing

For testing specific scenarios, use L3 Override to replace entire context:

```python
# Override replaces base context
context.add(ContextLayer(
    layer=Layer.OVERRIDE,
    content=test_scenario_full_context
))

# get_base() now returns override content
await port.update_session(VoiceSessionConfig(
    system_prompt=context.get_base()
))
```

---

## Summary: How LDCI Solves S2S Context Injection

### The Problem
S2S freezes context at session start. Applications need dynamic context updates.

### The Solution
LDCI provides:

1. **Layered context** - Different layers for different purposes
2. **Timing metadata** - Each layer knows WHEN it should be injected
3. **compile_for(timing)** - Get layers matching specific timing
4. **Same API for HTTP and S2S** - ContextManager works for both

### The Pattern

```python
# Session start: L1 via system_prompt
await port.connect(system_prompt=context.get_base())

# Turn start: L2 via add_text_item
if event.type == "speech_started":
    await port.add_text_item(context.compile_for(InjectTiming.TURN_START))

# After response: L4 via add_text_item
if event.type == "response_done":
    text = context.compile_for(InjectTiming.AFTER_RESPONSE)
    if text:
        await port.add_text_item(text)

# Proactive: L5 via add_text_item + create_response
await port.add_text_item(context.compile_for(InjectTiming.ASAP))
await port.create_response()
```

### The Key Principle

**S2S context injection is not about replicating the text API's stateless model.**

It's about designing a layered context strategy where:
- L1 Base provides stable identity (system_prompt at session start)
- L2 State provides dynamic context (add_text_item at turn start)
- L4 Derived provides background insights (add_text_item after response)
- L5 Proactive enables app-triggered AI speech

LDCI provides the structure. The app orchestrates the timing. The port executes the injection.

---

## Open Questions

1. **Context accumulation limits**: How many text items before performance degrades?

2. **Provider differences**: Does Gemini Live / other providers support similar patterns?

3. **Context compression**: Should LDCI provide summarization utilities?

4. **State persistence**: Should ContextManager support serialization for session recovery?

5. **Scheduled timing**: How to implement `InjectTiming.SCHEDULED` (every N turns)?
