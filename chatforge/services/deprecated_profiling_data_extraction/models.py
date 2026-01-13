"""
Pydantic models for CPDE-7 structured LLM output.

These models define the output schema for each extraction dimension.
Used with LangChain's `with_structured_output()` for guaranteed schema compliance.

This module contains TWO sets of models:

1. PER-MESSAGE MODELS (original)
   - For extracting from a single message at a time
   - No source attribution (you already know the source)
   - Use DIMENSION_MODELS registry
   - Example: CoreIdentityResult, OpinionsViewsResult

2. BATCH MODELS (with source attribution)
   - For extracting from multiple messages at once
   - Each item has source_message_id and source_quote for traceability
   - Use BATCH_DIMENSION_MODELS registry
   - Example: BatchCoreIdentityOutput, BatchOpinionsOutput

Each dimension has:
- An item model (single extracted fact)
- A result model (collection of items + has_content flag)
- For batch: an output wrapper model (for structured output)
"""

from pydantic import BaseModel, Field


# =============================================================================
# 1. Core Identity
# =============================================================================

class CoreIdentityItem(BaseModel):
    """A single identity fact about the person."""

    aspect: str = Field(
        description="Category of identity marker (e.g., age, profession, "
        "location, physical attribute, role, affiliation, condition, personality)"
    )
    state_value: str = Field(
        description="The actual value/state"
    )
    temporal: str | None = Field(
        default=None,
        description="Only if explicitly time-bound (e.g., 'currently', 'since 2020')"
    )
    relational_dimension: str | None = Field(
        default=None,
        description="Only if identity is relative to others (e.g., 'in my family', 'at work')"
    )


class CoreIdentityResult(BaseModel):
    """Extraction result for core identity dimension."""

    has_identity_content: bool = Field(
        description="Whether any identity information was found"
    )
    items: list[CoreIdentityItem] = Field(
        default_factory=list,
        description="List of extracted identity facts"
    )


# =============================================================================
# 2. Opinions & Views
# =============================================================================

class OpinionItem(BaseModel):
    """A single non-ephemeral opinion or belief."""

    about: str = Field(
        description="Topic/subject of the opinion"
    )
    view: str = Field(
        description="The stance/position taken"
    )
    qualifier: str | None = Field(
        default=None,
        description="Conditions, exceptions (e.g., 'unless...', 'except when...', 'probably')"
    )


class OpinionsViewsResult(BaseModel):
    """Extraction result for opinions/views dimension."""

    has_opinion_content: bool = Field(
        description="Whether any non-ephemeral opinions were found"
    )
    items: list[OpinionItem] = Field(
        default_factory=list,
        description="List of extracted opinions"
    )


# =============================================================================
# 3. Preferences & Patterns
# =============================================================================

class PreferenceItem(BaseModel):
    """A single stable preference or behavioral pattern."""

    activity_category: str = Field(
        description="Broad domain (e.g., work, sleep, communication, eating, social)"
    )
    activity: str = Field(
        description="Specific activity or behavior"
    )
    preference: str = Field(
        description="The pattern or preference"
    )
    context: str | None = Field(
        default=None,
        description="Conditions when this applies/doesn't apply"
    )


class PreferencesResult(BaseModel):
    """Extraction result for preferences/patterns dimension."""

    has_preference_content: bool = Field(
        description="Whether any preferences or patterns were found"
    )
    items: list[PreferenceItem] = Field(
        default_factory=list,
        description="List of extracted preferences"
    )


# =============================================================================
# 4. Desires, Wishes, Hopes & Needs
# =============================================================================

class DesireItem(BaseModel):
    """A single desire, wish, hope, or need."""

    type: str = Field(
        description="Type of aspiration: need/want/wish/hope"
    )
    target: str = Field(
        description="What they aspire to"
    )
    is_active: str = Field(
        default="unknown",
        description="Whether desire is current: yes/no/unknown/explicitly_uncertain"
    )
    intensity: str | None = Field(
        default=None,
        description="Intensity modifier (e.g., desperately, really, somewhat)"
    )
    temporal: str | None = Field(
        default=None,
        description="When relevant (e.g., soon, someday, by January)"
    )


class DesiresNeedsResult(BaseModel):
    """Extraction result for desires/needs dimension."""

    has_desire_content: bool = Field(
        description="Whether any desires, wishes, hopes, or needs were found"
    )
    items: list[DesireItem] = Field(
        default_factory=list,
        description="List of extracted desires/needs"
    )


# =============================================================================
# 5. Life Narrative
# =============================================================================

class NarrativeItem(BaseModel):
    """A single biographical element from life story."""

    what_happened: str = Field(
        description="Core biographical fact, no temporal markers"
    )
    period: str | None = Field(
        default=None,
        description="All temporal information (e.g., 'five years', '2019', 'childhood')"
    )
    significance: str | None = Field(
        default=None,
        description="Only if explicitly stated how it affected them"
    )


class LifeNarrativeResult(BaseModel):
    """Extraction result for life narrative dimension."""

    has_narrative_content: bool = Field(
        description="Whether any life narrative elements were found"
    )
    items: list[NarrativeItem] = Field(
        default_factory=list,
        description="List of extracted narrative elements"
    )


# =============================================================================
# 6. Events & Involvement
# =============================================================================

class EventItem(BaseModel):
    """A single significant event or occurrence."""

    event: str = Field(
        description="What happened/is happening"
    )
    involvement: str = Field(
        description="How they participated (e.g., attended, organized, experiencing)"
    )
    temporal: str | None = Field(
        default=None,
        description="When/duration (e.g., yesterday, current, ongoing, last month)"
    )
    entities_involved: list[str] | None = Field(
        default=None,
        description="Entities involved (people, organizations, groups, etc.)"
    )
    outcome: str | None = Field(
        default=None,
        description="Only if explicitly stated result/consequence"
    )


class EventsResult(BaseModel):
    """Extraction result for events dimension."""

    has_event_content: bool = Field(
        description="Whether any significant events were found"
    )
    items: list[EventItem] = Field(
        default_factory=list,
        description="List of extracted events"
    )


# =============================================================================
# 7. Entities & Relationships
# =============================================================================

class PropertyItem(BaseModel):
    """A single property key-value pair for entity properties."""

    key: str = Field(description="Property name (e.g., 'department', 'species', 'age')")
    value: str = Field(description="Property value (e.g., 'marketing', 'dog', 'old')")


class InteractionMetadata(BaseModel):
    """How the person interacts with an entity."""

    frequency: str | None = Field(
        default=None,
        description="How often (e.g., daily, weekly, rarely)"
    )
    context: str | None = Field(
        default=None,
        description="Interaction context (e.g., professional, personal, social)"
    )
    recency: str | None = Field(
        default=None,
        description="Current status (e.g., current, former, past)"
    )


class EntityItem(BaseModel):
    """A single entity (person, organization, place, etc.)."""

    name: str = Field(
        description="Entity name or identifier (e.g., 'Sarah', 'Google', 'my boss')"
    )
    entity_type: str = Field(
        description="Entity type (e.g., person, organization, place, product, pet)"
    )
    mentioned_properties: list[PropertyItem] = Field(
        default_factory=list,
        description="Properties mentioned about this entity as key-value pairs"
    )
    relationship_indicators: list[str] = Field(
        default_factory=list,
        description="How entity relates to speaker (e.g., colleague, employer, hometown)"
    )
    interaction_metadata: InteractionMetadata | None = Field(
        default=None,
        description="How they interact with this entity"
    )


class EntitiesResult(BaseModel):
    """Extraction result for entities dimension."""

    has_entity_content: bool = Field(
        description="Whether any significant entities were found"
    )
    items: list[EntityItem] = Field(
        default_factory=list,
        description="List of extracted entities"
    )


# =============================================================================
# Dimension Registry
# =============================================================================

DIMENSION_MODELS = {
    "core_identity": CoreIdentityResult,
    "opinions_views": OpinionsViewsResult,
    "preferences_patterns": PreferencesResult,
    "desires_needs": DesiresNeedsResult,
    "life_narrative": LifeNarrativeResult,
    "events": EventsResult,
    "entities_relationships": EntitiesResult,
}
"""Maps dimension names to their Pydantic result models."""


# =============================================================================
# Combined Extraction Result (optional convenience)
# =============================================================================

class FullExtractionResult(BaseModel):
    """Combined result from all dimensions (optional)."""

    core_identity: CoreIdentityResult | None = None
    opinions_views: OpinionsViewsResult | None = None
    preferences_patterns: PreferencesResult | None = None
    desires_needs: DesiresNeedsResult | None = None
    life_narrative: LifeNarrativeResult | None = None
    events: EventsResult | None = None
    entities_relationships: EntitiesResult | None = None


# =============================================================================
# =============================================================================
#
# BATCH EXTRACTION MODELS
#
# These models are for batch extraction where multiple messages are processed
# at once. Each item includes source attribution (source_message_id and
# source_quote) for traceability back to the original message.
#
# =============================================================================
# =============================================================================


# =============================================================================
# Batch 1. Core Identity
# =============================================================================

class BatchCoreIdentityItem(BaseModel):
    """A single identity fact with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    aspect: str = Field(
        description="Category of identity marker (e.g., age, profession, "
        "location, physical attribute, role, affiliation, condition, personality)"
    )
    state_value: str = Field(
        description="The actual value/state"
    )
    temporal: str | None = Field(
        default=None,
        description="Only if explicitly time-bound (e.g., 'currently', 'since 2020')"
    )
    relational_dimension: str | None = Field(
        default=None,
        description="Only if identity is relative to others (e.g., 'in my family', 'at work')"
    )


class BatchCoreIdentityResult(BaseModel):
    """Batch extraction result for core identity dimension."""

    has_content: bool = Field(
        description="Whether any identity information was found"
    )
    items: list[BatchCoreIdentityItem] = Field(
        default_factory=list,
        description="List of extracted identity facts with source attribution"
    )


class BatchCoreIdentityOutput(BaseModel):
    """Wrapper for core identity batch extraction output."""

    core_identity: BatchCoreIdentityResult


# =============================================================================
# Batch 2. Opinions & Views
# =============================================================================

class BatchOpinionItem(BaseModel):
    """A single opinion with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    about: str = Field(
        description="Topic/subject of the opinion"
    )
    view: str = Field(
        description="The stance/position taken"
    )
    qualifier: str | None = Field(
        default=None,
        description="Conditions, exceptions (e.g., 'unless...', 'except when...', 'probably')"
    )


class BatchOpinionsResult(BaseModel):
    """Batch extraction result for opinions/views dimension."""

    has_content: bool = Field(
        description="Whether any non-ephemeral opinions were found"
    )
    items: list[BatchOpinionItem] = Field(
        default_factory=list,
        description="List of extracted opinions with source attribution"
    )


class BatchOpinionsOutput(BaseModel):
    """Wrapper for opinions batch extraction output."""

    opinions_views: BatchOpinionsResult


# =============================================================================
# Batch 3. Preferences & Patterns
# =============================================================================

class BatchPreferenceItem(BaseModel):
    """A single preference with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    activity_category: str = Field(
        description="Broad domain (e.g., work, sleep, communication, eating, social)"
    )
    activity: str = Field(
        description="Specific activity or behavior"
    )
    preference: str = Field(
        description="The pattern or preference"
    )
    context: str | None = Field(
        default=None,
        description="Conditions when this applies/doesn't apply"
    )


class BatchPreferencesResult(BaseModel):
    """Batch extraction result for preferences/patterns dimension."""

    has_content: bool = Field(
        description="Whether any preferences or patterns were found"
    )
    items: list[BatchPreferenceItem] = Field(
        default_factory=list,
        description="List of extracted preferences with source attribution"
    )


class BatchPreferencesOutput(BaseModel):
    """Wrapper for preferences batch extraction output."""

    preferences_patterns: BatchPreferencesResult


# =============================================================================
# Batch 4. Desires, Wishes, Hopes & Needs
# =============================================================================

class BatchDesireItem(BaseModel):
    """A single desire with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    type: str = Field(
        description="Type of aspiration: need/want/wish/hope"
    )
    target: str = Field(
        description="What they aspire to"
    )
    is_active: str = Field(
        default="unknown",
        description="Whether desire is current: yes/no/unknown/explicitly_uncertain"
    )
    intensity: str | None = Field(
        default=None,
        description="Intensity modifier (e.g., desperately, really, somewhat)"
    )
    temporal: str | None = Field(
        default=None,
        description="When relevant (e.g., soon, someday, by January)"
    )


class BatchDesiresResult(BaseModel):
    """Batch extraction result for desires/needs dimension."""

    has_content: bool = Field(
        description="Whether any desires, wishes, hopes, or needs were found"
    )
    items: list[BatchDesireItem] = Field(
        default_factory=list,
        description="List of extracted desires with source attribution"
    )


class BatchDesiresOutput(BaseModel):
    """Wrapper for desires batch extraction output."""

    desires_needs: BatchDesiresResult


# =============================================================================
# Batch 5. Life Narrative
# =============================================================================

class BatchNarrativeItem(BaseModel):
    """A single narrative element with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    what_happened: str = Field(
        description="Core biographical fact, no temporal markers"
    )
    period: str | None = Field(
        default=None,
        description="All temporal information (e.g., 'five years', '2019', 'childhood')"
    )
    significance: str | None = Field(
        default=None,
        description="Only if explicitly stated how it affected them"
    )


class BatchNarrativeResult(BaseModel):
    """Batch extraction result for life narrative dimension."""

    has_content: bool = Field(
        description="Whether any life narrative elements were found"
    )
    items: list[BatchNarrativeItem] = Field(
        default_factory=list,
        description="List of extracted narrative elements with source attribution"
    )


class BatchNarrativeOutput(BaseModel):
    """Wrapper for narrative batch extraction output."""

    life_narrative: BatchNarrativeResult


# =============================================================================
# Batch 6. Events & Involvement
# =============================================================================

class BatchEventItem(BaseModel):
    """A single event with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    event: str = Field(
        description="What happened/is happening"
    )
    involvement: str = Field(
        description="How they participated (e.g., attended, organized, experiencing)"
    )
    temporal: str | None = Field(
        default=None,
        description="When/duration (e.g., yesterday, current, ongoing, last month)"
    )
    entities_involved: list[str] | None = Field(
        default=None,
        description="Entities involved (people, organizations, groups, etc.)"
    )
    outcome: str | None = Field(
        default=None,
        description="Only if explicitly stated result/consequence"
    )


class BatchEventsResult(BaseModel):
    """Batch extraction result for events dimension."""

    has_content: bool = Field(
        description="Whether any significant events were found"
    )
    items: list[BatchEventItem] = Field(
        default_factory=list,
        description="List of extracted events with source attribution"
    )


class BatchEventsOutput(BaseModel):
    """Wrapper for events batch extraction output."""

    events: BatchEventsResult


# =============================================================================
# Batch 7. Entities & Relationships
# =============================================================================

class BatchEntityItem(BaseModel):
    """A single entity with source attribution."""

    source_message_id: str = Field(
        description="The message ID where this was extracted from"
    )
    source_quote: str = Field(
        description="The exact quote from the message"
    )
    name: str = Field(
        description="Entity name or identifier (e.g., 'Sarah', 'Google', 'my boss')"
    )
    entity_type: str = Field(
        description="Entity type (e.g., person, organization, place, product, pet)"
    )
    mentioned_properties: list[PropertyItem] = Field(
        default_factory=list,
        description="Properties mentioned about this entity as key-value pairs"
    )
    relationship_indicators: list[str] = Field(
        default_factory=list,
        description="How entity relates to speaker (e.g., colleague, employer, hometown)"
    )
    interaction_metadata: InteractionMetadata | None = Field(
        default=None,
        description="How they interact with this entity (frequency, context, recency)"
    )


class BatchEntitiesResult(BaseModel):
    """Batch extraction result for entities dimension."""

    has_content: bool = Field(
        description="Whether any significant entities were found"
    )
    items: list[BatchEntityItem] = Field(
        default_factory=list,
        description="List of extracted entities with source attribution"
    )


class BatchEntitiesOutput(BaseModel):
    """Wrapper for entities batch extraction output."""

    entities_relationships: BatchEntitiesResult


# =============================================================================
# Batch Dimension Registry
# =============================================================================

BATCH_DIMENSION_MODELS = {
    "core_identity": BatchCoreIdentityOutput,
    "opinions_views": BatchOpinionsOutput,
    "preferences_patterns": BatchPreferencesOutput,
    "desires_needs": BatchDesiresOutput,
    "life_narrative": BatchNarrativeOutput,
    "events": BatchEventsOutput,
    "entities_relationships": BatchEntitiesOutput,
}
"""Maps dimension names to their batch Pydantic output models."""


# =============================================================================
# Batch Combined Extraction Result
# =============================================================================

class BatchProfilingDataExtractionResult(BaseModel):
    """Result container for profiling data extraction.

    All 7 dimension fields are optional:
    - None = dimension was not requested
    - has_content=False = requested but nothing found
    - has_content=True = requested and data found
    """

    core_identity: BatchCoreIdentityResult | None = None
    opinions_views: BatchOpinionsResult | None = None
    preferences_patterns: BatchPreferencesResult | None = None
    desires_needs: BatchDesiresResult | None = None
    life_narrative: BatchNarrativeResult | None = None
    events: BatchEventsResult | None = None
    entities_relationships: BatchEntitiesResult | None = None


# Backward compatibility alias
BatchFullExtractionResult = BatchProfilingDataExtractionResult


class BatchAll7Output(BaseModel):
    """Structured output model for extracting all 7 dimensions in a single LLM call.

    All fields are required for OpenAI structured output compatibility.
    Each dimension uses has_content=false with empty items when no data found.
    """

    core_identity: BatchCoreIdentityResult = Field(
        description="Core identity facts (age, profession, location, traits, etc.)"
    )
    opinions_views: BatchOpinionsResult = Field(
        description="Non-ephemeral opinions and views"
    )
    preferences_patterns: BatchPreferencesResult = Field(
        description="Stable preferences and behavioral patterns"
    )
    desires_needs: BatchDesiresResult = Field(
        description="Desires, wishes, hopes, and needs"
    )
    life_narrative: BatchNarrativeResult = Field(
        description="Life narrative and biographical facts"
    )
    events: BatchEventsResult = Field(
        description="Significant events and involvements"
    )
    entities_relationships: BatchEntitiesResult = Field(
        description="Entities (people, orgs, places) and relationships"
    )
