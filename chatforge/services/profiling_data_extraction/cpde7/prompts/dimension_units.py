"""
CPDE-7 Dimension Units for Proteas.

Each dimension is defined as a PromptTemplateUnit that can be combined
with others to create extraction prompts.
"""

from proteas import PromptTemplateUnit


# =============================================================================
# Header Unit (always included)
# =============================================================================

HEADER_UNIT = PromptTemplateUnit(
    name="header",
    order=1,
    content="""Your job is to extract profiling data from the given batch of chat messages.
Extract information across the specified dimensions.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Maintain dimensional boundaries - put data in the correct dimension
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)""",
)


# =============================================================================
# Dimension Units
# =============================================================================

CORE_IDENTITY_UNIT = PromptTemplateUnit(
    name="core_identity",
    order=10,
    prefix="=" * 77 + "\nDIMENSION: CORE IDENTITY\n" + "=" * 77,
    content="""
### What It Is
- What someone IS (roles, attributes, states, affiliations)
- Stable characteristics that define them
- Permanent or long-lasting aspects of who they are
- Examples: age, profession, location, physical attributes, chronic conditions, personality traits

### What It Is Not
- What they THINK → goes to Opinions & Views
- What they WANT → goes to Desires, Wishes, Hopes & Needs
- What they DID → goes to Events or Life Narrative
- What they PREFER → goes to Preferences & Patterns
- Temporary states → goes to Events (e.g., "I'm sick" is an event, not identity)

### Examples
✓ "I'm a 34-year-old software engineer" → aspect: "age", state_value: "34 years old"
✓ "I'm tall and diabetic" → aspect: "physical_attribute", state_value: "tall"
✗ "I'm sick" → goes to Events (temporary state)
✗ "I think remote work is better" → goes to Opinions

### Schema
{
  "core_identity": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "aspect": "...", "state_value": "...", "temporal": null, "relational_dimension": null}]
  }
}""",
)


OPINIONS_VIEWS_UNIT = PromptTemplateUnit(
    name="opinions_views",
    order=20,
    prefix="=" * 77 + "\nDIMENSION: OPINIONS & VIEWS\n" + "=" * 77,
    content="""
### What It Is
- Lasting beliefs and worldviews
- Beliefs about how things are or should be
- Value judgments that reflect worldview
- Stances on topics they'd likely hold tomorrow, next month

### What It Is Not
- Momentary reactions → skip ("This coffee is cold")
- Situational complaints → skip ("Traffic is bad today")
- What they ARE → goes to Core Identity
- What they WANT → goes to Desires

### Examples
✓ "Remote work is the future" → about: "remote work", view: "is the future"
✓ "AI is dangerous unless properly regulated" → about: "AI", view: "dangerous", qualifier: "unless properly regulated"
✗ "This meeting is pointless" → skip (ephemeral frustration)

### Schema
{
  "opinions_views": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "about": "...", "view": "...", "qualifier": null}]
  }
}""",
)


PREFERENCES_PATTERNS_UNIT = PromptTemplateUnit(
    name="preferences_patterns",
    order=30,
    prefix="=" * 77 + "\nDIMENSION: PREFERENCES & BEHAVIORAL PATTERNS\n" + "=" * 77,
    content="""
### What It Is
- Consistent behavioral choices
- Stated preferences for how they do things
- Habitual tendencies
- Key indicators: "always", "never", "usually", "typically", "prefer", "tend to"

### What It Is Not
- One-time actions → goes to Events
- What they ARE → goes to Core Identity
- What they BELIEVE → goes to Opinions & Views

### Examples
✓ "I always code better at night" → activity_category: "work", preference: "better at night"
✓ "I prefer texting over calling" → activity_category: "communication", preference: "texting over calling"
✗ "I skipped breakfast today" → goes to Events (one-time action)

### Schema
{
  "preferences_patterns": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "activity_category": "...", "activity": "...", "preference": "...", "context": null}]
  }
}""",
)


DESIRES_NEEDS_UNIT = PromptTemplateUnit(
    name="desires_needs",
    order=40,
    prefix="=" * 77 + "\nDIMENSION: DESIRES, WISHES, HOPES & NEEDS\n" + "=" * 77,
    content="""
### What It Is
- What the person wants, needs, wishes for, or hopes for
- Explicit desires: "I want...", "I need...", "I wish...", "I hope..."
- Goal statements: "My goal is...", "I'm trying to..."

### Type Distinctions
- need: Essential, required ("I need health insurance")
- want: Active desire ("I want to change careers")
- wish: Hypothetical, wistful ("I wish I could travel more")
- hope: Optimistic aspiration ("I hope to get promoted")

### Examples
✓ "I really want to reconnect with my daughter" → type: "want", target: "reconnect with daughter"
✓ "I hope to get promoted" → type: "hope", target: "get promoted"
✗ "I'm a very ambitious person" → goes to Core Identity

### Schema
{
  "desires_needs": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "type": "...", "target": "...", "is_active": "yes/no", "intensity": null, "temporal": null}]
  }
}""",
)


LIFE_NARRATIVE_UNIT = PromptTemplateUnit(
    name="life_narrative",
    order=50,
    prefix="=" * 77 + "\nDIMENSION: LIFE NARRATIVE\n" + "=" * 77,
    content="""
### What It Is
- Past experiences that form biographical arc
- Life chapters and phases
- Formative experiences
- Major transitions (career, location, relationship)

### What It Is Not
- Current/recent discrete occurrences → goes to Events
- Future planned occurrences → goes to Events
- What they ARE now → goes to Core Identity

### Key Distinction: Life Narrative vs Events
- "I lived in Tokyo for five years" → Life Narrative (biographical chapter)
- "I'm moving to Tokyo next month" → Events (upcoming occurrence)

### Examples
✓ "I lived in Tokyo for 3 years" → what_happened: "lived in Tokyo", period: "3 years"
✓ "Growing up poor shaped who I am" → what_happened: "grew up poor", significance: "shaped who I am"
✗ "I'm going through a divorce" → goes to Events (current, ongoing)

### Schema
{
  "life_narrative": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "what_happened": "...", "period": null, "significance": null}]
  }
}""",
)


EVENTS_UNIT = PromptTemplateUnit(
    name="events",
    order=60,
    prefix="=" * 77 + "\nDIMENSION: EVENTS & INVOLVEMENT\n" + "=" * 77,
    content="""
### What It Is
- Discrete occurrences (past, current, or future)
- Temporary ongoing states ("I'm sick", "I'm moving")
- Planned future events ("visiting Greece next summer")

### What It Is Not
- Permanent characteristics → goes to Core Identity
- Past biographical chapters → goes to Life Narrative
- Habitual patterns → goes to Preferences

### Temporary vs Permanent State
- "I'm sick" → Event (temporary)
- "I'm a teacher" → Identity (permanent role)
- "I'm pregnant" → Event (temporary state with endpoint)
- "I'm diabetic" → Identity (chronic condition)

### Examples
✓ "I'm interviewing at Google" → event: "job interview", involvement: "candidate", entities_involved: ["Google"]
✓ "My team won the hackathon" → event: "hackathon", involvement: "participant", outcome: "won"
✗ "I lived in Paris for 5 years" → goes to Life Narrative

### Schema
{
  "events": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "event": "...", "involvement": "...", "temporal": null, "entities_involved": null, "outcome": null}]
  }
}""",
)


ENTITIES_RELATIONSHIPS_UNIT = PromptTemplateUnit(
    name="entities_relationships",
    order=70,
    prefix="=" * 77 + "\nDIMENSION: ENTITIES & RELATIONSHIPS\n" + "=" * 77,
    content="""
### What It Is
- People: Named individuals or referenced relationships ("my boss", "Sarah")
- Organizations: Companies, schools, teams, institutions
- Places: Cities, countries, venues with significance
- Products/Technologies: Tools, platforms they use
- Pets: Animals they have relationship with

### What It Is Not
- Generic mentions without relationship context ("Apple announced something")
- Entities they're merely discussing, not connected to

### Parsing Rule
When entities are introduced with type descriptors (e.g., 'My dog Max', 'My cat Luna'), extract the descriptor as a property (species: dog, species: cat)

### Examples
✓ "Sarah from marketing mentors me weekly" → name: "Sarah", entity_type: "person", mentioned_properties: [{"key": "department", "value": "marketing"}]
✓ "My dog Max keeps me company" → name: "Max", entity_type: "pet", mentioned_properties: [{"key": "species", "value": "dog"}]
✗ "Apple announced a new iPhone" → skip (no personal relationship)

### Schema
{
  "entities_relationships": {
    "has_content": true/false,
    "items": [{"source_message_id": "...", "source_quote": "...", "name": "...", "entity_type": "...", "mentioned_properties": [], "relationship_indicators": [], "interaction_metadata": null}]
  }
}""",
)


# =============================================================================
# Messages Unit (placeholder for actual messages)
# =============================================================================

MESSAGES_UNIT = PromptTemplateUnit(
    name="messages",
    order=80,
    prefix="=" * 77 + "\nMESSAGES TO ANALYZE\n" + "=" * 77,
    content="$messages",
)


# =============================================================================
# Instructions Unit (always included)
# =============================================================================

INSTRUCTIONS_UNIT = PromptTemplateUnit(
    name="instructions",
    order=90,
    prefix="=" * 77 + "\nEXTRACTION INSTRUCTIONS\n" + "=" * 77,
    content="""
1. Read through ALL messages carefully
2. For each piece of profiling information found:
   - Determine which dimension it belongs to
   - Extract with proper attribution (source_message_id, source_quote)
   - Respect dimensional boundaries
3. Return the complete JSON structure with all requested dimensions
4. Empty dimensions should have has_content: false and items: []""",
)


# =============================================================================
# Registry
# =============================================================================

DIMENSION_UNITS = {
    "core_identity": CORE_IDENTITY_UNIT,
    "opinions_views": OPINIONS_VIEWS_UNIT,
    "preferences_patterns": PREFERENCES_PATTERNS_UNIT,
    "desires_needs": DESIRES_NEEDS_UNIT,
    "life_narrative": LIFE_NARRATIVE_UNIT,
    "events": EVENTS_UNIT,
    "entities_relationships": ENTITIES_RELATIONSHIPS_UNIT,
}

DIMENSION_NAMES = list(DIMENSION_UNITS.keys())


def get_dimension_unit(name: str) -> PromptTemplateUnit:
    """Get a dimension unit by name."""
    if name not in DIMENSION_UNITS:
        raise ValueError(f"Unknown dimension: {name}. Valid: {DIMENSION_NAMES}")
    return DIMENSION_UNITS[name]
