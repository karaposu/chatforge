# VoxStream Refactor: State Machine + Synchronization Primitives

## Executive Summary

The current VoxStream adapter has reliability issues stemming from **state desynchronization** between components. This document proposes a refactor using a **State Machine** combined with **Synchronization Primitives** to create a robust, race-condition-free audio system.

---

## Part 1: Current Problems (High Level)

### The Core Issue: Multiple Sources of Truth

The audio system currently has **four different places** tracking state:

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   VoiceSession._state.is_playing    "Is API responding?"    │
│                    │                                         │
│   VoxStreamAdapter._capturing       "Are we capturing?"      │
│                    │                                         │
│   VoxStream.is_playing              "Is audio playing?"      │
│                    │                                         │
│   VoxStream internal state          "Hardware state"         │
│                                                              │
│   ──────────────────────────────────────────────────────    │
│   These can ALL be different at the same moment.            │
│   Which one is true? We don't know.                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Symptoms We've Experienced

| Problem | What Happened | Root Cause |
|---------|---------------|------------|
| "Already capturing" error | VoxStream thought it was capturing when our code said it wasn't | State mismatch |
| Barge-in doesn't work | Audio still playing but `is_playing` said `False` | API state ≠ Audio state |
| PortAudio errors | Hardware conflicts during mode switches | No transition management |
| "No audio recorded" | User pressed stop before capture was ready | No "ready" signal |

### The Workarounds (Technical Debt)

We've added **fragile workarounds** that paper over the real issues:

```python
# Workaround 1: Check multiple sources (hope one is right)
if session._state.is_playing or audio.is_playing:
    ...

# Workaround 2: Add delays and hope things settle
await asyncio.sleep(0.15)  # 150ms - why? who knows

# Workaround 3: Defensive operations
await audio.stop_capture()  # Stop even if not capturing, just in case
```

These work *most of the time* but fail unpredictably.

---

## Part 2: Requirements for a Solution

### What We Need

#### 1. Single Source of Truth
One place that definitively answers: "What is the audio system doing right now?"

```
❌ Current: "Check these 4 flags and hope they agree"
✅ Needed:  "Ask the state machine, it always knows"
```

#### 2. Know When Things Actually Happen
Currently we call a method and *hope* it completes. We need to *know*.

```
❌ Current: start_capture() ... sleep(500ms) ... maybe it's ready?
✅ Needed:  start_capture() ... wait_for_ready() ... guaranteed ready
```

#### 3. Prevent Race Conditions
Two operations shouldn't be able to corrupt each other.

```
❌ Current: Thread A starts capture while Thread B stops playback → chaos
✅ Needed:  Operations are atomic, can't interleave dangerously
```

#### 4. Reliable Mode Switching (Barge-In)
Switching from playback to capture should be one atomic operation.

```
❌ Current: stop_playback() ... delays ... start_capture() ... hope it works
✅ Needed:  switch_to_capture() → handles everything internally, guaranteed to work
```

### Requirements Summary

| Requirement | Description |
|-------------|-------------|
| **R1** | Single authoritative state |
| **R2** | Awaitable state transitions (know when complete) |
| **R3** | Thread-safe / race-condition-free |
| **R4** | Atomic compound operations |
| **R5** | Clear valid states and transitions |

---

## Part 3: The Solution — State Machine + Sync Primitives

### Why Two Concepts?

These solve **different but complementary** problems:

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   STATE MACHINE                 SYNC PRIMITIVES             │
│   ─────────────                 ────────────────             │
│                                                              │
│   Defines WHAT:                 Defines HOW:                 │
│   • What states exist           • How to safely change       │
│   • What transitions valid      • How to wait for states     │
│   • What state we're in         • How to prevent races       │
│                                                              │
│   Answers: "What's happening?"  Answers: "Is it safe now?"   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### The State Machine

#### States

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│   IDLE ─────────► CAPTURE_STARTING ─────────► CAPTURING      │
│    │                                              │           │
│    │                                              │           │
│    │                                              ▼           │
│    │              PLAYBACK_STARTING ◄───────── STOPPING      │
│    │                     │                        ▲           │
│    │                     ▼                        │           │
│    └──────────────► PLAYING ──────────────────────┘           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

| State | Meaning |
|-------|---------|
| `IDLE` | Audio system ready, nothing happening |
| `CAPTURE_STARTING` | Microphone initializing, not ready yet |
| `CAPTURING` | Actively receiving audio chunks |
| `PLAYBACK_STARTING` | Speaker initializing |
| `PLAYING` | Actively outputting audio |
| `STOPPING` | Transitioning back to idle |

#### Why a State Machine?

**Single Source of Truth:**
```python
# Instead of checking 4 different flags:
if session._state.is_playing or audio._capturing or voxstream.is_playing:

# Just ask the state machine:
if adapter.state == AudioState.PLAYING:
```

**Clear Valid Transitions:**
```python
# The state machine knows what's allowed:
IDLE → CAPTURE_STARTING  ✅ Valid
PLAYING → CAPTURING      ❌ Invalid (must stop first)
```

### The Synchronization Primitives

#### What Are They?

Python's `asyncio` provides tools for coordinating concurrent operations:

| Primitive | Purpose | Our Use |
|-----------|---------|---------|
| `asyncio.Lock` | Only one operation at a time | Protect state changes |
| `asyncio.Event` | Signal that something happened | "Capture is ready" |
| `asyncio.Condition` | Wait for a condition to be true | "Wait until state is X" |

#### Why We Need Them

**Without Lock — Race Condition:**
```
Time    Thread A              Thread B
────    ─────────             ─────────
 1      read state (IDLE)
 2                            read state (IDLE)
 3      set state = CAPTURING
 4                            set state = PLAYING
 5
        Result: State is PLAYING but Thread A thinks it's CAPTURING
        → "Already capturing" error later
```

**With Lock — Safe:**
```
Time    Thread A              Thread B
────    ─────────             ─────────
 1      acquire lock ✓
 2      read state (IDLE)
 3      set state = CAPTURING try acquire lock... BLOCKED
 4      release lock
 5                            acquire lock ✓
 6                            read state (CAPTURING)
 7                            "Can't play while capturing" → clean error
```

**Without Event — Guessing:**
```python
await start_capture()
await asyncio.sleep(0.5)  # Hope 500ms is enough???
# Maybe ready, maybe not
```

**With Event — Certainty:**
```python
await start_capture()
await capture_ready_event.wait()  # Returns when ACTUALLY ready
# Guaranteed ready
```

### How They Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    ┌──────────────────┐                         │
│                    │   STATE MACHINE  │                         │
│                    │                  │                         │
│                    │  state: IDLE     │                         │
│                    │         ↓        │                         │
│                    │  state: CAPTURING│                         │
│                    └────────┬─────────┘                         │
│                             │                                    │
│           ┌─────────────────┼─────────────────┐                 │
│           │                 │                 │                 │
│           ▼                 ▼                 ▼                 │
│    ┌──────────┐     ┌──────────────┐   ┌───────────┐           │
│    │   LOCK   │     │  CONDITION   │   │   EVENT   │           │
│    │          │     │              │   │           │           │
│    │ Protects │     │ wait_for_    │   │ capture_  │           │
│    │ changes  │     │ state()      │   │ ready     │           │
│    └──────────┘     └──────────────┘   └───────────┘           │
│                                                                  │
│  "Only one           "Block until        "Quick check:          │
│   change at           state is X"         is capture ready?"    │
│   a time"                                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Solving Our Requirements

| Requirement | How It's Solved |
|-------------|-----------------|
| **R1** Single source of truth | State machine's `_state` property |
| **R2** Awaitable transitions | `Condition.wait_for()` and `Event.wait()` |
| **R3** Race-condition-free | `Lock` around all state changes |
| **R4** Atomic operations | `Lock` held during compound operations |
| **R5** Valid transitions | State machine enforces allowed transitions |

---

## Part 4: Implementation Sketch

### Core Structure

```python
class AudioState(Enum):
    IDLE = "idle"
    CAPTURE_STARTING = "capture_starting"
    CAPTURING = "capturing"
    PLAYBACK_STARTING = "playback_starting"
    PLAYING = "playing"
    STOPPING = "stopping"


class VoxStreamAdapter:
    def __init__(self):
        # === STATE MACHINE ===
        self._state = AudioState.IDLE

        # === SYNC PRIMITIVES ===
        self._state_lock = asyncio.Lock()
        self._state_condition = asyncio.Condition()
        self._capture_ready = asyncio.Event()

        # === CALLBACKS ===
        self.on_state_changed: Callable[[AudioState, AudioState], None] | None = None
```

### Key Operations

#### Safe State Transitions

```python
async def _set_state(self, new_state: AudioState) -> None:
    """Change state safely with notifications."""
    async with self._state_lock:
        old_state = self._state
        self._state = new_state

        # Update convenience events
        self._capture_ready.set() if new_state == AudioState.CAPTURING else self._capture_ready.clear()

        # Notify waiters
        async with self._state_condition:
            self._state_condition.notify_all()

        # Fire callback
        if self.on_state_changed:
            self.on_state_changed(old_state, new_state)
```

#### Waiting for States

```python
async def wait_for_state(self, target: AudioState, timeout: float = 5.0) -> bool:
    """Wait until state machine reaches target state."""
    async with self._state_condition:
        try:
            await asyncio.wait_for(
                self._state_condition.wait_for(lambda: self._state == target),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False
```

#### Atomic Barge-In

```python
async def switch_to_capture(self) -> AsyncGenerator[bytes, None]:
    """Atomic: stop playback and start capture."""
    async with self._state_lock:  # Exclusive access
        # Stop playback if needed
        if self._state in (AudioState.PLAYING, AudioState.PLAYBACK_STARTING):
            self._voxstream.interrupt_playback(force=True)
            await self._wait_for_idle_internal()

        # Start capture
        return await self._start_capture_internal()
```

---

## Part 5: Benefits

### Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| State tracking | 4 flags, often disagree | 1 state machine, always consistent |
| Knowing when ready | `sleep()` and hope | `wait_for_state()` with certainty |
| Race conditions | Possible, cause random errors | Impossible, lock prevents them |
| Barge-in | Multiple steps, can fail | Single atomic operation |
| Debugging | "Which flag is wrong?" | "What state? What transition?" |

### Error Messages Improvement

```
Before: "Already capturing"  (but we thought we stopped?)

After:  "Invalid transition: cannot start capture in state PLAYING.
         Must be in IDLE. Current state history: IDLE → PLAYING (2s ago)"
```

---

## Part 6: Implementation Phases

### Phase 1: Add State Machine to Adapter
- Add `AudioState` enum
- Add `_state` property
- Add `_set_state()` method
- Keep existing logic working

### Phase 2: Add Sync Primitives
- Add `_state_lock`
- Add `_state_condition`
- Add `_capture_ready` event
- Wrap state changes with lock

### Phase 3: Add Waiting Methods
- `wait_for_state()`
- `wait_for_capture_ready()`
- Remove `asyncio.sleep()` workarounds

### Phase 4: Add Atomic Operations
- `switch_to_capture()`
- Update `TurnBasedMode` to use it
- Remove multi-step barge-in logic

### Phase 5: Propagate to VoxStream Library (Future)
- Move state machine into VoxStream itself
- Adapter becomes thin wrapper
- Other adapters benefit too

---

## Conclusion

The combination of **State Machine** and **Synchronization Primitives** directly addresses our core problems:

- **State Machine** gives us a single source of truth and clear semantics
- **Sync Primitives** make it thread-safe and awaitable

This is not over-engineering — it's the standard pattern for managing stateful async systems. The current bugs prove we need this level of rigor.
