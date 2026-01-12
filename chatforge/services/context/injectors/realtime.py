"""
RealtimeContextInjector - Context injection for RealtimeVoiceAPIPort.

This injector handles context injection into the RealtimeVoiceAPIPort,
using add_text_item() to inject context as conversation items.
"""

import logging
from typing import TYPE_CHECKING

from chatforge.services.context.layer import ContextLayer
from chatforge.services.context.manager import ContextManager
from chatforge.services.context.types import InjectTiming


if TYPE_CHECKING:
    from chatforge.ports.realtime_voice import RealtimeVoiceAPIPort


__all__ = ["RealtimeContextInjector"]


logger = logging.getLogger(__name__)


class RealtimeContextInjector:
    """
    Inject context layers into RealtimeVoiceAPIPort.

    Uses add_text_item() to inject context without triggering a response.
    The context becomes part of the conversation history.

    Usage:
        from chatforge.services.context.injectors import RealtimeContextInjector

        injector = RealtimeContextInjector(port)

        async for event in port.events():
            if event.type == "speech_started":
                await injector.inject_for(context, InjectTiming.TURN_START)

            if event.type == "response_done":
                await injector.inject_for(context, InjectTiming.AFTER_RESPONSE)
                context.clear_derived()

    Attributes:
        port: The RealtimeVoiceAPIPort to inject into
    """

    def __init__(self, port: "RealtimeVoiceAPIPort") -> None:
        """
        Initialize the injector with a port.

        Args:
            port: RealtimeVoiceAPIPort instance to inject into
        """
        self._port = port

    async def inject(self, layer: ContextLayer) -> None:
        """
        Inject a single context layer.

        Uses port.add_text_item() to add the layer content to the
        conversation without triggering a response.

        Args:
            layer: The ContextLayer to inject
        """
        if not layer.content:
            logger.debug("Skipping empty layer: %s", layer.layer.value)
            return

        logger.debug(
            "Injecting layer: %s (order=%d, timing=%s)",
            layer.layer.value,
            layer.order,
            layer.inject_at.value,
        )
        await self._port.add_text_item(layer.content)

    async def inject_all(self, layers: list[ContextLayer]) -> None:
        """
        Inject multiple context layers.

        Layers are injected in the order provided (caller should sort by order).

        Args:
            layers: List of ContextLayer objects to inject
        """
        for layer in layers:
            await self.inject(layer)

    async def inject_for(
        self, context: ContextManager, timing: InjectTiming
    ) -> None:
        """
        Inject all layers matching timing from a ContextManager.

        Gets layers for the specified timing and injects them in order.

        Args:
            context: ContextManager to get layers from
            timing: Which injection timing to filter for

        Example:
            # On SPEECH_STARTED event
            await injector.inject_for(context, InjectTiming.TURN_START)

            # On RESPONSE_DONE event
            await injector.inject_for(context, InjectTiming.AFTER_RESPONSE)
        """
        layers = context.get_layers_for(timing)

        if not layers:
            logger.debug("No layers to inject for timing: %s", timing.value)
            return

        logger.debug(
            "Injecting %d layers for timing: %s",
            len(layers),
            timing.value,
        )
        await self.inject_all(layers)
