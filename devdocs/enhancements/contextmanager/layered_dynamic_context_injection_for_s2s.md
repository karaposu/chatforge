# Layered Dynamic Context Injection for S2S

## The Core Problem

Text APIs and S2S APIs have fundamentally different context models:

```
Text API:
  Request 1: [Context A + Message] → Response
  Request 2: [Context B + Message] → Response    ← Context can change completely
  Request 3: [Context C + Message] → Response

S2S API:
  Session Start: [Context A in system_prompt]
       ↓
  User speaks → AI responds
  User speaks → AI responds      ← Same Context A, frozen
  User speaks → AI responds
       ↓
  Session End
```

**The problem:** In S2S, context is set once at session start. But real applications have context that changes during the conversation.

---

## Why Not Just Update System Prompt?

OpenAI Realtime API allows `session.update` to change the system prompt mid-session. Why not use that?

| Factor | `session.update` | Reality |
|--------|------------------|---------|
| Latency | ~300ms | Too slow for real-time state |
| Token cost | Re-counted every turn | Expensive for large contexts |
| Frequency | Can call anytime | But shouldn't call often |

If your context changes every few seconds (user looking around, state updating), you can't afford 300ms latency and high token costs on every change.

---

## The Solution: LDCI 5-Layer Model

LDCI (Layered Dynamic Context Injection) provides a structured approach with 5 layers, each with its own injection timing.

### The 5 Layers

| Layer | Name | Purpose | S2S Timing | Mechanism |
|-------|------|---------|------------|-----------|
| L1 | **Base** | AI identity, rules | SESSION_START | `system_prompt` at connect |
| L2 | **State** | Current situation | TURN_START | `add_text_item()` on speech_started |
| L3 | **Override** | Full replacement | ON_DEMAND | `session.update` |
| L4 | **Derived** | Background insights | AFTER_RESPONSE | `add_text_item()` after response_done |
| L5 | **Proactive** | App-triggered speech | ASAP | `add_text_item()` + `create_response()` |

---

## Layer 1: Base Context

**What:** The stable foundation - character personality, scenario setup, rules.

**When:** Set once at session start. Update only on major transitions.

**How:** `system_prompt` in connection config

```python
context = ContextManager()

# L1: Base context
context.add(ContextLayer(
    layer=Layer.BASE,
    content="""You are a helpful assistant.
    You speak concisely in a friendly tone.
    You have access to the user's calendar and preferences.""",
    inject_at=InjectTiming.SESSION_START
))

# At session start
await port.connect(VoiceSessionConfig(
    system_prompt=context.get_base()
))
```

**Characteristics:**
- Persists across all turns
- Authoritative (AI treats as instructions)
- Expensive to change (~300ms latency)
- Set once, rarely updated

---

## Layer 2: State Context

**What:** Rapidly changing state - what user is looking at, current data, recent events.

**When:** Inject just before AI processes user input (on `SPEECH_STARTED`).

**How:** `add_text_item()` via `compile_for(InjectTiming.TURN_START)`

```python
# L2: State context - changes per turn
context.add(ContextLayer(
    layer=Layer.STATE,
    content=f"[Room: {current_room}] [Looking at: {current_object}]",
    inject_at=InjectTiming.TURN_START,
    order=10
))

# In event loop
async for event in port.events():
    if event.type == "speech_started":
        # Inject L2 before user speech is processed
        text = context.compile_for(InjectTiming.TURN_START)
        if text:
            await port.add_text_item(text)
```

**Characteristics:**
- Fast (~30ms)
- Cheap (counted once, not every turn)
- Accumulates in conversation history
- Less authoritative than system prompt

**Key insight:** The AI sees this text as part of the conversation, so it has context when processing the user's speech that follows.

---

## Layer 3: Override Context

**What:** Complete context replacement for testing or major state changes.

**When:** QA testing specific scenarios, room/scene transitions, session recovery.

**How:** `session.update` when override is set

```python
# L3: Override - replaces base context
context.add(ContextLayer(
    layer=Layer.OVERRIDE,
    content=test_scenario_full_context
))

# get_base() now returns override content
await port.update_session(VoiceSessionConfig(
    system_prompt=context.get_base()
))
```

**Characteristics:**
- Same latency/cost as L1
- Replaces base context entirely
- Essential for testing
- Use sparingly in production

---

## Layer 4: Derived Context

**What:** Insights from background processing or async analysis.

**When:** After AI response completes (during conversation pauses).

**How:** `add_text_item()` via `compile_for(InjectTiming.AFTER_RESPONSE)`

```python
# Background task produces insight
async def profile_analyzer():
    while True:
        await asyncio.sleep(30)
        insight = analyze_user_behavior()
        context.add(ContextLayer(
            layer=Layer.DERIVED,
            content=f"[Insight: {insight}]",
            inject_at=InjectTiming.AFTER_RESPONSE
        ))

# In event loop
async for event in port.events():
    if event.type == "response_done":
        # Inject L4 after AI finishes
        text = context.compile_for(InjectTiming.AFTER_RESPONSE)
        if text:
            await port.add_text_item(text)
        context.clear_derived()  # Clear after injection
```

**Characteristics:**
- Arrives asynchronously
- Suggestive authority (AI may incorporate)
- Doesn't interrupt conversation flow
- Queued until safe injection moment

**Examples:**
- "User seems frustrated based on recent messages"
- "Pattern detected: user asks about pricing frequently"
- "Profile update: user prefers concise responses"

---

## Layer 5: Proactive Context

**What:** Context for app-triggered AI speech (when AI should speak without user input).

**When:** External events, timers, background processes trigger AI to speak.

**How:** `add_text_item()` + `create_response()` via `compile_for(InjectTiming.ASAP)`

```python
# External event triggers proactive
async def on_meeting_reminder(meeting):
    # L5: Proactive context
    context.add(ContextLayer(
        layer=Layer.PROACTIVE,
        content=f"[Alert: User has meeting '{meeting.title}' in 5 minutes. Inform them.]",
        inject_at=InjectTiming.ASAP
    ))

    # App triggers the response
    text = context.compile_for(InjectTiming.ASAP)
    await port.add_text_item(text)
    await port.create_response()

    context.clear_proactive()
```

**Key insight:** "Proactive" is always app-orchestrated. The AI never spontaneously decides to speak - the app decides when and provides context for what to say.

**Examples:**
- Meeting reminders (timer triggered)
- Alerts (event triggered)
- Suggestions based on idle time
- Notifications from external systems

---

## The Timing Strategy

**When to inject each layer?**

```
Timeline:
  [Session Start] ─────────────────────────────────────────────────────→
        │
        ▼
  ┌─────────────────┐
  │ L1: Base        │  ← system_prompt at connect
  └─────────────────┘
        │
        ▼
  ┌──── Turn 1 ─────────────────────────────────────────────────────────┐
  │  SPEECH_STARTED ──→ L2: State injected                              │
  │  [user speaking...]                                                  │
  │  [AI processing...]                                                  │
  │  [AI responding...]                                                  │
  │  RESPONSE_DONE ──→ L4: Derived injected (if any)                    │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──── Turn 2 ─────────────────────────────────────────────────────────┐
  │  SPEECH_STARTED ──→ L2: State injected (fresh)                      │
  │  ...                                                                 │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──── [Idle/External Event] ──────────────────────────────────────────┐
  │  L5: Proactive injected ──→ create_response() ──→ AI speaks         │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌──── [Major Transition] ─────────────────────────────────────────────┐
  │  L3: Override ──→ session.update() ──→ New base context             │
  └─────────────────────────────────────────────────────────────────────┘
```

Each layer has its **natural injection point**:
- L1 at session start (system_prompt)
- L2 on SPEECH_STARTED (before processing)
- L3 on explicit application decision (session.update)
- L4 on RESPONSE_DONE (after AI finishes)
- L5 on external triggers (ASAP + create_response)

---

## Complete S2S Example

```python
from chatforge.services.context import (
    ContextManager, ContextLayer, Layer, InjectTiming
)

class S2SSessionHandler:
    def __init__(self):
        self.context = ContextManager()
        self.port = None

    async def start_session(self, user_id: str):
        # L1: Base context
        self.context.add(ContextLayer(
            layer=Layer.BASE,
            content=await self.build_base_prompt(user_id),
            inject_at=InjectTiming.SESSION_START
        ))

        # Connect with L1
        await self.port.connect(VoiceSessionConfig(
            system_prompt=self.context.get_base(),
            voice="nova",
            vad_mode="server"
        ))

        # Start background analyzer for L4
        asyncio.create_task(self.profile_analyzer())

    async def handle_events(self):
        async for event in self.port.events():
            match event.type:
                case "speech_started":
                    # Update L2 state with fresh context
                    self.context.clear_state()
                    self.context.add(ContextLayer(
                        layer=Layer.STATE,
                        content=await self.get_current_state(),
                        inject_at=InjectTiming.TURN_START
                    ))

                    # Inject L2
                    text = self.context.compile_for(InjectTiming.TURN_START)
                    if text:
                        await self.port.add_text_item(text)

                case "response_done":
                    # Inject L4 derived insights
                    text = self.context.compile_for(InjectTiming.AFTER_RESPONSE)
                    if text:
                        await self.port.add_text_item(text)
                    self.context.clear_derived()

    async def profile_analyzer(self):
        """Background task for L4 derived context."""
        while True:
            await asyncio.sleep(30)
            insight = await self.analyze_conversation()
            if insight:
                self.context.add(ContextLayer(
                    layer=Layer.DERIVED,
                    content=f"[Insight: {insight}]",
                    inject_at=InjectTiming.AFTER_RESPONSE
                ))

    async def on_major_transition(self, new_scene: dict):
        """L3: Override for major transitions."""
        self.context.add(ContextLayer(
            layer=Layer.OVERRIDE,
            content=self.build_scene_prompt(new_scene)
        ))

        await self.port.update_session(VoiceSessionConfig(
            system_prompt=self.context.get_base()
        ))

    async def on_external_alert(self, alert: str):
        """L5: Proactive for external events."""
        self.context.add(ContextLayer(
            layer=Layer.PROACTIVE,
            content=f"[Alert: {alert}. Inform the user.]",
            inject_at=InjectTiming.ASAP
        ))

        text = self.context.compile_for(InjectTiming.ASAP)
        await self.port.add_text_item(text)
        await self.port.create_response()

        self.context.clear_proactive()
```

---

## Context Formatting

**Don't dump raw JSON.** Format for LLM readability:

```python
# Bad - LLM has to parse JSON
await port.add_text_item(
    '{"location": "kitchen", "time": "14:30", "user_mood": "frustrated"}'
)

# Good - Human-readable, LLM-friendly
await port.add_text_item(
    "[Context: User is in the kitchen. Time is 2:30 PM. User seems frustrated.]"
)
```

Use bracketed prefixes like `[Context:]`, `[State:]`, `[Update:]`, `[Insight:]` to signal these are system injections, not user speech.

---

## Accumulation Problem

Text items accumulate in conversation history. After many injections:

```
Turn 1: [State: Room A, looking at painting]
User: "Hello"
AI: "Hi there!"

Turn 2: [State: Room A, looking at mirror]
User: "What is this?"
AI: "That's a mirror"

Turn 3: [State: Room B, looking at door]
[Insight: User seems curious]
User: "Where am I?"
AI: "You're in Room B"

... history keeps growing with context entries
```

**Mitigations:**

1. **Keep injections short** - Only include what's changed or immediately relevant
2. **Use delta updates** - `[Update: moved to Room B]` not full state each time
3. **Rely on base context** - Put stable info in system_prompt, not repeated text items
4. **Clear after injection** - `context.clear_derived()` after injecting L4
5. **Accept the trade-off** - Some accumulation is fine; it's still cheaper than session.update

---

## The 5-Layer Decision Tree

```
Is this context stable for the entire session?
  YES → Layer 1 (Base - system_prompt at start)
  NO ↓

Does it change frequently (every turn)?
  YES → Layer 2 (State - add_text_item on speech_started)
  NO ↓

Is it a major transition or test scenario?
  YES → Layer 3 (Override - session.update to replace)
  NO ↓

Is it a background insight (async analysis)?
  YES → Layer 4 (Derived - add_text_item after response_done)
  NO ↓

Should AI speak without user input (external trigger)?
  YES → Layer 5 (Proactive - add_text_item + create_response)
```

---

## S2S Statefulness: What It Gives vs What You Provide

### What S2S Maintains Automatically

Within a session, the provider tracks:

```
Session State (managed by provider):
├── system_prompt (your base instructions)
├── conversation_history
│   ├── User said: "Hello"
│   ├── AI said: "Hi there!"
│   ├── [Your injected context]
│   └── ... (all turns preserved)
└── tool_definitions + past tool results
```

**This is different from Text API** where you must send conversation history with every request.

### What S2S Does NOT Maintain

```
External State (you must inject):
├── Application state (game state, UI state, what user is looking at)
├── Real-time external data (time, weather, alerts)
├── State changes that happened outside the conversation
├── Background analysis insights
└── Cross-session context (from your DB)
```

### The Hybrid Reality

```
What S2S Gives You (free):
  - Conversation continuity within session
  - No need to re-send message history
  - Tool results persist

What You Provide via LDCI:
  - L1: Base identity (system_prompt)
  - L2: Dynamic app state (per-turn)
  - L3: Full replacement (major transitions)
  - L4: Background insights (async)
  - L5: Proactive triggers (external events)
```

### Conclusion

**S2S statefulness helps with conversation continuity but not application context.**

- S2S remembers what was **SAID** (conversation history)
- You inject what is **HAPPENING** (application state, external events)
- LDCI provides the structure for when and how to inject each type

---

## Summary

| Layer | Method | Speed | Cost | Timing | Use Case |
|-------|--------|-------|------|--------|----------|
| **L1 Base** | `system_prompt` | Slow | High | SESSION_START | Character, rules, stable setup |
| **L2 State** | `add_text_item()` | Fast | Low | TURN_START | Changing state, per-turn context |
| **L3 Override** | `session.update` | Slow | High | ON_DEMAND | Testing, major transitions |
| **L4 Derived** | `add_text_item()` | Fast | Low | AFTER_RESPONSE | Background insights, async analysis |
| **L5 Proactive** | `add_text_item()` + `create_response()` | Fast | Low | ASAP | External triggers, app-initiated speech |

**The key insight:** LDCI bridges the gap between "frozen context at session start" and "dynamic context per request" - giving S2S applications the context-awareness they need through structured, timed injection of 5 distinct layers.
