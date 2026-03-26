# Dialogic Function: Detailed Measurement Logic

Implementation specification for multi-label Dialogic Function classification. A developer should be able to build this from this document alone.


## System Overview

```
Input: Message text + conversation context

Step 1: Classification (multi-label with weights)
Step 2: Per-segment aggregation (function distribution)
Step 3: Dyadic comparison (function asymmetry)
Step 4: Output to consumers
```


## Step 1: Classification

**Runs on:** Every message
**Cost:** Low (classifier) or part of PRAGMA LLM call (if nuanced)

### LLM Classification Prompt

For nuanced or blended cases, use the PRAGMA LLM call. This can be added as a section after Topic Flow and before EI, or run through a separate lightweight classifier.

```
For the TARGET MESSAGE, classify its dialogic functions.
A message can perform MULTIPLE functions simultaneously.

Functions (pick all that apply, assign weights summing to ~1.0):

- challenging: questioning or opposing what's been said
- co_creating: building something new together
- explaining: teaching or clarifying information
- sharing: revealing personal stories, feelings, or experiences
- affirming: supporting or validating what's been said
- transmitting: transferring existing information neutrally
- querying: requesting information or input
- echoing: reflecting, confirming, or acknowledging

IMPORTANT:
- If sarcastic, classify the ACTUAL function, not the surface form
  ("Great job" said sarcastically = challenging, not affirming)
- A single message can have 2-4 functions. Assign weights by prominence.
- Simple messages often have 1-2 functions. Complex messages can have 3-4.
- Provide the exact quote that supports each function.

CONTEXT MESSAGES:
{context_messages}

TARGET MESSAGE:
Speaker: {sender}
Message: {content}

Return JSON:
{
  "dialogic_functions": [
    {"function": "...", "weight": 0.0-1.0, "evidence": "exact quote"}
  ]
}
```

### Mechanical Classifier (Alternative)

For high-throughput always-on classification, a trained classifier can handle clear-cut cases:

```python
def classify_dialogic_function(message_text, context=None):
    """Classify message into dialogic functions."""

    functions = []

    # Question detection
    if has_question_mark(message_text) or starts_with_question_word(message_text):
        if is_rhetorical(message_text, context):
            functions.append({"function": "challenging", "weight": 0.8})
            functions.append({"function": "querying", "weight": 0.2})
        else:
            functions.append({"function": "querying", "weight": 0.8})

    # First-person experience markers
    if has_first_person_past(message_text):
        functions.append({"function": "sharing", "weight": 0.5})

    # Explanation markers
    if has_explanation_structure(message_text):
        functions.append({"function": "explaining", "weight": 0.5})

    # Agreement markers
    if has_agreement_markers(message_text):
        functions.append({"function": "affirming", "weight": 0.5})

    # Disagreement markers
    if has_disagreement_markers(message_text):
        functions.append({"function": "challenging", "weight": 0.5})

    # Pure information (no opinion, no question, no personal)
    if is_neutral_information(message_text):
        functions.append({"function": "transmitting", "weight": 0.8})

    # Reflection markers
    if is_paraphrase_of_previous(message_text, context):
        functions.append({"function": "echoing", "weight": 0.7})

    # Proposal/building markers
    if has_proposal_language(message_text):
        functions.append({"function": "co_creating", "weight": 0.6})

    # Normalize weights
    functions = normalize_weights(functions)

    # If no functions detected, default
    if not functions:
        functions = [{"function": "transmitting", "weight": 1.0}]

    return functions

def normalize_weights(functions):
    """Normalize weights to sum to ~1.0, merge duplicates."""
    merged = {}
    for f in functions:
        key = f["function"]
        if key in merged:
            merged[key] = max(merged[key], f["weight"])
        else:
            merged[key] = f["weight"]

    total = sum(merged.values())
    if total == 0:
        return []

    return [
        {"function": k, "weight": round(v / total, 2)}
        for k, v in sorted(merged.items(), key=lambda x: -x[1])
    ]
```

### Helper Functions

```python
def has_question_mark(text):
    return "?" in text

def starts_with_question_word(text):
    question_words = ["what", "how", "why", "when", "where", "who", "which", "do", "does", "did", "is", "are", "can", "could", "would", "should"]
    first_word = text.strip().lower().split()[0] if text.strip() else ""
    return first_word in question_words

def has_first_person_past(text):
    markers = ["i tried", "i did", "i was", "i had", "i've been", "when i", "my experience", "at my last", "i remember"]
    return any(m in text.lower() for m in markers)

def has_explanation_structure(text):
    markers = ["the way it works", "basically", "in other words", "what this means", "the reason is", "because", "so that", "which means"]
    return any(m in text.lower() for m in markers)

def has_agreement_markers(text):
    markers = ["i agree", "exactly", "good point", "that's right", "absolutely", "definitely", "yes,", "yeah,", "true"]
    return any(m in text.lower() for m in markers)

def has_disagreement_markers(text):
    markers = ["i disagree", "but", "however", "actually", "i don't think", "that's not", "the problem is", "no,"]
    return any(m in text.lower() for m in markers)

def has_proposal_language(text):
    markers = ["what if", "we could", "how about", "let's try", "maybe we should", "i suggest", "what about"]
    return any(m in text.lower() for m in markers)

def is_neutral_information(text):
    return (not has_question_mark(text) and
            not has_first_person_past(text) and
            not has_agreement_markers(text) and
            not has_disagreement_markers(text) and
            not has_proposal_language(text))
```

### Output

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "dialogic_functions": [
    {"function": "sharing", "weight": 0.5, "evidence": "When I tried that approach..."},
    {"function": "challenging", "weight": 0.3, "evidence": "...it failed"},
    {"function": "explaining", "weight": 0.2, "evidence": "The problem was the coupling"}
  ]
}
```


## Step 2: Per-Segment Aggregation

**Runs on:** After segment completes (from Topic Flow)
**Cost:** Zero (arithmetic)

```python
def aggregate_segment_functions(segment_messages, participant):
    """Compute function distribution for a participant within a segment."""
    msgs = [m for m in segment_messages if m.sender == participant]

    if not msgs:
        return None

    function_totals = {
        "challenging": 0, "co_creating": 0, "explaining": 0,
        "sharing": 0, "affirming": 0, "transmitting": 0,
        "querying": 0, "echoing": 0
    }

    for msg in msgs:
        for func in msg.dialogic_functions:
            function_totals[func["function"]] += func["weight"]

    total = sum(function_totals.values())
    if total == 0:
        return None

    distribution = {
        k: round(v / total, 2)
        for k, v in function_totals.items()
    }

    dominant = max(distribution, key=distribution.get)
    diversity = compute_diversity(distribution)

    return {
        "distribution": distribution,
        "dominant_function": dominant,
        "diversity": diversity,
        "message_count": len(msgs),
    }

def compute_diversity(distribution):
    """Shannon entropy normalized to 0-1. Higher = more diverse functions."""
    import math
    values = [v for v in distribution.values() if v > 0]
    if not values:
        return 0.0
    entropy = -sum(v * math.log2(v) for v in values)
    max_entropy = math.log2(len(distribution))
    return round(entropy / max_entropy, 2) if max_entropy > 0 else 0.0
```


## Step 3: Dyadic Comparison

**Runs on:** Per segment, comparing participants
**Cost:** Zero (comparison)

```python
def compute_function_asymmetry(a_distribution, b_distribution):
    """Detect function role patterns between participants."""

    patterns = {
        "teacher_student": (
            a_distribution.get("explaining", 0) > 0.3 and
            b_distribution.get("querying", 0) > 0.3
        ) or (
            b_distribution.get("explaining", 0) > 0.3 and
            a_distribution.get("querying", 0) > 0.3
        ),

        "debate": (
            a_distribution.get("challenging", 0) > 0.2 and
            b_distribution.get("challenging", 0) > 0.2
        ),

        "collaborative": (
            a_distribution.get("co_creating", 0) > 0.2 and
            b_distribution.get("co_creating", 0) > 0.2
        ),

        "interview": (
            (a_distribution.get("querying", 0) > 0.4 and
             b_distribution.get("querying", 0) < 0.1) or
            (b_distribution.get("querying", 0) > 0.4 and
             a_distribution.get("querying", 0) < 0.1)
        ),

        "one_sided_sharing": (
            (a_distribution.get("sharing", 0) > 0.3 and
             b_distribution.get("sharing", 0) < 0.1) or
            (b_distribution.get("sharing", 0) > 0.3 and
             a_distribution.get("sharing", 0) < 0.1)
        ),
    }

    # Who asks vs who answers
    a_asks = a_distribution.get("querying", 0)
    b_asks = b_distribution.get("querying", 0)
    a_answers = a_distribution.get("explaining", 0) + a_distribution.get("transmitting", 0)
    b_answers = b_distribution.get("explaining", 0) + b_distribution.get("transmitting", 0)

    return {
        "patterns": {k: v for k, v in patterns.items() if v},
        "questioner": "a" if a_asks > b_asks + 0.1 else "b" if b_asks > a_asks + 0.1 else "balanced",
        "answerer": "a" if a_answers > b_answers + 0.1 else "b" if b_answers > a_answers + 0.1 else "balanced",
    }
```


## Step 4: Output to Consumers

### To Control Distribution

```json
{
  "segment_id": "t_002",
  "function_ratios": {
    "a_queries_ratio": 0.10,
    "b_queries_ratio": 0.40,
    "a_challenges_ratio": 0.15,
    "b_challenges_ratio": 0.05,
    "questioner": "b",
    "answerer": "a"
  }
}
```

### To Intent

```json
{
  "message_id": 7,
  "function_context_for_intent": {
    "dominant_function": "explaining",
    "suggests_intent": "inform",
    "function_intent_alignment": true
  }
}
```

### To Behavioral Profiling

```json
{
  "participant": "a",
  "function_profile": {
    "primary": "explaining",
    "secondary": "sharing",
    "rarely_uses": ["echoing", "co_creating"],
    "diversity_avg": 0.55,
    "pattern": "Teacher-style. Explains and shares more than queries or affirms.",
    "across_conversations": 5
  }
}
```


## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `classifier_type` | "llm" | "llm" for LLM classification, "mechanical" for rule-based |
| `max_functions_per_message` | 4 | Maximum number of functions assigned to a single message |
| `min_weight_threshold` | 0.1 | Minimum weight to include a function in the output |
| `sarcasm_detection` | true | Enable sarcasm detection (invert surface function) |
| `teacher_student_threshold` | 0.3 | Distribution threshold for teacher-student pattern detection |
| `debate_threshold` | 0.2 | Distribution threshold for debate pattern detection |