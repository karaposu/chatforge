# Interpretation Layer: Signal Gap Prompts

The Interpretation Layer reads all PRAGMA dimension outputs together and identifies tensions, inconsistencies, and patterns that no single dimension reveals. Signal gaps are one of its primary outputs.

Two prompts: per-message and per-segment.


## Per-Message Gap Check

Runs after all dimension LLM calls complete for a message. Reads the combined output and identifies tensions.

```
=============================================================================
PRAGMA INTERPRETATION: PER-MESSAGE TENSION ANALYSIS
=============================================================================

You are reading the combined PRAGMA analysis for a single message.
Your job is to identify any tensions or inconsistencies between
the dimension readings. Tensions reveal what's really happening
beneath the surface.

=============================================================================
DIMENSION READINGS FOR THIS MESSAGE
=============================================================================

TOPIC (from Topic Flow):
{topic_flow_output}

DIALOGIC FUNCTION:
{dialogic_function_output}

EXPRESSED INVOLVEMENT:
{ei_output}

INTENT:
{intent_output}

INVESTMENT:
{investment_output}

=============================================================================
INSTRUCTIONS
=============================================================================

Look at these readings together. Do any seem inconsistent with
each other?

Common tensions to watch for (but don't limit yourself to these):

- HIGH investment but LOW involvement: effort without activation.
  Why would someone put in effort but not be engaged?

- Intent classified as one thing but involvement/investment
  signals suggest another: surface intent vs actual behavior.
  Are they saying one thing but doing another?

- HIGH involvement but dialogic function is mostly echoing/affirming:
  activated but not contributing substance. Why?

- HIGH investment + LOW relevance to topic: putting effort into
  something off-topic. Deflection? Impression management?

- Intent = "discover" but dialogic function = mostly explaining:
  claim to be learning but actually teaching. Hidden agenda?

Also look for:
- Anything that seems "off" or surprising given the combination
- Readings that are unusually aligned (everything pointing the
  same direction can be meaningful too: genuine or performed?)

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "tensions_detected": true/false,
  "tensions": [
    {
      "dimensions_involved": ["dimension_a", "dimension_b"],
      "what_conflicts": "string describing the tension",
      "what_it_might_suggest": "string interpreting the tension",
      "confidence": 0.0-1.0
    }
  ],
  "overall_coherence": "coherent|minor_tensions|significant_tensions",
  "note": "string - any additional observation about the combined picture"
}

If no tensions detected:
{
  "tensions_detected": false,
  "tensions": [],
  "overall_coherence": "coherent",
  "note": "All readings are consistent. No hidden dynamics detected at message level."
}
```


## Per-Segment Gap Check

Runs after a topic segment completes and after the Dynamics Profile has been composed. Reads the Dynamics Profile description (not raw signals) and identifies relational tensions and hidden dynamics.

```
=============================================================================
PRAGMA INTERPRETATION: PER-SEGMENT TENSION ANALYSIS
=============================================================================

You are reading the Dynamics Profile for a conversation segment.
The Dynamics Profile DESCRIBES what happened. Your job is to
INTERPRET what it means: identify tensions, hidden dynamics,
and strategic patterns between participants.

=============================================================================
SEGMENT CONTEXT
=============================================================================

TOPIC:
{segment_topic_info}

SEGMENT: messages {start} to {end}

=============================================================================
DYNAMICS PROFILE
=============================================================================

{dynamics_profile_text}

=============================================================================
NOTABLE SIGNAL GAPS
=============================================================================

{notable_gaps_json}

=============================================================================
INSTRUCTIONS
=============================================================================

The Dynamics Profile describes WHAT is happening. You interpret WHY.
Look at the description and identify:

1. WITHIN-PARTICIPANT TENSIONS
   Does any participant's readings contradict each other?
   (e.g., A's investment is increasing but involvement is decreasing)

2. BETWEEN-PARTICIPANT TENSIONS
   Do the two participants' readings tell a conflicting story?
   (e.g., both claim to be leading, or one invests heavily while
   the other withdraws)

3. TRAJECTORY TENSIONS
   Do any readings start aligned but diverge? Or start diverged
   but converge? What happens at the inflection point?

4. INTENT-BEHAVIOR MISMATCHES
   Does either participant's intent arc match their actual
   behavioral signals? Or is there a gap between what they seem
   to be trying to do and what they're actually doing?

5. CONTROL DYNAMICS
   Who is actually running this segment? Does the control profile
   match the involvement and investment patterns? Or is someone
   controlling without investing (strategic) or investing without
   controlling (following)?

Common relational patterns to watch for:

- Pursuit/withdrawal: one escalates involvement while the other
  de-escalates

- Performative alignment: both readings look "correct" but
  something feels off. Too aligned? Too smooth?

- Hidden competition: both claim collaborative intent but control
  signals show competition

- Asymmetric investment: one participant carries the segment while
  the other coasts

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "within_participant_tensions": [
    {
      "participant": "a|b",
      "what_conflicts": "string",
      "what_it_suggests": "string"
    }
  ],
  "between_participant_tensions": [
    {
      "what_conflicts": "string",
      "what_it_suggests": "string",
      "pattern": "string (e.g., pursuit_withdrawal, hidden_competition, asymmetric_investment)"
    }
  ],
  "trajectory_tensions": [
    {
      "what_changed": "string",
      "inflection_at": "message_id or approximate",
      "what_it_suggests": "string"
    }
  ],
  "intent_behavior_mismatches": [
    {
      "participant": "a|b",
      "stated_intent": "string",
      "actual_behavior": "string",
      "what_it_suggests": "string"
    }
  ],
  "who_controls": {
    "primary_controller": "a|b|balanced",
    "control_mechanism": "string (verbosity|direction|register|mixed)",
    "matches_investment": true/false,
    "note": "string"
  },
  "segment_summary": "1-3 sentences summarizing what's REALLY happening in this segment"
}
```


## What These Prompts Replace

These two prompts replace the concept of "signal gaps as arithmetic computation." Instead of computing `|investment - involvement|` and looking up what the gap means, the LLM reads all dimension outputs together and identifies whatever tensions exist, including ones we never predefined.

The predefined gaps we documented earlier (investment-involvement, density-relevance, intent-behavior, etc.) become **known patterns** that the LLM might identify. But the LLM is free to find novel tensions too. The prompts list known patterns as examples, not as the complete set.


## When These Run

| Prompt | When | Cost | Frequency |
|---|---|---|---|
| Per-message | After all dimension LLM calls for a message | One LLM call | Every message (or selective) |
| Per-segment | After a topic segment completes | One LLM call | Every segment |


## Relationship to APT

These prompts produce the raw material for APT Inference. The tensions and patterns identified here (pursuit/withdrawal, hidden competition, asymmetric investment, intent-behavior mismatch) are what APT interprets as charm, hope, fear dynamics.

APT Inference is a FURTHER interpretation on top of these tension readings. It asks: "given these tensions and control patterns, what attachment dynamics are at play?" That's a separate query, but it consumes the output of these prompts.

```
Interpretation Layer pipeline:

  PRAGMA Signal Layer outputs (per message)
       │
       ├── Per-message tension check (reads raw signals)
       │   "Do these readings conflict?"
       │
       ▼
  Dynamics Profile (when segment completes, reads aggregated signals)
  "What is happening in this segment?" [DESCRIPTION]
       │
       ▼
  Per-segment tension check (reads Dynamics Profile text)
  "What's really happening between these participants?" [INTERPRETATION]
       │
       ▼
  APT Inference (on demand, reads Dynamics Profile + tensions)
  "What attachment dynamics explain these patterns?"
       │
       ▼
  APT Profiling (cross-conversation)
  "What are this person's stable attachment patterns?"
```