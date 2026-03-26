# APT Profiling — Specification

**Scope:** Per person, across all observed conversations and relationships
**Input:** Accumulated APT Inference outputs for one person + existing profile (if updating)
**Output:** Individual attachment bearings + presentation tendencies
**Method:** LLM semantic aggregation, updated incrementally after each conversation
**Question it answers:** "What moves this person?"


## What APT Profiling Is

APT Inference tells you what's happening in ONE conversation: "A is charmed by B's expertise."

APT Profiling tells you what's true about a person ACROSS conversations: "A tends to get charmed by expertise. Wealth does not charm A. A hopes for mentorship. A fears rejection."

It's the difference between one observation and a pattern.

```
APT Inference outputs (accumulated):
  Conv 1: A→B charm=high, reason="B's deep engineering knowledge"
  Conv 2: A→C charm=absent, reason="C talks about money, not substance"
  Conv 3: A→D charm=high, reason="D's research depth impressed A"
  Conv 4: A→E charm=moderate, reason="E knows the field but was condescending"

APT Profiling extracts:
  Charm trigger: intellectual expertise and depth of knowledge.
  Charm blocker: condescension reduces charm even when expertise is present.
  Non-trigger: wealth, status without substance.
```


## Two Sections

### 1. Attachment Bearings

What triggers each attachment variable for this person. Not levels (those are per-conversation), but **trigger patterns**: what specifically charms them, what they hope for, what they fear.

```
CHARM BEARINGS:
  Triggers: [what consistently produces charm]
  Blockers: [what prevents charm even when triggers are present]
  Non-triggers: [what doesn't produce charm despite seeming relevant]
  Evidence count: N conversations observed

HOPE BEARINGS:
  Triggers: [what makes them believe they can benefit]
  Blockers: [what kills hope]
  Non-triggers: [what doesn't produce hope]
  Evidence count: N

FEAR BEARINGS:
  Triggers: [what makes them fear loss]
  Blockers: [what reduces fear]
  Non-triggers: [what doesn't produce fear despite seeming relevant]
  Evidence count: N
```

### 2. Presentation Tendencies

How this person presents under different conditions. Extracted from the presentation descriptions in APT Inference outputs. Structured as **condition → behavior** mappings.

```
PRESENTATION TENDENCIES:
  When confident → [observed behavior pattern]
  When insecure → [observed behavior pattern]
  When challenged → [observed behavior pattern]
  When charmed → [observed behavior pattern]
  When pursuing hope → [observed behavior pattern]
  When afraid → [observed behavior pattern]
  Default style → [baseline behavior when no strong condition]
```


## Schema

```json
{
  "person_id": "string",
  "profile_version": "integer (increments on update)",
  "last_updated": "timestamp",
  "observation_count": "number of conversations analyzed",
  "confidence": "<very_low|low|moderate|high|very_high>",

  "attachment_bearings": {
    "charm": {
      "triggers": ["pattern 1", "pattern 2"],
      "blockers": ["pattern"],
      "non_triggers": ["pattern"],
      "summary": "one-sentence summary of what charms this person",
      "evidence_count": 4
    },
    "hope": {
      "triggers": ["pattern"],
      "blockers": ["pattern"],
      "non_triggers": ["pattern"],
      "summary": "one-sentence summary of what they hope for",
      "evidence_count": 3
    },
    "fear": {
      "triggers": ["pattern"],
      "blockers": ["pattern"],
      "non_triggers": ["pattern"],
      "summary": "one-sentence summary of what they fear",
      "evidence_count": 2
    }
  },

  "presentation_tendencies": {
    "when_confident": "description of behavior",
    "when_insecure": "description of behavior",
    "when_challenged": "description of behavior",
    "when_charmed": "description of behavior",
    "when_pursuing_hope": "description of behavior",
    "when_afraid": "description of behavior",
    "default_style": "description of baseline behavior",
    "frame_stability": "<stable|fragile|context_dependent>",
    "frame_note": "one sentence about frame behavior"
  },

  "notable_patterns": [
    {
      "pattern": "description of a cross-conversation pattern",
      "evidence": "which conversations support this",
      "counter_evidence": "which conversations contradict this (if any)"
    }
  ],

  "context_notes": [
    {
      "context": "<work|personal|formal|casual|etc>",
      "note": "how behavior differs in this context (if observed)"
    }
  ]
}
```


## Confidence Levels

| Level | Observation Count | Meaning |
|---|---|---|
| very_low | 1 conversation | Provisional. Single data point. Might be noise. |
| low | 2-3 conversations | Early patterns emerging. Could still be coincidence. |
| moderate | 4-7 conversations | Consistent patterns across multiple relationships. |
| high | 8-15 conversations | Stable patterns with counter-examples accounted for. |
| very_high | 16+ conversations | Reliable individual profile. Predictive. |


## How Update Works

APT Profiling is not rebuilt from scratch each time. It's incrementally updated by an LLM that reads the existing profile + new APT Inference output.

### Update Prompt

```
=============================================================================
APT PROFILING: PROFILE UPDATE
=============================================================================

You are updating an individual APT Profile based on a new conversation.

EXISTING PROFILE:
{existing_profile_json}

NEW APT INFERENCE (from latest conversation):
{new_apt_inference_json}

CONVERSATION CONTEXT (optional):
{context_metadata — work/personal/formal/casual}

=============================================================================
INSTRUCTIONS
=============================================================================

Read the new APT Inference and update the profile:

1. ATTACHMENT BEARINGS:
   - Do the new charm/hope/fear reasons CONFIRM existing triggers?
     If yes, strengthen the pattern.
   - Do they CONTRADICT existing triggers?
     If yes, add counter-evidence. Don't delete the pattern,
     but note the exception.
   - Do they reveal a NEW trigger not yet in the profile?
     If yes, add it with evidence_count=1.

2. PRESENTATION TENDENCIES:
   - Does the new presentation description match existing
     condition→behavior mappings?
   - Does it reveal a new condition or a new behavior under
     a known condition?
   - Update frame_stability if there's evidence of frame
     shift or consistency.

3. NOTABLE PATTERNS:
   - Any cross-conversation pattern becoming clearer?
   - Any pattern being weakened by counter-evidence?

4. CONFIDENCE:
   - Increment observation_count.
   - Update confidence level based on count.

5. CONTEXT:
   - If the new conversation has context metadata, note
     any context-specific behavior differences.

Do NOT average levels. Levels are per-conversation.
You aggregate REASONS and PATTERNS, not numbers.

=============================================================================
OUTPUT
=============================================================================

Return the full updated profile JSON (same schema as input,
with updates applied).
```


## Example Profile

```json
{
  "person_id": "person_a",
  "profile_version": 4,
  "last_updated": "2026-03-24T14:30:00Z",
  "observation_count": 4,
  "confidence": "low",

  "attachment_bearings": {
    "charm": {
      "triggers": [
        "deep technical or intellectual expertise",
        "original thinking that goes beyond conventional approaches"
      ],
      "blockers": [
        "condescension or superiority, even when expertise is genuine"
      ],
      "non_triggers": [
        "wealth or financial success alone",
        "social status without demonstrated substance"
      ],
      "summary": "Charmed by genuine intellectual depth, blocked by condescension.",
      "evidence_count": 4
    },
    "hope": {
      "triggers": [
        "access to mentorship or learning opportunities",
        "collaborative problem-solving on hard technical challenges"
      ],
      "blockers": [
        "transactional framing ('I'll teach you if you do X')"
      ],
      "non_triggers": [
        "career advancement or networking opportunities"
      ],
      "summary": "Hopes for intellectual mentorship and genuine collaboration.",
      "evidence_count": 3
    },
    "fear": {
      "triggers": [
        "being perceived as not knowledgeable enough",
        "intellectual dismissal"
      ],
      "blockers": [],
      "non_triggers": [
        "financial loss",
        "social exclusion"
      ],
      "summary": "Fears intellectual rejection. Financial or social threats don't register.",
      "evidence_count": 2
    }
  },

  "presentation_tendencies": {
    "when_confident": "Compressed, high-density communication. Asks targeted questions. Controls topic direction without dominating verbosity.",
    "when_insecure": "Over-explains. Density increases but novelty drops. Repeats prior points with added precision.",
    "when_challenged": "Involvement increases sharply. Shifts to explaining/defending mode. Frame weakens if challenge is on intellectual grounds.",
    "when_charmed": "Involvement spikes. Shifts to querying. Defers topic control to the charming party. Investment increases.",
    "when_pursuing_hope": "Steers topics toward areas where the other has expertise. Forward-looking intent. High density on planning subtopics.",
    "when_afraid": "Reluctance to disengage. Investment stays high even when involvement drops. Avoids challenging control.",
    "default_style": "Moderate involvement, moderate investment. Balanced control. Querying + sharing functions. Compressed communication.",
    "frame_stability": "fragile",
    "frame_note": "Frame is stable under general conditions but collapses when intellectual competence is challenged. Recovers slowly."
  },

  "notable_patterns": [
    {
      "pattern": "Charm and hope are correlated for this person: when charmed by expertise, also hopes for learning. These are not independent.",
      "evidence": "Conv 1, Conv 3: both showed high charm and moderate-high hope from same source",
      "counter_evidence": "None observed"
    },
    {
      "pattern": "Investment stays high even in fear state. This person does not withdraw when afraid. They stay and endure.",
      "evidence": "Conv 4: fear=moderate but investment remained high throughout",
      "counter_evidence": "None observed"
    }
  ],

  "context_notes": [
    {
      "context": "work/technical",
      "note": "All 4 observations are in technical/work contexts. No personal or casual data yet."
    }
  ]
}
```


## When APT Profiling Runs

Not per-message. Not per-segment. **Per conversation, after the conversation ends** (or at significant milestones in very long conversations).

```
Conversation ends
       │
       ▼
  All segment APT Inferences collected
       │
       ▼
  APT Profiling update prompt runs
  (reads existing profile + all APT Inferences from this conversation)
       │
       ▼
  Updated profile stored
```


## What APT Profiling Does NOT Do

- **Replace APT Inference.** APT Inference is still needed per conversation. The profile is built FROM inference outputs, not instead of them.
- **Predict with certainty.** The profile describes patterns, not laws. "Usually charmed by expertise" allows for exceptions.
- **Score relationships.** APT Profiling is about the individual. "What moves person A?" Not "how does A relate to B." That's APT Inference.
- **Average levels.** Levels (absent/low/moderate/high/very_high) are per-conversation. The profile extracts TRIGGER PATTERNS from the reason fields, not averages from the level fields.


## Downstream Consumers

| Consumer | What it reads | How |
|---|---|---|
| **Strategy engine** | Charm triggers + presentation tendencies | Determines how to engage this person effectively |
| **Profile Grains (FOP)** | Full profile | Combines with CPDE-7 for complete user understanding |
| **Human analyst** | Summary fields + notable patterns | Understands what moves this person |
| **Prediction** | Attachment bearings | Anticipates how this person will respond to a new relationship |