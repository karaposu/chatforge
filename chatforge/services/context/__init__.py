"""
LDCI (Layered Dynamic Context Injection) - Context Management for LLM Applications.

This module provides a modality-agnostic context management framework
implementing 5-layer dynamic context injection for LLM conversations.

The 5 Layers:
    L1 Base:      Stable foundation (AI identity, rules)
    L2 State:     Dynamic per-turn context (current situation)
    L3 Override:  Full context replacement (testing, major transitions)
    L4 Derived:   Background-computed insights (async analysis)
    L5 Proactive: App-triggered AI speech (external events)

Key Principle:
    ContextManager is a LIBRARY (you call it), not a framework (it calls you).
    It does NOT know about ports, events, or injection timing execution.
    The app controls when and how context is injected.

Usage (HTTP):
    from chatforge.services.context import ContextManager, ContextLayer, Layer

    context = ContextManager()

    # Add layers
    context.add(ContextLayer(layer=Layer.BASE, content=system_prompt))
    context.add(ContextLayer(layer=Layer.STATE, content=room_ctx, order=10))

    # Compile ALL layers (timing ignored for HTTP)
    compiled = context.compile()

    # Access L1 separately
    system_prompt = context.get_base()

Usage (S2S):
    from chatforge.services.context import (
        ContextManager, ContextLayer, Layer, InjectTiming
    )

    context = ContextManager()

    # Add layers with timing
    context.add(ContextLayer(
        layer=Layer.BASE,
        content=system_prompt,
        inject_at=InjectTiming.SESSION_START,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=room_ctx,
        inject_at=InjectTiming.TURN_START,
    ))

    # Connect with L1
    await port.connect(system_prompt=context.get_base())

    # Inject on events
    async for event in port.events():
        if event.type == "speech_started":
            text = context.compile_for(InjectTiming.TURN_START)
            if text:
                await port.add_text_item(text)
"""

from chatforge.services.context.layer import ContextLayer
from chatforge.services.context.manager import ContextManager
from chatforge.services.context.types import (
    Authority,
    CompileOptions,
    InjectTiming,
    Layer,
    Stability,
)


__all__ = [
    # Main classes
    "ContextManager",
    "ContextLayer",
    # Enums
    "Layer",
    "InjectTiming",
    "Authority",
    "Stability",
    # Options
    "CompileOptions",
]
