"""
Configuration for Profiling Data Extraction.

Controls what and how to extract from conversations.
"""

from dataclasses import dataclass, field


# CPF-7 Dimensions
CPF7_DIMENSIONS = [
    "core_identity",
    "opinions_views",
    "preferences_patterns",
    "desires_needs",
    "life_narrative",
    "events",
    "entities_relationships",
]


@dataclass
class ExtractionConfig:
    """
    Controls what and how to extract from conversations.

    Attributes:
        dimensions: Which CPF-7 dimensions to extract. Defaults to all 7.
        batch_size: Messages per LLM call.
        min_messages_for_extraction: Skip conversations with fewer messages.
        confidence_threshold: Minimum confidence to save extracted data.

    Example:
        # Extract only identity and preferences
        config = ExtractionConfig(
            dimensions=["core_identity", "preferences_patterns"],
        )

        # Full extraction with larger batches
        config = ExtractionConfig(
            batch_size=100,
            confidence_threshold=0.7,
        )
    """

    # Which CPF-7 dimensions to extract (all 7 by default)
    dimensions: list[str] = field(default_factory=lambda: list(CPF7_DIMENSIONS))

    # Extraction behavior
    batch_size: int = 50
    min_messages_for_extraction: int = 5
    confidence_threshold: float = 0.5

    def __post_init__(self) -> None:
        """Validate configuration."""
        invalid = set(self.dimensions) - set(CPF7_DIMENSIONS)
        if invalid:
            raise ValueError(
                f"Invalid dimensions: {invalid}. "
                f"Valid dimensions: {CPF7_DIMENSIONS}"
            )
