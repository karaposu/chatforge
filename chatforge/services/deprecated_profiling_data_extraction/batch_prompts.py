"""
Batch prompts for CPDE-7 (Conversational Profiling Data Extraction - 7 Dimensions).

This module contains:
- CPDE_ALL_7_BATCH: Combined prompt for extracting all 7 dimensions in a single LLM call
- CPDE_CORE_IDENTITY_BATCH: Single-dimension prompt for Core Identity extraction
- CPDE_OPINIONS_VIEWS_BATCH: Single-dimension prompt for Opinions & Views extraction
- CPDE_PREFERENCES_PATTERNS_BATCH: Single-dimension prompt for Preferences & Patterns extraction
- CPDE_DESIRES_NEEDS_BATCH: Single-dimension prompt for Desires & Needs extraction
- CPDE_LIFE_NARRATIVE_BATCH: Single-dimension prompt for Life Narrative extraction
- CPDE_EVENTS_BATCH: Single-dimension prompt for Events extraction
- CPDE_ENTITIES_RELATIONSHIPS_BATCH: Single-dimension prompt for Entities & Relationships extraction

Usage with Pydantic structured output:
    structured_llm = llm.with_structured_output(BatchExtractionResult)
    result = structured_llm.invoke([HumanMessage(content=prompt)])
"""

# =============================================================================
# SINGLE DIMENSION: CORE IDENTITY ONLY
# =============================================================================

CPDE_CORE_IDENTITY_BATCH = """

Your job is to extract CORE IDENTITY information from the given batch of chat messages.
Focus ONLY on identity facts - who the person IS.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY identity information - redirect other types mentally but don't extract them
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "I'm a 34-year-old software engineer"
  → Item 1: aspect: "age", state_value: "34 years old"
  → Item 2: aspect: "profession", state_value: "software engineer"

✓ "I'm tall and diabetic"
  → Item 1: aspect: "physical_attribute", state_value: "tall"
  → Item 2: aspect: "medical_condition", state_value: "diabetic"

✓ "I'm the skeptic in my group"
  → aspect: "personality_role", state_value: "skeptic", relational_dimension: "in my group"

✓ "I've been a nurse since 2015"
  → aspect: "profession", state_value: "nurse", temporal: "since 2015"

✓ "I'm a single mom with two kids living in Austin"
  → Item 1: aspect: "family_role", state_value: "single mom"
  → Item 2: aspect: "family", state_value: "has two kids"
  → Item 3: aspect: "location", state_value: "Austin"

✓ "I'm an introvert who works in sales"
  → Item 1: aspect: "personality", state_value: "introvert"
  → Item 2: aspect: "profession", state_value: "works in sales"

✓ "I'm Japanese-American and grew up bilingual"
  → Item 1: aspect: "ethnicity", state_value: "Japanese-American"
  → Item 2: aspect: "language", state_value: "bilingual"

✓ "I'm the CTO at a fintech startup"
  → Item 1: aspect: "role", state_value: "CTO"
  → Item 2: aspect: "employer_type", state_value: "fintech startup"

✗ "I'm sick" → NOT identity (temporary state → Events)
✗ "I'm moving to Seattle" → NOT identity (in progress action → Events)
✗ "I think remote work is better" → NOT identity (opinion → Opinions)
✗ "I want to travel more" → NOT identity (desire → Desires)
✗ "I always wake up early" → NOT identity (pattern → Preferences)
✗ "I lived in Paris for 5 years" → NOT identity (past experience → Life Narrative)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "core_identity": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "aspect": "string - category (age, profession, location, medical_condition, personality, etc.)",
        "state_value": "string - the actual value",
        "temporal": "string or null - only if explicitly time-bound (e.g., 'since 2015', 'currently')",
        "relational_dimension": "string or null - only if relative to others (e.g., 'in my family', 'at work')"
      }}
    ]
  }}
}}

If no identity information found, return: {{"core_identity": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for statements about WHO the person IS
3. Split compound identity statements into separate items
4. For each identity fact found:
   - Categorize the aspect (age, profession, location, etc.)
   - Extract the state_value
   - Add temporal only if explicitly time-bound
   - Add relational_dimension only if relative to others
   - Include source attribution
5. Return the complete JSON structure
6. If no identity information found, return has_content: false with empty items
"""

# =============================================================================
# SINGLE DIMENSION: OPINIONS & VIEWS ONLY
# =============================================================================

CPDE_OPINIONS_VIEWS_BATCH = """

Your job is to extract OPINIONS & VIEWS from the given batch of chat messages.
Focus ONLY on lasting beliefs and worldviews - what the person THINKS or BELIEVES.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY non-ephemeral opinions - skip momentary reactions
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

=============================================================================
EXAMPLES
=============================================================================

✓ "Remote work is the future"
  → about: "remote work", view: "is the future"

✓ "I think college is overrated and too expensive"
  → Item 1: about: "college", view: "overrated"
  → Item 2: about: "college", view: "too expensive"

✓ "AI is dangerous unless properly regulated"
  → about: "AI", view: "dangerous", qualifier: "unless properly regulated"

✓ "I love the product but hate the company"
  → Item 1: about: "the product", view: "love it"
  → Item 2: about: "the company", view: "hate it"

✓ "Electric cars are great but the infrastructure isn't ready"
  → Item 1: about: "electric cars", view: "great"
  → Item 2: about: "electric car infrastructure", view: "not ready"

✓ "I believe everyone deserves healthcare"
  → about: "universal healthcare", view: "everyone deserves it"

✓ "Kids these days spend too much time on screens"
  → about: "children's screen time", view: "too much"

✗ "This meeting is pointless" → skip (ephemeral frustration)
✗ "I'm so tired of this" → skip (momentary state)
✗ "The coffee here is terrible today" → skip (situational)
✗ "I'm a vegetarian" → Core Identity (what they ARE)
✗ "I want to learn Spanish" → Desires (what they WANT)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "opinions_views": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "about": "string - topic/subject of the opinion",
        "view": "string - the stance/position taken",
        "qualifier": "string or null - conditions, exceptions (e.g., 'unless...', 'except when...', 'probably')"
      }}
    ]
  }}
}}

If no opinions found, return: {{"opinions_views": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for statements about what the person THINKS or BELIEVES
3. Apply the persistence test: would they likely hold this view tomorrow?
4. Split compound opinions into separate items
5. For each opinion found:
   - Identify what it's about
   - Extract the view/stance
   - Add qualifier only if there are conditions/exceptions
   - Include source attribution
6. Return the complete JSON structure
7. If no lasting opinions found, return has_content: false with empty items
"""

# =============================================================================
# SINGLE DIMENSION: PREFERENCES & PATTERNS ONLY
# =============================================================================

CPDE_PREFERENCES_PATTERNS_BATCH = """

Your job is to extract PREFERENCES & BEHAVIORAL PATTERNS from the given batch of chat messages.
Focus ONLY on habitual behaviors and consistent choices - how the person typically DOES things.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY recurring patterns - skip one-time actions
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "I always code better at night"
  → activity_category: "work", activity: "coding", preference: "better at night"

✓ "I prefer texting over calling unless it's urgent"
  → activity_category: "communication", activity: "contacting people", preference: "texting over calling", context: "unless urgent"

✓ "I can't sleep without white noise and I always read before bed"
  → Item 1: activity_category: "sleep", activity: "falling asleep", preference: "requires white noise"
  → Item 2: activity_category: "sleep", activity: "bedtime routine", preference: "always reads before bed"

✓ "I usually skip breakfast but I never skip my morning coffee"
  → Item 1: activity_category: "eating", activity: "breakfast", preference: "usually skips"
  → Item 2: activity_category: "eating", activity: "morning coffee", preference: "never skips"

✓ "I work out early because the gym is empty then"
  → activity_category: "exercise", activity: "gym workouts", preference: "early morning", context: "because gym is empty"

✓ "I tend to procrastinate on big projects"
  → activity_category: "work", activity: "big projects", preference: "tends to procrastinate"

✓ "I never eat seafood"
  → activity_category: "eating", activity: "seafood", preference: "never eats"

✗ "I skipped breakfast today" → Events (one-time action)
✗ "I'm a morning person" → Core Identity (what they ARE)
✗ "I think breakfast is important" → Opinions (belief)
✗ "I want to start waking up earlier" → Desires (aspiration)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "preferences_patterns": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "activity_category": "string - broad domain (work, sleep, communication, eating, etc.)",
        "activity": "string - specific activity or behavior",
        "preference": "string - the pattern or preference",
        "context": "string or null - conditions when this applies/doesn't apply"
      }}
    ]
  }}
}}

If no preferences found, return: {{"preferences_patterns": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for statements about HOW the person typically does things
3. Look for pattern indicators: always, never, usually, prefer, tend to
4. Split compound patterns into separate items
5. For each pattern found:
   - Categorize the activity domain
   - Identify the specific activity
   - Extract the preference/pattern
   - Add context only if conditions are stated
   - Include source attribution
6. Return the complete JSON structure
7. If no patterns found, return has_content: false with empty items
"""

# =============================================================================
# SINGLE DIMENSION: DESIRES, WISHES, HOPES & NEEDS ONLY
# =============================================================================

CPDE_DESIRES_NEEDS_BATCH = """

Your job is to extract DESIRES, WISHES, HOPES & NEEDS from the given batch of chat messages.
Focus ONLY on what the person WANTS - their aspirations, goals, and needs.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY the aspiration itself - consequences go elsewhere
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "I really want to reconnect with my daughter"
  → type: "want", target: "reconnect with daughter", is_active: "yes", intensity: "really"

✓ "I desperately need better work-life balance"
  → type: "need", target: "better work-life balance", is_active: "yes", intensity: "desperately"

✓ "I hope to get promoted and I want to eventually lead a team"
  → Item 1: type: "hope", target: "get promoted", is_active: "yes"
  → Item 2: type: "want", target: "lead a team", is_active: "yes", temporal: "eventually"

✓ "I wish I could travel more but I need to save money first"
  → Item 1: type: "wish", target: "travel more", is_active: "yes"
  → Item 2: type: "need", target: "save money", is_active: "yes", temporal: "first"

✓ "I wanted to be a doctor but that ship has sailed"
  → type: "want", target: "be a doctor", is_active: "no"

✓ "I'm not sure I want kids anymore"
  → type: "want", target: "have kids", is_active: "explicitly_uncertain"

✓ "My goal is to retire by 50"
  → type: "want", target: "retire", is_active: "yes", temporal: "by 50"

✓ "I need to find a new apartment by next month"
  → type: "need", target: "find a new apartment", is_active: "yes", temporal: "by next month"

✗ "I'm a very ambitious person" → Core Identity (what they ARE)
✗ "I think everyone should travel" → Opinions (belief about others)
✗ "I always save 20% of my income" → Preferences (behavioral pattern)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "desires_needs": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "type": "string - need/want/wish/hope (pick one)",
        "target": "string - what they aspire to",
        "is_active": "string - yes/no/unknown/explicitly_uncertain",
        "intensity": "string or null - desperately/really/somewhat/slightly/etc.",
        "temporal": "string or null - soon/someday/by January/eventually/etc."
      }}
    ]
  }}
}}

If no desires found, return: {{"desires_needs": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for statements about what the person WANTS, NEEDS, WISHES, or HOPES
3. Classify each as need/want/wish/hope based on definitions
4. Determine if the desire is currently active
5. Split compound desires into separate items
6. For each desire found:
   - Classify the type
   - Extract the target
   - Determine is_active status
   - Add intensity only if explicitly stated
   - Add temporal only if timeframe mentioned
   - Include source attribution
7. Return the complete JSON structure
8. If no desires found, return has_content: false with empty items
"""

# =============================================================================
# SINGLE DIMENSION: LIFE NARRATIVE ONLY
# =============================================================================

CPDE_LIFE_NARRATIVE_BATCH = """

Your job is to extract LIFE NARRATIVE elements from the given batch of chat messages.
Focus ONLY on biographical information - the person's life story and past experiences.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY past biographical experiences - not current/future events
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "I lived in Tokyo for five years"
  → what_happened: "lived in Tokyo", period: "five years"

✓ "I got divorced in 2019 and it freed me to pursue my passions"
  → what_happened: "got divorced", period: "2019", significance: "freed me to pursue my passions"

✓ "Growing up poor in rural Texas shaped everything about who I am"
  → what_happened: "grew up poor in rural Texas", period: "childhood", significance: "shaped everything about who I am"

✓ "I dropped out of college and then started my own company"
  → Item 1: what_happened: "dropped out of college"
  → Item 2: what_happened: "started own company", period: "after dropping out"

✓ "I served in the military for 8 years and it taught me discipline"
  → what_happened: "served in military", period: "8 years", significance: "taught me discipline"

✓ "After my startup failed, I spent two years traveling before joining Google"
  → Item 1: what_happened: "startup failed"
  → Item 2: what_happened: "traveled", period: "two years, after startup failed"
  → Item 3: what_happened: "joined Google", period: "after traveling"

✓ "I was bullied in high school"
  → what_happened: "was bullied", period: "high school"

✓ "I immigrated to the US when I was 12"
  → what_happened: "immigrated to the US", period: "at age 12"

✗ "I'm going through a divorce" → Events (current, ongoing)
✗ "I'm moving to Seattle next month" → Events (future)
✗ "I'm a veteran" → Core Identity (current state derived from past)

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
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "life_narrative": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "what_happened": "string - core biographical fact, no temporal markers",
        "period": "string or null - all temporal information",
        "significance": "string or null - only if explicitly stated how it affected them"
      }}
    ]
  }}
}}

If no narrative found, return: {{"life_narrative": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for statements about the person's PAST experiences and life story
3. Distinguish past biographical info from current events
4. Split complex life sequences into separate items
5. For each narrative element found:
   - Extract what_happened (no temporal markers)
   - Move ALL temporal info to period
   - Add significance ONLY if explicitly stated
   - Include source attribution
6. Return the complete JSON structure
7. If no life narrative found, return has_content: false with empty items
"""

# =============================================================================
# SINGLE DIMENSION: EVENTS & INVOLVEMENT ONLY
# =============================================================================

CPDE_EVENTS_BATCH = """

Your job is to extract EVENTS & INVOLVEMENT from the given batch of chat messages.
Focus ONLY on discrete occurrences - things HAPPENING to or with the person.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY significant events - skip routine activities
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "I'm sick with the flu"
  → event: "sick with flu", involvement: "experiencing", temporal: "current"

✓ "I just had a three-hour interview with Google"
  → event: "job interview", involvement: "candidate", temporal: "just had", entities_involved: ["Google"]

✓ "My team won the hackathon last weekend!"
  → event: "hackathon", involvement: "participant", temporal: "last weekend", entities_involved: ["my team"], outcome: "won"

✓ "I'm renovating my kitchen and dealing with a difficult contractor"
  → Item 1: event: "kitchen renovation", involvement: "homeowner", temporal: "ongoing"
  → Item 2: event: "contractor dispute", involvement: "experiencing", temporal: "ongoing"

✓ "Got food poisoning at Jim's wedding and missed the whole reception"
  → event: "food poisoning at wedding", involvement: "guest/victim", entities_involved: ["Jim"], outcome: "missed reception"

✓ "I'm pregnant and we're moving to a bigger apartment next month"
  → Item 1: event: "pregnancy", involvement: "experiencing", temporal: "current"
  → Item 2: event: "moving to bigger apartment", involvement: "participant", temporal: "next month"

✓ "Presented at a TED talk and it went viral"
  → event: "TED talk presentation", involvement: "presenter", outcome: "went viral"

✓ "I'm getting married in June"
  → event: "wedding", involvement: "getting married", temporal: "June"

✗ "Had lunch" → skip (routine activity)
✗ "I hate being sick" → Opinions
✗ "I'm diabetic" → Core Identity (chronic condition)
✗ "I lived in Paris for 5 years" → Life Narrative (past biographical)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "events": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "event": "string - what happened/is happening",
        "involvement": "string - how they participated (attended, organized, experiencing, victim, etc.)",
        "temporal": "string or null - when/duration (yesterday, current, ongoing, next week, etc.)",
        "entities_involved": ["array of strings"] or null - others involved,
        "outcome": "string or null - only if explicitly stated result"
      }}
    ]
  }}
}}

If no events found, return: {{"events": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for discrete occurrences and temporary states
3. Apply significance filter - skip routine activities
4. Distinguish events from life narrative (current/future vs past biographical)
5. Split compound events into separate items
6. For each event found:
   - Describe the event
   - Identify their involvement/role
   - Add temporal info if stated
   - Add entities_involved if mentioned
   - Add outcome only if explicitly stated
   - Include source attribution
7. Return the complete JSON structure
8. If no significant events found, return has_content: false with empty items
"""

# =============================================================================
# SINGLE DIMENSION: ENTITIES & RELATIONSHIPS ONLY
# =============================================================================

CPDE_ENTITIES_RELATIONSHIPS_BATCH = """

Your job is to extract ENTITIES & RELATIONSHIPS from the given batch of chat messages.
Focus ONLY on significant people, organizations, places, and things connected to the person.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Extract ONLY entities with personal connection - skip generic mentions
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "Sarah from marketing has been mentoring me weekly"
  → name: "Sarah", entity_type: "person", mentioned_properties: [{{"key": "department", "value": "marketing"}}],
    relationship_indicators: ["colleague", "mentor"], interaction_metadata: {{"frequency": "weekly", "context": "professional", "recency": null}}

✓ "I've been using Notion for everything since I left Google"
  → Item 1: name: "Notion", entity_type: "product", mentioned_properties: [], relationship_indicators: ["tool"],
    interaction_metadata: {{"frequency": "regular", "context": null, "recency": "current"}}
  → Item 2: name: "Google", entity_type: "organization", mentioned_properties: [], relationship_indicators: ["employer"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "former"}}

✓ "My brother Tom and his wife Sarah are visiting from Seattle next week"
  → Item 1: name: "Tom", entity_type: "person", relationship_indicators: ["brother", "family"],
    mentioned_properties: [{{"key": "location", "value": "Seattle"}}]
  → Item 2: name: "Sarah", entity_type: "person", relationship_indicators: ["sister-in-law", "family"],
    mentioned_properties: [{{"key": "location", "value": "Seattle"}}]
  → Item 3: name: "Seattle", entity_type: "place", mentioned_properties: [], relationship_indicators: ["family location"]

✓ "My dog Max is getting old and my cat Luna keeps him company"
  → Item 1: name: "Max", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "dog"}}, {{"key": "age", "value": "old"}}],
    relationship_indicators: ["pet"]
  → Item 2: name: "Luna", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "cat"}}],
    relationship_indicators: ["pet"]

✓ "My therapist Dr. Chen has been incredibly helpful"
  → name: "Dr. Chen", entity_type: "person", mentioned_properties: [{{"key": "role", "value": "therapist"}}],
    relationship_indicators: ["healthcare provider"]

✓ "I grew up in Austin but now I live in Portland and work remotely for a startup in SF"
  → Item 1: name: "Austin", entity_type: "place", mentioned_properties: [], relationship_indicators: ["hometown"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "former"}}
  → Item 2: name: "Portland", entity_type: "place", mentioned_properties: [], relationship_indicators: ["residence"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "current"}}
  → Item 3: name: "startup in SF", entity_type: "organization", mentioned_properties: [], relationship_indicators: ["employer"],
    interaction_metadata: {{"frequency": null, "context": "remote", "recency": "current"}}

✓ "My mom calls me every Sunday"
  → name: "mom", entity_type: "person", mentioned_properties: [], relationship_indicators: ["mother", "family"],
    interaction_metadata: {{"frequency": "weekly", "context": null, "recency": null}}

✗ "Apple announced a new iPhone" → skip (no personal relationship)
✗ "The President gave a speech" → skip (merely discussing, not connected to)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object:

{{
  "entities_relationships": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
        "name": "string - entity name or identifier (e.g., 'Sarah', 'Google', 'my boss')",
        "entity_type": "string - person/organization/place/product/technology/pet/etc.",
        "mentioned_properties": [{{"key": "property_name", "value": "property_value"}}] - list of key-value pairs, empty list if none,
        "relationship_indicators": ["array of relationship types (colleague, employer, hometown, tool, etc.)"],
        "interaction_metadata": {{"frequency": "string or null", "context": "string or null", "recency": "string or null"}} or null
      }}
    ]
  }}
}}

If no entities found, return: {{"entities_relationships": {{"has_content": false, "items": []}}}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. Look for people, organizations, places, products, pets mentioned
3. Filter for personal connection - skip generic mentions
4. Extract multiple entities from compound statements
5. When entities are introduced with type descriptors (e.g., 'My dog Max', 'My cat Luna'), extract the descriptor as a property (species: dog, species: cat)
6. For each entity found:
   - Identify the name/identifier
   - Classify the type
   - Capture any mentioned properties
   - Identify relationship indicators
   - Add interaction metadata if stated
   - Include source attribution
7. Return the complete JSON structure
8. If no connected entities found, return has_content: false with empty items
"""

# =============================================================================
# ALL 7 DIMENSIONS COMBINED
# =============================================================================

CPDE_ALL_7_BATCH = """

Your job is to extract profiling data from the given batch of chat messages.
Extract information across ALL 7 dimensions simultaneously.

CRITICAL RULES:
- Do NOT infer or assume information not explicitly stated
- Maintain dimensional boundaries - put data in the correct dimension
- YOU must not force a meaning. IT IS OKAY TO NOT FIND DATA
- Each extracted item MUST include source attribution (source_message_id and source_quote)

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

✓ "I'm a 34-year-old software engineer"
  → Item 1: aspect: "age", state_value: "34 years old"
  → Item 2: aspect: "profession", state_value: "software engineer"

✓ "I'm tall and diabetic"
  → Item 1: aspect: "physical_attribute", state_value: "tall"
  → Item 2: aspect: "medical_condition", state_value: "diabetic"

✓ "I'm the skeptic in my group"
  → aspect: "personality_role", state_value: "skeptic", relational_dimension: "in my group"

✓ "I've been a nurse since 2015"
  → aspect: "profession", state_value: "nurse", temporal: "since 2015"

✗ "I'm sick" → goes to Events (temporary state)
✗ "I'm moving to Seattle" → goes to Events (in progress action)
✗ "I think remote work is better" → goes to Opinions

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
- Reactions to immediate context that won't persist
- What they ARE → goes to Core Identity
- What they WANT → goes to Desires

### Examples

✓ "Remote work is the future"
  → about: "remote work", view: "is the future"

✓ "I think college is overrated and too expensive"
  → Item 1: about: "college", view: "overrated"
  → Item 2: about: "college", view: "too expensive"

✓ "AI is dangerous unless properly regulated"
  → about: "AI", view: "dangerous", qualifier: "unless properly regulated"

✓ "I love the product but hate the company"
  → Item 1: about: "the product", view: "love it"
  → Item 2: about: "the company", view: "hate it"

✓ "Electric cars are great but the infrastructure isn't ready"
  → Item 1: about: "electric cars", view: "great"
  → Item 2: about: "electric car infrastructure", view: "not ready"

✗ "This meeting is pointless" → skip (ephemeral frustration)
✗ "I'm so tired of this" → skip (momentary state)
✗ "The coffee here is terrible today" → skip (situational complaint)

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

✓ "I always code better at night"
  → activity_category: "work", activity: "coding", preference: "better at night"

✓ "I prefer texting over calling unless it's urgent"
  → activity_category: "communication", activity: "contacting people", preference: "texting over calling", context: "unless urgent"

✓ "I can't sleep without white noise and I always read before bed"
  → Item 1: activity_category: "sleep", activity: "falling asleep", preference: "requires white noise"
  → Item 2: activity_category: "sleep", activity: "bedtime routine", preference: "always reads before bed"

✓ "I usually skip breakfast but I never skip my morning coffee"
  → Item 1: activity_category: "eating", activity: "breakfast", preference: "usually skips"
  → Item 2: activity_category: "eating", activity: "morning coffee", preference: "never skips"

✓ "I work out early because the gym is empty then"
  → activity_category: "exercise", activity: "gym workouts", preference: "early morning", context: "because gym is empty"

✗ "I skipped breakfast today" → goes to Events (one-time action)
✗ "I'm a morning person" → goes to Core Identity (what they ARE)
✗ "I think breakfast is important" → goes to Opinions (belief)

=============================================================================
DIMENSION 4: DESIRES, WISHES, HOPES & NEEDS
=============================================================================

### What It Is
- What the person wants, needs, wishes for, or hopes for
- Explicit desires: "I want...", "I need...", "I wish...", "I hope..."
- Goal statements: "My goal is...", "I'm trying to..."
- Implied needs from complaints: "I'm so burnt out" → may imply need for rest

### What It Is Not
- What they ARE → goes to Core Identity
- What they BELIEVE → goes to Opinions & Views
- What they consistently DO → goes to Preferences
- Past aspirations that are no longer active (mark is_active: "no")

### Type Distinctions (controlled vocabulary)
- need: Essential, required, necessary ("I need health insurance")
- want: Active desire, something they're seeking ("I want to change careers")
- wish: Hypothetical, wistful, may not be actionable ("I wish I could travel more")
- hope: Optimistic aspiration, uncertain outcome ("I hope to get promoted")

### Examples

✓ "I really want to reconnect with my daughter"
  → type: "want", target: "reconnect with daughter", is_active: "yes", intensity: "really"

✓ "I desperately need better work-life balance"
  → type: "need", target: "better work-life balance", is_active: "yes", intensity: "desperately"

✓ "I hope to get promoted and I want to eventually lead a team"
  → Item 1: type: "hope", target: "get promoted", is_active: "yes"
  → Item 2: type: "want", target: "lead a team", is_active: "yes", temporal: "eventually"

✓ "I wish I could travel more but I need to save money first"
  → Item 1: type: "wish", target: "travel more", is_active: "yes"
  → Item 2: type: "need", target: "save money", is_active: "yes", temporal: "first"

✓ "I wanted to be a doctor but that ship has sailed"
  → type: "want", target: "be a doctor", is_active: "no"

✓ "I'm not sure I want kids anymore"
  → type: "want", target: "have kids", is_active: "explicitly_uncertain"

✗ "I'm a very ambitious person" → goes to Core Identity (what they ARE)
✗ "I think everyone should travel" → goes to Opinions (belief about others)
✗ "I always save 20% of my income" → goes to Preferences (behavioral pattern)

=============================================================================
DIMENSION 5: LIFE NARRATIVE
=============================================================================

### What It Is
- Past experiences that form biographical arc
- Life chapters and phases
- Formative experiences
- Major transitions (career, location, relationship)
- Origin stories, challenges overcome, educational journey

### What It Is Not
- Current/recent discrete occurrences → goes to Events
- Future planned occurrences → goes to Events
- Temporary states → goes to Events
- What they ARE now → goes to Core Identity

### Key Distinction: Life Narrative vs Events
- "I lived in Tokyo for five years" → Life Narrative (biographical chapter)
- "I'm moving to Tokyo next month" → Events (upcoming occurrence)
- "I got divorced in 2019" → Life Narrative (past, biographical)
- "I'm going through a divorce" → Events (current, ongoing)

### Examples

✓ "I lived in Tokyo for five years"
  → what_happened: "lived in Tokyo", period: "five years"

✓ "I got divorced in 2019 and it freed me to pursue my passions"
  → what_happened: "got divorced", period: "2019", significance: "freed me to pursue my passions"

✓ "Growing up poor in rural Texas shaped everything about who I am"
  → what_happened: "grew up poor in rural Texas", period: "childhood", significance: "shaped everything about who I am"

✓ "I dropped out of college and then started my own company"
  → Item 1: what_happened: "dropped out of college", period: null, significance: null
  → Item 2: what_happened: "started own company", period: "after dropping out", significance: null

✓ "I served in the military for 8 years and it taught me discipline"
  → what_happened: "served in military", period: "8 years", significance: "taught me discipline"

✓ "After my startup failed, I spent two years traveling before joining Google"
  → Item 1: what_happened: "startup failed", period: null
  → Item 2: what_happened: "traveled", period: "two years, after startup failed"
  → Item 3: what_happened: "joined Google", period: "after traveling"

✗ "I'm going through a divorce" → goes to Events (current, ongoing)
✗ "I'm moving to Seattle next month" → goes to Events (future)
✗ "I'm a veteran" → goes to Core Identity (current state)

### Extraction Rules
- what_happened: Core biographical fact ONLY, no temporal markers
  ✓ "served in military", "lived in Paris", "got divorced"
  ✗ "served in military for 3 years" (move duration to period)
- period: ALL temporal information ("three years", "during college", "2008", "childhood")
- significance: ONLY if they explicitly state how it affected them
  ✓ "taught me resilience", "changed my perspective"
  ✗ Don't infer meaning they didn't express

=============================================================================
DIMENSION 6: EVENTS & INVOLVEMENT
=============================================================================

### What It Is
- Discrete occurrences (past, current, or future)
- Temporary ongoing states ("I'm sick", "I'm moving", "I'm renovating")
- Planned future events ("visiting Greece next summer")
- Things happening TO them or WITH them
- The KEY TEST: Is something temporary happening that they're experiencing?

### What It Is Not
- Opinions → goes to Opinions & Views
- Permanent characteristics → goes to Core Identity
- Chronic/defining conditions → goes to Core Identity
- Past biographical chapters → goes to Life Narrative
- Aspirations → goes to Desires
- Habitual patterns → goes to Preferences
- Observations without involvement ("there was an earthquake") → skip

### Temporary vs Permanent State
- "I'm sick" → Event (temporary)
- "I'm a teacher" → Identity (permanent role)
- "I'm pregnant" → Event (temporary state with endpoint)
- "I'm divorced" → Identity (permanent status)
- "I'm recovering from surgery" → Event (temporary)
- "I'm diabetic" → Identity (chronic condition)

### Significance Filter
Always extract: Life milestones, professional changes, health events, achievements, crises
Usually extract: Significant social events, travel, major purchases
Usually skip: Routine activities, daily occurrences, minor inconveniences

### Examples

✓ "I'm sick with the flu"
  → event: "sick with flu", involvement: "experiencing", temporal: "current"

✓ "I just had a three-hour interview with Google"
  → event: "job interview", involvement: "candidate", temporal: "just had", entities_involved: ["Google"]

✓ "My team won the hackathon last weekend!"
  → event: "hackathon", involvement: "participant", temporal: "last weekend", entities_involved: ["my team"], outcome: "won"

✓ "I'm renovating my kitchen and dealing with a difficult contractor"
  → Item 1: event: "kitchen renovation", involvement: "homeowner", temporal: "ongoing"
  → Item 2: event: "contractor dispute", involvement: "experiencing", temporal: "ongoing"

✓ "Got food poisoning at Jim's wedding and missed the whole reception"
  → event: "food poisoning at wedding", involvement: "guest/victim", entities_involved: ["Jim"], outcome: "missed reception"

✓ "I'm pregnant and we're moving to a bigger apartment next month"
  → Item 1: event: "pregnancy", involvement: "experiencing", temporal: "current"
  → Item 2: event: "moving to bigger apartment", involvement: "participant", temporal: "next month"

✓ "Presented at a TED talk and it went viral"
  → event: "TED talk presentation", involvement: "presenter", outcome: "went viral"

✗ "Had lunch" → skip (routine activity)
✗ "I hate being sick" → goes to Opinions
✗ "I'm diabetic" → goes to Core Identity (chronic condition)
✗ "I lived in Paris for 5 years" → goes to Life Narrative (past biographical)

=============================================================================
DIMENSION 7: ENTITIES & RELATIONSHIPS
=============================================================================

### What It Is
- People: Named individuals or referenced relationships ("my boss", "Sarah")
- Organizations: Companies, schools, teams, groups, institutions
- Places: Cities, countries, venues, locations with significance
- Products/Technologies: Tools, platforms, products they use
- Other: Any significant named entity relevant to understanding them

### What It Is Not
- Generic mentions without relationship context ("Apple announced something")
- Entities they're merely discussing, not connected to
- Passing references with no profiling value

### Extraction Priority
Focus on entities that reveal:
- Social/professional network
- Tools and environment they operate in
- Places significant to their life
- Organizations they're affiliated with

### Parsing Rule
When entities are introduced with type descriptors (e.g., 'My dog Max', 'My cat Luna'), extract the descriptor as a property (species: dog, species: cat)

### Examples

✓ "Sarah from marketing has been mentoring me weekly"
  → name: "Sarah", entity_type: "person", mentioned_properties: [{{"key": "department", "value": "marketing"}}],
    relationship_indicators: ["colleague", "mentor"], interaction_metadata: {{"frequency": "weekly", "context": "professional", "recency": null}}

✓ "I've been using Notion for everything since I left Google"
  → Item 1: name: "Notion", entity_type: "product", mentioned_properties: [], relationship_indicators: ["tool"],
    interaction_metadata: {{"frequency": "regular", "context": null, "recency": "current"}}
  → Item 2: name: "Google", entity_type: "organization", mentioned_properties: [], relationship_indicators: ["employer"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "former"}}

✓ "My brother Tom and his wife Sarah are visiting from Seattle next week"
  → Item 1: name: "Tom", entity_type: "person", relationship_indicators: ["brother", "family"],
    mentioned_properties: [{{"key": "location", "value": "Seattle"}}]
  → Item 2: name: "Sarah", entity_type: "person", relationship_indicators: ["sister-in-law", "family"],
    mentioned_properties: [{{"key": "location", "value": "Seattle"}}]
  → Item 3: name: "Seattle", entity_type: "place", mentioned_properties: [], relationship_indicators: ["family location"]

✓ "My dog Max is getting old and my cat Luna keeps him company"
  → Item 1: name: "Max", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "dog"}}, {{"key": "age", "value": "old"}}],
    relationship_indicators: ["pet"]
  → Item 2: name: "Luna", entity_type: "pet", mentioned_properties: [{{"key": "species", "value": "cat"}}],
    relationship_indicators: ["pet"]

✓ "My therapist Dr. Chen has been incredibly helpful"
  → name: "Dr. Chen", entity_type: "person", mentioned_properties: [{{"key": "role", "value": "therapist"}}],
    relationship_indicators: ["healthcare provider"]

✓ "I grew up in Austin but now I live in Portland and work remotely for a startup in SF"
  → Item 1: name: "Austin", entity_type: "place", mentioned_properties: [], relationship_indicators: ["hometown"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "former"}}
  → Item 2: name: "Portland", entity_type: "place", mentioned_properties: [], relationship_indicators: ["residence"],
    interaction_metadata: {{"frequency": null, "context": null, "recency": "current"}}
  → Item 3: name: "startup in SF", entity_type: "organization", mentioned_properties: [], relationship_indicators: ["employer"],
    interaction_metadata: {{"frequency": null, "context": "remote", "recency": "current"}}

✗ "Apple announced a new iPhone" → skip (no personal relationship)
✗ "The President gave a speech" → skip (merely discussing, not connected to)

=============================================================================
OUTPUT SCHEMA
=============================================================================

For each extracted item, you MUST include:
- source_message_id: The ID of the message this was extracted from
- source_quote: The exact text snippet that contains this information

Return a JSON object with all 7 dimensions:

{{
  "core_identity": {{
    "has_content": true/false,
    "items": [
      {{
        "source_message_id": "string - ID of source message",
        "source_quote": "string - exact quote from message",
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

If a dimension has no content, return: {{"has_content": false, "items": []}}

=============================================================================
MESSAGES TO ANALYZE
=============================================================================

{messages}

=============================================================================
EXTRACTION INSTRUCTIONS
=============================================================================

1. Read through ALL messages carefully
2. For each piece of profiling information found:
   - Determine which dimension it belongs to
   - Extract with proper attribution (source_message_id, source_quote)
   - Respect dimensional boundaries
3. Return the complete JSON structure with all 7 dimensions
4. Empty dimensions should have has_content: false and items: []
"""


# =============================================================================
# Schema Explanation (for documentation purposes)
# =============================================================================

SCHEMA_EXPLANATION = """
## CPDE-7 Batch Extraction Schema Explanation

### Why Source Attribution?
Every extracted item includes:
- `source_message_id`: Links back to the exact message
- `source_quote`: The verbatim text that was interpreted

This enables:
1. **Traceability**: Know exactly where each fact came from
2. **Verification**: Human reviewers can validate extractions
3. **Debugging**: Identify extraction errors or misinterpretations
4. **Incremental updates**: Re-extract only when source messages change

### Dimension Purposes

| Dimension | Answers | Example Question |
|-----------|---------|------------------|
| Core Identity | Who are they? | "What's their profession?" |
| Opinions & Views | What do they believe? | "How do they feel about AI?" |
| Preferences & Patterns | How do they behave? | "Do they prefer calls or texts?" |
| Desires & Needs | What do they want? | "What are their goals?" |
| Life Narrative | What's their story? | "Where did they grow up?" |
| Events | What's happening? | "Are they dealing with anything?" |
| Entities | Who/what matters to them? | "Who is Sarah to them?" |

### has_content Flag
Each dimension includes `has_content: true/false`:
- Enables quick filtering of empty dimensions
- Reduces downstream processing for sparse extractions
- Explicitly signals "we checked, nothing found" vs missing data

### Controlled Vocabularies

**desires_needs.type**: `need`, `want`, `wish`, `hope`
**desires_needs.is_active**: `yes`, `no`, `unknown`, `explicitly_uncertain`

These controlled vocabularies enable:
- Consistent categorization across extractions
- Reliable filtering and querying
- Reduced ambiguity in downstream processing

### Optional Fields
Fields marked "or null" are optional:
- Only populate when information is explicitly stated
- Never infer or assume values
- Null explicitly means "not mentioned" vs empty string
"""
