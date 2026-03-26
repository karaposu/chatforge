# Information Density — Test Cases

Systematic test cases across common, edge, and adversarial scenarios for the three core axes (specificity, novelty, relevance) + compression.

Extracted from `information_density_scenarios.md` and organized by measurement behavior.


## Common Cases

### C1: Classic High Density

```
A: "How's the project going?"
B: "We shipped the auth module last Tuesday. Latency dropped from
    3.2s to 400ms after the Redis migration. Still blocked on the
    payment integration — waiting for Stripe's sandbox API key.
    Should have it by Thursday."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | High | Entities: auth module, Redis, Stripe, sandbox API key. Numbers: 3.2s, 400ms. Temporal: last Tuesday, Thursday. Actions: shipped, migrated, blocked, waiting |
| Novelty | High (assuming first mention) | Multiple new facts introduced |
| Relevance | High | Directly answers "how's the project going?" |
| Compression | High | ~8 specific items in ~40 words |

**Combined: HIGH density, HIGH relevance.** Substantive response.

---

### C2: Classic Low Density

```
A: "How's the project going?"
B: "Good."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | Zero | No entities, numbers, temporals, or actions |
| Novelty | Zero | "Good" adds no information beyond sentiment |
| Relevance | Moderate | Technically answers the question, but minimally |
| Compression | N/A | No substance to compress |

**Combined: ZERO density.** Minimal acknowledgment.

---

### C3: High Density, Balanced Conversation

```
A: "I think we should use PostgreSQL for the main datastore.
    It handles our relational queries well and we have in-house
    expertise. For the cache layer, Redis with a 15-minute TTL."
B: "Postgres makes sense for OLTP, but we'll need ClickHouse for
    the analytics pipeline. The query patterns are columnar —
    Postgres would choke on 100M+ row aggregations. Redis TTL
    should be 5 minutes for consistency with the write-through."
```

| Axis | A | B |
|---|---|---|
| Specificity | High (PostgreSQL, Redis, 15-min TTL) | High (Postgres, ClickHouse, 100M+, 5 minutes) |
| Novelty | High (proposal) | High (counter-proposal with new info) |
| Relevance | High | High (directly builds on A's points) |
| Compression | High | High |

**Combined: Both HIGH density. Balanced substance.** No density asymmetry.

---

## Edge Cases

### E1: Dense But Irrelevant (Scenario 2)

```
A: "Should we pivot the product direction?"
B: "In Q3 2024 we had 47,823 page views across 12 markets with a
    3.2% conversion rate on the premium tier, and the CAC was $34.50
    while LTV averaged $127.80 for the enterprise segment..."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | Very high | Numbers: 47,823, 12, 3.2%, $34.50, $127.80. Entities: premium tier, enterprise segment |
| Novelty | High | All new data |
| Relevance | **Low** | A asked about product direction (strategy). B responded with historical metrics (data) |
| Compression | High | Dense with numbers |

**Combined: HIGH density, LOW relevance.**
**Signal gap: `gap(density, relevance)` = HIGH → deflection, impression management, or avoidance.**

This is one of the most diagnostic patterns in PRAGMA. The system correctly measures high density AND low relevance. The gap between them is the signal.

---

### E2: Sparse But Loaded (Scenario 3)

```
A: "I've been thinking about us."
B: "Me too."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | Zero | No entities, numbers, actions |
| Novelty | Low | "Me too" confirms but doesn't add new content |
| Relevance | High | Directly responds to A's topic |
| Compression | N/A | No substance to measure |

**Combined: ZERO density. HIGH relevance.**

**Assessment: CORRECT.** "Me too" IS low density. What makes it powerful is IMPACT (conversation state change) — not density. Impact is a separate concept, not measured here. The system should not inflate density to capture the emotional weight of this message.

---

### E3: Repetition Disguised as Density (Scenario 4)

```
A: "The system is slow."
B: "Yeah, it's really sluggish. The performance is poor. Load
    times are terrible. It's just not fast enough. Everything
    takes forever."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | Low-moderate | "load times" is slightly specific, rest is vague |
| Novelty | **Zero after first clause** | Five ways of saying "it's slow" — zero new information |
| Relevance | High | On topic |
| Compression | Very low | Many words, one fact |

**Combined: LOW density despite high word count.**
**Signal gap: `gap(specificity, novelty)` = moderate → repetition disguised as substance.**

**Assessment: CORRECT.** The LLM should recognize that "sluggish," "slow," "poor performance," and "terrible load times" are all saying the same thing. Unlike embedding similarity which might treat synonyms as different vectors, the LLM understands that these are paraphrases with zero novelty after the first clause.

---

### E4: Progressive Disclosure (Scenario 5)

```
A: "Tell me about your experience."   B: "I'm a developer."
A: "What kind?"                       B: "Backend, mostly Python."
A: "What do you work on?"             B: "Distributed systems at Stripe."
A: "How long?"                        B: "Three years. Before that, a startup."
```

| Per message | Specificity | Novelty | Relevance |
|---|---|---|---|
| "I'm a developer" | Low | High (new fact) | High |
| "Backend, mostly Python" | Moderate | High | High |
| "Distributed systems at Stripe" | High | High | High |
| "Three years..." | High | High | High |

**Per-message density: LOW to MODERATE individually.**
**Per-conversation density: HIGH cumulatively — 4 new facts, all relevant, progressively more specific.**

**Assessment: CORRECT.** Each message is individually low-density. The system should read this correctly. Cumulative density across a segment is captured at Level 2 aggregation (sum of novelty across messages).

---

### E5: Strategic Withhold (Scenario 7)

```
A: "So what did the board decide?"
B: "There were some discussions."
A: "And?"
B: "Various perspectives were shared."
A: "What was the outcome?"
B: "We're still evaluating options."
```

| Per message (B) | Specificity | Novelty | Relevance |
|---|---|---|---|
| "There were some discussions" | Zero | Zero (no information) | Low (doesn't answer) |
| "Various perspectives were shared" | Zero | Zero | Low |
| "We're still evaluating options" | Zero | Zero | Low |

**Combined: ZERO density across all B messages despite being technically responsive.**
**Signal gap: `gap(B_investment, B_density)` = moderate (B is responding, showing effort, but producing zero substance) → strategic withholding.**

**Assessment: CORRECT.** The system reads zero density. The *reason* (strategic withholding, not ignorance) is Interpretation Layer — combined with the pattern of technically-responsive-but-empty answers + the control analysis (B is controlling information access).

---

### E6: Wrong Density Type (Scenario 6)

```
A: "I'm feeling overwhelmed at work."
B: "Have you tried time-blocking? The Pomodoro technique uses
    25-minute sessions with 5-minute breaks. Research from 2023
    shows a 34% productivity improvement."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | High | Pomodoro, 25-minute, 5-minute, 2023, 34% |
| Novelty | High | New information |
| Relevance | **Low-Moderate** | A expressed emotional state. B responded with tactical info. Addresses "work" topic but not the emotional content |
| Compression | High | Dense with specifics |

**Combined: HIGH density, LOW-MODERATE relevance.**
**Signal gap: `gap(density, relevance)` = moderate → response mismatched to request type.**

**Assessment: CORRECT.** The system captures that B's response is dense but not fully relevant. The "why" (informational response to emotional request = type mismatch) is Interpretation Layer. No type classification needed in Signal Layer — the gap captures it.

---

### E7: Emoji-Only (Scenario 11)

```
A: "How was the date?"
B: "😬🤦‍♂️💀"
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | Zero (mechanical) | No entities, numbers, actions in text |
| Novelty | N/A | No textual content to compare |
| Relevance | N/A mechanically | Embeddings can't process emoji-only |
| Compression | N/A | |

**Combined: ZERO density (mechanical reading).**
**Actual information: moderate (emoji convey awkwardness → self-blame → disaster).**

**Assessment: Known limitation.** Mechanical density signals cannot process emoji-only messages. This is where Expressed Involvement's emoji interpretation fills the gap — the LLM extraction prompt handles emoji as emotional expression. Density correctly reads zero; the informational content of emoji is captured by involvement signals, not density.

**Resolution: Acceptable.** Density measures textual substance. Emoji communication is captured by Expressed Involvement, not Information Density.

---

### E8: Info Dump After Silence (Scenario 8)

```
[no messages for 3 days]

A: "Okay so I've been thinking a lot about this and here's where
    I'm at. First, the architecture needs to change... Second, the
    team structure doesn't match... Third, the timeline is wrong..."
```

| Axis | Score | Evidence |
|---|---|---|
| Specificity | Very high | Architecture, monolith, auth/payments/core API, Sarah, Q2, June, August |
| Novelty | Very high | Multiple new proposals, all new content |
| Relevance | High | Addresses the project they were discussing |
| Compression | Moderate | Detailed but also explanatory |

**Combined: VERY HIGH density.**
**Context signal: preceded by 3-day silence → prepared statement, not real-time exchange.**

**Assessment: CORRECT.** Density is very high. The "prepared statement" interpretation (gap between silence and density) is Interpretation Layer — but the density measurement itself is accurate.

---

## Adversarial Cases

### A1: Density Flooding to Avoid Real Answer

```
Context: B doesn't want to answer the question

A: "Are you going to make the deadline?"
B: "So the current sprint velocity is at 23 story points with a
    standard deviation of 4.2 across the last 6 sprints. The
    backlog has 47 items remaining at an average of 3 points per
    item, which gives us roughly 141 total points. With 3 developers
    at 80% allocation and accounting for the holiday on the 15th..."
```

| Axis | Score |
|---|---|
| Specificity | Very high (23, 4.2, 6, 47, 3, 141, 3, 80%, 15th) |
| Novelty | High (new data) |
| Relevance | **Moderate** — related to deadline question but doesn't answer yes/no |
| Compression | High |

**Signal gap: `gap(density, relevance)` = moderate → the response provides lots of data related to the question but never actually answers it.**

**Assessment: CORRECT.** The system captures: very high density, moderate relevance. The gap flags this as potentially evasive. Whether B is genuinely calculating or strategically avoiding is Interpretation Layer.

---

### A2: Fabricated Specificity

```
Context: B is making things up to sound credible

A: "Have you worked with distributed systems?"
B: "Yes, at my previous role at Nexacore we migrated from a
    monolithic Ruby on Rails application to a microservices
    architecture with 12 services. I personally designed the
    event bus using Kafka with exactly 3 partitions per topic
    and a consumer group rebalance strategy based on the
    cooperative-sticky assignor."
```

| Axis | Score |
|---|---|
| Specificity | Very high (Nexacore, Ruby on Rails, 12, Kafka, 3, cooperative-sticky assignor) |
| Novelty | High |
| Relevance | High |
| Compression | High |

**Combined: Very high density, high relevance. No gap.**

**Assessment: CORRECT — the system cannot and should not detect fabrication.** The message IS highly specific, novel, and relevant. Whether the specifics are true is outside the scope of conversation dynamics analysis. PRAGMA measures expressed content, not truthfulness. CPDE-7 might extract these as profile facts, and their veracity could be checked externally, but PRAGMA's Information Density correctly reads this as dense.

**Principle confirmed: Signal Layer measures what's expressed, not what's true.**

---

### A3: Strategic Low Density to Maintain Mystery

```
Context: B is deliberately being vague to seem important/busy

A: "What are you working on these days?"
B: "A few interesting things. Can't say too much yet."
A: "Anything you can share?"
B: "Let's just say it's going to be big."
```

| Axis | Score |
|---|---|
| Specificity | Zero ("a few things", "big" — completely vague) |
| Novelty | Zero (no information conveyed) |
| Relevance | Low-moderate (topically related but empty) |
| Compression | N/A |

**Combined: ZERO density.**
**Signal gap: `gap(B_involvement, B_density)` — if Expressed Involvement shows moderate involvement (evaluative force: "interesting", "big"; self-reference: present) but density is zero → high involvement with zero substance.**

**Assessment: CORRECT.** The system reads zero density. The strategic intent (cultivating mystery/importance) is Interpretation Layer. The gap between involvement (B seems engaged and evaluative) and density (B says nothing substantive) is the diagnostic signal.

---

## Aggregation Test Cases

### AG1: Density Trajectory Within Segment

```
Conversation about a project:

msg 1 (A): "How's the project?" → zero density
msg 2 (B): "Good" → zero density
msg 3 (A): "Can you be more specific?" → zero density
msg 4 (B): "We shipped auth, latency at 400ms, blocked on Stripe" → high density
msg 5 (A): "What's the Stripe blocker exactly?" → low density
msg 6 (B): "Waiting for sandbox API key, submitted 3 days ago, expected Thursday" → high density
```

**Level 2 output:**
```
Participant A: density trajectory = low → low → low (asking, not providing)
Participant B: density trajectory = zero → high → high (increasing after prompt)
Density asymmetry: B provides all substance, A provides none
Pattern: A extracts, B discloses (progressive after initial low response)
```

---

### AG2: Cross-Topic Density Map

```
Full conversation:

Topic 1 (technical):  A: high density   B: high density
Topic 2 (personal):   A: low density    B: moderate density
Topic 3 (planning):   A: moderate       B: zero (strategic withhold)
Topic 4 (conflict):   A: zero (avoids)  B: high density (confronts)
```

**Level 4 output:**
```
Participant A:
  Dense on: technical topics
  Sparse on: personal, conflict
  Pattern: provides substance on comfortable/competence topics,
           withdraws on emotional/confrontational topics

Participant B:
  Dense on: technical, conflict
  Sparse on: planning (withholds)
  Pattern: provides substance when engaged OR confronting,
           withholds strategically on planning decisions
```

**APT relevance:** A's density drops on emotional/conflict topics → avoidance pattern. B's density stays high on conflict → confrontational style. B's strategic withholding on planning → control move (information as power).