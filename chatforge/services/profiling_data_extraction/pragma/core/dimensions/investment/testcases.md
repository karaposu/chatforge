# Investment: Test Cases


## Common Cases

### C1: High Investment (Both Sources)

```
Context: A asked "How's the project?"
Response time: 45 seconds
Message: "Great question. We shipped auth last Tuesday, latency
at 400ms. But I'm worried about payments. I talked to Sarah
and she thinks we need another sprint. Have you seen the latest
test results? I put together a comparison doc."
```

| Signal | Score |
|---|---|
| Structural: fast response (45s) | 0.3 |
| Structural: long message (40+ words) | 0.3 |
| Content: elaboration (multi-sentence) | 0.2 |
| Content: question-asking ("Have you seen...") | 0.2 |
| Content: unsolicited detail (comparison doc mention) | 0.2 |

**Combined: HIGH.** Both sources agree.

---

### C2: Zero Investment

```
Context: A asked a detailed technical question
Response time: 3 hours
Message: "ok"
```

| Signal | Score |
|---|---|
| Structural: slow response (3h) | 0.0 |
| Structural: very short (1 word) | 0.0 |
| Content: no elaboration | 0.0 |
| Content: no questions | 0.0 |

**Combined: ZERO.**

---

### C3: High Structural, Low Content (Going Through Motions)

```
Context: Weekly standup
Response time: 10 seconds
Message: "Nothing new from my side. Same as last week."
```

| Signal | Score |
|---|---|
| Structural: very fast response | 0.3 |
| Structural: short but present | 0.1 |
| Content: no elaboration | 0.0 |
| Content: no questions | 0.0 |
| Content: no detail | 0.0 |

**Structural: 0.40. Content: 0.00.**
**Combined: 0.16 (low).**
**Signal gap: gap(structural, content) = 0.40.** Showing up fast but saying nothing. Obligation pattern.

---

### C4: Low Structural, High Content (Delayed But Substantive)

```
Context: A asked about architecture options
Response time: 2 days
Message: "Sorry for the delay. I've been thinking about this a lot.
Here's my analysis: Option A gives us better latency but Option B
scales horizontally. I built a comparison matrix. For our use case
(10k concurrent, 99.9% uptime) I'd recommend Option B with a
caching layer for the hot path. What do you think about the
tradeoff between consistency and availability?"
```

| Signal | Score |
|---|---|
| Structural: very slow response (2 days) | 0.0 |
| Structural: very long message | 0.3 |
| Content: extensive elaboration | 0.2 |
| Content: question-asking | 0.2 |
| Content: unsolicited detail (comparison matrix, specific numbers) | 0.2 |
| Content: depth of reasoning (tradeoff analysis) | 0.1 |

**Structural: 0.30. Content: 0.70.**
**Combined: 0.54 (moderate-high).**
**This is the "prepared statement" pattern from the density scenarios.** High content investment despite low structural investment. The 2-day delay was processing time, not disengagement.


## Edge Cases

### E1: Silence Breaking as Investment

```
Context: No messages for 24 hours. A initiates.
Response time: N/A (initiator)
Message: "Hey, I've been thinking about what you said yesterday.
I think you're right about the architecture."
```

| Signal | Score |
|---|---|
| Structural: silence breaker | 0.2 |
| Structural: moderate length | 0.2 |
| Content: references previous conversation | 0.1 |
| Content: elaboration (gives a position) | 0.1 |

**Combined: MODERATE.** Silence breaking is itself an investment signal. They chose to re-engage without being prompted.

---

### E2: Multi-Message Burst

```
Context: A sends 3 messages in rapid succession without B responding

Message 1: "Wait I just realized something"
Message 2: "The auth service isn't just slow, it's leaking connections"
Message 3: "I'm looking at the logs now. Connection pool exhaustion.
This explains the timeout pattern we've been seeing."
```

| Signal | Each message | Combined across burst |
|---|---|---|
| Structural: burst of 3 | 0.1 per msg (burst bonus) | High |
| Content: progressive elaboration | Increases across messages | High |
| Content: unsolicited investigation | Present | High |

**Combined: HIGH.** Multi-message bursts without response indicate high investment. The person is investing even without feedback.

---

### E3: Copy-Paste vs Genuine Elaboration

```
Message A (copy-paste): "Our auth system uses JWT tokens validated
at the API gateway. The middleware checks signatures against
the JWKS endpoint. Role-based access uses Redis for lookups."

Message B (genuine): "I think we should use JWT for auth. I've been
reading about it and the stateless nature means we don't need
session storage. But I'm worried about token revocation. How
do you handle that?"
```

Both messages are ~40 words. Both are detailed. But:
- Message A: transmitting (rote information, possibly pasted). Low content investment despite length.
- Message B: explaining + querying + sharing concern. High content investment.

**The difference is in Dialogic Function and Expressed Involvement, not word count.** Investment captures the structural signals (length, speed) but the QUALITY of investment needs other dimensions. This is why Investment alone is not sufficient. The signal gap `gap(investment, involvement)` catches this: copy-paste = high investment, low involvement.

---

### E4: Emoji as Investment

```
Context: A shares exciting news
Message: "🎉🎉🎉🔥❤️"
```

| Signal | Score |
|---|---|
| Structural: fast response (assumed) | Variable |
| Structural: short message | 0.0 |
| Content: no elaboration, no questions | 0.0 |

**Combined: LOW structurally.** But the emoji express engagement. This is where Expressed Involvement captures what Investment misses. Investment = low (minimal effort). Involvement = moderate (emotional activation). The gap signals: low effort but genuine reaction.


## Aggregation Test Cases

### AG1: Investment Trajectory Within Segment

```
A's messages in a segment:
  msg 1: investment 0.7 (detailed response, fast)
  msg 3: investment 0.5 (moderate, engaged)
  msg 5: investment 0.3 (shorter, slowing)
  msg 7: investment 0.1 (minimal, "ok")
```

**Trajectory: de-escalating.** A's investment drops across the segment. Could mean: topic exhaustion, losing interest, conversation winding down naturally.

Combined with involvement trajectory: if involvement is ALSO dropping → genuine disengagement. If involvement stays high but investment drops → strategic disengagement (control move? frustration?).

---

### AG2: Investment Asymmetry

```
Segment averages:
  A: structural 0.6, content 0.7, combined 0.66
  B: structural 0.2, content 0.1, combined 0.14

Asymmetry: A invests 4.7x more than B.
```

**This is a major asymmetry.** A is carrying the conversation. B is minimally engaged.

Combined with control signals: if B has high control despite low investment → B controls through strategic disengagement. If A has high control AND high investment → A is driving. If neither controls → the conversation is dying.