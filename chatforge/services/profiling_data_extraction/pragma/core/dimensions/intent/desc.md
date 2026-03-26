# Conversational Intent — Full Definition

**PRAGMA Dimension: Conversational Intent (output name)**
**Measurement: Dual-layer — classification piggybacked on EI call + mechanical computations**

**One-sentence definition:** Intent classifies what each participant is trying to accomplish per message (12 goal categories, confidence-scored), then computes hidden intent, shifts, arcs, and mismatches mechanically from the classifications and existing signals.


## What Intent Is

Intent is the WHY dimension. The other dimensions describe HOW the conversation unfolds. Intent describes WHY participants are in the conversation and what they're trying to achieve.

Intent is fundamentally different from the other PRAGMA dimensions because:
- It lives meaningfully at BOTH Signal Layer (per-message classification) and Interpretation Layer (arcs, strategy, emergent purpose)
- It has a fixed vocabulary AND freestyle explanation
- It detects its own hidden layer (signal gaps reveal hidden intent)
- It's most valuable as trajectory (intent arcs), not static label
- It directly answers the question practitioners most want answered: "WHY?"


## The 12 Intent Categories

Categories are **conversational goals** — what the participant is trying to achieve. Not methods (how they do it), not qualities (how honestly), not subtypes.

| Category | Goal | Key distinction |
|---|---|---|
| **Inform** | "I want them to know X" | Neutral knowledge transfer |
| **Discover** | "I want to learn/understand X" | Seeking, not giving |
| **Convince** | "I want them to agree/believe X" | Directional — changing their view |
| **Connect** | "I want to build/maintain relationship" | Relational, not topical |
| **Request** | "I want them to do/give X" | Action-seeking |
| **Process** | "I want to think/feel through X" | Internal, using conversation as thinking space |
| **Perform** | "I want to project an image/impression" | Self-presentation, perception management |
| **Control** | "I want to direct what happens" | Steering, managing, setting terms |
| **Support** | "I want to help/comfort them" | Other-directed care |
| **Avoid** | "I want to NOT engage with X" | Active disengagement |
| **Test** | "I want to probe their reaction" | Intelligence-gathering without exposure |
| **Co-create** | "I want to build something new together" | Mutual emergence |

Plus **"unclear"** for genuinely ambiguous messages (not an intent — a classification failure state).

### Category Eligibility Principle

A thing is an intent category if and only if it passes ALL of:
1. Is it a goal someone wants to ACHIEVE? (not a method, quality, or subtype)
2. Is it distinct from all existing 12 categories?
3. Can an LLM reliably distinguish it?

See `intent_cat_sensemaking.md` for the full 6-question eligibility test.

### Where Methods, Qualities, and Subtypes Live

| Thing | Where captured | Examples |
|---|---|---|
| **Methods** | PRAGMA signal combinations | Teach = Inform + Control. Scare = Control + negative EF. Charm = Convince + positive EF |
| **Qualities** | Signal gaps | Manipulate = gap(surface_intent, behavioral_signals). Performative = solicit → dismiss pattern |
| **Subtypes** | Freestyle explanation | Vent = "processing through venting." Defend = "convincing with self-protective framing" |


## Measurement Architecture

Intent is **dual-layer** — the only PRAGMA dimension that spans both:

```
EI LLM call (already exists, per-message)
  │
  ├── 5 micro-signals (existing — Expressed Involvement)
  │
  └── Intent classification (piggybacked — near-zero marginal cost)
       │
       ├── Signal Layer (mechanical computations):
       │    ├── Hidden intent (contradiction matrix lookup)
       │    ├── Intent shift (transition significance weight)
       │    ├── Intent mismatch (dyadic comparison)
       │    └── Intent avoidance (pattern detection)
       │
       └── Interpretation Layer (composed readings):
            ├── Intent arcs (pattern matching on sequences)
            ├── Dyadic arcs (pair comparison)
            ├── Emergent intent (co-creation detection)
            ├── Strategic intent (manipulation, performance)
            └── Intent → APT connection
```


## The Six Sub-Properties

### 1. Intent Classification (Signal Layer, per-message)

Per-message classification piggybacked on the Expressed Involvement LLM call.

**Output per message:**
- Primary intent (one of 12 categories)
- Secondary intent (one of 12 or null)
- Confidence (0.0-1.0)
- Explanation (1-2 sentences, freestyle)

Per-message intent is a **hypothesis**, not a fact. Early messages have low confidence. Confidence increases as patterns develop.

### 2. Hidden Intent (Signal Layer, per-message)

Detected when intent classification contradicts EI micro-signals.

**Contradiction matrix** — for each intent, what EI signals would contradict it:

| Classified as | Contradicting EI pattern | Hidden intent likely |
|---|---|---|
| **Inform** | High SRI + strong EF | Convince or Perform |
| **Inform** | High urgency + high SRI | Control or Request |
| **Discover** | Low RD + consistent direction | Control (guiding) or Test |
| **Discover** | High SRI + strong positive EF toward other | Connect or Request (flattering) |
| **Connect** | Low SRI + no TI + urgency later | Request (networking) |
| **Connect** | High density + specificity on other's work | Discover (intel) or Perform |
| **Support** | Low involvement + formulaic | Perform (performative support) or Avoid |
| **Support** | High SRI + topic control | Convince or Control wrapped in care |
| **Process** | Low SRI + directed questions | Test or Discover |
| **Co-create** | One side: low RD + consistent direction | Control (manipulation to predetermined outcome) |
| **Avoid** | High involvement despite low density | Control (information withholding as power) |

**Output:** `{hidden_intent_likely, contradiction_description, gap_magnitude}` or null if no contradiction detected.

### 3. Intent Shift (Signal Layer, per-segment)

Detected when classification changes between consecutive messages from the same participant.

**Transition significance** — not all shifts are equal:

| From → To | Significance | Why |
|---|---|---|
| Inform → Discover | 0.2 (minor) | Both information-oriented |
| Inform → Convince | 0.5 (moderate) | Neutral → advocating |
| Inform → Control | 0.8 (major) | Neutral → directive |
| Discover → Control | 0.8 (major) | Learning → steering |
| Connect → Request | 0.5 (moderate) | Relational → transactional |
| Connect → Avoid | 0.8 (major) | Engagement → withdrawal |
| Support → Control | 0.9 (major) | Caring → directing |
| Co-create → Avoid | 0.9 (major) | Collaboration → abandonment |
| Any → Avoid | 0.7 (significant) | Collapse to avoidance |

**Output:** `{from, to, significance_weight, at_message}` for each detected shift.

### 4. Intent Mismatch (Signal Layer, per-segment, dyadic)

Detected when participants have different dominant intents in the same segment.

| A's intent | B's intent | Mismatch type |
|---|---|---|
| Discover | Inform | **Complementary** — aligned despite different roles |
| Connect | Request | **Friction** — A wants relationship, B wants transaction |
| Discover | Convince | **Competing** — A explores, B pushes |
| Inform | Avoid | **Asymmetric engagement** — A shares, B withdraws |
| Control | Control | **Power contest** — both trying to direct |
| Process | Inform | **Level mismatch** — A needs emotional space, B gives data |

**Output:** `{a_intent, b_intent, mismatch_type, friction_level}`

### 5. Intent Avoidance (Signal Layer, per-segment)

Pattern of non-commitment: multiple consecutive "avoid" or "unclear" classifications + low involvement + control yielding.

**Detection:** `count(avoid + unclear) / total_messages > 0.5` within a segment, combined with low average Expressed Involvement and no topic direction attempts.

**Output:** `{is_avoiding: true, duration_messages, involvement_during_avoidance}`

### 6. Intent Arc (Interpretation Layer, per-segment + per-conversation)

The trajectory of intent classifications across a topic segment, compressed into a named pattern.

**11 named arc patterns:**

| Arc | Pattern | What it reveals |
|---|---|---|
| **Stable** | Same intent throughout | Single-purpose |
| **Shift** | A → B (single transition) | Triggered change |
| **Escalation** | A → A+ → A++ | Increasing intensity |
| **De-escalation** | A++ → A+ → A | Decreasing intensity |
| **Funnel** | Discover → Evaluate → Commit | Narrowing toward decision |
| **Recoil** | A → B → A | Tried and retreated |
| **Oscillation** | A → B → A → B | Can't settle |
| **Convergence** | Different → same | Resolution |
| **Divergence** | Same → different | Splitting |
| **Collapse** | Any → Avoid | Gave up |
| **Emergence** | Various → Co-create | New shared purpose |

**Dyadic arc patterns** (comparing both participants):

| A's arc | B's arc | Dyadic pattern |
|---|---|---|
| Matches B's | Matches A's | **Aligned** |
| Escalating | Stable | **Diverging** |
| Funnel | Stable | **Asymmetric pursuit** |
| Escalating | De-escalating | **Opposing** |
| Various → Co-create | Various → Co-create | **Convergent emergence** |

**Escalation ordering** for arc detection:
```
Low intensity → High intensity:
Inform → Discover → Convince → Control
Support → Connect → Request
```


## Aggregation Hierarchy

```
Level 1: Per message, per participant
  → Intent classification (primary + secondary + confidence + explanation)
  → Hidden intent (contradiction matrix)

Level 2: Per topic segment, per participant
  → Dominant intent (most frequent classification)
  → Intent arc (pattern from sequence)
  → Shift count + total significance
  → Avoidance detection

Level 3: Per topic segment, dyadic
  → Intent mismatch (comparison of dominant intents)
  → Dyadic arc (comparison of arc patterns)
  → Friction level

Level 4: Per conversation, per participant
  → Intent profile: which intents used, in what proportion
  → Arc patterns: how do intents typically evolve?
  → Shift triggers: what causes intent changes?

Level 5: Cross-conversation, per participant
  → Behavioral signature: stable intent patterns
  → "Starts with Discover, shifts to Convince after 3-4 messages"
  → APT connection: intent patterns correlate with attachment type
```


## Dependencies

| Dependency | What it provides | Required? |
|---|---|---|
| **Expressed Involvement LLM call** | Extraction vehicle — intent classification is piggybacked | Yes |
| **EI micro-signals** | Contradiction source for hidden intent detection | Yes |
| **Topic Flow** | Segment boundaries for arc computation | Yes |
| **Dialogic Function** | Supporting evidence for intent classification | Helpful but not required |


## Downstream Consumers

| Consumer | What it takes | Level |
|---|---|---|
| **Dynamics Profile** | Conversational Intent dimension (dominant per segment) | Level 2 |
| **APT Inference** | Intent mismatch + hidden intent patterns → charm/hope/fear | Level 3 |
| **Behavioral Profiling** | Cross-conversation intent patterns | Level 5 |
| **Interpretation Layer** | Intent arcs + hidden intent + shift patterns → strategic reading | Level 2-4 |
| **Signal Gaps** | gap(classified_intent, behavioral_signals) = hidden intent | Level 1 |


## Connection to APT

| Intent pattern | APT signal |
|---|---|
| A's intent shifts to Convince when B demonstrates expertise | A is charmed by B's competence |
| B's intent is consistently Request despite surface Connect | B's attachment is hope-driven (seeking benefit) |
| A avoids intent when specific topics arise | Fear-related avoidance on those topics |
| Persistent intent mismatch (A: Connect, B: Request) | Relationship means different things to each person |
| Hidden intent detected: surface Support, hidden Control | Manipulation through care — control disguised as help |
| Intent arc: Funnel (Discover → Request) across many relationships | Behavioral pattern: systematically networks for benefit |


## What Intent Does NOT Cover

- **What** they're talking about (content) — CPDE-7 and Topic Flow
- **How activated** they are (involvement) — Expressed Involvement
- **Who controls** the conversation — Control Distribution
- **How much substance** is shared — Information Density
- **Whether intent is genuine** (fully) — Interpretation Layer combines hidden intent + patterns across time. Per-message authenticity detection is limited