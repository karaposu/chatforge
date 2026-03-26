# APT Inference — Specification

**Position in pipeline:** After Interpretation Layer per-segment tension check
**Input:** Dynamics Profile text + per-segment tension analysis + prior APT readings (if any)
**Output:** Directional attachment readings (A→B, B→A) with categorical levels, reasons, presentation descriptions, and overall dynamic
**Method:** LLM query, on-demand or after each segment


## What APT Inference Is

APT Inference reads the Dynamics Profile and Interpretation Layer tensions for a segment and answers: **"What attachment dynamics explain these patterns?"**

It translates observed behavioral patterns into the APT vocabulary:
- **Charm**: how much does this participant look up to the other?
- **Hope**: how much does this participant believe they can benefit from the other?
- **Fear**: how much does this participant fear losing the other?

Plus a presentation reading:
- **Content**: what they say (topics, information, substance)
- **Style**: how they say it (involvement patterns, investment patterns, tempo)
- **Expressed Frame**: what investment dynamic their behavior implies ("I'm the selector" vs "please like me")


## Directionality

Attachment is relational and directional. A's attachment to B is independent from B's attachment to A.

```
A → B: charm=high, hope=moderate, fear=absent
B → A: charm=low, hope=high, fear=moderate
```

This asymmetry IS the dynamic. "A admires B but B needs something from A" tells you more than any single score.


## Categorical Levels

Charm, hope, and fear use 5 categorical levels:

| Level | Label | Meaning |
|---|---|---|
| 0 | absent | No signal of this attachment variable |
| 1 | low | Faint signal, could be noise |
| 2 | moderate | Clear signal, consistent across the segment |
| 3 | high | Strong signal, drives observable behavior |
| 4 | very_high | Dominant signal, shapes the entire dynamic |

Why categorical, not 0-1 floats: attachment cannot be measured to decimal precision. "Charm: 0.73" implies false precision. "Charm: high" correctly communicates the confidence level.


## What It Receives

```
1. DYNAMICS PROFILE (from Dynamics Profile layer):
   The composed natural language description of segment dynamics.

2. TENSION ANALYSIS (from Interpretation Layer per-segment check):
   Within-participant tensions, between-participant tensions,
   trajectory tensions, intent-behavior mismatches, control dynamics.

3. PRIOR APT READINGS (if this is not the first segment):
   The APT Inference output from prior segments in this conversation.
   Provides cumulative context. Attachment builds over time.
```


## LLM Prompt

```
=============================================================================
APT INFERENCE: ATTACHMENT & PRESENTATION READING
=============================================================================

You are performing an APT (Attachment & Presentation Theory) reading
for a conversation segment. Your job is to infer the attachment
dynamics between participants based on the observed behavioral patterns.

APT has two domains:

DOMAIN 1 — ATTACHMENT (why they stay):
  Charm: how much they look up to the other person.
    Signals: sustained involvement when the other speaks,
    seeking approval, querying, affirming toward the other,
    control tilted toward the other.
  Hope: belief they can benefit from this relationship.
    Signals: repeated engagement on topics where the other
    can provide value, forward-looking intent, increasing
    investment on specific topics, accessible high value.
  Fear: consequences of losing this relationship.
    Signals: asymmetric control they don't challenge,
    reluctance to disengage even when disinterested,
    careful word choices, avoidance of confrontation.

DOMAIN 2 — PRESENTATION (how they transmit):
  Content: what they say (topics, substance, information shared).
  Style: how they say it (involvement patterns, investment
    level, tempo, compression).
  Expressed Frame: what investment dynamic their behavior
    implies. "I set the agenda" vs "I follow your lead" vs
    "we're equals." Not their internal state. What their
    behavior communicates.

=============================================================================
SEGMENT DATA
=============================================================================

DYNAMICS PROFILE:
{dynamics_profile_text}

TENSION ANALYSIS:
{tension_analysis_json}

PRIOR APT READINGS (from earlier segments, if any):
{prior_apt_readings_or_none}

=============================================================================
INSTRUCTIONS
=============================================================================

For EACH participant, reading their behavior TOWARD the other:

1. Score charm, hope, and fear on 5 levels:
   absent / low / moderate / high / very_high

2. For EACH score, provide a reason grounded in the Dynamics Profile
   or tension analysis. The reason must reference specific observed
   dynamics, not vague impressions.

   GOOD reason: "Charm is high because A's involvement increases
   specifically when B demonstrates expertise, and A's dialogic
   function shifts to querying when B speaks."

   BAD reason: "A seems impressed by B." (not grounded)

3. Describe their presentation (content, style, expressed frame)
   as free-text. What are they communicating and how?

4. If prior APT readings exist, note what changed and why.
   Attachment evolves across segments. State whether this segment
   confirms, shifts, or contradicts prior readings.

5. Provide an overall dynamic summary: what is the attachment
   relationship between these participants in this segment?

6. Rate your confidence in this reading:
   low (first segment, sparse data),
   moderate (2-3 segments, consistent patterns),
   high (4+ segments, stable patterns confirmed)

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "segment_id": "{segment_id}",

  "a_toward_b": {
    "attachment": {
      "charm": {
        "level": "<absent|low|moderate|high|very_high>",
        "reason": "<one sentence grounded in dynamics>"
      },
      "hope": {
        "level": "<absent|low|moderate|high|very_high>",
        "reason": "<one sentence grounded in dynamics>"
      },
      "fear": {
        "level": "<absent|low|moderate|high|very_high>",
        "reason": "<one sentence grounded in dynamics>"
      }
    },
    "presentation": {
      "content": "<what A communicates to B — topics, substance>",
      "style": "<how A communicates — involvement, investment, tempo>",
      "expressed_frame": "<what A's behavior implies about the dynamic>"
    }
  },

  "b_toward_a": {
    "attachment": {
      "charm": {
        "level": "<absent|low|moderate|high|very_high>",
        "reason": "<one sentence grounded in dynamics>"
      },
      "hope": {
        "level": "<absent|low|moderate|high|very_high>",
        "reason": "<one sentence grounded in dynamics>"
      },
      "fear": {
        "level": "<absent|low|moderate|high|very_high>",
        "reason": "<one sentence grounded in dynamics>"
      }
    },
    "presentation": {
      "content": "<what B communicates to A>",
      "style": "<how B communicates>",
      "expressed_frame": "<what B's behavior implies about the dynamic>"
    }
  },

  "overall_dynamic": "<1-3 sentences describing the attachment
    relationship. Who is more attached? What drives it?
    What is the asymmetry?>",

  "evolution": "<if prior readings exist: what changed and why.
    If first segment: 'initial reading'>",

  "confidence": "<low|moderate|high>"
}
```


## Example Output

```json
{
  "segment_id": "t_003",

  "a_toward_b": {
    "attachment": {
      "charm": {
        "level": "high",
        "reason": "A's involvement increases when B shares technical expertise, and A shifts to querying function exclusively during B's explanations."
      },
      "hope": {
        "level": "moderate",
        "reason": "A's intent is consistently 'discover' toward B, and A steers topics toward areas where B has demonstrated knowledge."
      },
      "fear": {
        "level": "absent",
        "reason": "A freely challenges B's control attempts and redirects topic without hesitation."
      }
    },
    "presentation": {
      "content": "A shares personal context and asks targeted questions. High density on A's own domain, low density when responding to B's topics.",
      "style": "High involvement, moderate investment. Fast responses but concise. Compressed communication style.",
      "expressed_frame": "A presents as a peer seeking specific knowledge. Neither deferential nor dominant. 'I have my expertise, you have yours.'"
    }
  },

  "b_toward_a": {
    "attachment": {
      "charm": {
        "level": "low",
        "reason": "B's involvement does not increase when A speaks. B's dialogic function stays in explaining mode regardless of A's input."
      },
      "hope": {
        "level": "high",
        "reason": "B invests heavily in topics where A can provide access or decisions. B's density increases specifically on planning-related subtopics."
      },
      "fear": {
        "level": "moderate",
        "reason": "B does not challenge A's topic redirects despite higher verbosity. B's investment remains high even when involvement drops, consistent with reluctance to disengage."
      }
    },
    "presentation": {
      "content": "B provides detailed technical information and positions solutions. High density, moderate novelty.",
      "style": "High investment (long, fast responses) but moderate involvement. Thorough but not activated.",
      "expressed_frame": "B presents as the expert provider. 'I have what you need.' Investment asymmetry implies B values A's approval of the technical direction."
    }
  },

  "overall_dynamic": "A is charmed by B's expertise and is actively discovering what B knows. B needs something from A (likely decision-making authority or access) and is investing heavily to demonstrate value. The asymmetry is: A admires, B needs. A has the stronger frame because A's attachment is curiosity (optional), while B's is instrumental (necessary).",

  "evolution": "initial reading",

  "confidence": "low"
}
```


## When It Runs

APT Inference runs **after the per-segment tension check completes**, as the final step in the Interpretation Layer pipeline for that segment.

It can also run **on-demand** at any point in the conversation, using whatever segments have been analyzed so far.

For multi-segment conversations, each new APT Inference receives the prior segment's APT output as context. This creates a cumulative reading that grows more confident over time.

```
Segment 1 completes → DP → Tension Check → APT Inference (confidence: low)
Segment 2 completes → DP → Tension Check → APT Inference (reads prior, confidence: moderate)
Segment 3 completes → DP → Tension Check → APT Inference (reads prior, confidence: moderate-high)
```


## What APT Inference Does NOT Do

- **Profile.** APT Inference is per-conversation, per-pair. It does not aggregate across conversations. That's APT Profiling.
- **Prescribe.** It does not say what to do. "A is charmed by B" is a reading, not a recommendation.
- **Guarantee accuracy.** Attachment inference is inherently uncertain. The confidence field communicates this. Early readings can be wrong.
- **Extract signals.** All signals come from PRAGMA. APT Inference only interprets composed outputs.


## Downstream Consumer

| Consumer | What it reads | How |
|---|---|---|
| **APT Profiling** | Attachment levels + reasons across many conversations | Aggregates into individual attachment bearings |
| **Human analyst** | Overall dynamic + per-participant readings | Understands the relationship |
| **Strategy engine** | Attachment asymmetry + expressed frame | Determines engagement approach |


## Relationship to Existing Docs

- **apt_layer.md**: The theory. Defines charm/hope/fear and presentation. This spec is the implementation.
- **dynamics_profile.md**: Produces the primary input (segment description).
- **interpretation_layer_prompts.md**: Produces the tension analysis input. The pipeline diagram there shows APT Inference as the next step.
- **pragma.md**: References APT Inference as a downstream output. This spec fills in the details.