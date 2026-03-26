# Investment: Detailed Measurement Logic

Implementation specification. LLM-based semantic assessment per message.


## System Overview

```
Inputs:
  - Message text + conversation context
  - Topic Flow context (what topic is being discussed)

Step 1: LLM assessment (structural effort + content effort + overall)
Step 2: Per-segment aggregation
Step 3: Dyadic comparison
Step 4: Output to consumers
```

## Step 1: LLM Assessment

Investment is assessed per message via LLM call. The prompt (see `desc.md` for full prompt text) asks the LLM to evaluate:

1. **Structural effort**: is this a quick/minimal or substantial response?
2. **Content effort**: did they elaborate beyond what was needed?
3. **Overall investment**: combined assessment

Key instruction to the LLM: long does NOT mean high effort (copy-paste is long but zero-effort). Short does NOT mean low effort (a precise answer to a complex question is high-effort). The LLM assesses the semantic effort, not the mechanical proxies.

### Output per message

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "investment": {
    "structural_effort": {
      "level": "moderate",
      "evidence": "Responded within minutes with a multi-sentence message"
    },
    "content_effort": {
      "level": "high",
      "evidence": "Elaborated beyond the question with comparison data and a follow-up question"
    },
    "overall_investment": "high",
    "explanation": "Provided more detail than asked for, including unsolicited comparison and a question to continue the discussion"
  }
}
```

### Level mapping for computation

```python
INVESTMENT_LEVELS = {
    "zero": 0.0,
    "low": 0.25,
    "moderate": 0.5,
    "high": 0.75,
    "very_high": 1.0,
}

def investment_score(llm_output):
    return INVESTMENT_LEVELS.get(llm_output["overall_investment"], 0.5)
```


## Step 2: Per-Segment Aggregation

```python
def aggregate_segment_investment(segment_messages, participant):
    msgs = [m for m in segment_messages if m.sender == participant]
    if not msgs:
        return None

    scores = [investment_score(m.investment) for m in msgs]

    return {
        "avg_investment": round(mean(scores), 2),
        "trajectory": compute_trajectory(scores),
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


## Step 3: Dyadic Comparison

```python
def compute_investment_asymmetry(a_agg, b_agg):
    if not a_agg or not b_agg:
        return None

    diff = a_agg["avg_investment"] - b_agg["avg_investment"]

    return {
        "more_invested": "a" if diff > 0.1 else "b" if diff < -0.1 else "balanced",
        "asymmetry_magnitude": round(abs(diff), 2),
        "a_investment": a_agg["avg_investment"],
        "b_investment": b_agg["avg_investment"],
    }
```


## Step 4: Output to Consumers

### To Signal Gaps

```json
{
  "signal_gaps": [
    {
      "gap": "investment_vs_involvement",
      "participant": "a",
      "investment": 0.65,
      "involvement": 0.20,
      "magnitude": 0.45,
      "hint": "High effort, low activation. Obligation pattern."
    },
    {
      "gap": "investment_vs_density",
      "participant": "b",
      "investment": 0.55,
      "density": 0.15,
      "magnitude": 0.40,
      "hint": "High effort, low substance. Waffling or struggling."
    }
  ]
}
```

### To Control Distribution

```json
{
  "segment_id": "t_002",
  "investment_for_control": {
    "a_investment": 0.65,
    "b_investment": 0.25,
    "asymmetry": "a invests significantly more",
    "verbosity_context": "A's high investment feeds verbosity control assessment"
  }
}
```

### To Behavioral Profiling

```json
{
  "participant": "a",
  "investment_profile": {
    "avg_investment": 0.58,
    "investment_by_topic_type": {
      "technical": 0.72,
      "personal": 0.35,
      "planning": 0.55
    },
    "pattern": "High investor on technical topics. Low on personal. Content investment exceeds structural (thinks before responding).",
    "across_conversations": 4
  }
}
```


## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `trajectory_threshold` | 0.15 | Score change to classify as increasing/decreasing |
| `asymmetry_threshold` | 0.10 | Difference to declare asymmetry |
| `context_window` | 5 | Number of preceding messages included in LLM prompt |

**Investment uses its own LLM call per message.** The LLM assesses structural effort, content effort, and overall investment semantically.