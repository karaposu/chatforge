# Energy — Full Definition

**PRAGMA Dimension: Expressed Involvement (Energy)**
**Atomic Unit: Five micro-signals (SRI, EF, TI, RD, US)**

**One-sentence definition:** Energy measures how present and activated each participant is in what they're saying, tracked as a trajectory over time per participant per topic.


## What Energy Is

Energy is not a primitive — it's emergent. It emerges from the trajectory of Expressed Involvement across messages, topics, and participants. It is the conversational equivalent of temperature: you don't measure temperature directly, you measure molecular motion and temperature emerges from the aggregate.

Expressed Involvement is the molecular motion. Energy is the temperature.


## The Atomic Unit: Expressed Involvement

**Definition:** The degree to which the speaker's self is present and activated in what they're saying.

Some messages are pure information relay — the speaker is absent from the content. Others are charged with the speaker's reaction, state, judgment, preoccupation. The difference is expressed involvement.

```
Zero:      "The meeting is at 3pm."        (relaying information)
Zero:      "noted."                         (acknowledging receipt)
Low:       "I think we should prepare."     (mild opinion, calm)
Moderate:  "I really think we need to..."   (emphasis, personal stake)
High:      "I can't stop thinking about it" (preoccupation, self consumed)
High:      "Wait — are you saying...??"     (disruption, surprise, activated)
```

Expressed Involvement is **irreducibly semantic** — no mechanical proxy captures the difference between "noted." (dismissive zero) and "understood." (respectful zero). It requires LLM-based extraction.

**Critical distinction:** Expressed Involvement measures what is *expressed*, not what is *felt*. A person performing high involvement and a person genuinely highly involved produce the same signal. Whether involvement is genuine or performed is Interpretation Layer territory.


## The Five Micro-Signals

Expressed Involvement decomposes into five detectable micro-signals:

### 1. Self-Reference Intensity (SRI)

How much the speaker puts themselves into the statement — their identity, experience, or position at stake.

| Level | Example |
|-------|---------|
| Absent | "It's possible." |
| Present | "I think it's possible." |
| Invested | "I'm convinced this is the way." |
| Exposed | "This is exactly what I've been struggling with for months." |

### 2. Evaluative Force (EF)

How strongly they judge or evaluate what they're discussing — intensity of evaluation, independent of direction.

| Level | Example |
|-------|---------|
| Absent | "The project exists." |
| Mild | "The project is fine." |
| Moderate | "The project is going well." |
| Strong | "The project is incredible." / "The project is a disaster." |

EF has **direction** (positive, negative, mixed, masked_negative) in addition to level. Direction is topic-relative when possible.

### 3. Temporal Involvement (TI)

Whether this subject occupies them beyond the current message — past thinking, future concern, ongoing preoccupation.

| Level | Example |
|-------|---------|
| Absent | "okay" |
| Present-only | "That's interesting." |
| Extended | "I've been thinking about this a lot." |
| Consuming | "I can't stop thinking about this. I was up all night." |

### 4. Reactive Disruption (RD)

Whether the conversation is changing their state right now — surprise, realization, shock, sudden understanding.

| Level | Example |
|-------|---------|
| Absent | "I see your point." |
| Mild | "Huh, I hadn't thought of that." |
| Moderate | "Wait — that changes everything." |
| Strong | "Oh my god. Are you serious??" |

### 5. Urgency Signal (US)

Whether there's time pressure, necessity, or imperative force in how they frame things.

| Level | Example |
|-------|---------|
| Absent | "Whenever you get a chance." |
| Mild | "It would be good to look at this soon." |
| Moderate | "We should really address this." |
| Strong | "We need to talk about this now." |

### Combined Score

Zero micro-signals firing = zero involvement (pure relay, speaker absent).
All five at high intensity = maximum involvement (speaker fully activated).

The involvement score is not a simple average — it's the overall impression of how present the speaker is. One signal at strong level can dominate (a strong Reactive Disruption makes the message high-involvement even if other signals are absent).


## Aggregation Hierarchy

Expressed Involvement aggregates through 5 levels:

```
LEVEL 1: Per message, per participant
  → Raw: 5 micro-signals + combined involvement score
  → Unit: single message
  → Source: LLM extraction (every message)

LEVEL 2: Per topic segment, per participant
  → Trajectory: escalating / de-escalating / stable / pulsing
  → Evaluative direction: positive / negative / mixed trending
  → Average involvement within segment
  → Unit: topic segment (from Topic Flow)
  → Source: computed from Level 1

LEVEL 3: Per topic segment, dyadic
  → Involvement asymmetry: who is more involved on this topic?
  → Trajectory divergence: are they moving in the same or opposite direction?
  → Unit: topic segment × participant pair
  → Source: computed by comparing Level 2 across participants

LEVEL 4: Per conversation, per participant
  → Topic involvement map: which topics activate this person?
  → Cross-topic pattern: involvement varies how across topics?
  → Unit: full conversation × participant
  → Source: computed from Level 2 across topics

LEVEL 5: Cross-conversation, per participant
  → Stable involvement patterns: what consistently activates them?
  → Behavioral signature: "high on technical, low on social"
  → Unit: participant across many conversations
  → Source: aggregated from Level 4
```


## Output Dimensions

Energy produces two output dimensions in the Dynamics Profile:

### Expressed Involvement Trajectory (per segment)

The trajectory of involvement + evaluative direction over a topic segment.

| Involvement trend | Evaluative direction | Label |
|---|---|---|
| Escalating | Positive | Building excitement |
| Escalating | Negative | Conflict building |
| De-escalating | Positive | Resolution, settling |
| De-escalating | Negative | Giving up, resignation |
| Stable high | Mixed | Sustained tension |
| Pulsing | Any | Rhythmic engagement |

### Investment Quality (per segment, per participant)

Whether involvement aligns with investment signals:

| Investment | Involvement | Interpretation |
|---|---|---|
| High | High | Genuine engagement |
| High | Low | Obligation, going through motions |
| Low | High | Frustrated but disengaging from effort |
| Low | Low | Disengaged |


## Dependencies

| Dependency | What it provides | Required? |
|---|---|---|
| **Topic Flow** | Segment boundaries, topic context for per-topic aggregation | Yes, for Level 2+ |
| **Message Properties** | Timestamps, word counts, context for LLM prompt | Yes, for context |


## Downstream Consumers

| Consumer | What it takes | Level |
|---|---|---|
| **Emotional Trajectory** (Signal Layer) | Per-segment involvement trajectory | Level 2 |
| **Control Distribution** (Signal Layer) | Emotional register control — involvement trajectory comparison between participants | Level 3 |
| **Dynamics Profile** | Expressed Involvement dimension | Level 2 mapped to output |
| **Behavioral Profiling** | Cross-conversation involvement patterns | Level 5 |
| **APT Inference** | Involvement asymmetry per topic → charm/hope/fear signals | Level 3 |
| **APT Profiling** | Aggregated attachment bearings from involvement patterns | Level 5 |
| **Signal Gaps** | gap(investment, involvement), gap(involvement, control_effect) | Level 2-3 |


## Why LLM, Not Mechanical

Mechanical proxies (word count, punctuation, response speed) are poor approximations of involvement:

| Mechanical proxy | What it approximates | When it's wrong |
|---|---|---|
| Word count (high) | High involvement | Copy-paste, verbose habit |
| Exclamation marks | RD or EF | Stylistic habit, sarcasm |
| Response speed (fast) | US or high involvement | Habitual fast-responder |
| Caps usage | High intensity | Stylistic emphasis |
| Question marks (many) | SRI or RD | Interrogation style |

Every proxy has failure modes that produce systematically wrong readings. Only LLM extraction can reliably assess the semantic reality of how present the speaker is. The LLM extraction runs on every message.


## Prompt Refinements (from Stress Testing)

The LLM extraction prompt must handle:

1. **Sarcasm:** detect and invert EF direction. Flag as sarcastic.
2. **Quotation/attribution:** assign EF to quoted source, not speaker. Speaker's involvement is in the act of quoting.
3. **Formulaic language:** recognize boilerplate ("Hope you're well", "Best regards"), suppress false signals.
4. **Emoji interpretation:** map common emoji to micro-signal equivalents when text is absent.
5. **Passive-aggression:** detect surface-depth inversion, output both surface EF and detected underlying EF. Flag as passive_aggressive_pattern.


## What Energy Does NOT Cover

- **Why** someone is involved — Interpretation Layer
- **Whether** involvement is genuine or performed — Interpretation Layer
- **What** they're involved about (content extraction) — CPDE-7
- **Who** they're involved with (relational dynamics) — APT via Level 3
- **Strategic meaning** of involvement patterns — Interpretation Layer

Energy measures one thing: **how present and activated is the speaker in this utterance, tracked over time.** Everything else is built on top.