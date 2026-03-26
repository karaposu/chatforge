# Conversational Intent — Detailed Measurement Logic

Implementation specification for measuring Conversational Intent. A developer should be able to build this from this document alone.

Intent is unique: it piggybacks on the Expressed Involvement LLM call (near-zero marginal cost) and then uses mechanical computations for all sub-properties.


## System Overview

```
Inputs:
  • EI LLM call (already exists — intent classification added to same prompt)
  • EI micro-signals (for hidden intent contradiction detection)
  • Topic Flow (segment boundaries for arc computation)

Step 1: Intent classification (piggybacked on EI LLM call)
Step 2: Hidden intent detection (contradiction matrix lookup)
Step 3: Intent shift detection (transition significance)
Step 4: Per-segment aggregation (dominant intent + arc)
Step 5: Intent mismatch (dyadic comparison)
Step 6: Intent avoidance detection
Step 7: Output to consumers
```


## Step 1: Intent Classification

**Runs on:** Every message (piggybacked on EI call)
**Cost:** Near-zero marginal (added to existing EI LLM call)

### Extended EI Prompt

The Expressed Involvement prompt gains one additional section:

```
[... existing 5 micro-signal instructions ...]

6. INTENT CLASSIFICATION
   What is the speaker trying to accomplish with this message?
   
   Classify the conversational GOAL — what they want to achieve,
   not how they're doing it or how honestly.
   
   Primary intent (pick one):
   inform | discover | convince | connect | request | process |
   perform | control | support | avoid | test | co_create | unclear
   
   Secondary intent (pick one or null — only if a clear second
   goal is present, not just a nuance of the primary):
   [same vocabulary]
   
   Confidence: 0.0-1.0
   Higher if the intent is unambiguous from this single message.
   Lower if multiple intents are equally plausible.
   
   Explanation: 1-2 sentences. Why this classification?
   Include any nuance: subtypes, methods, layering.
   Examples: "Informing with a mentoring dynamic"
            "Discovering but questions narrow consistently — may be testing"
            "Surface connect, but urgency suggests a request is coming"
```

### Output

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "intent": {
    "primary": "convince",
    "secondary": "inform",
    "confidence": 0.7,
    "explanation": "Presents comparative data to reposition project status. Surface looks informational but evaluative force and self-reference suggest advocacy."
  }
}
```

### Classification Guidelines for Edge Cases

| Situation | Classification | Confidence |
|---|---|---|
| Formulaic greeting ("Hope you're well") | unclear | 0.1 |
| Single emoji response | unclear | 0.2 |
| "ok" / "sure" / "noted" | unclear or avoid (context-dependent) | 0.3 |
| Question that could be genuine or probing | discover or test | 0.3-0.5 |
| Layered message (comfort then advice) | primary: support, secondary: inform | 0.7 |
| Sarcastic message | classify the UNDERLYING intent, not surface | 0.5-0.7 |


## Step 2: Hidden Intent Detection

**Runs on:** Every message with both intent classification and EI micro-signals
**Cost:** Zero (rule-based lookup)

### Contradiction Matrix

```python
CONTRADICTION_RULES = [
    {
        "classified_as": "inform",
        "contradicting_signals": {
            "sri": ["invested", "exposed"],
            "ef_level": ["strong"],
        },
        "hidden_intent": "convince",
        "description": "Classified as neutral informing but high personal stake and strong evaluation suggest advocacy",
        "confidence_modifier": 0.6,
    },
    {
        "classified_as": "inform",
        "contradicting_signals": {
            "us": ["moderate", "strong"],
            "sri": ["invested", "exposed"],
        },
        "hidden_intent": "control",
        "description": "Classified as informing but urgency and personal stake suggest directing",
        "confidence_modifier": 0.5,
    },
    {
        "classified_as": "discover",
        "contradicting_signals": {
            "rd": ["absent"],
            # + requires pattern check: consistent direction
        },
        "hidden_intent": "control",
        "description": "Classified as discovering but zero surprise and consistent direction suggest guiding toward predetermined outcome",
        "confidence_modifier": 0.5,
        "requires_pattern": "consistent_direction",
    },
    {
        "classified_as": "discover",
        "contradicting_signals": {
            "sri": ["invested", "exposed"],
            "ef_level": ["strong"],
            "ef_direction": ["positive"],
        },
        "hidden_intent": "connect",
        "description": "Classified as discovering but strong positive evaluation with high self-reference suggests relationship-building, not information-seeking",
        "confidence_modifier": 0.5,
    },
    {
        "classified_as": "connect",
        "contradicting_signals": {
            "sri": ["absent"],
            "ti": ["absent"],
        },
        "hidden_intent": "request",
        "description": "Classified as connecting but no personal investment and no temporal involvement — may be instrumentalizing the connection",
        "confidence_modifier": 0.4,
        "requires_pattern": "urgency_emerging_later",
    },
    {
        "classified_as": "support",
        "contradicting_signals": {
            "involvement_score_below": 0.2,
        },
        "hidden_intent": "perform",
        "description": "Classified as supporting but very low involvement — performative support, not genuine care",
        "confidence_modifier": 0.5,
    },
    {
        "classified_as": "support",
        "contradicting_signals": {
            "sri": ["invested", "exposed"],
            # + requires pattern check: topic control
        },
        "hidden_intent": "control",
        "description": "Classified as supporting but high self-reference with topic control suggest directing wrapped in care",
        "confidence_modifier": 0.5,
        "requires_pattern": "topic_control_present",
    },
    {
        "classified_as": "process",
        "contradicting_signals": {
            "sri": ["absent"],
        },
        "hidden_intent": "test",
        "description": "Classified as processing but no self-reference — may be probing disguised as thinking aloud",
        "confidence_modifier": 0.4,
    },
    {
        "classified_as": "co_create",
        "contradicting_signals": {
            "rd": ["absent"],
        },
        "hidden_intent": "control",
        "description": "Classified as co-creating but one participant shows zero reactive disruption — may be guiding to predetermined outcome while appearing collaborative",
        "confidence_modifier": 0.5,
        "requires_pattern": "consistent_direction",
    },
    {
        "classified_as": "avoid",
        "contradicting_signals": {
            "involvement_score_above": 0.5,
        },
        "hidden_intent": "control",
        "description": "Classified as avoiding but high involvement — not disengaged, actively withholding information as a power move",
        "confidence_modifier": 0.5,
    },
]
```

### Implementation

```python
def detect_hidden_intent(classified_intent, ei_signals, involvement_score, conversation_patterns=None):
    """Check contradiction matrix for hidden intent."""
    
    applicable_rules = [
        r for r in CONTRADICTION_RULES
        if r["classified_as"] == classified_intent
    ]
    
    for rule in applicable_rules:
        if matches_signals(rule["contradicting_signals"], ei_signals, involvement_score):
            # Check pattern requirements if any
            if "requires_pattern" in rule:
                if not check_pattern(rule["requires_pattern"], conversation_patterns):
                    continue
            
            return {
                "hidden_intent_likely": rule["hidden_intent"],
                "contradiction": rule["description"],
                "gap_magnitude": compute_gap_magnitude(
                    classified_intent, ei_signals, rule
                ),
                "confidence": rule["confidence_modifier"],
            }
    
    return {"hidden_intent_likely": None}

def matches_signals(required_signals, ei_signals, involvement_score):
    """Check if EI signals match contradiction pattern."""
    for signal_name, required_levels in required_signals.items():
        if signal_name == "involvement_score_below":
            if involvement_score >= required_levels:
                return False
        elif signal_name == "involvement_score_above":
            if involvement_score <= required_levels:
                return False
        else:
            actual_level = getattr(ei_signals, signal_name, {}).get("level")
            if actual_level not in required_levels:
                return False
    return True
```

### Output

```json
{
  "message_id": 7,
  "hidden_intent": {
    "hidden_intent_likely": "convince",
    "contradiction": "Classified as inform but high self-reference and strong evaluative force suggest advocacy",
    "gap_magnitude": 0.6,
    "confidence": 0.6
  }
}
```

Or `{"hidden_intent_likely": null}` when no contradiction detected.


## Step 3: Intent Shift Detection

**Runs on:** Every message where previous message from same participant has an intent classification
**Cost:** Zero (comparison + lookup)

### Transition Significance Matrix

```python
TRANSITION_SIGNIFICANCE = {
    # Minor (information-oriented shifts)
    ("inform", "discover"): 0.2,
    ("discover", "inform"): 0.2,
    ("support", "connect"): 0.2,
    ("connect", "support"): 0.2,
    
    # Moderate (purpose shifts)
    ("inform", "convince"): 0.5,
    ("discover", "convince"): 0.5,
    ("convince", "inform"): 0.3,
    ("convince", "request"): 0.5,
    ("connect", "request"): 0.5,
    ("support", "convince"): 0.5,
    ("inform", "request"): 0.5,
    ("discover", "request"): 0.5,
    
    # Major (trajectory changes)
    ("inform", "control"): 0.8,
    ("discover", "control"): 0.8,
    ("connect", "avoid"): 0.8,
    ("support", "control"): 0.9,
    ("connect", "control"): 0.9,
    ("inform", "avoid"): 0.9,
    ("co_create", "avoid"): 0.9,
    ("convince", "control"): 0.7,
    ("discover", "avoid"): 0.7,
    ("process", "control"): 0.7,
}

DEFAULT_SIGNIFICANCE = 0.5  # for unlisted transitions
```

### Implementation

```python
def detect_intent_shift(current_intent, previous_intent):
    """Detect and weight intent shift."""
    if current_intent == previous_intent:
        return None
    
    pair = (previous_intent, current_intent)
    significance = TRANSITION_SIGNIFICANCE.get(pair, DEFAULT_SIGNIFICANCE)
    
    # Determine direction
    if is_escalation(previous_intent, current_intent):
        direction = "escalation"
    elif is_de_escalation(previous_intent, current_intent):
        direction = "de_escalation"
    else:
        direction = "lateral"
    
    return {
        "from": previous_intent,
        "to": current_intent,
        "significance": significance,
        "direction": direction,
    }

INTENSITY_ORDER = {
    "inform": 1, "discover": 2, "convince": 3, "control": 4,
    "support": 1, "connect": 2, "request": 3,
}

def is_escalation(from_intent, to_intent):
    from_level = INTENSITY_ORDER.get(from_intent, 0)
    to_level = INTENSITY_ORDER.get(to_intent, 0)
    return to_level > from_level and from_level > 0

def is_de_escalation(from_intent, to_intent):
    from_level = INTENSITY_ORDER.get(from_intent, 0)
    to_level = INTENSITY_ORDER.get(to_intent, 0)
    return to_level < from_level and to_level > 0
```


## Step 4: Per-Segment Aggregation

**Runs on:** When a topic segment completes (from Topic Flow)
**Cost:** Zero (computed from per-message classifications)

### Dominant Intent

```python
def compute_dominant_intent(intent_sequence):
    """Most frequent intent in the segment, weighted by confidence."""
    weighted_counts = {}
    for intent_entry in intent_sequence:
        primary = intent_entry["primary"]
        conf = intent_entry["confidence"]
        weighted_counts[primary] = weighted_counts.get(primary, 0) + conf
    
    if not weighted_counts:
        return "unclear"
    
    return max(weighted_counts, key=weighted_counts.get)
```

### Intent Arc Classification

```python
def classify_intent_arc(intent_sequence):
    """Classify sequence into named arc pattern."""
    if len(intent_sequence) < 2:
        return {"arc": "insufficient_data"}
    
    # Extract primary intents, collapse consecutive duplicates
    primaries = [e["primary"] for e in intent_sequence if e["primary"] != "unclear"]
    if not primaries:
        return {"arc": "unclear"}
    
    unique = collapse_consecutive(primaries)
    
    # Single intent throughout
    if len(unique) == 1:
        return {"arc": "stable", "intent": unique[0]}
    
    # Ends in avoid = collapse
    if unique[-1] == "avoid":
        return {
            "arc": "collapse",
            "from": unique[0],
            "at": find_first_occurrence(primaries, "avoid"),
        }
    
    # Ends in co_create = emergence
    if unique[-1] == "co_create" and unique[0] != "co_create":
        return {"arc": "emergence", "from": unique[0]}
    
    # A → B → A pattern = recoil
    if len(unique) == 3 and unique[0] == unique[2]:
        return {
            "arc": "recoil",
            "base": unique[0],
            "attempted": unique[1],
        }
    
    # Check for oscillation
    if is_oscillating(primaries):
        return {
            "arc": "oscillation",
            "between": list(set(unique)),
        }
    
    # Two unique = simple shift, check escalation
    if len(unique) == 2:
        if is_escalation(unique[0], unique[1]):
            return {"arc": "escalation", "from": unique[0], "to": unique[1]}
        if is_de_escalation(unique[0], unique[1]):
            return {"arc": "de_escalation", "from": unique[0], "to": unique[1]}
        return {"arc": "shift", "from": unique[0], "to": unique[1]}
    
    # Check for funnel pattern (progressive narrowing)
    if is_funnel(unique):
        return {"arc": "funnel", "stages": unique}
    
    # Check for full escalation (3+ steps up)
    if all(is_escalation(unique[i], unique[i+1]) for i in range(len(unique)-1)):
        return {"arc": "escalation", "from": unique[0], "to": unique[-1]}
    
    # Check for full de-escalation
    if all(is_de_escalation(unique[i], unique[i+1]) for i in range(len(unique)-1)):
        return {"arc": "de_escalation", "from": unique[0], "to": unique[-1]}
    
    return {"arc": "complex", "sequence": unique}

def collapse_consecutive(lst):
    """Remove consecutive duplicates: [a,a,b,b,b,a] → [a,b,a]"""
    result = [lst[0]]
    for item in lst[1:]:
        if item != result[-1]:
            result.append(item)
    return result

def is_funnel(sequence):
    """Check for discover → evaluate/convince → request/commit pattern."""
    return (
        sequence[0] in ("discover", "test") and
        sequence[-1] in ("request", "convince", "control") and
        len(sequence) >= 3
    )

def is_oscillating(sequence, min_switches=3):
    """Check for alternating pattern."""
    switches = sum(1 for i in range(1, len(sequence)) if sequence[i] != sequence[i-1])
    return switches >= min_switches
```

### Segment Output

```json
{
  "segment_id": "t_002",
  "participant": "a",
  "intent_aggregate": {
    "dominant_intent": "convince",
    "intent_arc": {"arc": "escalation", "from": "inform", "to": "convince"},
    "shift_count": 1,
    "total_shift_significance": 0.5,
    "confidence_avg": 0.72,
    "hidden_intent_detected": true,
    "avoidance_detected": false
  }
}
```


## Step 5: Intent Mismatch

**Runs on:** Per-segment, comparing both participants
**Cost:** Zero (comparison)

```python
MISMATCH_TYPES = {
    # Complementary pairs (low friction)
    frozenset({"discover", "inform"}): ("complementary", 0.1),
    frozenset({"request", "support"}): ("complementary", 0.1),
    frozenset({"process", "support"}): ("complementary", 0.2),
    
    # Friction pairs
    frozenset({"connect", "request"}): ("friction", 0.7),
    frozenset({"process", "inform"}): ("level_mismatch", 0.6),
    frozenset({"discover", "convince"}): ("competing", 0.5),
    frozenset({"connect", "avoid"}): ("friction", 0.8),
    
    # Power contests
    frozenset({"control", "control"}): ("power_contest", 0.8),
    frozenset({"convince", "convince"}): ("competing", 0.6),
}

def compute_intent_mismatch(a_dominant, b_dominant):
    """Compare dominant intents between participants."""
    if a_dominant == b_dominant:
        return {"mismatch_type": "aligned", "friction_level": 0.0}
    
    pair = frozenset({a_dominant, b_dominant})
    mismatch_type, friction = MISMATCH_TYPES.get(pair, ("unclassified", 0.4))
    
    return {
        "a_intent": a_dominant,
        "b_intent": b_dominant,
        "mismatch_type": mismatch_type,
        "friction_level": friction,
    }
```

### Dyadic Arc Comparison

```python
def compute_dyadic_arc(a_arc, b_arc):
    """Compare arc patterns between participants."""
    if a_arc["arc"] == b_arc["arc"]:
        return "aligned"
    
    # Both converge to co_create
    if a_arc.get("arc") == "emergence" and b_arc.get("arc") == "emergence":
        return "convergent_emergence"
    
    # One escalates, other de-escalates
    if (a_arc["arc"] == "escalation" and b_arc["arc"] == "de_escalation") or \
       (a_arc["arc"] == "de_escalation" and b_arc["arc"] == "escalation"):
        return "opposing"
    
    # One has a directed arc, other is stable
    if a_arc["arc"] in ("escalation", "funnel", "collapse") and b_arc["arc"] == "stable":
        return "asymmetric"
    if b_arc["arc"] in ("escalation", "funnel", "collapse") and a_arc["arc"] == "stable":
        return "asymmetric"
    
    return "diverging"
```


## Step 6: Intent Avoidance Detection

**Runs on:** Per-segment
**Cost:** Zero (pattern check)

```python
def detect_intent_avoidance(intent_sequence, involvement_scores, control_signals):
    """Detect pattern of intent avoidance."""
    avoid_unclear_count = sum(
        1 for e in intent_sequence
        if e["primary"] in ("avoid", "unclear")
    )
    
    total = len(intent_sequence)
    if total == 0:
        return {"is_avoiding": False}
    
    avoid_ratio = avoid_unclear_count / total
    avg_involvement = mean(involvement_scores) if involvement_scores else 0
    
    # No direction attempts
    direction_attempts = sum(
        1 for c in control_signals
        if c.get("topic_direction", {}).get("redirect_attempts", 0) > 0
    )
    
    is_avoiding = (
        avoid_ratio > 0.5 and
        avg_involvement < 0.3 and
        direction_attempts == 0
    )
    
    return {
        "is_avoiding": is_avoiding,
        "avoid_ratio": avoid_ratio,
        "avg_involvement_during": avg_involvement,
        "duration_messages": avoid_unclear_count,
    }
```


## Step 7: Output to Consumers

### To Dynamics Profile

```json
{
  "dimension": "conversational_intent",
  "segment": "t_002",
  "value": {
    "a_dominant": "convince",
    "b_dominant": "discover",
    "a_arc": "escalation",
    "b_arc": "stable",
    "mismatch": "competing",
    "label": "A is pushing (escalating from inform to convince). B is still exploring. Competing intents — A's advocacy may undermine B's exploration."
  }
}
```

### To APT Inference

```json
{
  "intent_patterns": {
    "a_shifts_to_convince_when_challenged": true,
    "b_avoids_on_conflict_topics": true,
    "hidden_intent_detected": {
      "participant": "a",
      "surface": "inform",
      "hidden": "convince",
      "frequency": "3 of 7 messages"
    },
    "mismatch_pattern": "A pursues (funnel), B withdraws (collapse) — pursuit/withdrawal dynamic",
    "apt_hints": {
      "a_control_seeking_under_pressure": true,
      "b_fear_driven_avoidance": true
    }
  }
}
```

### To Signal Gaps

```json
{
  "signal_gaps": [
    {
      "gap": "classified_intent_vs_ei_signals",
      "participant": "a",
      "classified": "inform",
      "ei_suggests": "convince",
      "magnitude": 0.6,
      "hint": "Surface informing, actual advocacy — hidden intent"
    }
  ]
}
```

### To Behavioral Profiling

```json
{
  "participant": "a",
  "intent_profile": {
    "primary_intents": {"convince": 0.35, "inform": 0.25, "discover": 0.20, "control": 0.15, "other": 0.05},
    "typical_arc": "escalation (starts informing, shifts to convincing when challenged)",
    "hidden_intent_frequency": 0.3,
    "shift_triggers": ["challenged on competence", "timeline pressure"],
    "avoidance_topics": ["personal questions", "budget discussions"],
    "consistency": "stable across 4 conversations"
  }
}
```


## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `default_transition_significance` | 0.5 | Weight for unlisted intent transitions |
| `avoidance_ratio_threshold` | 0.5 | Proportion of avoid/unclear to trigger avoidance detection |
| `avoidance_involvement_threshold` | 0.3 | Max involvement for avoidance to be detected |
| `oscillation_min_switches` | 3 | Minimum direction changes for oscillation arc |
| `low_confidence_threshold` | 0.3 | Below this, classification is treated as uncertain |
| `hidden_intent_min_gap` | 0.4 | Minimum gap magnitude to report hidden intent |


## Data Flow Summary

```
Message arrives
     │
     ▼
Step 1: EI LLM call (existing) + Intent classification (piggybacked)
     │   → 5 micro-signals + intent {primary, secondary, confidence, explanation}
     │
     ├── Step 2: Hidden intent detection (mechanical)
     │   → contradiction_matrix(classified_intent, ei_signals)
     │   → {hidden_intent_likely, gap_magnitude} or null
     │
     ├── Step 3: Intent shift detection (mechanical)
     │   → compare current vs previous classification
     │   → {from, to, significance, direction} or null
     │
     When segment completes:
     │
     ├── Step 4: Per-segment aggregation
     │   → dominant_intent, intent_arc, shift_summary
     │
     ├── Step 5: Intent mismatch (dyadic)
     │   → compare A's dominant vs B's dominant
     │   → {mismatch_type, friction_level}
     │   → dyadic_arc comparison
     │
     ├── Step 6: Intent avoidance detection
     │   → pattern check on avoid/unclear ratio + involvement
     │
     └── Step 7: Output to consumers
          ├── Dynamics Profile → intent dimension
          ├── APT Inference → mismatch + hidden intent + shift patterns
          ├── Signal Gaps → classified vs behavioral
          └── Behavioral Profiling → cross-conversation intent patterns
```

**Total additional LLM cost: ZERO.** Intent classification piggybacks on the existing EI call. All sub-properties are mechanical computations.