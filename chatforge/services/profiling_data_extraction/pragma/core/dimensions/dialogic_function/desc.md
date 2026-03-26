# Dialogic Function: Full Definition

**PRAGMA Dimension: Dialogic Function**
**Measurement: Multi-label classification per message**

**One-sentence definition:** Dialogic Function classifies what each message DOES in the conversation, allowing multiple simultaneous functions with weights.


## What Dialogic Function Is

The action performed by each message. Not what it says (content), not why it's said (intent), not how involved the speaker is (involvement). What the message DOES as a conversational act.

A message can blend functions. "When I tried that approach, it failed" simultaneously challenges an idea and shares experience. The system preserves this blending rather than forcing single classification.


## The Eight Functions

| Function | What it does | Example |
|---|---|---|
| **Challenging** | Questioning or opposing what's been said | "I don't think that approach will scale." |
| **Co-creating** | Building something new together | "What if we combined both ideas?" |
| **Explaining** | Teaching or clarifying information | "The way it works is, the event loop manages..." |
| **Sharing** | Revealing personal stories, feelings, or experiences | "When I was at my last company, we tried..." |
| **Affirming** | Supporting or validating what's been said | "That's a great point. I completely agree." |
| **Transmitting** | Transferring existing information neutrally | "The meeting is at 3pm in room 204." |
| **Querying** | Requesting information or input | "What do you think about the timeline?" |
| **Echoing** | Reflecting, confirming, or acknowledging | "So you're saying we should prioritize speed?" |


## Multi-Label Output

Each message produces a ranked list of functions with weights and evidence:

```json
{
  "message_id": 7,
  "dialogic_functions": [
    {"function": "sharing", "weight": 0.5, "evidence": "When I tried that approach..."},
    {"function": "challenging", "weight": 0.3, "evidence": "...it failed"},
    {"function": "explaining", "weight": 0.2, "evidence": "The problem was the coupling between..."}
  ]
}
```

Weights sum to approximately 1.0. The primary function has the highest weight. Secondary functions capture the blending.


## Measurement Method

**Tier:** Mechanical (classifier) for standard cases. LLM for nuanced/blended cases.

**Mechanical classifier:** A fine-tuned text classifier trained on labeled conversation data. Fast, cheap, handles clear-cut cases.

**LLM fallback:** For messages where the classifier confidence is low or multiple functions score similarly. Uses the shared PRAGMA LLM call (if running) or a separate lightweight call.

**Practical recommendation:** Start with LLM classification (accurate, handles blending natively). Transition to mechanical classifier as labeled data accumulates from LLM outputs. Use LLM as the accuracy benchmark.


## Unit of Analysis

**Per message.** Every message gets a dialogic function classification. This is the most granular dimension in PRAGMA.

No aggregation is needed for the function classification itself. But function DISTRIBUTIONS per segment and per participant feed into other dimensions:
- Control Distribution uses function ratios (who asks vs who answers)
- Intent uses function distributions to support classification (heavy Querying = discover intent)
- Hidden intent uses function patterns (always Explaining but classified as Discover = possible mismatch)


## Aggregation

### Per Segment, Per Participant

```json
{
  "segment_id": "t_002",
  "participant": "a",
  "function_distribution": {
    "explaining": 0.40,
    "querying": 0.05,
    "sharing": 0.25,
    "challenging": 0.15,
    "affirming": 0.10,
    "transmitting": 0.05,
    "co_creating": 0.00,
    "echoing": 0.00
  },
  "dominant_function": "explaining",
  "function_diversity": 0.65
}
```

### Per Segment, Dyadic

```json
{
  "segment_id": "t_002",
  "function_asymmetry": {
    "a_queries_b_explains": false,
    "a_explains_b_queries": true,
    "a_challenges_b_affirms": false,
    "teacher_student_pattern": true,
    "debate_pattern": false,
    "collaborative_pattern": false
  }
}
```

### Cross-Conversation, Per Participant

```json
{
  "participant": "a",
  "behavioral_function_profile": {
    "primary_function": "explaining",
    "secondary_function": "sharing",
    "rarely_uses": ["echoing", "affirming"],
    "function_diversity_avg": 0.55,
    "pattern": "Teacher-style communicator. Explains and shares more than queries or affirms."
  }
}
```


## Dependencies

| Dependency | What it provides | Required? |
|---|---|---|
| **Message text** | Input for classification | Yes |
| **Conversation context** | Preceding messages for disambiguation | Helpful but not required |


## Downstream Consumers

| Consumer | What it uses | How |
|---|---|---|
| **Control Distribution** | Function ratios (who asks vs answers, who challenges vs affirms) | Per-segment dyadic comparison |
| **Intent** | Function distribution supports intent classification | Heavy Querying = discover. Heavy Explaining = inform. Heavy Challenging = convince |
| **Intent (hidden)** | Function pattern vs intent classification = contradiction detection | Always Explaining but classified as Discover = mismatch |
| **Information Density** | Function context (Explaining messages expected to be denser than Echoing) | Density norms per function type |
| **Behavioral Profiling** | Cross-conversation function profile | Stable communication style |
| **CPDE-7** | Function context helps content extraction | Sharing messages more likely to contain personal facts |


## What Dialogic Function Does NOT Cover

- **WHY** the function is being used (that's Intent)
- **HOW MUCH** effort is behind it (that's Investment)
- **HOW activated** the speaker is (that's Expressed Involvement)
- **Strategic meaning** of function patterns (that's Interpretation Layer)
- **Topic context** of the function (that's Topic Flow)