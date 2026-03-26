# Behavioral Profiling — Specification

**Scope:** Per person, across all observed conversations
**Input:** PRAGMA Level 4-5 aggregations (cross-conversation dimension summaries)
**Output:** Communication signature describing HOW this person talks
**Method:** Mechanical aggregation of structured data + LLM composition into readable profile
**Question it answers:** "How does this person communicate?"


## What Behavioral Profiling Is

Behavioral Profiling describes observable communication patterns WITHOUT interpreting WHY. It reads PRAGMA dimension outputs directly, not APT readings.

```
APT Profiling:  "What moves this person?"
                → Charmed by expertise, fears rejection

Behavioral Profiling:  "How does this person communicate?"
                       → High density on technical topics, controls through
                         topic direction, compressed style, primarily queries
```

Behavioral Profiling tells you the WHAT. APT Profiling tells you the WHY. Both are per-person, cross-conversation. But Behavioral Profiling never touches attachment, charm, hope, or fear. It stays at the observable level.


## What It Aggregates

Each PRAGMA dimension already defines Level 5 (cross-conversation, per participant) in its `desc.md`. Behavioral Profiling composes these into one profile.

| Dimension | What Level 5 provides | Behavioral Profile reads as |
|---|---|---|
| **Expressed Involvement** | Avg micro-signals, dominant signals, trajectory patterns | "Consistently high self-reference, moderate evaluative force. Involvement spikes on technical topics." |
| **Information Density** | Topic-density map, avg specificity/novelty/relevance | "High density on technical topics, low on personal. High compression. Specific but sometimes repetitive." |
| **Control Distribution** | Dominant control mechanism, effect rate | "Controls through topic direction (75% effect rate). Rarely dominates verbosity. Balanced emotional register." |
| **Investment** | Avg score, consistency | "Consistently high investment. Fast responder. Does not withdraw." |
| **Dialogic Function** | Function distribution | "40% querying, 30% explaining, 20% sharing, 10% affirming. Rarely challenges." |
| **Conversational Intent** | Dominant intent categories | "Primary: discover (45%), inform (30%). Rarely: control, avoid." |
| **Temporal Structure** | Preferred conversation shapes | "Tends toward linear conversations. Rarely circular." |


## Aggregation: Two Steps

### Step 1: Mechanical Aggregation (no LLM)

Compute cross-conversation statistics from Level 4 data per dimension:

```python
def aggregate_behavioral_data(conversations, person_id):
    all_involvement = []
    all_density = []
    all_control = []
    all_investment = []
    all_functions = []
    all_intents = []

    for conv in conversations:
        level4 = conv.get_level4(person_id)
        all_involvement.append(level4.involvement)
        all_density.append(level4.density)
        all_control.append(level4.control)
        all_investment.append(level4.investment)
        all_functions.extend(level4.function_distribution)
        all_intents.extend(level4.intent_distribution)

    return {
        "involvement": {
            "avg": mean([i.avg for i in all_involvement]),
            "dominant_signals": most_common([i.dominant for i in all_involvement]),
            "stability": std_dev([i.avg for i in all_involvement]),
            "topic_sensitivity": topic_variance(all_involvement),
        },
        "density": {
            "avg_specificity": mean([d.specificity for d in all_density]),
            "avg_novelty": mean([d.novelty for d in all_density]),
            "avg_compression": mean([d.compression for d in all_density]),
            "topic_density_map": aggregate_topic_maps(all_density),
        },
        "control": {
            "dominant_mechanism": most_common([c.mechanism for c in all_control]),
            "avg_effect_rate": mean([c.effect_rate for c in all_control]),
            "verbosity_share": mean([c.verbosity for c in all_control]),
        },
        "investment": {
            "avg": mean([i.score for i in all_investment]),
            "consistency": 1.0 - std_dev([i.score for i in all_investment]),
        },
        "function_distribution": distribution(all_functions),
        "intent_distribution": distribution(all_intents),
        "conversation_count": len(conversations),
    }
```

### Step 2: LLM Composition (per profile update)

The LLM reads the mechanical aggregation and composes a readable communication signature.

```
=============================================================================
BEHAVIORAL PROFILING: COMMUNICATION SIGNATURE
=============================================================================

You are composing a behavioral profile for a person based on their
communication patterns across multiple conversations.

DESCRIBE how this person communicates. Do not interpret WHY.

AGGREGATED DATA:
{mechanical_aggregation_json}

CONVERSATION COUNT: {count}

PRIOR PROFILE (if updating):
{existing_profile_or_none}

=============================================================================
INSTRUCTIONS
=============================================================================

Compose a communication signature covering:

1. INVOLVEMENT STYLE: How present and activated is this person
   typically? What triggers higher or lower involvement?
   Which micro-signals are dominant?

2. DENSITY STYLE: How much substance do they typically provide?
   On which topics are they dense vs sparse? Are they specific?
   Novel? Compressed?

3. CONTROL STYLE: How do they control conversations? Topic
   direction? Verbosity? Emotional register? How effective
   are their control attempts?

4. INVESTMENT PATTERN: How much effort do they put in?
   Is it consistent or variable? Fast or slow responder?

5. FUNCTION PROFILE: What do they primarily do in conversations?
   Query? Explain? Share? Challenge? What's their function mix?

6. INTENT PROFILE: What are they usually trying to accomplish?
   Discover? Inform? Connect? What's their typical goal?

7. NOTABLE PATTERNS: Anything that stands out across
   conversations. Consistent behaviors, surprising gaps,
   or distinctive combinations.

Rules:
- DESCRIBE, don't interpret. "High involvement on technical topics"
  not "passionate about technology."
- Use numbers where they add precision. "Controls through topic
  direction with 75% effect rate."
- Note consistency. "Stable across 8 conversations" vs
  "variable, ranges from low to high."
- If updating, note what changed from prior profile.

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "person_id": "{person_id}",
  "profile_version": <integer>,
  "observation_count": <integer>,
  "confidence": "<very_low|low|moderate|high|very_high>",

  "signature": {
    "involvement_style": "<description>",
    "density_style": "<description>",
    "control_style": "<description>",
    "investment_pattern": "<description>",
    "function_profile": "<description>",
    "intent_profile": "<description>"
  },

  "notable_patterns": [
    "<pattern description>"
  ],

  "headline": "<one sentence communication signature>",

  "raw_aggregation": {
    <the mechanical aggregation data, preserved for reference>
  }
}
```


## Example Profile

```json
{
  "person_id": "person_a",
  "profile_version": 3,
  "observation_count": 8,
  "confidence": "moderate",

  "signature": {
    "involvement_style": "Consistently high self-reference and temporal involvement. Evaluative force is moderate. Involvement spikes on technical topics and drops on personal/social topics. Reactive disruption is rare. Stable across 8 conversations.",
    "density_style": "High density on technical topics (avg specificity 0.7, novelty 0.6). Low density on personal topics (avg specificity 0.3). High compression across all topics. Tends to be specific but occasionally repetitive when explaining foundational concepts.",
    "control_style": "Controls primarily through topic direction (75% effect rate across conversations). Verbosity share is balanced (45-55%). Does not dominate through volume. Emotional register is neutral-to-analytical. Rarely uses emotional register as a control mechanism.",
    "investment_pattern": "Consistently high investment (avg 0.78, std 0.08). Fast responder. Does not withdraw even in disagreements. Investment remains high across all conversation types observed.",
    "function_profile": "Querying (38%), Explaining (28%), Sharing (18%), Affirming (10%), Co-creating (6%). Rarely challenges (<2%). Never echoes.",
    "intent_profile": "Primary: Discover (42%), Inform (28%). Secondary: Co-create (15%). Rare: Control (5%), Connect (5%). Never: Avoid, Perform."
  },

  "notable_patterns": [
    "Involvement and density are correlated for this person: when involvement is high, density is also high. They don't get activated without providing substance.",
    "Function mix shifts toward querying when involvement is high, and toward explaining when involvement is moderate. High involvement = learning mode. Moderate = teaching mode.",
    "Investment never drops below 0.6 across any conversation. This person does not disengage."
  ],

  "headline": "High-investment, query-dominant communicator who controls through topic direction and provides dense, compressed substance on technical topics."
}
```


## Confidence Levels

Same as APT Profiling:

| Level | Observation Count | Meaning |
|---|---|---|
| very_low | 1 conversation | Single data point |
| low | 2-3 conversations | Early patterns |
| moderate | 4-7 conversations | Consistent patterns |
| high | 8-15 conversations | Stable patterns |
| very_high | 16+ conversations | Reliable signature |


## When It Runs

After each conversation ends. Same timing as APT Profiling update.

```
Conversation ends
       │
       ▼
  Level 4 aggregation computed for this conversation
       │
       ▼
  Behavioral Profiling update
  (reads existing profile + new Level 4 data)
       │
       ▼
  Updated profile stored
```


## What Behavioral Profiling Does NOT Do

- **Interpret.** "High involvement on technical topics" not "passionate about technology."
- **Infer attachment.** No charm, hope, fear. That's APT Profiling.
- **Replace per-conversation analysis.** The profile describes patterns across conversations. Each conversation still gets full PRAGMA analysis.
- **Predict motives.** It says what someone DOES, not why.


## Relationship to APT Profiling

```
PRAGMA dimensions (per conversation)
       │
       ├── Level 5 aggregation → Behavioral Profiling
       │   "How does this person communicate?"
       │   Observable patterns. No interpretation.
       │
       └── APT Inference → APT Profiling
           "What moves this person?"
           Attachment triggers. Interpretation layer.
```

Both profiles describe the same person. They complement each other:
- Behavioral Profiling: "This person queries a lot and invests heavily."
- APT Profiling: "This person is charmed by expertise and hopes for mentorship."

Together: "This person queries a lot BECAUSE they're charmed by expertise and hope to learn."

But the behavioral profile stands alone without APT. It's useful for personalization, coaching, and segmentation even without attachment theory.


## Downstream Consumers

| Consumer | What it reads | How |
|---|---|---|
| **Profile Grains (FOP)** | Full signature | Combines with CPDE-7 + APT Profiling |
| **Personalization** | Function profile + density style | Adapts communication approach |
| **Human analyst** | Headline + signature | Quick understanding of communication style |
| **APT Profiling** | Does NOT read behavioral profile | They're parallel, not sequential |