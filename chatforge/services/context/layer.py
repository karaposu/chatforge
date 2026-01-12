"""
ContextLayer - First-class context object with metadata.

ContextLayer is the fundamental unit of context in LDCI. Each layer
carries content along with metadata about when and how it should
be injected.
"""

from dataclasses import dataclass, field
import time
from typing import TYPE_CHECKING

from .types import Authority, CompileOptions, InjectTiming, Layer, Stability


if TYPE_CHECKING:
    pass


__all__ = ["ContextLayer"]


@dataclass
class ContextLayer:
    """
    A piece of context with metadata.

    ContextLayer is a first-class object created before adding to
    ContextManager. This enables:
    - Reuse and storage of layers
    - Clear metadata in one place
    - Type safety and validation
    - Easy testing (create, inspect, then add)

    Attributes:
        layer: Which layer type (BASE, STATE, OVERRIDE, DERIVED, PROACTIVE)
        content: The actual context string
        prefix: Header text prepended to content (e.g., "=== ROOM CONTEXT ===")
        default: Fallback content when content is empty
        inject_at: When to inject (for S2S) - ignored for HTTP
        order: Sort order for multiple items in same timing/layer
        authority: How AI should treat this (design-time metadata)
        stability: How often this changes (informational)
        timestamp: When this layer was created
        source: Where this layer came from (for debugging)

    Example:
        # Create a state layer for room context
        room_layer = ContextLayer(
            layer=Layer.STATE,
            content="Player is in the Art Gallery. A large painting hangs on the wall.",
            inject_at=InjectTiming.TURN_START,
            order=10,
        )

        # Create a derived layer for insights
        insight_layer = ContextLayer(
            layer=Layer.DERIVED,
            content="User seems interested in art based on recent questions.",
            inject_at=InjectTiming.AFTER_RESPONSE,
        )

        # Add to manager
        context.add(room_layer)
        context.add(insight_layer)
    """

    # Required
    layer: Layer
    content: str = ""

    # Formatting
    prefix: str = ""  # Header text prepended to content (e.g., "=== ROOM CONTEXT ===")
    default: str = ""  # Fallback when content is empty

    # Injection timing (for S2S - when should this be injected?)
    inject_at: InjectTiming = InjectTiming.TURN_START

    # Ordering (for multiple items in same timing/layer)
    order: int = 0

    # Metadata (informational, not runtime)
    authority: Authority = Authority.INFORMATIVE
    stability: Stability = Stability.TURN

    # Tracking
    timestamp: float = field(default_factory=time.time)
    source: str = "app"

    def render(self, options: CompileOptions | None = None) -> str:
        """
        Render content for compilation.

        Uses content if available, otherwise falls back to default.
        Prepends prefix if set.

        Args:
            options: Compile options that may affect rendering

        Returns:
            Rendered content string (empty string if no content/default)
        """
        actual = self.content if self.content else self.default
        if not actual:
            return ""
        if self.prefix:
            return f"{self.prefix}\n{actual}"
        return actual

    def __repr__(self) -> str:
        """Concise representation for debugging."""
        actual = self.content if self.content else self.default
        content_preview = (
            actual[:50] + "..." if len(actual) > 50 else actual
        ) if actual else "(empty)"
        return (
            f"ContextLayer(layer={self.layer.value}, "
            f"inject_at={self.inject_at.value}, "
            f"order={self.order}, "
            f"content={content_preview!r})"
        )

    def __add__(self, other: "ContextLayer | str") -> str:
        """Concatenate with another layer or string."""
        if isinstance(other, ContextLayer):
            return self.render() + "\n\n" + other.render()
        return self.render() + str(other)

    def __radd__(self, other: str) -> str:
        """Support string + ContextLayer."""
        return str(other) + "\n\n" + self.render()
