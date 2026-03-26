# Sensemaking: Topic Flow as the Missing Foundation of CAF

Structural Sensemaking Analysis of the hypothesis that CAF's measurement problems stem from a missing foundational layer — multi-dimensional topic flow analysis — and that building it first would make most other dimensions computable.

---

## SV1 — Baseline Understanding

CAF has 9 dimensions. Most are vague and unmeasurable. Prior sensemaking concluded that the fix is "measure primitives per message, derive patterns." But maybe the reason so many dimensions resist per-message measurement is that they're not *message-level* phenomena at all — they're *topic-level* phenomena. Temporal Structure literally requires topic flow analysis. Power Distribution requires knowing who controls topics. Energy makes more sense per-topic than per-message. Intent correlates with topic. If topic flow analysis were running as a foundation, many of the "vague" dimensions might become straightforward computations on top of it.

---

## Phase 1 — Cognitive Anchor Extraction

### Constraints

- C1: Topic flow analysis is itself a hard problem — topic segmentation, drift detection, and hierarchy are open NLP challenges
- C2: Prior sensemaking already concluded segments should be "approximate" via sliding windows and shift heuristics, not precise
- C3: Any foundational layer must be cheap enough to run always-on (mechanical tier), not require LLM per message
- C4: Conversations don't always have clean topics — some are free-flowing, associative, or multi-threaded

### Key Insights

- K1: **Many CAF dimensions are secretly topic-relative.** "Information density" only makes sense relative to a topic. "Energy dynamics" are often energy-toward-a-topic, not energy-in-general. "Intent" often shifts when topic shifts. The vagueness isn't in the dimensions — it's in the missing reference frame (topic).
- K2: **Topic flow would solve the segment boundary problem.** The prior sensemaking identified "conversation piece" boundaries as a blocker. Topic flow analysis IS segment detection — it gives you the boundaries that other dimensions need.
- K3: **Topic flow would solve the "relative to what?" problem.** "High information density" means nothing in absolute terms. "High information density for this topic in this conversation" is meaningful. Topic provides the context that makes relative measurement anchored.
- K4: **Dialogic Functions — the only well-defined dimension — is topic-independent.** What a message *does* (querying, explaining, affirming) doesn't require topic context. Everything that failed the measurability test does require topic context. This is not a coincidence.
- K5: **Power Distribution becomes computable with topic flow.** Who introduces topics? Who follows? Who redirects? Who abandons topics when the other person changes them? These are all topic flow operations, not message-level features.
- K6: **Temporal Structure IS topic flow.** Linear = topics progress sequentially. Circular = returning to previous topics. Branching = multiple parallel topics. Fragmented = disconnected topic jumps. Temporal Structure is literally the shape of topic flow.

### Structural Points

- S1: Topic flow analysis could serve as infrastructure under multiple CAF dimensions, not just Temporal Structure
- S2: The relationship is: Topic Flow → enables → Segment Detection → enables → Segment-level dimensions (Power, Energy Trajectory, Intent)
- S3: Topic flow has its own measurable primitives: topic introduction, topic continuation, topic shift, topic return, topic abandonment, topic merge
- S4: Topic flow operations can be attributed to participants — "who did what to which topic" — creating a per-participant topic behavior profile

### Foundational Principles

- P1: If a single missing layer explains why 5+ dimensions are vague, the fix is the layer, not patching each dimension independently
- P2: Topic flow is to CAF what a coordinate system is to physics — it provides the reference frame that makes measurements meaningful
- P3: The foundational layer must be cheaper than the dimensions it enables — otherwise it doesn't reduce total system cost

### Meaning-Nodes

- M1: Topic flow as infrastructure vs topic flow as one more dimension
- M2: The distinction between what a message does (dialogic function) and what a message is about (topic)
- M3: Topic as the missing reference frame for relative measurements


### SV2 — Anchor-Informed Understanding

The insight reframes the CAF problem entirely. The prior approach was: "each dimension is independently vague, fix each one." The new frame is: **most dimensions are vague because they lack a common reference frame, and that reference frame is topic flow.**

This isn't adding a 10th dimension. Topic flow is infrastructure — it's the coordinate system that makes the other dimensions measurable. Just as you can't measure velocity without defining a reference frame, you can't measure "information density" or "energy dynamics" without knowing what topic the information/energy is about.

K4 is the strongest anchor: the only dimension that passed measurability (Dialogic Functions) is the only one that doesn't need topic context. Everything else failed *because* topic context was missing.

---

## Phase 2 — Perspective Checking

### Technical / Logical

Topic flow analysis decomposes into several computable operations:

1. **Topic Detection** — what is this message about? (Embedding-based clustering, keyword extraction, or LLM classification)
2. **Topic Continuity** — is this message continuing the previous topic? (Embedding similarity to previous messages)
3. **Topic Shift** — did the topic change? (Similarity drop below threshold)
4. **Topic Return** — did we come back to an earlier topic? (Similarity to messages >N steps back)
5. **Topic Attribution** — who introduced this topic? Who continued it? Who shifted away?

Operations 2-5 can run cheaply on pre-computed embeddings. Operation 1 needs either LLM or embedding + clustering. The embedding approach (compute once, compare cheaply) fits the mechanical tier.

**New anchor:** TA1 — Topic flow can be approximated cheaply using message embeddings. Compute embedding per message (one-time cost), then all topic operations are vector comparisons (near-zero marginal cost).

### Human / User

From a practitioner's perspective, topics are how people naturally think about conversations. "We talked about X, then shifted to Y, then came back to X." This is the natural unit of conversation memory. Topic flow matches human intuition better than per-message scoring.

**New anchor:** TA2 — Topic flow produces human-readable conversation summaries as a side effect. "Topics discussed: [work stress, weekend plans, mutual friend Sarah, back to work stress]" — this is immediately useful, unlike raw signal vectors.

### Strategic / Long-term

If topic flow is the foundational layer, it changes the build order from the prior sensemaking. Instead of "consumer-first, build what Behavioral Profiling needs," it becomes "build topic flow first, then layer dimensions on top."

But this risks the same analysis paralysis identified before — spending months on the foundation before any consumer gets value. The question is: does topic flow deliver value on its own, or only through the dimensions it enables?

**New anchor:** TA3 — Topic flow analysis has standalone value (conversation summarization, topic tracking, topic preference profiling) independent of CAF dimensions. It's not just infrastructure — it's a product feature.

### Risk / Failure

The risk is that topic flow analysis turns out to be harder than expected, becoming its own rabbit hole. NLP topic segmentation has been studied for decades without a definitive solution. If CAF's progress depends on solving topic flow first, and topic flow is hard, progress stalls.

Mitigation: the prior sensemaking already accepted "approximate" segmentation. Topic flow doesn't need to be perfect. It needs to be good enough that dimensions computed on top of it are useful.

**New anchor:** TA4 — Topic flow quality bar is "good enough for downstream dimensions," not "linguistically precise." Embedding similarity with a tunable threshold is likely sufficient.

### Resource / Feasibility

Embedding computation: one embedding per message (e.g., using a small model like `all-MiniLM-L6-v2`). ~128 dimensions, fast inference. Storage is trivial. Similarity computation is O(n) per new message against conversation history.

This is dramatically cheaper than LLM calls. It fits squarely in the mechanical tier.

**New anchor:** TA5 — Topic flow via embeddings is the cheapest possible foundation — cheaper than the per-message mechanical signals already proposed for energy.

### Ethical / Systemic

Topic flow analysis reveals what people talk about and how they navigate between subjects. Combined with APT, it reveals which topics trigger attachment (charm when discussing X, hope when discussing Y). This adds to the influence engineering potential noted in prior sensemaking.

**New anchor:** TA6 — Topic-level behavioral patterns are even more revealing than message-level signals. "Person A always introduces topic X when they want something" is a powerful inference.


### SV3 — Multi-Perspective Understanding

Major reframe from SV2: topic flow is not just useful — it may be **the cheapest and highest-leverage thing to build first.**

Key shifts:

1. **Embeddings make topic flow cheap.** This isn't an expensive LLM-dependent layer. It's vector math on top of one-time embedding computation. It belongs in the mechanical tier.
2. **Topic flow has standalone value.** It's not just CAF infrastructure — conversation summarization and topic tracking are product features.
3. **Topic flow resolves multiple blockers simultaneously.** Segment boundaries, relative baselines, temporal structure, power attribution — all become computable once topic flow exists.
4. **The quality bar is "good enough," not perfect.** Approximate topic flow is sufficient for downstream dimensions.

The relationship between topic flow and CAF dimensions becomes clearer:

```
Topic Flow (foundation)
    │
    ├── directly computes → Temporal Structure
    ├── provides segments for → Energy Trajectory, Power Balance, Intent
    ├── provides reference frame for → Information Density (novelty within topic)
    ├── provides attribution for → Power Distribution (who controls topics)
    └── provides context for → Investment signals (which topics get energy)
```

---

## Phase 3 — Ambiguity Collapse

### Ambiguity 1: Is topic flow a CAF dimension or infrastructure?

The original CAF doesn't list "topic" as a dimension. Temporal Structure is the closest, but it describes the *shape* of topic flow, not topic flow itself.

**Resolution:** Topic flow is infrastructure, not a dimension. It's the layer that makes dimensions computable. Just as Contextual Dimensions were reclassified as input/metadata, Topic Flow is reclassified as a foundational computation that other dimensions depend on.

**What is now fixed:** Topic Flow sits below the measurement layer, as a prerequisite computation.

**What is no longer allowed:** Treating topic flow as optional or as just another dimension alongside the others.

**What now depends on this choice:** The CAF 2.0 architecture now has three layers: Topic Flow → Measurement Primitives → Output Dimensions. Previously it was two layers (Measurement → Output).

**What changed in the conceptual model:** CAF has a foundation layer that wasn't previously identified. The architecture gains depth.


### Ambiguity 2: How is "topic" defined operationally?

"Topic" can mean anything from a single subject ("the weather") to a broad theme ("life dissatisfaction"). Granularity is undefined.

**Resolution:** Topic is defined operationally as *semantic continuity between consecutive messages*. A topic persists as long as consecutive messages have high embedding similarity. A topic boundary occurs when similarity drops. This sidesteps the granularity question — the system doesn't label topics, it detects continuity and shifts.

The output is not "topic = work stress." The output is:
- Messages 1-7: continuous (high similarity)
- Message 8: shift (low similarity to 7, no similarity to earlier)
- Messages 8-12: continuous
- Message 13: return (low similarity to 12, high similarity to messages 1-7)

Topic labels can be computed later (via LLM summarization of clusters) but aren't required for CAF dimensions to work.

**What is now fixed:** Topic = semantic continuity pattern, not a labeled category.

**What is no longer allowed:** Requiring topic labels before dimensions can be computed. Debating topic taxonomy.

**What now depends on this choice:** Embedding model choice and similarity threshold become tunable parameters.

**What changed in the conceptual model:** Topic flow becomes a pattern detection problem (continuity/shift/return), not a classification problem (what is this about?).


### Ambiguity 3: Does topic flow replace the "sliding window + shift heuristics" approach from prior sensemaking?

The prior sensemaking proposed approximate segments via sliding windows. Topic flow is a more principled approach to the same problem.

**Resolution:** Topic flow subsumes and replaces the sliding window approach. Embedding-based continuity detection gives natural segment boundaries grounded in content, not arbitrary window sizes. This is both more principled and approximately the same computational cost.

**What is now fixed:** Segment boundaries come from topic flow, not fixed windows.

**What is no longer allowed:** Arbitrary window sizes as the primary segmentation strategy (windows can still be used as a fallback or smoothing mechanism).

**What now depends on this choice:** The quality of segment-level dimensions now depends on embedding quality and similarity thresholds.

**What changed in the conceptual model:** Segmentation is no longer a hack — it's a first-class computation with a clear methodology.


### Ambiguity 4: What exactly does topic flow make computable that wasn't before?

Need to be specific about what dimensions unlock and how.

**Resolution:** Mapping each previously-vague dimension to what topic flow provides:

| Dimension | What was missing | What topic flow provides |
|-----------|-----------------|------------------------|
| **Temporal Structure** | Needed topic flow analysis | IS topic flow shape (linear, circular, branching, fragmented) — directly computed |
| **Information Density** | "Dense relative to what?" | Dense relative to this topic segment. Novelty = new info within current topic |
| **Energy Dynamics** | Energy toward what? Trajectory over what span? | Energy per topic segment. Trajectory = energy change across segments |
| **Power Distribution** | Who controls the flow — but flow of what? | Who introduces topics, who follows, who redirects, who abandons |
| **Conversational Intent** | Inferred, not observed | Correlates with topic transitions — when someone shifts topic, why? Intent clusters by topic |
| **Engagement/Investment** | Signals need context | Which topics get high investment (long responses, questions, elaboration) vs low |

**What is now fixed:** Each vague dimension now has a concrete path to computation through topic flow.

**What is no longer allowed:** Claiming these dimensions are "inherently unmeasurable." They're measurable once the reference frame exists.

**What now depends on this choice:** Implementation priority — topic flow must be built before these dimensions can be computed.

**What changed in the conceptual model:** The "5 vague dimensions" diagnosis is revised. They weren't vague — they were missing their reference frame.


### SV4 — Clarified Understanding

The CAF measurement problem was misdiagnosed. The 5 "vague" dimensions aren't vague because their definitions are poor. They're vague because they all depend on a missing foundational computation — topic flow — that provides the reference frame for measurement.

What is now clear:
- Topic flow is infrastructure, not a dimension — it sits below the measurement layer
- Topic = semantic continuity pattern, detected via embeddings, not a labeled category
- Topic flow directly computes Temporal Structure and provides the reference frame for Information Density, Energy Dynamics, Power Distribution, Conversational Intent, and Investment
- Embedding-based topic flow fits the mechanical (always-on) tier — it's cheap
- Topic flow has standalone value (summarization, topic tracking) beyond enabling CAF dimensions

What is no longer viable:
- Treating each vague dimension as an independent measurement problem
- Using arbitrary sliding windows as the primary segmentation approach
- Claiming these dimensions are inherently unmeasurable

---

## Phase 4 — Degrees-of-Freedom Reduction

### Fixed Variables

| Variable | Fixed Value |
|----------|------------|
| Role of topic flow | Infrastructure layer, not a dimension |
| Topic definition | Semantic continuity via embeddings |
| Computation cost | Mechanical tier (embedding + vector similarity) |
| Segmentation method | Topic continuity/shift detection replaces sliding windows |
| Build order | Topic flow first, then dimensions on top |

### Eliminated Options

- Independently solving each dimension's measurement problem without a shared foundation
- Arbitrary fixed-window segmentation as primary approach
- Requiring topic labels/taxonomy before dimensions can work
- Treating topic flow as an LLM-dependent expensive operation

### Remaining Viable Paths

**Path A — Embeddings Only**
Compute message embeddings. Detect continuity/shift/return patterns. Layer dimensions directly on similarity scores. No topic labels. Cheapest, fastest to ship.

**Path B — Embeddings + Lightweight Topic Labels**
Same as Path A, but add a clustering step to group continuous segments and generate summary labels (via LLM on segment text, batch). Provides human-readable output ("Topics: work, family, AI"). More useful for product features but adds cost.

**Path C — Embeddings + Full Topic Graph**
Build a topic hierarchy/graph showing parent topics, sub-topics, relationships between topics, and topic evolution over time. Most powerful for deep analysis but most complex to build.

### Assessment

Path A first, extend to Path B when product features need labels. Path C is research-grade and can wait.


### SV5 — Constrained Understanding

The CAF 2.0 architecture is now three layers, not two:

```
Layer 0: Topic Flow (foundation)
         → Embedding per message
         → Continuity/shift/return detection
         → Segment boundaries
         → Topic attribution (who introduced, continued, shifted)

Layer 1: Measurement Primitives (per-message + per-segment)
         → Dialogic Function (per message, classification)
         → Investment Signals (per message, mechanical)
         → Specificity Signals (per message, mechanical)
         → Energy Signals (per message, mechanical + semantic)
         → Power Balance (per segment, from topic attribution + investment)
         → Energy Trajectory (per segment, from energy signals over segment)
         → Segment Intent (per segment, from dialogic functions + topic context)

Layer 2: Output Dimensions (CAF vocabulary)
         → The original 9 dimensions, computed from Layer 0 + Layer 1
```

Build order: Layer 0 → Layer 1 primitives → Layer 2 outputs → downstream consumers (Behavioral Profiling, APT).

---

## Phase 5 — Conceptual Stabilization

### SV6 — Stabilized Model

**The CAF measurement problem was a missing-foundation problem, not a dimension-definition problem. Topic flow analysis is the foundational layer that makes most CAF dimensions computable.**

```
┌─────────────────────────────────────────────────────────┐
│                   RAW CONVERSATION                      │
│              (messages, timing, metadata)                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│             LAYER 0: TOPIC FLOW (foundation)            │
│                                                         │
│   Per-message:                                          │
│    • Compute embedding                                  │
│    • Detect: continuity | shift | return                │
│    • Attribute: who introduced, continued, shifted      │
│                                                         │
│   Output:                                               │
│    • Segment boundaries                                 │
│    • Topic continuity graph                             │
│    • Per-participant topic behavior                     │
│    • Temporal Structure (topic flow shape)              │
│                                                         │
│   Cost: Mechanical tier (embedding + vector math)       │
└─────────────────────────────────────────────────────────┘
                         │
                         │  provides reference frame
                         ▼
┌─────────────────────────────────────────────────────────┐
│          LAYER 1: MEASUREMENT PRIMITIVES                │
│                                                         │
│   Per-message (topic-aware):                            │
│    • Dialogic Function (classification)                 │
│    • Investment Signals (time, length, elaboration)     │
│    • Specificity Signals (entities, numbers, concrete)  │
│    • Energy Signals (mechanical + semantic)             │
│                                                         │
│   Per-segment (computed over topic segments):           │
│    • Power Balance (topic control + investment ratio)   │
│    • Energy Trajectory (energy direction over segment)  │
│    • Segment Intent (function distribution + context)   │
│    • Information Density (novelty within topic)         │
│                                                         │
│   Cost: Mechanical always-on, semantic selective        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│          LAYER 2: OUTPUT DIMENSIONS (CAF vocabulary)    │
│                                                         │
│   1. Dialogic Functions    ← Layer 1 direct             │
│   2. Conversational Intent ← Layer 1 segment intent     │
│   3. Contextual Dimensions ← input metadata             │
│   4. Energy Dynamics       ← Layer 1 energy trajectory  │
│   5. Information Density   ← Layer 1 per-topic density  │
│   6. Power Distribution    ← Layer 1 power balance      │
│   7. Temporal Structure    ← Layer 0 topic flow shape   │
│   8+9. Investment Level    ← Layer 1 investment signals │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    Behavioral      APT            APT
    Profiling     Inference      Profiling
```

### What topic flow unlocks for each dimension

| Dimension | Before topic flow | After topic flow |
|-----------|------------------|-----------------|
| Temporal Structure | "Needs topic flow analysis" — blocked | Directly computed: shape of topic continuity graph |
| Information Density | "Dense relative to what?" — no anchor | Dense relative to current topic. Novelty within segment is computable |
| Energy Dynamics | "Energy toward what?" — directionless | Energy per topic. Trajectory over topic-bounded segments |
| Power Distribution | "Who controls flow" — flow undefined | Who introduces/redirects/abandons topics. Computable from topic attribution |
| Intent | "Inferred, not observed" — vague | Correlates with topic transitions. Clusters by topic segment |
| Investment | "Signals need context" — contextless | Which topics get high investment vs low. Contextualizes all mechanical signals |

### How SV6 differs from SV1

SV1 saw the problem as "dimensions are vague and need individual decomposition into primitives." SV6 sees the problem as **"dimensions were missing their reference frame, and that reference frame is topic flow."**

The critical insight: **Dialogic Functions was the only measurable dimension because it's the only one that doesn't need topic context.** Every dimension that failed the measurability test failed because it implicitly depends on knowing what topic the conversation is in. Once topic flow exists as a foundational layer, those dimensions become straightforward computations.

This changes the build strategy from "pick dimensions, decompose each" to **"build topic flow first, then most dimensions become computable as a consequence."**

Topic flow via embeddings is cheap (mechanical tier), has standalone value (summarization, topic tracking), and unlocks the entire CAF measurement system. It is the highest-leverage single component to build.