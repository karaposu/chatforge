# Prompt templates for Profile Miner LLM Service
# Based on CPF-7 (Conversational Profiling Framework - 7 Dimensions)

CORE_IDENTITY_PROMPT = """
=== CORE IDENTITY EXTRACTION ===

Extract facts about WHO THE PERSON IS from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract from TARGET MESSAGE.

WHAT COUNTS AS CORE IDENTITY:
- What someone IS (roles, attributes, states, affiliations)
- Stable characteristics that define them

WHAT DOES NOT COUNT (extract in other dimensions):
- What they THINK → opinions
- What they WANT → desires  
- What they DID → events/narrative
- What they PREFER → preferences
- Temporary states → events

EXAMPLES:
✓ "I'm a 34-year-old software engineer" → identity
✓ "I'm tall" → identity
✓ "I'm diabetic" → identity (chronic/defining condition)
✓ "I'm the skeptic in my group" → identity
✗ "I'm sick" → event (temporary)
✗ "I'm moving to Seattle" → event (in progress)
✗ "I think remote work is better" → opinion

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

INSTRUCTIONS:
- Extract each identity fact as a separate item
- Use the aspect/state_value schema (do NOT use predefined fields)
- aspect = what category of identity (age, profession, location, physical attribute, role, affiliation, condition, personality, etc.)
- state_value = the actual value/state
- temporal = only if explicitly time-bound ("currently", "since 2020")
- relational_dimension = only if identity is relative to others ("in my family", "at work")

Return JSON:
{{
  "has_identity_content": true/false,
  "items": [
    {{
      "aspect": "string - category of identity marker",
      "state_value": "string - the value",
      "temporal": "string or null",
      "relational_dimension": "string or null"
    }}
  ]
}}

If no identity information in target message, return:
{{"has_identity_content": false, "items": []}}
"""
OPINIONS_VIEWS_PROMPT = """
=== NON-EPHEMERAL OPINIONS & VIEWS EXTRACTION ===

Extract lasting beliefs and worldviews from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract from TARGET MESSAGE.

THE KEY TEST: Will this opinion likely persist beyond the current context?

WHAT COUNTS AS NON-EPHEMERAL:
- Beliefs about how things are or should be
- Value judgments that reflect worldview
- Stances on topics they'd likely hold tomorrow, next month

WHAT DOES NOT COUNT (ephemeral):
- "This coffee is cold" → momentary reaction
- "Traffic is bad today" → situational complaint
- "I'm annoyed right now" → temporary state
- Reactions to immediate context that won't persist

EXAMPLES:
✓ "Remote work is the future" → lasting belief
✓ "I think college is overrated" → worldview
✓ "AI is dangerous unless regulated" → conditional opinion (use qualifier)
✓ "Social media is toxic but necessary for business" → two opinions, split them
✗ "This meeting is pointless" → ephemeral frustration
✗ "I'm so tired of this" → momentary state

HANDLING COMPLEX OPINIONS:
- "AI is dangerous unless properly regulated"
  → about: "AI", view: "dangerous", qualifier: "unless properly regulated"

- "I love the product but hate the company"
  → Split into TWO separate items:
     1. about: "the product", view: "love it", qualifier: null
     2. about: "the company", view: "hate it", qualifier: null

DIMENSIONAL BOUNDARIES:
- Extract ONLY the opinion itself
- If they give reasoning ("because..."), that reasoning may belong in other dimensions or nowhere
- "I hate cities because I grew up rural" → extract "hates cities", the biographical info goes elsewhere

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

Return JSON:
{{
  "has_opinion_content": true/false,
  "items": [
    {{
      "about": "string - topic/subject of opinion",
      "view": "string - the stance/position taken",
      "qualifier": "string or null - conditions, exceptions ('unless...', 'except when...', 'probably')"
    }}
  ]
}}

If no non-ephemeral opinions in target message, return:
{{"has_opinion_content": false, "items": []}}
"""


PREFERENCES_PATTERNS_PROMPT = """
=== STABLE PREFERENCES & BEHAVIORAL PATTERNS EXTRACTION ===

Extract recurring choices and behavioral tendencies from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract from TARGET MESSAGE.

WHAT COUNTS AS PREFERENCE/PATTERN:
- Consistent behavioral choices
- Stated preferences for how they do things
- Habitual tendencies
- Recurring approaches to activities

WHAT DOES NOT COUNT:
- One-time actions → events
- What they ARE → identity
- What they BELIEVE → opinions
- What they WANT → desires

KEY INDICATORS:
- "always", "never", "usually", "typically", "prefer", "tend to"
- "I can't [X] without [Y]"
- "I [verb] better when..."
- Comparative preferences ("X over Y")

EXAMPLES:
✓ "I always code better at night"
  → activity_category: "work", activity: "coding", preference: "better at night", context: null

✓ "I prefer texting over calling unless it's urgent"
  → activity_category: "communication", activity: "contacting people", preference: "texting over calling", context: "unless urgent"

✓ "I can't sleep without white noise"
  → activity_category: "sleep", activity: "falling asleep", preference: "requires white noise", context: null

✓ "I usually skip breakfast but always have coffee"
  → Split into TWO items:
     1. activity_category: "eating", activity: "breakfast", preference: "usually skips", context: null
     2. activity_category: "eating", activity: "morning coffee", preference: "always has", context: null

✗ "I skipped breakfast today" → event (one-time)
✗ "I'm a morning person" → identity (what they are)
✗ "I think breakfast is important" → opinion (what they believe)

ACTIVITY_CATEGORY GUIDANCE:
Categories emerge from content. Common domains include:
work, communication, sleep, eating, exercise, learning, social, travel, shopping, entertainment, productivity, health
But use whatever category fits — don't force into predefined buckets.

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

Return JSON:
{{
  "has_preference_content": true/false,
  "items": [
    {{
      "activity_category": "string - broad domain (work, sleep, communication, etc.)",
      "activity": "string - specific activity or behavior",
      "preference": "string - the pattern or preference",
      "context": "string or null - conditions when this applies/doesn't apply"
    }}
  ]
}}

If no preferences/patterns in target message, return:
{{"has_preference_content": false, "items": []}}
"""

DESIRES_NEEDS_PROMPT = """
=== DESIRES, WISHES, HOPES & NEEDS EXTRACTION ===

Extract what the person wants, needs, wishes for, or hopes for from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract from TARGET MESSAGE.

TYPE DISTINCTIONS (controlled vocabulary):
- need: Essential, required, necessary ("I need health insurance")
- want: Active desire, something they're seeking ("I want to change careers")
- wish: Hypothetical, wistful, may not be actionable ("I wish I could travel more")
- hope: Optimistic aspiration, uncertain outcome ("I hope to get promoted")

WHAT COUNTS:
- Explicit desires: "I want...", "I need...", "I wish...", "I hope..."
- Goal statements: "My goal is...", "I'm trying to..."
- Implied needs from complaints: "I'm so burnt out" → may imply need for rest/change

WHAT DOES NOT COUNT:
- What they ARE → identity
- What they BELIEVE → opinions
- What they consistently DO → preferences
- Past aspirations stated as current fact → check is_active

DIMENSIONAL BOUNDARY PRINCIPLE:
Extract ONLY the aspiration itself. Consequences and context go elsewhere.

"I desperately need health insurance by January or I'll lose my medication"
→ Extract: type: "need", target: "health insurance", intensity: "desperately", temporal: "by January"
→ Do NOT extract "or I'll lose medication" here (that's an event/consequence)

HANDLING PAST VS CURRENT:
- "I want to travel" → is_active: "yes"
- "I wanted to be a doctor" → is_active: "no" (past, didn't happen)
- "I've always wanted to write a book" → is_active: "yes" (ongoing)
- "I'm not sure I want kids anymore" → is_active: "explicitly_uncertain"

EXAMPLES:
✓ "I really want to reconnect with my daughter"
  → type: "want", target: "reconnect with daughter", is_active: "yes", intensity: "really", temporal: null

✓ "I hoped to get promoted last year but didn't"
  → type: "hope", target: "get promoted", is_active: "no", intensity: null, temporal: "last year"

✓ "I desperately need better work-life balance"
  → type: "need", target: "better work-life balance", is_active: "yes", intensity: "desperately", temporal: null

✓ "Someday I wish I could just quit and travel the world"
  → type: "wish", target: "quit and travel the world", is_active: "yes", intensity: null, temporal: "someday"

✗ "I'm a very ambitious person" → identity (what they are)
✗ "I think everyone should travel" → opinion (what they believe)

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

Return JSON:
{{
  "has_desire_content": true/false,
  "items": [
    {{
      "type": "string - need/want/wish/hope (pick one)",
      "target": "string - what they aspire to",
      "is_active": "string - yes/no/unknown/explicitly_uncertain",
      "intensity": "string or null - desperately/really/somewhat/etc.",
      "temporal": "string or null - soon/someday/by January/etc."
    }}
  ]
}}

If no desires/needs in target message, return:
{{"has_desire_content": false, "items": []}}
"""

LIFE_NARRATIVE_PROMPT = """
=== LIFE NARRATIVE EXTRACTION ===

Extract biographical elements and life story from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract from TARGET MESSAGE.

WHAT COUNTS AS LIFE NARRATIVE:
- Past experiences that form their biographical arc
- Life chapters and phases
- Formative experiences
- Major transitions (career, location, relationship)
- Origin stories
- Challenges overcome
- Educational journey

WHAT DOES NOT COUNT:
- Current/recent discrete occurrences → Events dimension
- Future planned occurrences → Events dimension
- Temporary states → Events dimension
- What they ARE now → Identity dimension

KEY DISTINCTION — LIFE NARRATIVE VS EVENTS:
- "I lived in Tokyo for five years" → Life Narrative (biographical chapter)
- "I'm moving to Tokyo next month" → Events (upcoming occurrence)
- "I got divorced in 2019" → Life Narrative (past, biographical)
- "I'm going through a divorce" → Events (current, ongoing)

EXTRACTION RULES (critical):

**what_happened** — Core biographical fact ONLY:
✓ DO: "served in military", "lived in Paris", "got divorced", "dropped out of college"
✗ DON'T: "served in military for 3 years", "lived in Paris during college"
→ Remove: duration words (for, during), time markers (last year, in 2020, when I was 25)

**period** — ALL temporal information:
✓ DO: "three years", "during college", "age 5-15", "in the 90s", "after graduation", "2008", "childhood"
→ Include: duration, specific dates, life phases, age ranges, relative timing
→ If no temporal info given, use null

**significance** — ONLY if explicitly stated:
✓ DO: "taught me resilience", "changed my perspective", "made me who I am", "forced me to rebuild"
✗ DON'T: Infer or interpret meaning they didn't express
→ If they don't say how it affected/changed them, use null
→ "It was tough" is NOT significance unless they say it changed/taught them something

PARSING EXAMPLES:

| Statement | what_happened | period | significance |
|-----------|---------------|--------|--------------|
| "I lived in Japan for five years" | "lived in Japan" | "five years" | null |
| "My divorce in 2019 freed me" | "divorce" | "2019" | "freed me" |
| "Growing up poor shaped everything" | "grew up poor" | "childhood" | "shaped everything" |
| "I studied art throughout my twenties" | "studied art" | "twenties" | null |
| "After my startup failed, I joined Google" | Split into TWO items | | |

SPLITTING COMPLEX STATEMENTS:
"After my startup failed, I joined Google to learn from the best"
→ Item 1: what_happened: "startup failed", period: null, significance: null
→ Item 2: what_happened: "joined Google", period: "after startup failed", significance: "to learn from the best"

COMMON MISTAKES TO AVOID:
1. Embedding time in what_happened: "worked at Google for 10 years" → Split it
2. Inferring significance: Don't add meaning they didn't express
3. Missing compound periods: "from age 5 to 15" is ONE period value
4. Including future plans: Those belong in Events dimension
5. Over-interpreting: "It was hard" ≠ significance unless they say it changed them

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

Return JSON:
{{
  "has_narrative_content": true/false,
  "items": [
    {{
      "what_happened": "string - core biographical fact, no temporal markers",
      "period": "string or null - all temporal information",
      "significance": "string or null - only if explicitly stated how it affected them"
    }}
  ]
}}

If no life narrative content in target message, return:
{{"has_narrative_content": false, "items": []}}
"""

EVENTS_PROMPT = """
=== EVENTS & INVOLVEMENT EXTRACTION ===

Extract significant events and occurrences from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract from TARGET MESSAGE.

THE KEY TEST: Is something temporary happening that they're experiencing or participating in?

WHAT COUNTS AS EVENTS:
- Discrete occurrences (past, current, or future)
- Temporary ongoing states ("I'm sick", "I'm moving", "I'm renovating")
- Planned future events ("visiting Greece next summer")
- Things happening TO them or WITH them

WHAT DOES NOT COUNT:
- Opinions ("I hate meetings") → Opinions dimension
- Permanent characteristics ("I'm tall") → Identity dimension
- Chronic/defining conditions ("I'm diabetic") → Identity dimension
- Past biographical chapters ("I lived in Paris for 5 years") → Life Narrative dimension
- Aspirations ("I want to travel") → Desires dimension
- Habitual patterns ("I always get sick in winter") → Preferences dimension
- Observations without involvement ("there was an earthquake") → Skip

DISTINGUISHING EVENTS FROM LIFE NARRATIVE:
- Events: Current, recent, or future discrete occurrences
- Life Narrative: Past experiences that form biographical arc

"I'm going through a divorce" → Event (current, ongoing)
"I got divorced in 2019" → Life Narrative (past, biographical)
"I'm moving to Tokyo" → Event (in progress)
"I lived in Tokyo for five years" → Life Narrative (biographical chapter)

TEMPORARY VS PERMANENT STATE:
- "I'm sick" → Event (temporary)
- "I'm a teacher" → Identity (permanent role)
- "I'm pregnant" → Event (temporary state with endpoint)
- "I'm divorced" → Identity (permanent status)
- "I'm recovering from surgery" → Event (temporary)
- "I'm diabetic" → Identity (chronic condition)

INVOLVEMENT TYPES:
How did they participate? Examples:
- attended, organized, hosted, presented, witnessed
- participated, competed, won, lost
- experiencing, undergoing, surviving, recovering
- victim, recipient, beneficiary
- organizer, leader, guest, member

EXTRACTION RULES:

**event** — What happened/is happening:
- Core description without temporal markers or people names
- ✓ "TED talk presentation", "sick with flu", "job interview"
- ✗ "TED talk presentation last month with Sarah"

**involvement** — Their role/participation:
- How they were involved
- ✓ "presenter", "experiencing", "organizer", "attended", "recipient"

**temporal** — When/duration (flexible format):
- ✓ "yesterday", "last month", "current", "ongoing", "next week", "three hours", "during COVID"
- Use "current" or "ongoing" for present states

**people_involved** — Others involved (optional):
- List of people, relationships, or organizations
- ✓ ["Sarah"], ["my team"], ["Google"], ["mom", "sister"]
- Include direct participants only, not everyone mentioned
- Use relationship descriptors when names aren't given ("my boss", "the team")

**outcome** — Stated result (optional):
- ONLY if they explicitly state what resulted
- ✓ "got the job", "missed the reception", "flopped"
- ✗ Don't infer outcomes they didn't state

SIGNIFICANCE FILTERING:
Not all events warrant extraction. Apply this test:
- Will this event matter in a week? A month?
- Would they tell a friend about it?

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

EXAMPLES:

"Presented at a TED talk last month"
→ event: "TED talk presentation", involvement: "presenter", temporal: "last month", people_involved: null, outcome: null

"I'm sick with the flu"
→ event: "sick with flu", involvement: "experiencing", temporal: "current", people_involved: null, outcome: null

"Got food poisoning at Jim's wedding and missed the reception"
→ event: "food poisoning at wedding", involvement: "guest/victim", temporal: null, people_involved: ["Jim"], outcome: "missed reception"

"The conference I organized flopped"
→ event: "conference", involvement: "organizer", temporal: null, people_involved: null, outcome: "flopped"

"Just had a three-hour interview with Google"
→ event: "job interview", involvement: "candidate", temporal: "just had", people_involved: ["Google"], outcome: null

"My team won the hackathon!"
→ event: "hackathon", involvement: "participant/winner", temporal: null, people_involved: ["my team"], outcome: "won"

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

Return JSON:
{{
  "has_event_content": true/false,
  "items": [
    {{
      "event": "string - what happened/is happening",
      "involvement": "string - how they participated",
      "temporal": "string or null - when/duration",
      "people_involved": ["array of strings"] or null,
      "outcome": "string or null - only if explicitly stated"
    }}
  ]
}}

If no significant events in target message, return:
{{"has_event_content": false, "items": []}}
"""

ENTITIES_PROMPT = """
=== ENTITY EXTRACTION & RELATIONSHIPS ===

Extract people, organizations, places, and other significant entities from the TARGET MESSAGE.
Use CONTEXT MESSAGES to resolve references, but ONLY extract entities from TARGET MESSAGE.

WHAT TO EXTRACT:
- People: Named individuals or referenced relationships ("my boss", "Sarah")
- Organizations: Companies, schools, teams, groups, institutions
- Places: Cities, countries, venues, locations with significance
- Products/Technologies: Tools, platforms, products they use or mention
- Other: Any other significant named entity relevant to understanding them

UNIFIED ENTITY SCHEMA:
Every entity uses the same structure regardless of type.

**name** — The entity identifier:
- For named entities: "Sarah", "Google", "Seattle"
- For unnamed but identified: "my boss", "the team", "my therapist"

**type** — Entity category:
- person, organization, place, product, technology, pet, etc.

**mentioned_properties** — Any properties/facts mentioned about this entity:
- Flexible object — capture whatever is stated
- ✓ {"department": "marketing", "expertise": "growth hacking"}
- ✓ {"size": "startup", "industry": "fintech"}
- ✓ {"neighborhood": "downtown", "vibe": "expensive"}
- Only include properties actually mentioned, not inferred

**relationship_indicators** — How this entity relates to the speaker:
- Array of relationship types
- ✓ ["colleague", "mentor"]
- ✓ ["employer", "current"]
- ✓ ["hometown"]
- ✓ ["friend", "roommate"]
- Can have multiple: someone can be both "colleague" and "friend"

**interaction_metadata** — How they interact with this entity (optional):
- frequency: "daily", "weekly", "rarely", "once", etc.
- context: "professional", "personal", "social", "online", etc.
- recency: "current", "former", "past", etc.
- Only include if interaction pattern is mentioned or clearly implied

ENTITY DISAMBIGUATION:
When entities could be ambiguous, capture disambiguating context:

"John from accounting" 
→ name: "John", mentioned_properties: {"department": "accounting"}

"My brother John"
→ name: "John", relationship_indicators: ["brother", "family"]

"John (the CEO)"
→ name: "John", mentioned_properties: {"role": "CEO"}

"The Google I worked at vs Google now"
→ Two separate entities with different interaction_metadata recency

EXAMPLES:

"Sarah from marketing has been mentoring me weekly"
→ {
    "name": "Sarah",
    "type": "person",
    "mentioned_properties": {"department": "marketing"},
    "relationship_indicators": ["colleague", "mentor"],
    "interaction_metadata": {"frequency": "weekly", "context": "professional"}
  }

"I've been using Notion for everything since I left Google"
→ Entity 1: {
    "name": "Notion",
    "type": "product",
    "mentioned_properties": null,
    "relationship_indicators": ["tool"],
    "interaction_metadata": {"frequency": "regular", "context": "productivity", "recency": "current"}
  }
→ Entity 2: {
    "name": "Google",
    "type": "organization",
    "mentioned_properties": null,
    "relationship_indicators": ["employer"],
    "interaction_metadata": {"recency": "former"}
  }

"My hometown Seattle is too expensive now but I still visit my parents there"
→ Entity 1: {
    "name": "Seattle",
    "type": "place",
    "mentioned_properties": {"cost": "expensive"},
    "relationship_indicators": ["hometown"],
    "interaction_metadata": {"recency": "former resident", "frequency": "visits"}
  }
→ Entity 2: {
    "name": "parents",
    "type": "person",
    "mentioned_properties": {"location": "Seattle"},
    "relationship_indicators": ["family", "parents"],
    "interaction_metadata": {"frequency": "visits"}
  }

"My dog Max is getting old"
→ {
    "name": "Max",
    "type": "pet",
    "mentioned_properties": {"species": "dog", "age": "old"},
    "relationship_indicators": ["pet", "owner"],
    "interaction_metadata": null
  }

WHAT NOT TO EXTRACT:
- Generic mentions without relationship context ("Apple announced something")
- Entities they're merely discussing, not connected to
- Passing references with no profiling value

EXTRACTION PRIORITY:
Focus on entities that reveal something about the person's:
- Social/professional network
- Tools and environment they operate in
- Places significant to their life
- Organizations they're affiliated with

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}

Return JSON:
{{
  "has_entity_content": true/false,
  "items": [
    {{
      "name": "string - entity name or identifier",
      "type": "string - person/organization/place/product/technology/pet/etc.",
      "mentioned_properties": {{}} or null,
      "relationship_indicators": ["array of relationship types"],
      "interaction_metadata": {{"frequency": "...", "context": "...", "recency": "..."}} or null
    }}
  ]
}}

If no significant entities in target message, return:
{{"has_entity_content": false, "items": []}}
"""