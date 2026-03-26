# Information Density — Full Definition

**PRAGMA Dimension: Information Density (output name)**
**Measurement: All three axes (specificity, novelty, relevance) are LLM assessed per message, per participant.**

**One-sentence definition:** Information Density measures how much new, relevant substance is in a message, assessed through three LLM-evaluated axes: specificity, novelty, and relevance.


## What Information Density Is

How much substantive content a message carries, relative to the active topic. Not word count (verbose ≠ dense). Not impact (a short question can change everything but is low density). Not receiver-relative (what's new to A may be basic to B — the system measures text properties, not receiver experience).

```
Low density:   "Good."
Low density:   "Yeah, it's really sluggish. The performance is poor.
                Load times are terrible." (repetition ≠ density)
High density:  "We shipped the auth module last Tuesday. Latency dropped
                from 3.2s to 400ms after the Redis migration. Still
                blocked on payment integration — waiting for Stripe's
                sandbox API key. Should have it by Thursday."
```


## Measurement Approach

All three axes are LLM assessed per message, per participant, in a single LLM call:

- **Specificity** → LLM assessed. "How concrete and precise is this message?" Action concreteness ("work on it" vs "refactor the auth module") is a semantic judgment, not a count. Entity gradients ("someone" vs "my colleague" vs "Sarah from the platform team") require understanding reference quality, not just NER detection.
- **Novelty** → LLM assessed. "Does this message add new information relative to what has been said so far in this topic segment?" Embedding similarity cannot reliably distinguish paraphrase from genuine novelty. An LLM can.
- **Relevance** → LLM assessed. "How relevant is this message to the active topic or the question it responds to?" Semantic relevance is a judgment, not a vector distance.

All three axes require understanding meaning in context. Specificity is not just counting entities: it's judging how concrete the communication is across entities, time references, quantities, and actions. That gradient is semantic.


## The Three Core Axes

### 1. Specificity — How Concrete

How precise and concrete is the content? Named things vs vague references.

| Low | High |
|-----|------|
| "I've been working on some stuff" | "I've been building a metacognition layer for Claude Code" |
| "It was good" | "The response time dropped from 3s to 400ms" |
| "We should talk sometime" | "Free Saturday at 2pm?" |

**Sub-dimensions** (output as a vector, not a single score):

| Type | Low | High |
|------|-----|------|
| Entity | "someone" | "John from the engineering team" |
| Temporal | "sometime" | "Saturday 2pm" |
| Quantitative | "a lot" | "47%" |
| Action | "work on it" | "refactor the auth module" |

**Source:** LLM assessment (per message, per participant)
**Resolution:** Per message. The LLM evaluates how concrete the message is across four sub-dimensions: entity, temporal, quantitative, and action specificity. Output as a vector, not a collapsed score.

### 2. Novelty — How New

How much of this is new information within the current topic, vs repetition or rehashing?

| Low | High |
|-----|------|
| Restating what was already said | Introducing a new concept |
| "Like I mentioned before..." | "Here's something I haven't brought up yet..." |
| Circular conversation | Forward movement |

**Source:** LLM assessment (per message, per participant)
**Resolution:** Per message. The LLM sees the current message and the prior messages within the same topic segment, then judges how much genuinely new information this message adds.

This cannot be done mechanically. Embedding similarity fails on paraphrase: "The system is slow" → "Performance is poor" → "Load times are terrible" have different surface forms but carry the same meaning. An LLM correctly recognizes these as repetition, not novelty.

### 3. Relevance — How On-Topic

Is this dense relative to what was asked or the active topic?

**Source:** LLM assessment (per message, per participant)
**Resolution:** Per message. The LLM sees the current message, the active topic (from Topic Flow), and the preceding question (if any), then judges how relevant this message is to what's being discussed.

Semantic relevance is a judgment that requires understanding context. "Redis migration details" is highly relevant when discussing system performance, irrelevant when discussing team morale. Only an LLM can make that contextual determination.

**Why this matters:** High density + low relevance is one of the most diagnostic signal gaps in PRAGMA. It reveals deflection, impression management, or avoidance (see Signal Gaps section).

### Supplementary: Compression — How Efficiently

Information-to-word ratio. How much substance per word?

**Computation:** `compression = specificity_score / word_count`

| Compression | Content | What it looks like |
|---|---|---|
| High | High | Expert communication ("Auth broken. Redis down. Fix by 5pm.") |
| Low | High | Verbose but informative |
| Low | Low | Waffling |
| High | Low | Terse but empty (rare) |

**Source:** Computed from LLM specificity score + Message Properties word count


## What Was Removed from Scope

### Type (factual vs analytical vs emotional)

Originally an axis. Removed because the diagnostic cases are captured by signal gaps:
- Scenario 6 (emotional question, factual answer) shows up as `gap(density, relevance)` — the response is dense but not relevant to the emotional content
- Why the gap exists (wrong content type) is Interpretation Layer, not Signal Layer

### Impact (conversation state change)

Originally an axis. Removed because it's not a message property — it's retrospective:
- "Me too" is correctly LOW density (2 words, no specificity)
- What makes it important is impact on conversation state, not density
- Impact requires looking forward (did topics shift? did involvement change?)
- Separate concept that may become its own signal, but is not density

### Receiver-Relative Density

Originally considered. Removed because unmeasurable from text:
- Same message is dense for A (new concepts) and sparse for B (basic knowledge)
- The system can't know what each participant already knows
- Density measures text properties, not receiver experience


## Aggregation Hierarchy

```
LEVEL 1: Per message
──────────────────────────────────────────────
  Specificity vector: [entity: 3, temporal: 1, quantitative: 2, action: 2]
  Compression: 0.14 (8 specific items / 57 words)

LEVEL 2: Per topic segment, per participant
──────────────────────────────────────────────
  Specificity avg: 0.6
  Novelty: 0.7 (mostly new content within segment)
  Relevance: 0.85 (on-topic)
  Combined density: high, relevant, novel
  Density trajectory: stable / increasing / decreasing

LEVEL 3: Per topic segment, dyadic
──────────────────────────────────────────────
  Density asymmetry: A provides 80% of the substance, B provides 20%
  Relevance asymmetry: both on-topic (balanced)
  Signal gap: gap(B_investment, B_density) = high → B is investing
    effort (long messages) but low substance → waffling or struggling

LEVEL 4: Per conversation, per participant
──────────────────────────────────────────────
  Topic density map:
    Topic 1 (technical): A high density, B low
    Topic 2 (personal): A low density, B moderate
  Pattern: A is dense on technical, sparse on personal

LEVEL 5: Cross-conversation, per participant
──────────────────────────────────────────────
  Behavioral signature:
    "High specificity, high compression = expert communicator"
    "High specificity, low novelty = repetitive but detailed"
    "Low specificity across all topics = vague communicator"
```


## Dependencies

| Dependency | What it provides | Required? |
|---|---|---|
| **Topic Flow** | Segment boundaries, active topic identity, prior messages in segment | Yes — context for all three axes |
| **Message Properties** | Word count | Yes — compression computation |
| **LLM** | Specificity, novelty, and relevance assessment per message | Yes — all three axes |


## Downstream Consumers

| Consumer | What it takes | Level |
|---|---|---|
| **Dynamics Profile** | Information Density dimension (per segment) | Level 2 |
| **Signal Gaps** | gap(density, relevance), gap(specificity, novelty), gap(investment, density) | Level 2-3 |
| **Behavioral Profiling** | Density patterns across conversations | Level 5 |
| **APT Inference** | Density asymmetry — who provides substance? Density per topic — what topics get detail? | Level 3-4 |
| **Interpretation Layer** | High density + low relevance patterns for deflection/impression management detection | Level 2-3 |


## Signal Gaps from Density

| Gap | High value means | Interpretation Layer reads it as |
|---|---|---|
| `gap(density, relevance)` | Dense but off-topic | Deflection, impression management, avoidance |
| `gap(specificity, novelty)` | Specific but repetitive | Repetition disguised as substance |
| `gap(investment, density)` | High effort but low substance | Waffling, struggling, or obligation |
| `gap(density_A, density_B)` | One participant much denser | Information asymmetry, expertise gap, or withholding |


## Connection to APT

Information Density connects to APT through asymmetry patterns:

| Density pattern | APT signal |
|---|---|
| A provides high density on topics where A wants to impress B | Charm attempt — displaying competence through substance |
| B provides low density despite high investment on certain topics | Withholding or processing — possible fear signal |
| High gap(density, relevance) from A toward B | Impression management — flooding with impressive but irrelevant data |
| A's density increases specifically on topics B cares about | Hope — A invests substance where it might benefit them |
| Density asymmetry shifts after control moment | Whoever lost control reduces density (disengagement) |


## What Information Density Does NOT Cover

- **Why** density is high or low — Interpretation Layer
- **Impact** of a message on conversation state — separate concept
- **Content type** (factual vs analytical vs emotional) — Interpretation Layer via signal gaps
- **Receiver experience** — out of scope, not measurable from text
- **What** the information is about (content extraction) — CPDE-7