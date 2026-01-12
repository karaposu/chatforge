"""
Core types for LDCI (Layered Dynamic Context Injection).

This module defines the fundamental enums and types used throughout
the context management system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


__all__ = [
    "Layer",
    "Authority",
    "Stability",
    "InjectTiming",
    "CompileOptions",
]


class Layer(Enum):
    """
    The 5 context layers in LDCI.

    Each layer serves a distinct purpose in context injection:
    - BASE: Stable foundation (AI identity, rules)
    - STATE: Dynamic per-turn context (current situation)
    - OVERRIDE: Full context replacement (testing, major transitions)
    - DERIVED: Background-computed insights (async analysis)
    - PROACTIVE: App-triggered AI speech (external events)
    """

    BASE = "base"  # L1: Stable foundation
    STATE = "state"  # L2: Per-turn dynamic state
    OVERRIDE = "override"  # L3: Full replacement
    DERIVED = "derived"  # L4: Background insights
    PROACTIVE = "proactive"  # L5: App-triggered speech


class Authority(Enum):
    """
    How the AI should treat this context (design-time metadata).

    This is informational - helps developers understand intent,
    but doesn't affect runtime behavior.
    """

    DIRECTIVE = "directive"  # Must follow (rules, constraints)
    INFORMATIVE = "informative"  # Should consider (state, facts)
    SUGGESTIVE = "suggestive"  # May incorporate (hints, insights)


class Stability(Enum):
    """
    How often context changes (informational metadata).

    Helps developers understand the expected lifecycle of context.
    """

    STATIC = "static"  # Never changes (base identity)
    SESSION = "session"  # Once per session
    TURN = "turn"  # Every turn
    EVENT = "event"  # On external event


class InjectTiming(Enum):
    """
    WHEN a layer should be injected (for S2S/persistent connections).

    HTTP ignores this - compile() returns all layers.
    S2S uses compile_for(timing) to get layers for specific moments.

    Timing values:
    - SESSION_START: Once when session begins (system_prompt)
    - TURN_START: Before each user turn (on SPEECH_STARTED)
    - AFTER_RESPONSE: After AI response completes (on RESPONSE_DONE)
    - SCHEDULED: Every N turns or N seconds
    - ASAP: Inject immediately (proactive triggers)
    - ON_EVENT: On specific external event
    """

    SESSION_START = "session_start"
    TURN_START = "turn_start"
    AFTER_RESPONSE = "after_response"
    SCHEDULED = "scheduled"
    ASAP = "asap"
    ON_EVENT = "on_event"


@dataclass
class CompileOptions:
    """
    Options passed to compile() that affect layer rendering.

    These are compile-time flags that layers can react to.
    For most use cases, the defaults are sufficient.

    Attributes:
        verbose: Include full context vs condensed (default: True)
        custom: Extensible dict for app-specific flags
    """

    verbose: bool = True
    custom: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get custom flag value."""
        return self.custom.get(key, default)
