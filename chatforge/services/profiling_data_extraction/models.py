"""
Pydantic models for CPDE-7 structured LLM output.

These models define the output schema for each extraction dimension.
Used with LangChain's `with_structured_output()` for guaranteed schema compliance.

Each dimension has:
- An item model (single extracted fact)
- A result model (collection of items + has_content flag)
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
    people_involved: list[str] | None = Field(
        default=None,
        description="Others involved (individuals, relationships, organizations)"
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
    type: str = Field(
        description="Entity type (e.g., person, organization, place, product, pet)"
    )
    mentioned_properties: dict | None = Field(
        default=None,
        description="Properties mentioned about this entity"
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
