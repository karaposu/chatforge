"""
PRAGMA: Conversational Act Analysis — Pydantic Models.

Structured output models for all PRAGMA dimensions, layers, and outputs.
Used with LangChain's `with_structured_output()` for guaranteed schema compliance.

Three levels of models:
1. PER-MESSAGE — what each LLM call returns (Signal Layer)
2. PER-SEGMENT — aggregated from per-message outputs (Dynamics Profile)
3. PER-CONVERSATION — interpretation and attachment readings

Following CPDE-7 pattern: Item → Result → Output → Combined
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class FuzzyLevel(str, Enum):
    absent = "absent"
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


class SRILevel(str, Enum):
    absent = "absent"
    present = "present"
    invested = "invested"
    exposed = "exposed"


class EFLevel(str, Enum):
    absent = "absent"
    mild = "mild"
    moderate = "moderate"
    strong = "strong"


class EFDirection(str, Enum):
    positive = "positive"
    negative = "negative"
    mixed = "mixed"
    masked_negative = "masked_negative"
    neutral = "neutral"


class TILevel(str, Enum):
    absent = "absent"
    present_only = "present_only"
    extended = "extended"
    consuming = "consuming"


class RDLevel(str, Enum):
    absent = "absent"
    mild = "mild"
    moderate = "moderate"
    strong = "strong"


class USLevel(str, Enum):
    absent = "absent"
    mild = "mild"
    moderate = "moderate"
    strong = "strong"


class InvestmentLevel(str, Enum):
    zero = "zero"
    low = "low"
    moderate = "moderate"
    high = "high"


class NoveltyLabel(str, Enum):
    zero = "zero"
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


class RelevanceLabel(str, Enum):
    off_topic = "off_topic"
    tangential = "tangential"
    related = "related"
    on_topic = "on_topic"
    precisely_on_topic = "precisely_on_topic"


class SpecificityLabel(str, Enum):
    absent = "absent"
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


class IntentCategory(str, Enum):
    inform = "inform"
    discover = "discover"
    convince = "convince"
    connect = "connect"
    request = "request"
    process = "process"
    perform = "perform"
    control = "control"
    support = "support"
    avoid = "avoid"
    test = "test"
    co_create = "co_create"
    unclear = "unclear"


class DialogicFunction(str, Enum):
    challenging = "challenging"
    co_creating = "co_creating"
    explaining = "explaining"
    sharing = "sharing"
    affirming = "affirming"
    transmitting = "transmitting"
    querying = "querying"
    echoing = "echoing"


class TrajectoryLabel(str, Enum):
    increasing = "increasing"
    decreasing = "decreasing"
    stable = "stable"
    pulsing = "pulsing"
    insufficient_data = "insufficient_data"


class CoherenceLevel(str, Enum):
    coherent = "coherent"
    minor_tensions = "minor_tensions"
    significant_tensions = "significant_tensions"


class AttachmentLevel(str, Enum):
    absent = "absent"
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


class ConfidenceLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class FrameStability(str, Enum):
    stable = "stable"
    fragile = "fragile"
    context_dependent = "context_dependent"


# =============================================================================
# 1. EXPRESSED INVOLVEMENT (Energy) — Per Message
# =============================================================================

class EIMicroSignals(BaseModel):
    """Five micro-signals of Expressed Involvement."""

    self_reference_intensity: SRILevel = Field(
        description="How much the speaker puts themselves at stake"
    )
    sri_evidence: str = Field(description="Quote or description supporting SRI level")

    evaluative_force: EFLevel = Field(
        description="How strongly they judge what they're discussing"
    )
    ef_direction: EFDirection = Field(description="Direction of evaluation")
    ef_evidence: str = Field(description="Quote or description supporting EF level")

    temporal_involvement: TILevel = Field(
        description="Whether this subject occupies them beyond the current message"
    )
    ti_evidence: str = Field(description="Quote or description supporting TI level")

    reactive_disruption: RDLevel = Field(
        description="Whether the conversation is changing their state right now"
    )
    rd_evidence: str = Field(description="Quote or description supporting RD level")

    urgency_signal: USLevel = Field(
        description="Whether there's time pressure or imperative force"
    )
    us_evidence: str = Field(description="Quote or description supporting US level")


class EIOutput(BaseModel):
    """Expressed Involvement extraction result for one message."""
    micro_signals: EIMicroSignals
    is_sarcastic: bool = Field(default=False, description="Whether sarcasm was detected")
    sarcasm_note: str | None = Field(default=None, description="Sarcasm details if detected")


# =============================================================================
# 2. CONVERSATIONAL INTENT — Per Message
# =============================================================================

class IntentOutput(BaseModel):
    """Intent classification for one message."""

    category: IntentCategory = Field(description="Primary intent category")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the classification"
    )
    explanation: str = Field(
        description="One sentence explaining why this category was chosen"
    )
    secondary_category: IntentCategory | None = Field(
        default=None,
        description="Secondary intent if the message blends goals"
    )


# =============================================================================
# 3. INFORMATION DENSITY — Per Message
# =============================================================================

class SpecificityVector(BaseModel):
    """Four sub-dimensions of specificity."""

    entity: float = Field(ge=0.0, le=1.0, description="How specific are entity references")
    temporal: float = Field(ge=0.0, le=1.0, description="How precise are time references")
    quantitative: float = Field(ge=0.0, le=1.0, description="How much numeric precision")
    action: float = Field(ge=0.0, le=1.0, description="How concrete are described actions")
    combined: float = Field(ge=0.0, le=1.0, description="Overall specificity")
    label: SpecificityLabel = Field(description="Categorical label for specificity")


class DensityOutput(BaseModel):
    """Information Density assessment for one message."""

    specificity: SpecificityVector
    novelty: float = Field(ge=0.0, le=1.0, description="How new is this content")
    novelty_label: NoveltyLabel
    novelty_explanation: str = Field(description="Why this novelty score")
    relevance: float = Field(ge=0.0, le=1.0, description="How on-topic is this")
    relevance_label: RelevanceLabel
    relevance_explanation: str = Field(description="Why this relevance score")


# =============================================================================
# 4. INVESTMENT — Per Message
# =============================================================================

class InvestmentOutput(BaseModel):
    """Investment assessment for one message."""

    structural_effort: InvestmentLevel = Field(
        description="Structural investment (length, speed, initiation)"
    )
    content_effort: InvestmentLevel = Field(
        description="Content investment (elaboration, unsolicited detail, depth)"
    )
    overall: InvestmentLevel = Field(description="Combined investment level")
    explanation: str = Field(
        description="Why this investment level, relative to what the moment called for"
    )


# =============================================================================
# 5. DIALOGIC FUNCTION — Per Message
# =============================================================================

class FunctionWeight(BaseModel):
    """A single dialogic function with weight and evidence."""
    function: DialogicFunction
    weight: float = Field(ge=0.0, le=1.0, description="Relative weight of this function")
    evidence: str = Field(description="Quote or description supporting this function")


class DialogicFunctionOutput(BaseModel):
    """Multi-label dialogic function classification for one message."""
    functions: list[FunctionWeight] = Field(
        description="Ranked list of functions with weights"
    )


# =============================================================================
# COMBINED: Per-Message Signal Layer Result
# =============================================================================

class PragmaMessageResult(BaseModel):
    """All Signal Layer outputs for a single message."""

    message_id: str
    sender: str
    expressed_involvement: EIOutput | None = None
    intent: IntentOutput | None = None
    density: DensityOutput | None = None
    investment: InvestmentOutput | None = None
    dialogic_function: DialogicFunctionOutput | None = None


# =============================================================================
# PER-SEGMENT: Aggregated Outputs
# =============================================================================

class ParticipantSegmentAggregation(BaseModel):
    """Aggregated dimension readings for one participant in one segment."""

    participant: str
    message_count: int

    ei_avg_level: float | None = Field(default=None, description="Average involvement score")
    ei_dominant_signals: list[str] | None = None
    ei_trajectory: TrajectoryLabel | None = None

    intent_dominant: IntentCategory | None = None
    intent_arc: str | None = Field(default=None, description="How intent evolved across segment")

    density_avg_specificity: float | None = None
    density_avg_novelty: float | None = None
    density_avg_relevance: float | None = None
    density_trajectory: TrajectoryLabel | None = None

    investment_avg: InvestmentLevel | None = None
    investment_trajectory: TrajectoryLabel | None = None

    dominant_functions: list[DialogicFunction] | None = None
    function_distribution: dict[str, float] | None = None

    control_verbosity_share: float | None = None
    control_topic_direction_attempts: int | None = None
    control_topic_direction_effect: float | None = None
    control_emotional_register: str | None = None


class SignalGap(BaseModel):
    """A detected gap between two dimensions."""
    gap_name: str = Field(description="e.g., investment_vs_involvement")
    participant: str
    magnitude: float = Field(ge=0.0, le=1.0)
    description: str


class DyadicComparison(BaseModel):
    """Comparison between two participants in a segment."""
    involvement_asymmetry: float | None = None
    density_asymmetry: float | None = None
    investment_asymmetry: float | None = None
    control_balance: str | None = None
    denser_participant: str | None = None
    more_involved_participant: str | None = None


class SegmentAggregation(BaseModel):
    """Full aggregation for one topic segment."""

    segment_id: str
    topic_label: str
    message_range: str
    message_count: int

    participants: list[ParticipantSegmentAggregation]
    dyadic: DyadicComparison | None = None
    signal_gaps: list[SignalGap] = Field(default_factory=list)


# =============================================================================
# DYNAMICS PROFILE — Per Segment
# =============================================================================

class DynamicsProfileOutput(BaseModel):
    """LLM-composed description of segment dynamics."""

    segment_id: str
    dynamics_profile: str = Field(description="Natural language description of dynamics")
    headline: str = Field(description="One sentence summary")
    notable_gaps: list[SignalGap] = Field(default_factory=list)


# =============================================================================
# INTERPRETATION LAYER — Per Message + Per Segment
# =============================================================================

class TensionItem(BaseModel):
    """A single detected tension between dimensions."""
    dimensions_involved: list[str]
    what_conflicts: str
    what_it_might_suggest: str
    confidence: float = Field(ge=0.0, le=1.0)


class MessageTensionOutput(BaseModel):
    """Per-message tension analysis."""
    tensions_detected: bool
    tensions: list[TensionItem] = Field(default_factory=list)
    overall_coherence: CoherenceLevel
    note: str | None = None


class WithinParticipantTension(BaseModel):
    participant: str
    what_conflicts: str
    what_it_suggests: str


class BetweenParticipantTension(BaseModel):
    what_conflicts: str
    what_it_suggests: str
    pattern: str | None = None


class TrajectoryTension(BaseModel):
    what_changed: str
    inflection_at: str | None = None
    what_it_suggests: str


class IntentBehaviorMismatch(BaseModel):
    participant: str
    stated_intent: str
    actual_behavior: str
    what_it_suggests: str


class ControlDynamic(BaseModel):
    primary_controller: str
    control_mechanism: str
    matches_investment: bool
    note: str


class SegmentTensionOutput(BaseModel):
    """Per-segment tension analysis (reads Dynamics Profile)."""
    within_participant_tensions: list[WithinParticipantTension] = Field(default_factory=list)
    between_participant_tensions: list[BetweenParticipantTension] = Field(default_factory=list)
    trajectory_tensions: list[TrajectoryTension] = Field(default_factory=list)
    intent_behavior_mismatches: list[IntentBehaviorMismatch] = Field(default_factory=list)
    who_controls: ControlDynamic | None = None
    segment_summary: str


# =============================================================================
# APT INFERENCE — Per Segment
# =============================================================================

class AttachmentReading(BaseModel):
    """Charm/Hope/Fear reading with reason."""
    level: AttachmentLevel
    reason: str = Field(description="Grounded in dynamics, not vague")


class AttachmentDomain1(BaseModel):
    """Domain 1: Attachment (why they stay)."""
    charm: AttachmentReading
    hope: AttachmentReading
    fear: AttachmentReading


class PresentationDomain2(BaseModel):
    """Domain 2: Presentation (how they transmit)."""
    content: str = Field(description="What they communicate")
    style: str = Field(description="How they communicate")
    expressed_frame: str = Field(description="What investment dynamic their behavior implies")


class DirectionalReading(BaseModel):
    """One participant's attachment toward the other."""
    attachment: AttachmentDomain1
    presentation: PresentationDomain2


class APTInferenceOutput(BaseModel):
    """Directional APT reading for a segment."""

    segment_id: str
    a_toward_b: DirectionalReading
    b_toward_a: DirectionalReading
    overall_dynamic: str = Field(description="1-3 sentences on the attachment relationship")
    evolution: str = Field(description="What changed from prior readings, or 'initial reading'")
    confidence: ConfidenceLevel


# =============================================================================
# BEHAVIORAL PROFILING — Cross-Conversation
# =============================================================================

class BehavioralSignature(BaseModel):
    """Communication style profile for one person."""
    involvement_style: str
    density_style: str
    control_style: str
    investment_pattern: str
    function_profile: str
    intent_profile: str


class BehavioralProfileOutput(BaseModel):
    """Cross-conversation behavioral profile."""

    person_id: str
    profile_version: int
    observation_count: int
    confidence: ConfidenceLevel
    signature: BehavioralSignature
    notable_patterns: list[str] = Field(default_factory=list)
    headline: str


# =============================================================================
# APT PROFILING — Cross-Conversation
# =============================================================================

class AttachmentBearing(BaseModel):
    """Trigger patterns for one attachment variable."""
    triggers: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    non_triggers: list[str] = Field(default_factory=list)
    summary: str
    evidence_count: int = 0


class PresentationTendencies(BaseModel):
    """Condition → behavior mappings."""
    when_confident: str | None = None
    when_insecure: str | None = None
    when_challenged: str | None = None
    when_charmed: str | None = None
    when_pursuing_hope: str | None = None
    when_afraid: str | None = None
    default_style: str | None = None
    frame_stability: FrameStability | None = None
    frame_note: str | None = None


class NotablePattern(BaseModel):
    pattern: str
    evidence: str
    counter_evidence: str | None = None


class APTProfileOutput(BaseModel):
    """Cross-conversation APT profile."""

    person_id: str
    profile_version: int
    observation_count: int
    confidence: ConfidenceLevel

    charm: AttachmentBearing
    hope: AttachmentBearing
    fear: AttachmentBearing

    presentation: PresentationTendencies
    notable_patterns: list[NotablePattern] = Field(default_factory=list)
    context_notes: list[dict] = Field(default_factory=list)


# =============================================================================
# COMBINED: Full Conversation Result
# =============================================================================

class PragmaConversationResult(BaseModel):
    """Complete PRAGMA output for one conversation."""

    conversation_id: str | None = None
    message_results: list[PragmaMessageResult] = Field(default_factory=list)
    segment_aggregations: list[SegmentAggregation] = Field(default_factory=list)
    dynamics_profiles: list[DynamicsProfileOutput] = Field(default_factory=list)
    message_tensions: list[MessageTensionOutput] = Field(default_factory=list)
    segment_tensions: list[SegmentTensionOutput] = Field(default_factory=list)
    apt_inferences: list[APTInferenceOutput] = Field(default_factory=list)