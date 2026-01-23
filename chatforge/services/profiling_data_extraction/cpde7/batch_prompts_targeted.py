"""
Targeted batch prompts for CPDE-7 (Conversational Profiling Data Extraction - 7 Dimensions).

This module uses Option B: Inline Markers for targeted extraction.

Messages are formatted with role markers:
- "(TARGET)" - Extract profiling data from these messages
- "(CONTEXT)" - Use for understanding references only, do NOT extract from

This prevents extracting AI assumptions, reflections, and leading questions as profile facts.
Only explicitly stated information in TARGET messages becomes profile data.

Usage:
    # Format messages with markers
    messages = format_messages_with_markers(
        messages=[...],
        target_roles=["user"],  # Only extract from user messages
    )

    # Use with structured output
    prompt = CPDE_ALL_7_TARGETED.format(messages=messages)
    structured_llm = llm.with_structured_output(BatchAll7Output)
    result = structured_llm.invoke([HumanMessage(content=prompt)])

See batch_cpde7_improvement.md for rationale and design decisions.
"""

# =============================================================================
# TARGETING RULES (shared across all prompts)
# =============================================================================

TARGETING_RULES = """
=============================================================================
TARGETING RULES (CRITICAL)
=============================================================================

Messages are marked with either "(TARGET)" or "(CONTEXT)":

**TARGET messages** - Extract profiling data ONLY from these
**CONTEXT messages** - Use for understanding references, do NOT extract from

CRITICAL RULES:
1. source_message_id MUST reference a TARGET message only
2. Do NOT extract facts stated only in CONTEXT messages
3. If a TARGET message confirms something from CONTEXT, extract it from TARGET
4. CONTEXT helps you understand what TARGET messages mean

### Why This Matters

CONTEXT messages (e.g., assistant responses) may contain:
- Assumptions about the person
- Reflections/summaries of what was said
- Leading questions or hypotheses
- AI-generated characterizations

These should NOT become profile facts unless the person explicitly confirms them
in a TARGET message.

### Confirmation Strength

When a TARGET message confirms something from CONTEXT:

STRONG confirmation (DO extract):
- "Yes, exactly"
- "That's right"
- "Absolutely"
- "Yes, I do hate my job"

WEAK confirmation (DO NOT extract):
- "Maybe"
- "I guess"
- "I don't know"
- "Perhaps"
- "Sort of"

Only extract from strong, clear confirmations.
"""

# =============================================================================
# SINGLE DIMENSION: CORE IDENTITY ONLY (TARGETED)
# =============================================================================

CPDE_CORE_IDENTITY_TARGETED = """

Your job is to extract CORE IDENTITY information from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT IS CORE IDENTITY?
=============================================================================

### What It Is
- What someone IS (roles, attributes, states, affiliations)
- Stable characteristics that define them
- Permanent or long-lasting aspects of who they are

### Categories of Identity
- **Age**: "I'm 34", "I'm in my 40s"
- **Profession/Role**: "I'm a software engineer", "I'm a manager", "I'm a student"
- **Location**: "I live in Seattle", "I'm based in London"
- **Physical attributes**: "I'm tall", "I have red hair"
- **Medical conditions** (chronic/defining): "I'm diabetic", "I'm deaf", "I have ADHD"
- **Personality traits**: "I'm an introvert", "I'm the skeptic in my group"
- **Affiliations**: "I'm a Democrat", "I'm Catholic", "I'm vegan"
- **Family roles**: "I'm a mother of three", "I'm the oldest sibling"
- **Nationality/Ethnicity**: "I'm Japanese", "I'm Mexican-American"

### What It Is NOT (do not extract these)
- What they THINK → Opinions & Views dimension
- What they WANT → Desires dimension
- What they DID → Events or Life Narrative dimension
- What they PREFER → Preferences dimension
- Temporary states → Events dimension (e.g., "I'm sick", "I'm tired", "I'm moving")

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "I'm a 34-year-old software engineer"
  → Item 1: aspect: "age", state_value: "34 years old"
  → Item 2: aspect: "profession", state_value: "software engineer"

✓ TARGET: "I'm tall and diabetic"
  → Item 1: aspect: "physical_attribute", state_value: "tall"
  → Item 2: aspect: "medical_condition", state_value: "diabetic"

✓ TARGET: "I'm the skeptic in my group"
  → aspect: "personality_role", state_value: "skeptic", relational_dimension: "in my group"

✓ CONTEXT: "You seem like an introvert"
  TARGET: "Yes, I definitely am"
  → aspect: "personality", state_value: "introvert" (from TARGET confirmation)

✗ CONTEXT: "You seem like someone who values efficiency over relationships"
  TARGET: "Maybe, I guess"
  → Do NOT extract (weak confirmation)

✗ CONTEXT: "So you're a workaholic?"
  TARGET: "I don't know about that"
  → Do NOT extract (denial/uncertainty)

✗ TARGET: "I always code better at night"
  → Do NOT extract - this is a PREFERENCE (how they work), not identity (who they are)

✗ TARGET: "I really want to transition into AI/ML"
  → Do NOT extract - this is a DESIRE, not identity

✗ TARGET: "I'm currently interviewing at Google"
  → Do NOT extract - this is an EVENT (temporary), not identity

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "core_identity": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "aspect": "string - category (age, profession, location, medical_condition, personality, etc.)",
        "state_value": "string - the actual value",
        "temporal": "string or null - only if explicitly time-bound (e.g., 'since 2015', 'currently')",
        "relational_dimension": "string or null - only if relative to others (e.g., 'in my family', 'at work')"
      }}
    ]
  }}
}}

If no identity information found in TARGET messages, return: {{"core_identity": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for identity statements ONLY in TARGET messages
4. Use CONTEXT to understand what TARGET messages mean
5. For confirmations, only extract if TARGET gives STRONG confirmation
6. Split compound identity statements into separate items
7. For each identity fact found in TARGET:
   - Categorize the aspect (age, profession, location, etc.)
   - Extract the state_value
   - Add temporal only if explicitly time-bound
   - Add relational_dimension only if relative to others
   - Include source attribution from TARGET message
8. Return the complete JSON structure
9. If no identity information in TARGET messages, return has_content: false
"""

# =============================================================================
# SINGLE DIMENSION: OPINIONS & VIEWS ONLY (TARGETED)
# =============================================================================

CPDE_OPINIONS_VIEWS_TARGETED = """

Your job is to extract OPINIONS & VIEWS from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT ARE OPINIONS & VIEWS?
=============================================================================

### What It Is
- Lasting beliefs and worldviews
- Beliefs about how things are or should be
- Value judgments that reflect worldview
- Stances on topics they'd likely hold tomorrow, next month

### The KEY TEST
Will this opinion likely persist beyond the current context?

### Types of Opinions
- **Beliefs about topics**: "Remote work is the future", "AI is dangerous"
- **Value judgments**: "College is overrated", "Money isn't everything"
- **Preferences as beliefs**: "Python is better than Java" (opinion, not preference)
- **Conditional opinions**: "X is good unless Y" (capture the qualifier)

### What It Is NOT (do not extract these)
- Momentary reactions → skip ("This coffee is cold")
- Situational complaints → skip ("Traffic is bad today")
- Temporary states → skip ("I'm annoyed right now")
- What they ARE → Core Identity dimension
- What they WANT → Desires dimension
- What they DO habitually → Preferences dimension

### Opinion vs Desire - How to Tell

Opinions express beliefs about THE WORLD:
- "Remote work IS the future" (belief about how things are)
- "AI IS dangerous" (judgment about something external)

Desires express PERSONAL wants:
- "I WANT to work remotely" (personal aspiration)
- "I HOPE to transition to AI" (personal goal)

Quick test:
- "X is/are/should be..." → Opinion (about the world)
- "I want/hope/wish/need..." → Desire (about themselves)

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "Remote work is the future"
  → about: "remote work", view: "is the future"

✓ TARGET: "I think college is overrated and too expensive"
  → Item 1: about: "college", view: "overrated"
  → Item 2: about: "college", view: "too expensive"

✓ TARGET: "AI is dangerous unless properly regulated"
  → about: "AI", view: "dangerous", qualifier: "unless properly regulated"

✓ CONTEXT: "Do you think remote work is better?"
  TARGET: "Absolutely, it's the future"
  → about: "remote work", view: "is the future" (from TARGET)

✗ CONTEXT: "It sounds like you hate your job"
  TARGET: "Maybe, I don't know"
  → Do NOT extract (weak/uncertain response)

✗ TARGET: "This meeting is pointless" → skip (ephemeral frustration)

✗ TARGET: "I really want to transition into AI/ML"
  → Do NOT extract - "I want" signals a personal desire, not a belief about AI/ML itself

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "opinions_views": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "about": "string - topic/subject of the opinion",
        "view": "string - the stance/position taken",
        "qualifier": "string or null - conditions, exceptions (e.g., 'unless...', 'except when...', 'probably')"
      }}
    ]
  }}
}}

If no opinions found in TARGET messages, return: {{"opinions_views": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for opinion statements ONLY in TARGET messages
4. Use CONTEXT to understand what TARGET messages mean
5. Apply the persistence test: would they likely hold this view tomorrow?
6. For confirmations, only extract if TARGET gives STRONG confirmation
7. Split compound opinions into separate items
8. For each opinion found in TARGET:
   - Identify what it's about
   - Extract the view/stance
   - Add qualifier only if there are conditions/exceptions
   - Include source attribution from TARGET message
9. Return the complete JSON structure
10. If no lasting opinions in TARGET messages, return has_content: false
"""

# =============================================================================
# SINGLE DIMENSION: PREFERENCES & PATTERNS ONLY (TARGETED)
# =============================================================================

CPDE_PREFERENCES_PATTERNS_TARGETED = """

Your job is to extract PREFERENCES & BEHAVIORAL PATTERNS from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- Extract ONLY recurring patterns - skip one-time actions
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT ARE PREFERENCES & PATTERNS?
=============================================================================

### What It Is
- Consistent behavioral choices
- Stated preferences for how they do things
- Habitual tendencies
- Recurring approaches to activities

### Key Indicators
- "always", "never", "usually", "typically", "prefer", "tend to"
- "I can't [X] without [Y]"
- "I [verb] better when..."
- Comparative preferences ("X over Y")

### Activity Categories (examples, not exhaustive)
work, communication, sleep, eating, exercise, learning, social, travel, shopping, entertainment, productivity, health

### What It Is NOT (do not extract these)
- One-time actions → Events dimension ("I skipped breakfast today")
- What they ARE → Core Identity dimension ("I'm a morning person")
- What they BELIEVE → Opinions dimension ("I think breakfast is important")
- What they WANT → Desires dimension ("I want to exercise more")

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "I always code better at night"
  → activity_category: "work", activity: "coding", preference: "better at night"

✓ TARGET: "I prefer texting over calling unless it's urgent"
  → activity_category: "communication", activity: "contacting people", preference: "texting over calling", context: "unless urgent"

✓ TARGET: "I can't sleep without white noise and I always read before bed"
  → Item 1: activity_category: "sleep", activity: "falling asleep", preference: "requires white noise"
  → Item 2: activity_category: "sleep", activity: "bedtime routine", preference: "always reads before bed"

✓ CONTEXT: "Do you usually work late?"
  TARGET: "Yes, I always code better at night"
  → activity_category: "work", activity: "coding", preference: "better at night" (from TARGET)

✗ CONTEXT: "You seem like someone who avoids confrontation"
  TARGET: "Maybe"
  → Do NOT extract (weak confirmation of AI assumption)

✗ TARGET: "I skipped breakfast today" → Events (one-time action)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "preferences_patterns": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "activity_category": "string - broad domain (work, sleep, communication, eating, etc.)",
        "activity": "string - specific activity or behavior",
        "preference": "string - the pattern or preference",
        "context": "string or null - conditions when this applies/doesn't apply"
      }}
    ]
  }}
}}

If no preferences found in TARGET messages, return: {{"preferences_patterns": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for preference/pattern statements ONLY in TARGET messages
4. Look for pattern indicators: always, never, usually, prefer, tend to
5. For confirmations, only extract if TARGET gives STRONG confirmation
6. Split compound patterns into separate items
7. For each pattern found in TARGET:
   - Categorize the activity domain
   - Identify the specific activity
   - Extract the preference/pattern
   - Add context only if conditions are stated
   - Include source attribution from TARGET message
8. Return the complete JSON structure
9. If no patterns in TARGET messages, return has_content: false
"""

# =============================================================================
# SINGLE DIMENSION: DESIRES, WISHES, HOPES & NEEDS ONLY (TARGETED)
# =============================================================================

CPDE_DESIRES_NEEDS_TARGETED = """

Your job is to extract DESIRES, WISHES, HOPES & NEEDS from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- Extract ONLY the aspiration itself - consequences go elsewhere
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT ARE DESIRES & NEEDS?
=============================================================================

### What It Is
- What the person wants, needs, wishes for, or hopes for
- Explicit desires: "I want...", "I need...", "I wish...", "I hope..."
- Goal statements: "My goal is...", "I'm trying to..."
- Implied needs from complaints: "I'm so burnt out" → may imply need for rest

### Type Distinctions (controlled vocabulary)
- **need**: Essential, required, necessary ("I need health insurance")
- **want**: Active desire, something they're seeking ("I want to change careers")
- **wish**: Hypothetical, wistful, may not be actionable ("I wish I could travel more")
- **hope**: Optimistic aspiration, uncertain outcome ("I hope to get promoted")

### is_active Values
- **yes**: Currently active desire
- **no**: Past desire that's no longer active
- **unknown**: Can't determine from context
- **explicitly_uncertain**: They expressed uncertainty ("I'm not sure I want...")

### What It Is NOT (do not extract these)
- What they ARE → Core Identity dimension
- What they BELIEVE → Opinions dimension
- What they consistently DO → Preferences dimension
- Past aspirations stated as current fact → check is_active

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "I really want to reconnect with my daughter"
  → type: "want", target: "reconnect with daughter", is_active: "yes", intensity: "really"

✓ TARGET: "I desperately need better work-life balance"
  → type: "need", target: "better work-life balance", is_active: "yes", intensity: "desperately"

✓ TARGET: "I hope to get promoted and I want to eventually lead a team"
  → Item 1: type: "hope", target: "get promoted", is_active: "yes"
  → Item 2: type: "want", target: "lead a team", is_active: "yes", temporal: "eventually"

✓ CONTEXT: "Do you want to change careers?"
  TARGET: "Yes, I really do"
  → type: "want", target: "change careers", is_active: "yes", intensity: "really" (from TARGET)

✗ CONTEXT: "It sounds like you need a vacation"
  TARGET: "Maybe"
  → Do NOT extract (weak confirmation of AI suggestion)

✗ CONTEXT: "Are you afraid of being abandoned?"
  TARGET: "I don't know"
  → Do NOT extract (uncertainty, AI hypothesis)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "desires_needs": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "type": "string - need/want/wish/hope (pick one)",
        "target": "string - what they aspire to",
        "is_active": "string - yes/no/unknown/explicitly_uncertain",
        "intensity": "string or null - desperately/really/somewhat/slightly/etc.",
        "temporal": "string or null - soon/someday/by January/eventually/etc."
      }}
    ]
  }}
}}

If no desires found in TARGET messages, return: {{"desires_needs": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for desire/need statements ONLY in TARGET messages
4. Classify each as need/want/wish/hope based on definitions
5. Determine if the desire is currently active
6. For confirmations, only extract if TARGET gives STRONG confirmation
7. Split compound desires into separate items
8. For each desire found in TARGET:
   - Classify the type
   - Extract the target
   - Determine is_active status
   - Add intensity only if explicitly stated
   - Add temporal only if timeframe mentioned
   - Include source attribution from TARGET message
9. Return the complete JSON structure
10. If no desires in TARGET messages, return has_content: false
"""

# =============================================================================
# SINGLE DIMENSION: LIFE NARRATIVE ONLY (TARGETED)
# =============================================================================

CPDE_LIFE_NARRATIVE_TARGETED = """

Your job is to extract LIFE NARRATIVE elements from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- Extract ONLY past biographical experiences - not current/future events
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT IS LIFE NARRATIVE?
=============================================================================

### What It Is
- Past experiences that form biographical arc
- Life chapters and phases
- Formative experiences
- Major transitions (career, location, relationship)
- Origin stories, challenges overcome, educational journey

### Key Distinction: Life Narrative vs Events
- Life Narrative = PAST biographical chapters ("I lived in Tokyo for five years")
- Events = CURRENT or FUTURE occurrences ("I'm moving to Tokyo next month")

### What It Is NOT (do not extract these)
- Current/recent discrete occurrences → Events dimension
- Future planned occurrences → Events dimension
- Temporary states → Events dimension
- What they ARE now → Core Identity dimension

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "I lived in Tokyo for five years"
  → what_happened: "lived in Tokyo", period: "five years"

✓ TARGET: "I got divorced in 2019 and it freed me to pursue my passions"
  → what_happened: "got divorced", period: "2019", significance: "freed me to pursue my passions"

✓ TARGET: "Growing up poor in rural Texas shaped everything about who I am"
  → what_happened: "grew up poor in rural Texas", period: "childhood", significance: "shaped everything about who I am"

✓ CONTEXT: "Tell me about your background"
  TARGET: "I dropped out of college and started my own company"
  → Item 1: what_happened: "dropped out of college"
  → Item 2: what_happened: "started own company", period: "after dropping out"

✗ CONTEXT: "So you had a difficult childhood?"
  TARGET: "I guess so"
  → Do NOT extract (weak confirmation of AI characterization)

✗ TARGET: "I'm going through a divorce" → Events (current, ongoing)
✗ TARGET: "I'm moving to Seattle next month" → Events (future)

=============================================================================
EXTRACTION RULES
=============================================================================

### what_happened
- Core biographical fact ONLY, no temporal markers
- ✓ "served in military", "lived in Paris", "got divorced"
- ✗ "served in military for 3 years" (move duration to period)

### period
- ALL temporal information
- ✓ "three years", "during college", "2008", "childhood", "at age 12"
- If no temporal info given, use null

### significance
- ONLY if they explicitly state how it affected them
- ✓ "taught me resilience", "changed my perspective", "made me who I am"
- ✗ Don't infer meaning they didn't express
- "It was tough" is NOT significance unless they say it changed them

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "life_narrative": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "what_happened": "string - core biographical fact, no temporal markers",
        "period": "string or null - all temporal information",
        "significance": "string or null - only if explicitly stated how it affected them"
      }}
    ]
  }}
}}

If no narrative found in TARGET messages, return: {{"life_narrative": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for biographical statements ONLY in TARGET messages
4. Distinguish past biographical info from current events
5. For confirmations, only extract if TARGET gives STRONG confirmation
6. Split complex life sequences into separate items
7. For each narrative element found in TARGET:
   - Extract what_happened (no temporal markers)
   - Move ALL temporal info to period
   - Add significance ONLY if explicitly stated
   - Include source attribution from TARGET message
8. Return the complete JSON structure
9. If no life narrative in TARGET messages, return has_content: false
"""

# =============================================================================
# SINGLE DIMENSION: EVENTS & INVOLVEMENT ONLY (TARGETED)
# =============================================================================

CPDE_EVENTS_TARGETED = """

Your job is to extract EVENTS & INVOLVEMENT from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- Extract ONLY significant events - skip routine activities
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT ARE EVENTS?
=============================================================================

### What It Is
- Discrete occurrences (past, current, or future)
- Temporary ongoing states ("I'm sick", "I'm moving", "I'm renovating")
- Planned future events ("visiting Greece next summer")
- Things happening TO them or WITH them

### The KEY TEST
Is something temporary happening that they're experiencing or participating in?

### Temporary vs Permanent State
- "I'm sick" → Event (temporary)
- "I'm a teacher" → Identity (permanent role)
- "I'm pregnant" → Event (temporary state with endpoint)
- "I'm divorced" → Identity (permanent status)
- "I'm recovering from surgery" → Event (temporary)
- "I'm diabetic" → Identity (chronic condition)

### What It Is NOT (do not extract these)
- Opinions → Opinions dimension
- Permanent characteristics → Core Identity dimension
- Chronic/defining conditions → Core Identity dimension
- Past biographical chapters → Life Narrative dimension
- Aspirations → Desires dimension
- Habitual patterns → Preferences dimension
- Observations without involvement → skip ("there was an earthquake")

=============================================================================
SIGNIFICANCE FILTER
=============================================================================

**Always extract:**
- Life milestones (graduation, marriage, birth, death)
- Professional changes (promotion, job loss, interview)
- Health events (sick, injured, surgery, recovering)
- Achievements (won award, completed marathon, published)
- Crises (accident, emergency, major setback)

**Usually extract:**
- Significant social events (wedding attended, reunion)
- Travel (trips, visits, relocations in progress)
- Major purchases/decisions

**Usually skip:**
- Routine activities ("had lunch", "went shopping")
- Daily occurrences ("commuted", "had a meeting")
- Minor inconveniences

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "I'm sick with the flu"
  → event: "sick with flu", involvement: "experiencing", temporal: "current"

✓ TARGET: "I just had a three-hour interview with Google"
  → event: "job interview", involvement: "candidate", temporal: "just had", entities_involved: ["Google"]

✓ TARGET: "My team won the hackathon last weekend!"
  → event: "hackathon", involvement: "participant", temporal: "last weekend", entities_involved: ["my team"], outcome: "won"

✓ CONTEXT: "How are you feeling?"
  TARGET: "Terrible, I've been sick with the flu all week"
  → event: "sick with flu", involvement: "experiencing", temporal: "all week" (from TARGET)

✗ CONTEXT: "It sounds like you're going through a rough time"
  TARGET: "I guess"
  → Do NOT extract (weak confirmation of AI characterization)

✗ TARGET: "Had lunch" → skip (routine activity)
✗ TARGET: "I lived in Paris for 5 years" → Life Narrative (past biographical)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "events": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "event": "string - what happened/is happening",
        "involvement": "string - how they participated (attended, organized, experiencing, victim, etc.)",
        "temporal": "string or null - when/duration (yesterday, current, ongoing, next week, etc.)",
        "entities_involved": ["array of strings"] or null - others involved,
        "outcome": "string or null - only if explicitly stated result"
      }}
    ]
  }}
}}

If no events found in TARGET messages, return: {{"events": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for event statements ONLY in TARGET messages
4. Apply significance filter - skip routine activities
5. Distinguish events from life narrative (current/future vs past biographical)
6. For confirmations, only extract if TARGET gives STRONG confirmation
7. Split compound events into separate items
8. For each event found in TARGET:
   - Describe the event
   - Identify their involvement/role
   - Add temporal info if stated
   - Add entities_involved if mentioned
   - Add outcome only if explicitly stated
   - Include source attribution from TARGET message
9. Return the complete JSON structure
10. If no significant events in TARGET messages, return has_content: false
"""

# =============================================================================
# SINGLE DIMENSION: ENTITIES & RELATIONSHIPS ONLY (TARGETED)
# =============================================================================

CPDE_ENTITIES_RELATIONSHIPS_TARGETED = """

Your job is to extract ENTITIES & RELATIONSHIPS from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- Extract ONLY entities with personal connection - skip generic mentions
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
WHAT ARE ENTITIES?
=============================================================================

### What It Is
- **People**: Named individuals or referenced relationships ("my boss", "Sarah")
- **Organizations**: Companies, schools, teams, groups, institutions
- **Places**: Cities, countries, venues, locations with significance
- **Products/Technologies**: Tools, platforms, products they use
- **Pets**: Animals they own or care for
- **Other**: Any significant named entity relevant to understanding them

### Extraction Priority
Focus on entities that reveal:
- Social/professional network
- Tools and environment they operate in
- Places significant to their life
- Organizations they're affiliated with

### What It Is NOT (do not extract these)
- Generic mentions without relationship context ("Apple announced something")
- Entities they're merely discussing, not connected to
- Passing references with no profiling value

=============================================================================
EXAMPLES
=============================================================================

✓ TARGET: "Sarah from marketing has been mentoring me weekly"
  → name: "Sarah", entity_type: "person", mentioned_properties: [{{"key": "department", "value": "marketing"}}],
    relationship_indicators: ["colleague", "mentor"], interaction_metadata: {{"frequency": "weekly", "context": "professional", "recency": null}}

✓ TARGET: "I've been using Notion for everything since I left Google"
  → Item 1: name: "Notion", entity_type: "product", mentioned_properties: [], relationship_indicators: ["tool"],
    interaction_metadata: {{"frequency": "regular", "context": null, "recency": "current"}}
  → Item 2: name: "Google", entity_type: "organization", mentioned_properties: [], relationship_indicators: ["employer"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "former"}}

✓ TARGET: "My dog Max is getting old and my cat Luna keeps him company"
  → Item 1: name: "Max", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "dog"}}, {{"key": "age", "value": "old"}}],
    relationship_indicators: ["pet"]
  → Item 2: name: "Luna", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "cat"}}],
    relationship_indicators: ["pet"]

✓ CONTEXT: "Who do you work with?"
  TARGET: "My colleague Sarah mentors me"
  → name: "Sarah", entity_type: "person", relationship_indicators: ["colleague", "mentor"] (from TARGET)

✗ CONTEXT: "It sounds like your boss is difficult"
  TARGET: "Maybe"
  → Do NOT extract (weak confirmation of AI characterization about entity)

✗ TARGET: "Apple announced a new iPhone" → skip (no personal relationship)

=============================================================================
PARSING RULE
=============================================================================

When entities are introduced with type descriptors (e.g., 'My dog Max', 'My cat Luna'),
extract the descriptor as a property (species: dog, species: cat)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object:

{{
  "entities_relationships": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "name": "string - entity name or identifier (e.g., 'Sarah', 'Google', 'my boss')",
        "entity_type": "string - person/organization/place/product/technology/pet/etc.",
        "mentioned_properties": [{{"key": "property_name", "value": "property_value"}}] - list of key-value pairs, empty list if none,
        "relationship_indicators": ["array of relationship types (colleague, employer, hometown, tool, etc.)"],
        "interaction_metadata": {{"frequency": "string or null", "context": "string or null", "recency": "string or null"}} or null
      }}
    ]
  }}
}}

If no entities found in TARGET messages, return: {{"entities_relationships": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the conversation
2. Identify which messages are TARGET vs CONTEXT
3. Look for entity mentions ONLY in TARGET messages
4. Filter for personal connection - skip generic mentions
5. For confirmations, only extract if TARGET gives STRONG confirmation
6. Extract multiple entities from compound statements
7. When entities are introduced with type descriptors, extract as property
8. For each entity found in TARGET:
   - Identify the name/identifier
   - Classify the type
   - Capture any mentioned properties
   - Identify relationship indicators
   - Add interaction metadata if stated
   - Include source attribution from TARGET message
9. Return the complete JSON structure
10. If no connected entities in TARGET messages, return has_content: false
"""

# =============================================================================
# ALL 7 DIMENSIONS COMBINED (TARGETED)
# =============================================================================

CPDE_ALL_7_TARGETED = """

Your job is to extract profiling data from TARGET messages only.
Use CONTEXT messages to understand references, but ONLY extract from TARGET messages.
Extract information across ALL 7 dimensions simultaneously.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY from messages marked "(TARGET)"
- source_message_id MUST be from a TARGET message
- Maintain dimensional boundaries - put data in the correct dimension
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)
""" + TARGETING_RULES + """
=============================================================================
DIMENSION 1: CORE IDENTITY
=============================================================================

### What It Is
- What someone IS (roles, attributes, states, affiliations)
- Stable characteristics that define them
- Permanent or long-lasting aspects of who they are
- Examples: age, profession, location, physical attributes, chronic conditions, personality traits, affiliations

### What It Is Not
- What they THINK → goes to Opinions & Views
- What they WANT → goes to Desires, Wishes, Hopes & Needs
- What they DID → goes to Events or Life Narrative
- What they PREFER → goes to Preferences & Patterns
- Temporary states → goes to Events (e.g., "I'm sick" is an event, not identity)

### Examples

✓ TARGET: "I'm a 34-year-old software engineer"
  → Item 1: aspect: "age", state_value: "34 years old"
  → Item 2: aspect: "profession", state_value: "software engineer"

✗ CONTEXT: "You seem like an introvert"
  TARGET: "Maybe"
  → Do NOT extract (weak confirmation)

✗ TARGET: "I always code better at night"
  → Do NOT extract - this is a PREFERENCE (how they work), not identity (who they are)

✗ TARGET: "I really want to transition into AI/ML"
  → Do NOT extract - this is a DESIRE, not identity

=============================================================================
DIMENSION 2: OPINIONS & VIEWS
=============================================================================

### What It Is
- Lasting beliefs and worldviews
- Beliefs about how things are or should be
- Value judgments that reflect worldview
- Stances on topics they'd likely hold tomorrow, next month
- The KEY TEST: Will this opinion likely persist beyond the current context?

### What It Is Not
- Momentary reactions → skip ("This coffee is cold")
- Situational complaints → skip ("Traffic is bad today")
- Temporary states → skip ("I'm annoyed right now")

### Opinion vs Desire - How to Tell

Opinions express beliefs about THE WORLD:
- "Remote work IS the future" (belief about how things are)
- "AI IS dangerous" (judgment about something external)

Desires express PERSONAL wants:
- "I WANT to work remotely" (personal aspiration)
- "I HOPE to transition to AI" (personal goal)

Quick test:
- "X is/are/should be..." → Opinion (about the world)
- "I want/hope/wish/need..." → Desire (about themselves)

### Examples

✓ TARGET: "Remote work is the future"
  → about: "remote work", view: "is the future"

✓ TARGET: "AI is dangerous unless properly regulated"
  → about: "AI", view: "dangerous", qualifier: "unless properly regulated"

✗ TARGET: "This meeting is pointless" → skip (ephemeral frustration)

✗ TARGET: "I really want to transition into AI/ML"
  → Do NOT extract - "I want" signals a personal desire, not a belief about AI/ML itself

=============================================================================
DIMENSION 3: PREFERENCES & BEHAVIORAL PATTERNS
=============================================================================

### What It Is
- Consistent behavioral choices
- Stated preferences for how they do things
- Habitual tendencies
- Recurring approaches to activities
- Key indicators: "always", "never", "usually", "typically", "prefer", "tend to"

### What It Is Not
- One-time actions → goes to Events
- What they ARE → goes to Core Identity
- What they BELIEVE → goes to Opinions & Views
- What they WANT → goes to Desires

### Examples

✓ TARGET: "I always code better at night"
  → activity_category: "work", activity: "coding", preference: "better at night"

✓ TARGET: "I prefer texting over calling unless it's urgent"
  → activity_category: "communication", activity: "contacting people", preference: "texting over calling", context: "unless urgent"

✗ TARGET: "I skipped breakfast today" → goes to Events (one-time action)

=============================================================================
DIMENSION 4: DESIRES, WISHES, HOPES & NEEDS
=============================================================================

### What It Is
- What the person wants, needs, wishes for, or hopes for
- Explicit desires: "I want...", "I need...", "I wish...", "I hope..."
- Goal statements: "My goal is...", "I'm trying to..."

### Type Distinctions (controlled vocabulary)
- need: Essential, required, necessary ("I need health insurance")
- want: Active desire, something they're seeking ("I want to change careers")
- wish: Hypothetical, wistful, may not be actionable ("I wish I could travel more")
- hope: Optimistic aspiration, uncertain outcome ("I hope to get promoted")

### Examples

✓ TARGET: "I really want to reconnect with my daughter"
  → type: "want", target: "reconnect with daughter", is_active: "yes", intensity: "really"

✓ TARGET: "I desperately need better work-life balance"
  → type: "need", target: "better work-life balance", is_active: "yes", intensity: "desperately"

✗ CONTEXT: "It sounds like you need a vacation"
  TARGET: "Maybe"
  → Do NOT extract (weak confirmation of AI suggestion)

=============================================================================
DIMENSION 5: LIFE NARRATIVE
=============================================================================

### What It Is
- Past experiences that form biographical arc
- Life chapters and phases
- Formative experiences
- Major transitions (career, location, relationship)

### Key Distinction: Life Narrative vs Events
- "I lived in Tokyo for five years" → Life Narrative (biographical chapter)
- "I'm moving to Tokyo next month" → Events (upcoming occurrence)
- "I got divorced in 2019" → Life Narrative (past, biographical)
- "I'm going through a divorce" → Events (current, ongoing)

### Examples

✓ TARGET: "I lived in Tokyo for five years"
  → what_happened: "lived in Tokyo", period: "five years"

✓ TARGET: "Growing up poor in rural Texas shaped everything about who I am"
  → what_happened: "grew up poor in rural Texas", period: "childhood", significance: "shaped everything about who I am"

✗ TARGET: "I'm going through a divorce" → goes to Events (current, ongoing)

=============================================================================
DIMENSION 6: EVENTS & INVOLVEMENT
=============================================================================

### What It Is
- Discrete occurrences (past, current, or future)
- Temporary ongoing states ("I'm sick", "I'm moving", "I'm renovating")
- Planned future events ("visiting Greece next summer")

### Temporary vs Permanent State
- "I'm sick" → Event (temporary)
- "I'm a teacher" → Identity (permanent role)
- "I'm pregnant" → Event (temporary state with endpoint)
- "I'm diabetic" → Identity (chronic condition)

### Significance Filter
Always extract: Life milestones, professional changes, health events, achievements, crises
Usually skip: Routine activities, daily occurrences, minor inconveniences

### Examples

✓ TARGET: "I'm sick with the flu"
  → event: "sick with flu", involvement: "experiencing", temporal: "current"

✓ TARGET: "I just had a three-hour interview with Google"
  → event: "job interview", involvement: "candidate", temporal: "just had", entities_involved: ["Google"]

✗ TARGET: "Had lunch" → skip (routine activity)

=============================================================================
DIMENSION 7: ENTITIES & RELATIONSHIPS
=============================================================================

### What It Is
- People: Named individuals or referenced relationships ("my boss", "Sarah")
- Organizations: Companies, schools, teams, groups, institutions
- Places: Cities, countries, venues, locations with significance
- Products/Technologies: Tools, platforms, products they use
- Pets: Animals they have relationship with

### What It Is Not
- Generic mentions without relationship context ("Apple announced something")
- Entities they're merely discussing, not connected to

### Parsing Rule
When entities are introduced with type descriptors (e.g., 'My dog Max', 'My cat Luna'), extract the descriptor as a property (species: dog, species: cat)

### Examples

✓ TARGET: "Sarah from marketing has been mentoring me weekly"
  → name: "Sarah", entity_type: "person", mentioned_properties: [{{"key": "department", "value": "marketing"}}],
    relationship_indicators: ["colleague", "mentor"], interaction_metadata: {{"frequency": "weekly", "context": "professional", "recency": null}}

✓ TARGET: "My dog Max is getting old"
  → name: "Max", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "dog"}}, {{"key": "age", "value": "old"}}],
    relationship_indicators: ["pet"]

✗ TARGET: "Apple announced a new iPhone" → skip (no personal relationship)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of a TARGET message (never CONTEXT)
- source_quote: The exact text snippet from that TARGET message

Return a JSON object with all 7 dimensions:

{{
  "core_identity": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of TARGET message only",
        "source_quote": "string - exact quote from TARGET message",
        "aspect": "string - category (age, profession, location, condition, etc.)",
        "state_value": "string - the actual value",
        "temporal": "string or null - only if explicitly time-bound",
        "relational_dimension": "string or null - only if relative to others"
      }}
    ]
  }},
  "opinions_views": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string",
        "source_quote": "string",
        "about": "string - topic/subject of opinion",
        "view": "string - the stance/position taken",
        "qualifier": "string or null - conditions, exceptions"
      }}
    ]
  }},
  "preferences_patterns": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string",
        "source_quote": "string",
        "activity_category": "string - broad domain (work, sleep, communication, etc.)",
        "activity": "string - specific activity or behavior",
        "preference": "string - the pattern or preference",
        "context": "string or null - conditions when this applies"
      }}
    ]
  }},
  "desires_needs": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string",
        "source_quote": "string",
        "type": "string - need/want/wish/hope (pick one)",
        "target": "string - what they aspire to",
        "is_active": "string - yes/no/unknown/explicitly_uncertain",
        "intensity": "string or null - desperately/really/somewhat/etc.",
        "temporal": "string or null - soon/someday/by January/etc."
      }}
    ]
  }},
  "life_narrative": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string",
        "source_quote": "string",
        "what_happened": "string - core biographical fact, no temporal markers",
        "period": "string or null - all temporal information",
        "significance": "string or null - only if explicitly stated"
      }}
    ]
  }},
  "events": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string",
        "source_quote": "string",
        "event": "string - what happened/is happening",
        "involvement": "string - how they participated",
        "temporal": "string or null - when/duration",
        "entities_involved": ["array of strings"] or null,
        "outcome": "string or null - only if explicitly stated"
      }}
    ]
  }},
  "entities_relationships": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string",
        "source_quote": "string",
        "name": "string - entity name or identifier",
        "entity_type": "string - person/organization/place/product/technology/pet/etc.",
        "mentioned_properties": [{{"key": "string", "value": "string"}}] - list of key-value pairs, empty list if none,
        "relationship_indicators": ["array of relationship types"],
        "interaction_metadata": {{"frequency": "string or null", "context": "string or null", "recency": "string or null"}} or null
      }}
    ]
  }}
}}

If a dimension has no content in TARGET messages, return: {{"has_content": false, "items": []}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages to understand the full conversation
2. Identify which messages are TARGET vs CONTEXT
3. ONLY extract from TARGET messages - use CONTEXT for understanding only
4. For each piece of profiling information found in TARGET messages:
   - Determine which dimension it belongs to
   - Extract with proper attribution (source_message_id from TARGET, source_quote)
   - Respect dimensional boundaries
5. For confirmations, only extract if TARGET gives STRONG confirmation
6. Return the complete JSON structure with all 7 dimensions
7. Empty dimensions should have has_content: false and items: []
"""


# =============================================================================
# HELPER FUNCTION: Format messages with inline markers
# =============================================================================

def format_messages_with_markers(
    messages: list[dict],
    target_roles: list[str] | None = None,
    target_message_ids: set[str] | None = None,
) -> str:
    """
    Format messages with inline (TARGET) and (CONTEXT) markers.

    Args:
        messages: List of message dicts with keys:
            - id: Message ID
            - role: Role (e.g., "user", "assistant")
            - content: Message content
        target_roles: Roles to mark as TARGET (e.g., ["user"])
        target_message_ids: Specific message IDs to mark as TARGET

    Returns:
        Formatted string with markers for use in prompts.

    Example:
        >>> messages = [
        ...     {"id": "msg_1", "role": "assistant", "content": "What do you do?"},
        ...     {"id": "msg_2", "role": "user", "content": "I'm an engineer"},
        ... ]
        >>> print(format_messages_with_markers(messages, target_roles=["user"]))
        Message ID: msg_1
        Role: assistant (CONTEXT)
        Content: What do you do?

        Message ID: msg_2
        Role: user (TARGET)
        Content: I'm an engineer
    """
    if target_roles is None:
        target_roles = ["user"]

    if target_message_ids is None:
        target_message_ids = set()

    formatted_parts = []

    for msg in messages:
        msg_id = msg.get("id", "unknown")
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Determine if this is a TARGET or CONTEXT message
        is_target = (
            role in target_roles or
            msg_id in target_message_ids
        )
        marker = "TARGET" if is_target else "CONTEXT"

        formatted_parts.append(
            f"Message ID: {msg_id}\n"
            f"Role: {role} ({marker})\n"
            f"Content: {content}"
        )

    return "\n\n".join(formatted_parts)
