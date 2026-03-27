"""
Configuration for PRAGMA: Conversational Act Analysis.

Controls what dimensions to extract, which layers to run,
and how to process conversations.
"""

from dataclasses import dataclass, field


PRAGMA_DIMENSIONS = [
    "expressed_involvement",
    "intent",
    "density",
    "investment",
    "dialogic_function",
]

PRAGMA_MECHANICAL_DIMENSIONS = [
    "control_distribution",
    "temporal_structure",
]

PRAGMA_UPPER_LAYERS = [
    "dynamics_profile",
    "interpretation_layer",
    "apt_inference",
]


@dataclass
class PragmaConfig:
    """
    Controls what and how PRAGMA extracts from conversations.

    Attributes:
        dimensions: Which LLM-based dimensions to extract. Defaults to all 5.
        run_topic_flow: Whether to run Topic Flow upstream. Required for
            density (novelty/relevance need segment context) and
            control_distribution (topic direction needs Topic Flow).
        run_dynamics_profile: Whether to compose Dynamics Profile per segment.
        run_interpretation: Whether to run Interpretation Layer tension checks.
        run_apt_inference: Whether to run APT Inference per segment.
        parallel_extraction: Whether to run LLM calls in parallel (faster, more cost).
        topic_flow_immediate_window: Messages in immediate Topic Flow window.
        topic_flow_medium_window: Messages in medium Topic Flow window.
        topic_flow_medium_frequency: Run medium window every N messages.
        topic_flow_long_window: Messages in long Topic Flow window.
        topic_flow_long_frequency: Run long window every N messages.

    Example:
        # Full extraction (all dimensions + all layers)
        config = PragmaConfig()

        # Only involvement and intent (cheapest useful subset)
        config = PragmaConfig(
            dimensions=["expressed_involvement", "intent"],
            run_dynamics_profile=False,
            run_interpretation=False,
            run_apt_inference=False,
        )

        # Signal Layer only (no upper layers)
        config = PragmaConfig(
            run_dynamics_profile=False,
            run_interpretation=False,
            run_apt_inference=False,
        )

        # Fast parallel extraction
        config = PragmaConfig(parallel_extraction=True)
    """

    # Which LLM-based dimensions to extract (all 5 by default)
    dimensions: list[str] = field(
        default_factory=lambda: list(PRAGMA_DIMENSIONS)
    )

    # Topic Flow (upstream infrastructure)
    run_topic_flow: bool = True
    topic_flow_immediate_window: int = 3
    topic_flow_medium_window: int = 20
    topic_flow_medium_frequency: int = 5
    topic_flow_long_window: int = 50
    topic_flow_long_frequency: int = 10

    # Upper layers
    run_dynamics_profile: bool = True
    run_interpretation: bool = True
    run_apt_inference: bool = True

    # Execution
    parallel_extraction: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        invalid = set(self.dimensions) - set(PRAGMA_DIMENSIONS)
        if invalid:
            raise ValueError(
                f"Invalid dimensions: {invalid}. "
                f"Valid dimensions: {PRAGMA_DIMENSIONS}"
            )

        if "density" in self.dimensions and not self.run_topic_flow:
            raise ValueError(
                "Density dimension requires Topic Flow for novelty/relevance context. "
                "Either enable run_topic_flow or remove 'density' from dimensions."
            )

    @property
    def llm_calls_per_message(self) -> int:
        """Estimate LLM calls per message for this config."""
        count = 0
        if self.run_topic_flow:
            count += 1
        if "expressed_involvement" in self.dimensions or "intent" in self.dimensions:
            count += 1  # EI + Intent share one call
        if "density" in self.dimensions:
            count += 1
        if "investment" in self.dimensions:
            count += 1
        if "dialogic_function" in self.dimensions:
            count += 1
        return count

    @property
    def runs_ei_intent(self) -> bool:
        return (
            "expressed_involvement" in self.dimensions
            or "intent" in self.dimensions
        )