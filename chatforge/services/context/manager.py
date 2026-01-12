"""
ContextManager - Orchestrates layered context injection.

ContextManager is the main class for managing context layers. It stores
layers, provides compilation, and supports filtering by injection timing.

Key principle: ContextManager is a LIBRARY (you call it), not a framework
(it calls you). It does NOT know about ports, events, or injection timing
execution - the app controls all of that.
"""

from typing import Optional

from .layer import ContextLayer
from .types import CompileOptions, InjectTiming, Layer


__all__ = ["ContextManager"]


class ContextManager:
    """
    Orchestrates layered context injection.

    ContextManager stores context layers and provides methods to compile
    them into strings for LLM consumption. It supports both HTTP (stateless)
    and S2S (persistent) modalities through different compilation methods.

    Usage (HTTP):
        context = ContextManager()

        # Add layers
        context.add(ContextLayer(layer=Layer.BASE, content=system_prompt))
        context.add(ContextLayer(layer=Layer.STATE, content=room_ctx, order=10))

        # Compile ALL layers (timing ignored)
        compiled = context.compile()

        # Access L1 separately for system message
        system_prompt = context.get_base()

    Usage (S2S):
        context = ContextManager()

        # Add layers with timing
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

    def __init__(self) -> None:
        """Initialize ContextManager with empty layer storage."""
        # L1: Base (single layer)
        self._base: Optional[ContextLayer] = None

        # L2: State (multiple, ordered)
        self._state: list[ContextLayer] = []

        # L3: Override (replaces base when set)
        self._override: Optional[ContextLayer] = None

        # L4: Derived (multiple, ordered)
        self._derived: list[ContextLayer] = []

        # L5: Proactive (multiple, ordered)
        self._proactive: list[ContextLayer] = []

    # ─────────────────────────────────────────────────────────────
    # Core: Add Layer
    # ─────────────────────────────────────────────────────────────

    def add(self, layer: ContextLayer) -> None:
        """
        Add a context layer.

        The layer is stored in the appropriate internal list based on
        its layer type. Multiple layers of the same type are allowed
        (except BASE and OVERRIDE which are single).

        Args:
            layer: The ContextLayer to add
        """
        if layer.layer == Layer.BASE:
            self._base = layer
        elif layer.layer == Layer.STATE:
            self._state.append(layer)
        elif layer.layer == Layer.OVERRIDE:
            self._override = layer
        elif layer.layer == Layer.DERIVED:
            self._derived.append(layer)
        elif layer.layer == Layer.PROACTIVE:
            self._proactive.append(layer)

    # ─────────────────────────────────────────────────────────────
    # L1: Base Context
    # ─────────────────────────────────────────────────────────────

    def get_base(self) -> Optional[str]:
        """
        Get L1 base context for session initialization.

        Returns override content if set, otherwise base content.
        This is used for system_prompt in S2S or SystemMessage in HTTP.

        Returns:
            Base context string, or None if not set
        """
        if self._override:
            return self._override.content
        return self._base.content if self._base else None

    # ─────────────────────────────────────────────────────────────
    # Layer Management
    # ─────────────────────────────────────────────────────────────

    def clear_state(self) -> None:
        """Clear all L2 state context (typically for new turn)."""
        self._state.clear()

    def clear_override(self) -> None:
        """Clear L3 override (restore base)."""
        self._override = None

    def clear_derived(self) -> None:
        """Clear L4 derived context."""
        self._derived.clear()

    def clear_proactive(self) -> None:
        """Clear L5 proactive context."""
        self._proactive.clear()

    def clear_all(self) -> None:
        """Clear all layers except base."""
        self.clear_state()
        self.clear_override()
        self.clear_derived()
        self.clear_proactive()

    # ─────────────────────────────────────────────────────────────
    # Layer Access
    # ─────────────────────────────────────────────────────────────

    def has_layers_for(self, timing: InjectTiming) -> bool:
        """
        Check if there are any layers matching the specified timing.

        Args:
            timing: Which injection timing to check

        Returns:
            True if at least one layer matches the timing
        """
        return len(self.get_layers_for(timing)) > 0

    def get_layers_for(self, timing: InjectTiming) -> list[ContextLayer]:
        """
        Get layer objects matching the specified timing.

        Use this when you want to work with layer objects directly,
        e.g., with a ContextInjector or custom injection logic.

        Args:
            timing: Which injection timing to filter for

        Returns:
            List of ContextLayer objects matching timing, sorted by order

        Example:
            layers = context.get_layers_for(InjectTiming.TURN_START)
            for layer in layers:
                await injector.inject(layer)
        """
        layers: list[ContextLayer] = []

        for layer in self._state:
            if layer.inject_at == timing:
                layers.append(layer)

        for layer in self._derived:
            if layer.inject_at == timing:
                layers.append(layer)

        for layer in self._proactive:
            if layer.inject_at == timing:
                layers.append(layer)

        layers.sort(key=lambda x: x.order)
        return layers

    # ─────────────────────────────────────────────────────────────
    # Compilation
    # ─────────────────────────────────────────────────────────────

    def compile(self, **options) -> str:
        """
        Compile ALL layers (L2-L5) into a single string.

        Used for HTTP where timing doesn't matter - all context
        is assembled before the request.

        L1 (Base) is NOT included - access via get_base() separately.
        L3 (Override) is NOT included - it replaces L1 in get_base().

        Args:
            **options: Compile-time flags (verbose, custom, etc.)

        Returns:
            Compiled context string (L2 + L4 + L5, ordered)

        Example:
            compiled = context.compile()
            response = llm.invoke([
                SystemMessage(content=context.get_base()),
                *history,
                HumanMessage(content=compiled + "\\n" + user_input)
            ])
        """
        compile_opts = CompileOptions(**options)

        # Collect all layers to compile (NOT L1, NOT L3)
        layers: list[ContextLayer] = []

        # L2: State
        layers.extend(self._state)

        # L4: Derived
        layers.extend(self._derived)

        # L5: Proactive
        layers.extend(self._proactive)

        return self._compile_layers(layers, compile_opts)

    def compile_for(self, timing: InjectTiming, **options) -> str:
        """
        Compile only layers matching the specified timing.

        Convenience method that calls get_layers_for() and compiles to string.
        Use get_layers_for() if you need the layer objects directly.

        Args:
            timing: Which injection timing to filter for
            **options: Compile-time flags (verbose, custom, etc.)

        Returns:
            Compiled context string for layers matching timing

        Example:
            # On SPEECH_STARTED event
            text = context.compile_for(InjectTiming.TURN_START)
            if text:
                await port.add_text_item(text)

            # On RESPONSE_DONE event
            text = context.compile_for(InjectTiming.AFTER_RESPONSE)
            if text:
                await port.add_text_item(text)
        """
        compile_opts = CompileOptions(**options)
        layers = self.get_layers_for(timing)
        return self._compile_layers(layers, compile_opts)

    def _compile_layers(
        self, layers: list[ContextLayer], options: CompileOptions
    ) -> str:
        """
        Internal method to compile a list of layers.

        Args:
            layers: List of layers to compile
            options: Compile options

        Returns:
            Compiled string with layers joined by double newlines
        """
        if not layers:
            return ""

        # Sort by order
        sorted_layers = sorted(layers, key=lambda x: x.order)

        # Render each layer
        parts = [layer.render(options) for layer in sorted_layers]

        # Filter out empty parts
        parts = [p for p in parts if p]

        return "\n\n".join(parts)

    # ─────────────────────────────────────────────────────────────
    # Inspection
    # ─────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        """Concise representation for debugging."""
        counts = {
            "base": 1 if self._base else 0,
            "state": len(self._state),
            "override": 1 if self._override else 0,
            "derived": len(self._derived),
            "proactive": len(self._proactive),
        }
        return f"ContextManager({counts})"

    @property
    def layer_counts(self) -> dict[str, int]:
        """Get counts of each layer type."""
        return {
            "base": 1 if self._base else 0,
            "state": len(self._state),
            "override": 1 if self._override else 0,
            "derived": len(self._derived),
            "proactive": len(self._proactive),
        }
