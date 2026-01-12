"""
Context Injectors - Port-aware injection helpers for S2S.

This module provides the ContextInjector protocol and implementations
for injecting context layers into different port types.

Injectors are OPTIONAL - you can also use:
- compile_for(timing) for string output
- get_layers_for(timing) for manual layer handling

Injectors are useful when you want:
- Per-layer error handling
- Custom formatting per layer type
- Logging/observability per layer
- Reusable injection patterns

Usage:
    from chatforge.services.context.injectors import RealtimeContextInjector

    injector = RealtimeContextInjector(port)

    async for event in port.events():
        if event.type == "speech_started":
            await injector.inject_for(context, InjectTiming.TURN_START)
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from chatforge.services.context.layer import ContextLayer
    from chatforge.services.context.manager import ContextManager
    from chatforge.services.context.types import InjectTiming


__all__ = [
    "ContextInjector",
]


class ContextInjector(Protocol):
    """
    Protocol for injecting context layers into a port.

    Implementations handle the actual injection mechanics for
    different port types (RealtimeVoiceAPIPort, WebSocket, etc.).

    This is a Protocol - implementations don't need to inherit from it,
    they just need to implement the required methods.
    """

    async def inject(self, layer: "ContextLayer") -> None:
        """
        Inject a single context layer.

        Args:
            layer: The ContextLayer to inject
        """
        ...

    async def inject_all(self, layers: list["ContextLayer"]) -> None:
        """
        Inject multiple context layers.

        Args:
            layers: List of ContextLayer objects to inject
        """
        ...

    async def inject_for(
        self, context: "ContextManager", timing: "InjectTiming"
    ) -> None:
        """
        Inject all layers matching timing from a ContextManager.

        Convenience method that gets layers for timing and injects them.

        Args:
            context: ContextManager to get layers from
            timing: Which injection timing to filter for
        """
        ...
