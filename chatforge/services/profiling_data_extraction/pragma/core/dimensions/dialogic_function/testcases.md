# Dialogic Function: Test Cases

Test cases for multi-label function classification.


## Common Cases

### C1: Pure Querying

```
Message: "What's the status of the deployment?"
```

Expected: `[{querying: 1.0}]`
Single function, no blending.

---

### C2: Pure Transmitting

```
Message: "The meeting is at 3pm in conference room B."
```

Expected: `[{transmitting: 1.0}]`
Pure information transfer. No opinion, no personal experience.

---

### C3: Pure Affirming

```
Message: "Exactly. That's a great point."
```

Expected: `[{affirming: 0.8}, {echoing: 0.2}]`
Primarily affirming (supporting the idea). Slight echoing (confirming).

---

### C4: Blended Sharing + Challenging

```
Message: "When I tried that approach at my last company, it failed badly."
```

Expected: `[{sharing: 0.5}, {challenging: 0.5}]`
Shares personal experience AND challenges the proposed approach simultaneously.

---

### C5: Blended Explaining + Sharing

```
Message: "The way React hooks work is you declare state with useState.
I actually struggled with this when I first learned it."
```

Expected: `[{explaining: 0.6}, {sharing: 0.4}]`
Technical explanation blended with personal experience.

---

### C6: Co-creating

```
Message: "What if we combined your caching idea with the event-driven
approach? We could have the cache invalidate on events."
```

Expected: `[{co_creating: 0.7}, {explaining: 0.3}]`
Building something new from combining ideas. Explanation of how it would work.

---

### C7: Echoing

```
Message: "So you're saying we should delay the launch by two weeks
to fix the auth issues?"
```

Expected: `[{echoing: 0.8}, {querying: 0.2}]`
Reflecting back what was said (echoing) with slight question seeking confirmation.


## Edge Cases

### E1: Question That's Really a Challenge

```
Context: B just proposed a risky architecture change
Message: "Have you considered what happens when we need to scale to 10x users?"
```

Expected: `[{challenging: 0.6}, {querying: 0.4}]`
Surface form is a question (querying) but the function is challenging the proposal. The question implies "you haven't thought about this."

---

### E2: Compliment That's Really Dismissing

```
Context: Junior team member presented an idea
Message: "That's a creative thought. Let's go with the standard approach though."
```

Expected: `[{affirming: 0.3}, {challenging: 0.5}, {transmitting: 0.2}]`
Surface affirms ("creative thought") but actually dismisses the idea and transmits a decision. The affirming is performative.

---

### E3: Single Word Responses

```
Message: "okay"
```

Expected: `[{echoing: 0.7}, {affirming: 0.3}]`
Acknowledging receipt (echoing) with mild agreement (affirming). Low confidence overall.

```
Message: "No."
```

Expected: `[{challenging: 0.8}, {transmitting: 0.2}]`
Opposing (challenging) and conveying a decision (transmitting).

---

### E4: Long Message with Multiple Functions

```
Message: "I agree with the overall direction. But I think the timeline
is too aggressive. When I led a similar project at Google, we took
6 months for the migration alone. Can we discuss what's realistic?"
```

Expected:
```json
[
  {"function": "affirming", "weight": 0.2, "evidence": "I agree with the overall direction"},
  {"function": "challenging", "weight": 0.3, "evidence": "the timeline is too aggressive"},
  {"function": "sharing", "weight": 0.25, "evidence": "When I led a similar project at Google"},
  {"function": "querying", "weight": 0.25, "evidence": "Can we discuss what's realistic?"}
]
```

Four functions in one message. Each clause has a different function.

---

### E5: Emoji-Only

```
Message: "👍"
```

Expected: `[{affirming: 0.6}, {echoing: 0.4}]`
Thumb up = agreement (affirming) + acknowledgment (echoing).

```
Message: "🤔"
```

Expected: `[{echoing: 0.5}, {querying: 0.5}]`
Thinking face = processing (echoing) + implicit question (querying, "tell me more").

---

### E6: Sarcastic Message

```
Context: Third time the build broke this week
Message: "Great job on the deployment. Really impressive."
```

Expected: `[{challenging: 0.8}, {sharing: 0.2}]`
Surface form is affirming but actual function is challenging (criticizing). The sarcasm inverts the surface classification.

---

### E7: Rhetorical Question

```
Message: "Do we really want to ship this to customers?"
```

Expected: `[{challenging: 0.8}, {querying: 0.2}]`
Not genuinely querying. Using question form to challenge the decision. The "really" signals rhetorical intent.


## Aggregation Test Cases

### AG1: Function Distribution Reveals Role

```
Participant A across 20 messages:
  explaining: 8 messages (40%)
  querying: 2 messages (10%)
  sharing: 4 messages (20%)
  transmitting: 3 messages (15%)
  challenging: 2 messages (10%)
  affirming: 1 message (5%)

Participant B across 15 messages:
  querying: 6 messages (40%)
  affirming: 4 messages (27%)
  echoing: 3 messages (20%)
  explaining: 2 messages (13%)
```

**Function asymmetry:**
- A: 40% explaining, 10% querying = teacher/expert role
- B: 40% querying, 27% affirming = student/learner role
- Pattern: teacher-student dynamic

This feeds into Control Distribution (A controls through expertise, B follows through questions) and Intent (A's intent = inform, B's intent = discover).

---

### AG2: Function Shift Within Segment

```
Early messages in segment:
  A: querying, querying, querying (discovery mode)

Mid messages:
  A: challenging, challenging (shifted to challenging B's answers)

Late messages:
  A: transmitting (making a decision)
```

**Function arc:** querying → challenging → transmitting = "asked questions, wasn't satisfied, made own decision"

This correlates with intent arc (discover → convince → control) and control shift (A takes direction control mid-segment).