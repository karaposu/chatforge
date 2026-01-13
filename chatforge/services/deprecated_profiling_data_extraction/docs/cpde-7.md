
# CPDE-7: A Universal Framework for Conversational Profiling Data Extraction 

Conversational Profiling Data Extraction CPDE-7

## Introduction

The rise of Large Language Models has made semantic understanding of conversation accessible at scale. We can now extract rich, structured data from natural language with unprecedented accuracy. Yet despite these capabilities, there's no standardized framework defining *what* to extract and *how* to structure it for profiling purposes.

CPDE-7 (Conversational Profiling Framework - 7 Dimensions) fills this gap. It provides a comprehensive, implementation-agnostic specification for extracting profiling data from human conversation.

## Why Now?

Three trends make this framework critical:

1. **LLM Democratization**: Semantic analysis that once required specialized NLP pipelines is now a simple API call
2. **Conversation Explosion**: Voice interfaces, chatbots, and messaging platforms generate billions of conversations daily
3. **Profiling Necessity**: Personalization, recommendation systems, and AI assistants all require structured user understanding

Without a standard framework, every team reinvents profiling extraction, leading to:
- Inconsistent data structures across applications
- Missed extraction opportunities
- Privacy and ethical blindspots
- Inability to share tools and best practices

CPDE-7 provides the missing standard.

## The Challenge of Conversational Data

Every day, billions of conversations happen across chat apps, support tickets, social platforms, and voice assistants. Hidden within this unstructured text is a goldmine of information about people—their needs, preferences, relationships, and stories. But how do we extract this systematically?

Traditional approaches rely on keyword matching or sentiment analysis, but these miss the rich, multi-dimensional nature of human conversation. When someone says "I've been working at Google for three years but the Berkeley commute is killing me," they're simultaneously revealing their employer, tenure, residential area, and a pain point. A keyword system might catch "Google" but miss the deeper intelligence.

CPDE-7 defines a systematic approach to capturing all these layers of meaning.

## The Core Insight: Conversations Have Layers

When people talk, they reveal information across multiple dimensions simultaneously. Consider this simple message:

> "Just moved to Seattle for my new role at Amazon. Missing my family back in Boston, but excited about leading the AI team."

In one sentence, the speaker has shared:
- **Identity facts** (Amazon employee, team lead)
- **Recent events** (relocation, job change)
- **Emotional states** (missing family, excitement)
- **Relationships** (family in Boston)
- **Professional focus** (AI leadership)

A robust extraction system needs to be able to capture all these dimensions, not just the obvious keywords. 

## The Architecture: Seven Dimensions of Extraction

After analyzing thousands of conversations across different domains, we've identified seven fundamental dimensions that comprehensively capture profiling data:

### 1. Core Identity
These are the fundamental facts about who someone is. Names, roles, demographics—the stable attributes that define a person in social and professional contexts.

Predefining core_identity fields (name, age, job, etc.) would miss tons of identity markers that matter in different contexts. People express identity in incredibly diverse ways.

*"I'm a 34-year-old software engineer"* → Extracts: age: 34, profession: software_engineer




We Extract as core_identity when someone states what they ARE, not:

What they THINK (opinions)
What they WANT (desires)
What they DID (events)
What they PREFER (preferences)


and the template for extraction is like this: 


{ 
  "aspect": "physical attribute",
  "state_value": "tall", 
  "temporal": null,
  "relational_dimension": null 
}






### 2. Non-Ephemeral Opinions & Views
Not every opinion matters for profiling. "The coffee is cold" is ephemeral; "I think remote work is the future" reveals lasting beliefs. This dimension captures persistent worldviews while filtering out momentary reactions.

The key test: Will this opinion likely persist beyond the current context?


## Non-Ephemeral Opinions & Views Schema

```python
opinion_item = {
    "about": str,      # Topic/subject of the opinion
    "view": str,       # The stance/position taken
    "qualifier": str   # Optional: conditions, exceptions, or context
}
```

### Field Descriptions

**`about`** - What the opinion concerns (Bitcoin, remote work, marriage)  
**`view`** - The actual opinion/stance expressed  
**`qualifier`** - Modifiers that limit or condition the view ("except when...", "unless...", "probably")

### Why This Works

1. **Decomposition achieved** - Complex opinions split into atomic parts without losing meaning

2. **Handles contradictions naturally** - "Love the product, hate the company" becomes two clear items

3. **Preserves nuance** - Qualifier field captures conditions without overcomplicating the structure

4. **Query-friendly** - Can easily find all opinions about "Bitcoin" or all "negative" views

5. **LLM-extractable** - Simple enough that LLMs consistently identify topic vs stance

### Examples
```json
// Simple: "Traditional education is outdated"
{"about": "traditional education", "view": "outdated", "qualifier": null}

// Complex: "AI is dangerous unless properly regulated"
{"about": "AI", "view": "dangerous", "qualifier": "unless properly regulated"}

// Contradictory: Split into multiple items
[
  {"about": "social media", "view": "toxic", "qualifier": null},
  {"about": "social media", "view": "necessary", "qualifier": "for business"}
]
```

The schema is minimal yet captures the full spectrum from simple beliefs to complex conditional opinions. It decomposes without losing essential meaning.





### 3. Stable Preferences & Patterns
How someone consistently behaves tells us more than what they claim. This dimension identifies recurring choices and behavioral tendencies.

*"I always code better at night"* → Extracts: work_pattern: nocturnal, productivity_preference: evening


## Stable Preferences & Patterns Schema

```python
preference_pattern_item = {
    "activity_category": str,  # Broad domain for grouping/searching
    "activity": str,           # Specific activity or behavior
    "preference": str,          # The actual pattern/preference
    "context": str             # Optional: conditions or exceptions
}
```

### Field Descriptions

**`activity_category`** - High-level domain (work, communication, sleep, consumption, social, etc.)  
**`activity`** - The specific activity being described  
**`preference`** - The behavioral pattern or consistent choice  
**`context`** - Optional conditions when this preference applies or doesn't apply

### Why This Structure

The four-field approach provides a crucial balance between specificity and searchability. The `activity_category` field acts as an index, enabling rapid filtering across profiles ("show all sleep-related patterns"), while the `activity` field preserves the specific behavior being described. This hierarchical approach means applications can operate at either level of granularity as needed.

Categories are intentionally **not standardized** - they emerge naturally from the data, allowing for domain-specific needs and cultural variations. A medical app might extract categories like "medication" or "symptoms" while a fitness app finds "recovery" or "nutrition" patterns.

### Examples

```json
// "I prefer texting over calling unless it's urgent"
{
  "activity_category": "communication",
  "activity": "contacting people",
  "preference": "texting over calling",
  "context": "unless urgent"
}

// "I always code better at night"
{
  "activity_category": "work",
  "activity": "coding",
  "preference": "always better at night",
  "context": null
}

// "I can't sleep without white noise"
{
  "activity_category": "sleep",
  "activity": "falling asleep",
  "preference": "requires white noise",
  "context": null
}
```

The schema captures both the pattern and its domain, enabling sophisticated behavioral analysis while maintaining the simplicity needed for consistent extraction.

### 4. Desires, Wishes, Hopes & Needs
Understanding what someone wants—from immediate needs to life ambitions—enables prediction and personalization. This forward-looking dimension captures motivational drivers.

*"I really need better work-life balance"* → Extracts: need: work_life_balance, priority: high

## Desires, Wishes, Hopes & Needs Schema

```python
aspiration_item = {
    "type": str,        # need/want/wish/hope (controlled vocabulary)
    "target": str,      # What they aspire to
    "is_active": str,   # yes/no/unknown/explicity_uncertain- whether desire is current
    "intensity": str,   # Optional: desperately/really/somewhat
    "temporal": str     # Optional: when relevant (soon/someday/by January)
}
```

### Field Descriptions

**`type`** - Limited to four verbs that span the aspiration spectrum: need (essential), want (active desire), wish (hypothetical), hope (optimistic aspiration)

**`target`** - The object of aspiration, what they're expressing desire for

**`is_active`** - Critical for distinguishing current aspirations from historical ones ("I wanted kids" with is_active:"no" vs "I want kids" with is_active:"yes")

**`intensity`** - Captures natural language emphasis without forcing numerical scales

**`temporal`** - When this aspiration is relevant or targeted

### The Dimensional Boundary Principle

A key insight in CPDE-7 is that **each dimension extracts only what belongs to it**. When someone says:

> "I desperately need health insurance by January or I'll lose my medication"

The Desires/Wishes/Hopes/Needs dimension captures ONLY the aspiration:
- The desire: "desperately need health insurance by January"

The consequence ("or I'll lose medication") is NOT extracted here. It might belong in:
- Events dimension (potential future event)
- Core identity (has medical condition requiring medication)
- Or nowhere - not all information needs extraction

This discipline prevents dimensions from bleeding into each other. We decompose the sentence and each dimension takes only its relevant piece. The result is cleaner data that doesn't duplicate or conflate different types of information.

### Examples

```json
// "I really want to reconnect with my daughter"
{
  "type": "want",
  "target": "reconnect with daughter",
  "is_active": "yes",
  "intensity": "really",
  "temporal": null
}

// "I hoped to get promoted last year but didn't"
{
  "type": "hope",
  "target": "get promoted",
  "is_active": "no",  // Past, unfulfilled
  "intensity": null,
  "temporal": "last year"
}
```

This focused extraction ensures the dimension serves its purpose: understanding what people aspire to, without trying to capture entire narratives or causal chains.


### 5. Life Narrative
People are stories. This dimension pieces together the narrative arc—formative experiences, major transitions, and how individuals frame their journey.

*"After my startup failed, I joined Google to learn from the best"* → Extracts: startup_founder: failed, learning_motivation: true, career_transition: entrepreneur_to_corporate

Life Narrative Schema

```python
narrative_item = {
    "what_happened": str,   # Core fact only, no temporal markers
    "period": str,          # All temporal information
    "significance": str     # Only explicit meaning/impact statements
}
```

Field Descriptions

**`what_happened`** - The biographical element being shared. Direct, factual description of an experience, phase, or event from their life story.

**`period`** - Temporal context when available (childhood, college years, last year, age 25, etc.). Flexible format to accommodate how people naturally express life timing.

**`significance`** - Only populated when someone explicitly states how this shaped, changed, or affected them. Many life narrative elements are shared without interpretation, and that's fine.

 Distinguishing Life Narrative from Events

The key distinction:
- **Life Narrative**: Elements of their life story, typically past, that form their biographical arc
- **Events**: Current, recent, or future discrete occurrences

"I lived in Tokyo for five years" → Life Narrative (biographical chapter)  
"I'm moving to Tokyo next month" → Events (upcoming occurrence)

 Examples

```json
// "I was raised by my grandmother"
{
  "what_happened": "raised by grandmother",
  "period": "childhood",
  "significance": null
}

// "My bankruptcy in 2008 forced me to rebuild everything"
{
  "what_happened": "bankruptcy",
  "period": "2008",
  "significance": "forced me to rebuild everything"
}

// "I spent three years in the military"
{
  "what_happened": "served in military",
  "period": "three years",
  "significance": null
}
```

Design Principle

Life Narrative extraction is deliberately inclusive - not every biographical element needs explicit meaning-making. People share their life stories through simple facts ("I went to MIT") as much as through interpreted experiences ("MIT opened my eyes to possibility"). Both are valid narrative elements.

The schema captures the story someone tells about their journey, whether they provide interpretation or simply state what happened. The significance field remains optional, filled only when meaning is explicitly provided.

 Extraction Rules for LLMs

**`what_happened`** - Extract the core biographical fact:
- ✅ DO: "served in military", "lived in Paris", "got divorced"
- ❌ DON'T: "served in military for 3 years", "lived in Paris during college"
- Remove: Duration words (for, during), time markers (last year, in 2020)

**`period`** - Extract ALL temporal information:
- ✅ DO: "three years", "during college", "age 5-15", "in the 90s", "after graduation"
- ❌ DON'T: Leave temporal info in what_happened field
- Include: Duration, specific dates, life phases, age ranges, relative timing

**`significance`** - ONLY extract if explicitly stated:
- ✅ DO: "taught me resilience", "changed my perspective", "made me who I am"
- ❌ DON'T: Infer or interpret meaning that isn't directly stated
- Rule: If they don't say how it affected them, leave null

 Parsing Examples

| Statement | what_happened | period | significance |
|-----------|---------------|---------|--------------|
| "I lived in Japan for five years" | "lived in Japan" | "five years" | null |
| "My divorce in 2019 freed me" | "divorce" | "2019" | "freed me" |
| "Growing up poor" | "grew up poor" | "childhood" | null |
| "I studied art throughout my twenties" | "studied art" | "twenties" | null |

 Common Parsing Mistakes to Avoid

1. **Embedding time in what_happened**: "worked at Google for 10 years" → Should split
2. **Inferring significance**: Don't add meaning they didn't express
3. **Missing compound periods**: "from age 5 to 15" is one period value, not split
4. **Over-interpreting**: "It was tough" is not significance unless they say it changed/taught them

These guidelines ensure consistent extraction across different LLM implementations.

### 6. Events & Involvement
What someone does or experiences, filtered by significance. Not every event matters—we need configurable thresholds to separate signal from noise.

The system asks: Will this event matter in a week? A month? Would they tell a friend about it?



 Events & Involvement Schema

```python
event_item = {
    "event": str,              # What happened/is happening
    "involvement": str,        # How they participated
    "temporal": str,           # Optional: when/duration
    "people_involved": [str],  # Optional: others involved
    "outcome": str            # Optional: stated result/consequence
}
```

Field Descriptions

**`event`** - The occurrence or activity. Core description without temporal markers or people names.

**`involvement`** - The person's role or participation type (attended, organized, witnessed, survived, won, participated, experiencing, etc.)

**`temporal`** - When it happened or how long it lasted. Flexible format: "yesterday", "three hours", "last summer", "during COVID", "current", "ongoing"

**`people_involved`** - List of people or entities involved. Can include individuals ("Sarah"), relationships ("my team"), or organizations ("Google")

**`outcome`** - Only populated if they explicitly state what resulted. Not interpretations, only stated consequences.

Distinguishing Events from Other Dimensions

Events capture **temporary occurrences or states with user involvement**, not:
- Opinions ("I hate meetings") → Opinion dimension
- Permanent characteristics ("I'm tall") → Core identity  
- Chronic conditions ("I'm diabetic") → Core identity
- Past biographical chapters ("I lived in Paris for 5 years") → Life narrative
- Aspirations ("I want to travel") → Desires/wishes
- Patterns ("I always get sick in winter") → Preferences/patterns

The key test: Is something temporary happening that they're experiencing or participating in?

Examples

```json
// "Presented at TED talk last month"
{
  "event": "TED talk presentation",
  "involvement": "presenter",
  "temporal": "last month",
  "people_involved": null,
  "outcome": null
}

// "I'm sick with the flu"
{
  "event": "sick with flu",
  "involvement": "experiencing",
  "temporal": "current",
  "people_involved": null,
  "outcome": null
}

// "Got food poisoning at Jim's wedding and missed the reception"
{
  "event": "food poisoning at wedding",
  "involvement": "guest/victim",
  "temporal": null,
  "people_involved": ["Jim"],
  "outcome": "missed reception"
}
```

Significance Filtering

Not all events warrant extraction. The framework allows configurable thresholds:

**High Significance** (always extract):
- Life milestones (graduation, marriage, birth)
- Professional changes (promotion, job loss)
- Achievements (won award, completed marathon)
- Crises (accident, illness, emergency)
- Health events (sick, injured, recovering)

**Medium Significance** (domain-dependent):
- Social events (parties, meetups)
- Travel (trips, visits)
- Learning experiences (workshops, courses)

**Low Significance** (usually skip):
- Routine activities (had lunch, went shopping)
- Daily occurrences (commuted, had meeting)

Applications configure their own threshold based on use case.

Extraction Guidelines for LLMs

**DO Extract**:
- Events where user was actively involved
- Temporary ongoing states ("I'm sick", "I'm moving", "I'm renovating")
- Future planned events ("visiting Greece next summer")
- Events with clear boundaries or temporary nature
- Group events where user participated

**DON'T Extract**:
- Observations without involvement ("there was an earthquake")
- Permanent states ("I'm tall", "I'm introverted")
- Chronic/defining conditions ("I'm diabetic" → core_identity)
- Habitual patterns ("I go to gym every day" → preferences_patterns)
- Pure opinions about events without participation

**Temporal State Guidelines**:
- "I'm sick" → Extract (temporary event)
- "I'm a teacher" → Don't extract (identity)
- "I'm pregnant" → Extract (temporary state with endpoint)
- "I'm divorced" → Don't extract (permanent status → identity)

**People_involved Guidelines**:
- Include direct participants, not everyone mentioned
- Can include organizations/entities, not just individuals
- Use relationship descriptors when names aren't given ("my boss", "the team")
Common Parsing Patterns

| Statement | event | involvement | temporal | people_involved | outcome |
|-----------|-------|-------------|----------|-----------------|---------|
| "I'm recovering from surgery" | "recovering from surgery" | "experiencing" | "current" | null | null |
| "Attended mom's 60th birthday" | "60th birthday" | "attended" | null | ["mom"] | null |
| "Got married in Vegas last year" | "got married" | "participant" | "last year" | null | "in Vegas" |
| "The conference I organized flopped" | "conference" | "organizer" | null | null | "flopped" |

This schema captures what happened or is happening while maintaining clear boundaries with other dimensions, enabling rich event extraction without narrative overlap.



### 7. Entity Extraction & Relationships
People don't exist in isolation. This dimension maps their world—the people, organizations, places, and things they interact with.

```json
{
  "name": "Sarah",
  "type": "person",
  "mentioned_properties": {
    "department": "marketing",
    "expertise": "growth hacking"
  },
  "relationship_indicators": ["colleague", "mentor"],
  "interaction_metadata": {
    "frequency": "weekly",
    "context": "professional"
  }
}
```


## Some points

Temporal decay and contradiction handling are unaddressed. If someone said "I love my job" in January and "I hate my job" in March, what's the profile state? The document mentions the problem but doesn't solve it. But this is not an issue of profiling data extractor. 



## The Technical Implementation

### Moving Beyond Keywords: LLM-Powered Understanding

Traditional extraction systems fail because they lack semantic understanding. CPDE-7 leverages Large Language Models to truly comprehend context. All data extraction should be done via LLMs 












### Configurable Extraction Levels

Not every application needs every detail. A dating app cares about hobbies and relationship goals; a professional network focuses on skills and career trajectory. Profile Miner supports configurable extraction:

```python
config = {
    'core_identity': True,
    'opinions_views': True,
    'preferences_patterns': True,
    'desires_needs': True,
    'life_narrative': False,  # Not needed for this use case
    'events': 'significant_only',  # Filter threshold
    'entities': True
}
```

## Handling Edge Cases

### The Overlap Problem
"I got divorced last year" is both an event and part of life narrative. Rather than forcing single categorization, Profile Miner allows multi-dimension assignment with confidence scores.

### Entity Disambiguation
When someone mentions "John," which John? The system (if entity capture is enabled) captures disambiguation context:
- *"John from accounting"* → professional context
- *"My brother John"* → family relationship
- *"John (the CEO)"* → hierarchical indicator

### Temporal Context
*"I hate my job"* hits differently than *"I hated my last job."* The system preserves temporal markers to distinguish current states from historical facts.

## Real-World Applications

### Social Networking 2.0
Imagine a dating app that actually understands you. Not just age and location, but that you're an early-morning runner who values intellectual conversations and is navigating career transition anxiety. Profile Miner makes this possible.

### Conversational AI Memory
Voice assistants that remember not just your calendar, but your story. "You mentioned your startup last month—how's that going?" This contextual continuity transforms transactional interactions into relationships.

### Enterprise Intelligence
Companies analyzing customer support conversations can identify not just immediate issues but underlying needs, relationship dynamics, and churn predictors—all from natural conversation.



## Looking Forward: The Graph Layer

Profile Miner is the extraction layer in a larger ecosystem. Extracted data feeds into:

- **Knowledge Graphs**: Connecting entities and relationships
- **Behavioral Models**: Predicting preferences and actions
- **Matching Engines**: Finding compatible people or opportunities
- **Personalization Systems**: Adapting experiences to individual needs

The key insight is separation of concerns: Profile Miner extracts what was said, downstream systems interpret what it means.

## Conclusion: Structured Understanding at Scale

We're living through an explosion of conversational interfaces—chat, voice, video. The organizations and applications that can systematically understand these conversations will have an enormous advantage. But understanding requires structure.

Profile Miner bridges this gap, transforming messy human conversation into clean, structured data ready for analysis, personalization, and intelligence applications. It's not about surveillance or manipulation—it's about building systems that truly understand and serve human needs.

The technology is here. The frameworks are emerging. The question isn't whether conversational profiling will transform how we build applications—it's who will build them responsibly and effectively.




