# Energy — Detailed Measurement Logic

Implementation specification for measuring Expressed Involvement and computing Energy dynamics. A developer should be able to build this from this document alone.


## System Overview

```
Input: Raw message + conversation context + topic segment

Step 1: LLM extraction of 5 micro-signals (every message)
Step 2: Per-message involvement score
Step 3: Per-segment aggregation (trajectory)
Step 4: Per-segment dyadic comparison (asymmetry)
Step 5: Output to consumers
```


## Step 1: LLM Extraction of 5 Micro-Signals

**Runs on:** Every message.
**Cost:** One LLM call per message.

### Prompt Structure

```
You are analyzing a conversation message for expressed involvement — 
how present and activated the speaker is in what they're saying.

For the TARGET MESSAGE below, evaluate five micro-signals. For each,
provide a level and the evidence (exact quote) that supports it.

IMPORTANT RULES:
- Measure EXPRESSED involvement, not what you think they genuinely feel
- If sarcastic: detect sarcasm, invert evaluative force direction, flag
- If quoting someone else: attribute evaluative force to the quoted 
  person, not the speaker
- Ignore formulaic expressions (greetings, closings, pleasantries) — 
  these carry near-zero involvement regardless of literal content
- If emoji-only or emoji-heavy: interpret emoji as emotional expression
  and map to micro-signals
- If passive-aggressive: flag evaluative force as "masked_negative" 
  with the surface reading preserved

CONTEXT MESSAGES (for reference):
{context_messages}

TARGET MESSAGE:
Speaker: {sender}
Message: {content}

Evaluate these five micro-signals:

1. SELF-REFERENCE INTENSITY (SRI)
   How much the speaker's identity/experience/position is at stake.
   Levels: absent | present | invested | exposed

2. EVALUATIVE FORCE (EF)
   How strongly they judge/evaluate what they're discussing.
   Levels: absent | mild | moderate | strong
   Direction: positive | negative | mixed | masked_negative | neutral

3. TEMPORAL INVOLVEMENT (TI)
   Whether this subject occupies them beyond the current message.
   Levels: absent | present_only | extended | consuming

4. REACTIVE DISRUPTION (RD)
   Whether the conversation is changing their state right now.
   Levels: absent | mild | moderate | strong

5. URGENCY SIGNAL (US)
   Whether there's time pressure or imperative force.
   Levels: absent | mild | moderate | strong

Return JSON:
{
  "self_reference_intensity": {
    "level": "...",
    "evidence": "..." or null
  },
  "evaluative_force": {
    "level": "...",
    "direction": "...",
    "evidence": "..." or null,
    "surface": "..." (only if different from direction, e.g. sarcasm),
    "flag": "..." or null (e.g. "sarcastic", "passive_aggressive", 
            "quoting_other", "formulaic")
  },
  "temporal_involvement": {
    "level": "...",
    "evidence": "..." or null
  },
  "reactive_disruption": {
    "level": "...",
    "evidence": "..." or null
  },
  "urgency_signal": {
    "level": "...",
    "evidence": "..." or null
  }
}
```

### Output

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "expressed_involvement": {
    "self_reference_intensity": {
      "level": "invested",
      "evidence": "I'm convinced this is the way"
    },
    "evaluative_force": {
      "level": "strong",
      "direction": "positive",
      "evidence": "this is incredible",
      "surface": null,
      "flag": null
    },
    "temporal_involvement": {
      "level": "extended",
      "evidence": "I've been thinking about this"
    },
    "reactive_disruption": {
      "level": "absent",
      "evidence": null
    },
    "urgency_signal": {
      "level": "mild",
      "evidence": "we should look at this"
    }
  }
}
```


## Step 2: Per-Message Involvement Score

**Computes:** A single involvement score from the 5 micro-signals.
**Runs:** Immediately after Step 3.

### Level-to-Number Mapping

```python
LEVEL_SCORES = {
    # SRI
    "absent": 0.0, "present": 0.3, "invested": 0.7, "exposed": 1.0,
    # EF
    "absent": 0.0, "mild": 0.3, "moderate": 0.6, "strong": 1.0,
    # TI
    "absent": 0.0, "present_only": 0.2, "extended": 0.6, "consuming": 1.0,
    # RD
    "absent": 0.0, "mild": 0.3, "moderate": 0.7, "strong": 1.0,
    # US
    "absent": 0.0, "mild": 0.2, "moderate": 0.6, "strong": 1.0,
}
```

### Combination Logic

```python
def compute_involvement_score(signals):
    sri = LEVEL_SCORES[signals.self_reference_intensity.level]
    ef  = LEVEL_SCORES[signals.evaluative_force.level]
    ti  = LEVEL_SCORES[signals.temporal_involvement.level]
    rd  = LEVEL_SCORES[signals.reactive_disruption.level]
    us  = LEVEL_SCORES[signals.urgency_signal.level]

    # Weighted combination — EF and SRI are strongest indicators
    weighted = (
        sri * 0.25 +
        ef  * 0.30 +
        ti  * 0.20 +
        rd  * 0.15 +
        us  * 0.10
    )

    # Dominance rule: any single signal at "strong" level
    # pulls the overall score up (one strong signal = high involvement)
    max_signal = max(sri, ef, ti, rd, us)
    if max_signal >= 0.9:
        weighted = max(weighted, 0.7)

    return round(weighted, 2)
```

### Involvement Labels

```python
def involvement_label(score):
    if score <= 0.05: return "zero"
    if score <= 0.20: return "low"
    if score <= 0.50: return "moderate"
    if score <= 0.75: return "high"
    return "very_high"
```

### Output

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "involvement_score": 0.62,
  "involvement_label": "high",
  "evaluative_direction": "positive",
  "flags": []
}
```


## Step 3: Per-Segment Aggregation (Trajectory)

**Computes:** Involvement trajectory over a topic segment, per participant.
**Input:** Sequence of per-message involvement scores within a topic segment (from Topic Flow).
**Runs:** After all messages in a segment have Step 4 scores.

### Input

```python
segment = {
    "topic_id": "t_002",
    "messages": [
        {"msg_id": 3, "sender": "a", "score": 0.72, "direction": "positive"},
        {"msg_id": 4, "sender": "b", "score": 0.45, "direction": "positive"},
        {"msg_id": 5, "sender": "a", "score": 0.55, "direction": "positive"},
        {"msg_id": 6, "sender": "b", "score": 0.30, "direction": "neutral"},
        {"msg_id": 7, "sender": "a", "score": 0.25, "direction": "neutral"},
    ]
}
```

### Computation — Per Participant

```python
def compute_trajectory(scores):
    """Given ordered list of scores, determine trajectory."""
    if len(scores) < 2:
        return "insufficient_data"

    first_half = mean(scores[:len(scores)//2])
    second_half = mean(scores[len(scores)//2:])
    diff = second_half - first_half

    # Check for pulsing (alternating high/low)
    if is_pulsing(scores):
        return "pulsing"

    if diff > 0.15:
        return "escalating"
    elif diff < -0.15:
        return "de_escalating"
    else:
        avg = mean(scores)
        if avg > 0.5:
            return "stable_high"
        elif avg < 0.2:
            return "stable_low"
        else:
            return "stable_moderate"

def is_pulsing(scores, threshold=0.25):
    """Detect alternating pattern."""
    direction_changes = 0
    for i in range(1, len(scores)):
        if abs(scores[i] - scores[i-1]) > threshold:
            direction_changes += 1
    return direction_changes >= len(scores) * 0.6
```

### Output — Level 2

```json
{
  "topic_id": "t_002",
  "participant": "a",
  "trajectory": "de_escalating",
  "avg_involvement": 0.51,
  "start_involvement": 0.72,
  "end_involvement": 0.25,
  "evaluative_direction_trend": "positive_to_neutral",
  "message_count": 3
}
```


## Step 4: Per-Segment Dyadic Comparison (Asymmetry)

**Computes:** Involvement asymmetry between participants within a topic segment.
**Input:** Level 2 outputs for both participants on the same topic segment.
**Runs:** After Step 5 for all participants.

### Computation

```python
def compute_asymmetry(participant_a_l2, participant_b_l2):
    avg_diff = participant_a_l2.avg_involvement - participant_b_l2.avg_involvement

    # Trajectory divergence
    trajectories = (participant_a_l2.trajectory, participant_b_l2.trajectory)
    if trajectories == ("escalating", "de_escalating") or \
       trajectories == ("de_escalating", "escalating"):
        divergence = "diverging"
    elif participant_a_l2.trajectory == participant_b_l2.trajectory:
        divergence = "aligned"
    else:
        divergence = "mixed"

    return {
        "more_involved": "a" if avg_diff > 0.1 else "b" if avg_diff < -0.1 else "balanced",
        "asymmetry_magnitude": abs(avg_diff),
        "trajectory_divergence": divergence,
    }
```

### Output — Level 3

```json
{
  "topic_id": "t_002",
  "asymmetry": {
    "more_involved": "a",
    "asymmetry_magnitude": 0.22,
    "trajectory_divergence": "aligned",
    "participant_a": {"trajectory": "de_escalating", "avg": 0.51},
    "participant_b": {"trajectory": "de_escalating", "avg": 0.29}
  }
}
```


## Step 5: Output to Consumers

### To Emotional Trajectory (Signal Layer)

```json
{
  "topic_id": "t_002",
  "participant": "a",
  "involvement_trajectory": "de_escalating",
  "evaluative_direction_trend": "positive_to_neutral"
}
```

### To Control Distribution (Signal Layer)

For emotional register control — compare trajectory shapes:

```json
{
  "topic_id": "t_002",
  "emotional_shifts": [
    {"msg_id": 5, "participant": "a", "direction": "decrease"},
    {"msg_id": 6, "participant": "b", "direction": "decrease", "lag": 1}
  ],
  "register_leader": "a",
  "register_follower": "b"
}
```

### To Dynamics Profile

```json
{
  "dimension": "emotional_dynamics",
  "segment": "t_002",
  "value": "de_escalating",
  "detail": {
    "involvement_trend": "de_escalating",
    "evaluative_trend": "positive_to_neutral",
    "label": "Settling — initial enthusiasm cooling to neutral"
  }
}
```

### To APT Inference (via Interpretation Layer)

```json
{
  "topic_id": "t_002",
  "involvement_asymmetry": {
    "a": 0.51,
    "b": 0.29,
    "more_involved": "a",
    "pattern": "a consistently more involved on this topic"
  }
}
```

### To Signal Gaps

```json
{
  "signal_gaps": [
    {
      "gap": "investment_vs_involvement",
      "participant": "b",
      "investment": 0.6,
      "involvement": 0.29,
      "magnitude": 0.31,
      "interpretation_hint": "high effort, low activation — obligation?"
    }
  ]
}
```


## Data Flow Summary

```
Message arrives
     │
     ▼
Step 1: LLM extraction (5 micro-signals) [every message]
     │
     ▼
Step 2: Compute involvement score
     │
     ▼                          Per-message score
     │
     When topic segment completes:
     │
     ▼
Step 3: Per-segment trajectory (per participant)
     │
     ▼
Step 4: Dyadic asymmetry comparison
     │
     ▼
Step 5: Output to consumers
     ├── Expressed Involvement Trajectory → Dynamics Profile
     ├── Control Distribution → emotional register
     ├── APT Inference → charm/hope/fear signals
     ├── Behavioral Profiling → cross-conversation patterns
     └── Signal Gaps → diagnostic combinations
```


## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `context_window` | 5 | Number of preceding messages to include in LLM prompt |
| `trajectory_min_messages` | 2 | Minimum messages per participant per segment for trajectory |
| `trajectory_threshold` | 0.15 | Score difference between halves to call escalating/de-escalating |
| `pulsing_threshold` | 0.25 | Score change between consecutive messages to count as pulse |
| `asymmetry_threshold` | 0.1 | Average score difference to declare one participant more involved |
| `ef_weight` | 0.30 | Weight of evaluative force in combined score |
| `sri_weight` | 0.25 | Weight of self-reference intensity |
| `ti_weight` | 0.20 | Weight of temporal involvement |
| `rd_weight` | 0.15 | Weight of reactive disruption |
| `us_weight` | 0.10 | Weight of urgency signal |