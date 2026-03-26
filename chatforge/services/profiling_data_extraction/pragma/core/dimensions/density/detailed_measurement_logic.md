# Information Density — Detailed Measurement Logic

Implementation specification for measuring Information Density. A developer should be able to build this from this document alone.

All three axes (specificity, novelty, relevance) are LLM assessed per message, per participant, in a single LLM call.


## System Overview

```
Inputs:
  • Topic Flow (segment boundaries, active topic, prior messages in segment)
  • Message Properties (word count)

Step 1: Specificity + Novelty + Relevance assessment (single LLM call per message)
Step 2: Compression computation (from LLM specificity score + word count)
Step 3: Combined density score
Step 4: Per-segment aggregation
Step 5: Dyadic comparison
Step 6: Output to consumers

One LLM call per message produces all three axes. Everything after that is mechanical aggregation.
```


## Step 1: Specificity + Novelty + Relevance Assessment (LLM)

**Runs on:** Every message
**Source:** Topic Flow (active topic, prior messages in segment) + preceding question (if any) + Message Properties
**Method:** Single LLM call per message that assesses all three axes together

### LLM Prompt Structure

```
You are assessing the information density of a message in a conversation.

ACTIVE TOPIC (from Topic Flow):
{topic_label}

PRIOR MESSAGES IN THIS TOPIC SEGMENT:
{prior_messages_in_segment}

PRECEDING MESSAGE / QUESTION (if any):
{preceding_message}

CURRENT MESSAGE:
Sender: {sender}
Text: {message_text}

Assess the following three axes:

1. SPECIFICITY: How concrete and precise is this message?
   Evaluate four sub-dimensions:
   - Entity: How specific are references to people, organizations,
     technologies, places?
     "someone" = 0.0, "my colleague" = 0.3, "Sarah" = 0.7,
     "Sarah from the platform team" = 1.0
   - Temporal: How precise are time references?
     "sometime" = 0.0, "soon" = 0.2, "this week" = 0.5,
     "Thursday 2pm" = 1.0
   - Quantitative: How much numeric precision?
     "a lot" = 0.0, "47%" = 0.7, "3.2s to 400ms" = 1.0
   - Action: How concrete are the described actions?
     "work on it" = 0.2, "improve the system" = 0.4,
     "refactor the auth module" = 0.8,
     "migrate Redis to cluster mode with 3 replicas" = 1.0
   Score each sub-dimension 0.0 to 1.0.

2. NOVELTY: How much genuinely NEW information does this message add
   relative to what has already been said in this topic segment?
   Consider:
   - Does it introduce facts, ideas, or perspectives not yet stated?
   - Or does it restate, paraphrase, or repeat existing content?
   - "The system is slow" followed by "Performance is poor" followed by
     "Load times are terrible" = three messages, zero novelty after the first.
   Score 0.0 to 1.0.
   Provide a one-sentence explanation.

3. RELEVANCE: How relevant is this message to the active topic
   and/or the preceding question?
   Consider:
   - Does it address what is currently being discussed?
   - Does it answer or engage with the preceding message?
   - Or does it introduce unrelated content?
   - Context matters: "Redis migration" is relevant when discussing
     system performance, irrelevant when discussing team morale.
   Score 0.0 to 1.0.
   Provide a one-sentence explanation.

Respond in JSON:
{
  "specificity": {
    "entity": <float 0.0-1.0>,
    "temporal": <float 0.0-1.0>,
    "quantitative": <float 0.0-1.0>,
    "action": <float 0.0-1.0>,
    "combined": <float 0.0-1.0>,
    "label": "<absent|low|moderate|high|very_high>"
  },
  "novelty": {
    "score": <float 0.0-1.0>,
    "label": "<zero|low|moderate|high|very_high>",
    "explanation": "<one sentence>"
  },
  "relevance": {
    "score": <float 0.0-1.0>,
    "label": "<off_topic|tangential|related|on_topic|precisely_on_topic>",
    "explanation": "<one sentence>"
  }
}
```

### Specificity Interpretation

| Score | Label | Meaning |
|---|---|---|
| 0.0 - 0.1 | absent | No concrete content at all ("Good.", "ok") |
| 0.1 - 0.3 | low | Vague references, no precision ("I've been working on some stuff") |
| 0.3 - 0.6 | moderate | Some concrete elements mixed with vague ones |
| 0.6 - 0.8 | high | Multiple concrete references, numbers, named entities |
| 0.8 - 1.0 | very_high | Highly precise across all sub-dimensions |

### Novelty Interpretation

| Score | Label | Meaning |
|---|---|---|
| 0.0 - 0.2 | zero/low | Essentially restating prior content |
| 0.2 - 0.4 | low | Minor variations on existing content |
| 0.4 - 0.6 | moderate | Related but adding new aspects |
| 0.6 - 0.8 | high | Substantially new content within the topic |
| 0.8 - 1.0 | very_high | Entirely new content (or first in segment) |

### Relevance Interpretation

| Score | Label | Meaning |
|---|---|---|
| 0.0 - 0.3 | off_topic | Content doesn't relate to active discussion |
| 0.3 - 0.5 | tangential | Adjacent topic |
| 0.5 - 0.7 | related | Same broad topic area |
| 0.7 - 0.9 | on_topic | Directly addresses the discussion |
| 0.9 - 1.0 | precisely_on_topic | Directly answers a question |

### Why All Three Are LLM

- **Specificity** requires semantic judgment. Action concreteness ("work on it" vs "refactor the auth module") cannot be scored by counting words. Entity gradients ("someone" vs "my colleague") require understanding reference quality. NER detects entities but cannot score HOW specific they are.
- **Novelty** requires semantic comparison. Embedding similarity fails on paraphrase: "The system is slow" → "Performance is poor" → "Load times are terrible" are different embeddings but zero novelty.
- **Relevance** requires contextual judgment. "Redis migration" is relevant or irrelevant depending on the active topic. Cosine similarity to a topic centroid is a crude proxy.

One LLM call, three axes, per message, per participant.

### Output

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "specificity": {
    "entity": 0.67,
    "temporal": 0.70,
    "quantitative": 0.50,
    "action": 0.80,
    "combined": 0.66,
    "label": "high"
  },
  "novelty": {
    "score": 0.72,
    "label": "high",
    "explanation": "Introduces Redis migration details not previously mentioned in this segment."
  },
  "relevance": {
    "score": 0.82,
    "label": "on_topic",
    "explanation": "Directly addresses the system performance discussion with specific infrastructure details."
  }
}
```


## Step 2: Compression Computation

**Runs on:** Every message (after LLM assessment)
**Source:** Specificity combined score (from Step 1 LLM output) + Message Properties (word count)

```python
def compute_compression(specificity_combined, word_count):
    """Information-to-word ratio."""
    if word_count == 0:
        return 0.0

    # Normalize: specificity is 0-1, word_count varies
    # Use log scale for word count to avoid penalizing reasonable length
    import math
    normalized_length = math.log(max(word_count, 1)) / math.log(100)  # log scale, 100 words = 1.0

    if normalized_length == 0:
        return specificity_combined

    compression = specificity_combined / normalized_length

    return round(min(compression, 2.0), 2)  # Cap at 2.0
```

### Compression Interpretation

| Score | Meaning | Example |
|---|---|---|
| 0.0 | No substance | "Good." |
| 0.0 - 0.5 | Low compression — verbose relative to content | Long message with few specifics |
| 0.5 - 1.0 | Moderate compression — balanced | Normal detailed message |
| 1.0 - 2.0 | High compression — efficient | "Auth broken. Redis down. Fix by 5pm." |

### Output

```json
{
  "message_id": 7,
  "compression": 1.15,
  "compression_label": "high"
}
```


## Step 3: Combined Density Score

```python
def compute_density(specificity, novelty, relevance, compression):
    """Combined Information Density score."""

    # Core density: specificity + novelty + relevance
    core_density = (
        specificity * 0.35 +
        novelty * 0.35 +
        relevance * 0.30
    )

    return {
        "core_density": round(core_density, 2),
        "specificity": specificity,
        "novelty": novelty,
        "relevance": relevance,
        "compression": compression,
        "label": density_label(core_density),
    }

def density_label(score):
    if score <= 0.10: return "zero"
    if score <= 0.30: return "low"
    if score <= 0.55: return "moderate"
    if score <= 0.75: return "high"
    return "very_high"
```

### Output — Per Message

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "density": {
    "core_density": 0.68,
    "label": "high",
    "specificity": 0.66,
    "novelty": 0.72,
    "relevance": 0.82,
    "compression": 1.15
  }
}
```


## Step 4: Per-Segment Aggregation

```python
def aggregate_segment_density(segment_messages, participant):
    """Aggregate density across a topic segment for one participant."""
    msgs = [m for m in segment_messages if m.sender == participant]

    if not msgs:
        return None

    densities = [m.density for m in msgs]

    return {
        "avg_density": mean([d.core_density for d in densities]),
        "avg_specificity": mean([d.specificity for d in densities]),
        "avg_novelty": mean([d.novelty for d in densities]),
        "avg_relevance": mean([d.relevance for d in densities]),
        "avg_compression": mean([d.compression for d in densities]),
        "trajectory": compute_trajectory(
            [d.core_density for d in densities]
        ),
        "message_count": len(msgs),
    }

def compute_trajectory(scores):
    if len(scores) < 2:
        return "insufficient_data"
    first_half = mean(scores[:len(scores)//2])
    second_half = mean(scores[len(scores)//2:])
    diff = second_half - first_half
    if diff > 0.15: return "increasing"
    if diff < -0.15: return "decreasing"
    return "stable"
```

### Output — Level 2

```json
{
  "segment_id": "t_002",
  "participant": "a",
  "density_aggregate": {
    "avg_density": 0.62,
    "avg_specificity": 0.58,
    "avg_novelty": 0.70,
    "avg_relevance": 0.78,
    "avg_compression": 0.95,
    "trajectory": "stable",
    "message_count": 4
  }
}
```


## Step 5: Dyadic Comparison

```python
def compute_density_asymmetry(participant_a_agg, participant_b_agg):
    """Compare density between participants within a segment."""

    a_density = participant_a_agg.avg_density if participant_a_agg else 0
    b_density = participant_b_agg.avg_density if participant_b_agg else 0

    diff = a_density - b_density

    return {
        "denser_participant": "a" if diff > 0.1 else "b" if diff < -0.1 else "balanced",
        "asymmetry_magnitude": abs(diff),
        "a_density": a_density,
        "b_density": b_density,
    }
```

### Output — Level 3

```json
{
  "segment_id": "t_002",
  "density_asymmetry": {
    "denser_participant": "a",
    "asymmetry_magnitude": 0.35,
    "a_density": 0.62,
    "b_density": 0.27
  }
}
```


## Step 6: Output to Consumers

### To Dynamics Profile

```json
{
  "dimension": "information_density",
  "segment": "t_002",
  "value": {
    "density_level": "high",
    "avg_density": 0.62,
    "trajectory": "stable",
    "asymmetry": "a provides most substance",
    "label": "A provides detailed, relevant content. B contributes minimally."
  }
}
```

### To Signal Gaps

```json
{
  "signal_gaps": [
    {
      "gap": "density_vs_relevance",
      "participant": "b",
      "density": 0.71,
      "relevance": 0.32,
      "magnitude": 0.39,
      "hint": "Dense but off-topic — deflection or impression management?"
    },
    {
      "gap": "specificity_vs_novelty",
      "participant": "a",
      "specificity": 0.65,
      "novelty": 0.15,
      "magnitude": 0.50,
      "hint": "Specific but repetitive — rehashing with detail"
    },
    {
      "gap": "investment_vs_density",
      "participant": "b",
      "investment": 0.70,
      "density": 0.20,
      "magnitude": 0.50,
      "hint": "High effort, low substance — waffling or struggling"
    }
  ]
}
```

### To Behavioral Profiling

```json
{
  "participant": "a",
  "density_profile": {
    "avg_density": 0.58,
    "avg_compression": 1.05,
    "topic_density_map": {
      "technical": 0.75,
      "personal": 0.25,
      "planning": 0.50
    },
    "pattern": "High density on technical topics, low on personal. High compression = expert communicator.",
    "consistency": "stable across 4 conversations"
  }
}
```

### To APT Inference

```json
{
  "density_patterns": {
    "a_density_increases_on": ["topics where B demonstrates expertise"],
    "b_density_increases_on": ["topics where B wants something from A"],
    "asymmetry_shift_after_control_moment": "A's density dropped after losing control in segment t_003",
    "hint": "B increases substance when pursuing benefits (hope signal). A's density correlates with control — drops when disempowered."
  }
}
```


## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `specificity_density_weight` | 0.35 | Weight of specificity in core density |
| `novelty_density_weight` | 0.35 | Weight of novelty in core density |
| `relevance_density_weight` | 0.30 | Weight of relevance in core density |
| `trajectory_threshold` | 0.15 | Score change to classify as increasing/decreasing |
| `asymmetry_threshold` | 0.10 | Density difference to declare asymmetry |
| `compression_cap` | 2.0 | Maximum compression score |


## Data Flow Summary

```
Message arrives
     │
     ├── Step 1: Specificity + Novelty + Relevance (single LLM call) [LLM]
     │    → specificity vector (entity, temporal, quantitative, action) + combined
     │    → novelty score + explanation
     │    → relevance score + explanation
     │
     ├── Step 2: Compression (from LLM specificity + word count) [mechanical]
     │    → specificity / word_count ratio
     │
     └── Step 3: Combined density score [mechanical]
              │
              ▼
     Step 4: Per-segment aggregation (per participant) [mechanical]
              │
              ▼
     Step 5: Dyadic comparison (density asymmetry) [mechanical]
              │
              ▼
     Step 6: Output to consumers
              ├── Dynamics Profile → Information Density dimension
              ├── Signal Gaps → density vs relevance, specificity vs novelty, etc.
              ├── Behavioral Profiling → density patterns per topic
              └── APT Inference → density asymmetry as engagement signal
```

**LLM cost: One call per message** (all three axes assessed together). Compression, combined density, aggregation, and dyadic comparison are mechanical computations on top of LLM output.