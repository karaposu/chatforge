# Sensemaking: What It Means for a CDA Dimension to Be "Well-Defined"

When is a dimension concluded? What makes a definition "good enough"? How do we know we're done?

---

## SV1 — Baseline Understanding

We said "Energy is solved" and "Information Density is explored but not concluded." But what exactly does "solved" mean? We need criteria — a checklist that any dimension must pass before it's considered defined. Without this, "solved" is a feeling, not a judgment.

---

## Phase 1 — Cognitive Anchor Extraction

### Constraints

- C1: A definition that can't be measured is philosophy, not engineering
- C2: A measurement that can't trace to evidence is assertion, not analysis
- C3: A system that works on clean examples but breaks on edge cases is fragile, not defined
- C4: A dimension that can't feed downstream consumers (Behavioral Profiling, APT) is disconnected, not useful

### Key Insights

- K1: **"Defined" has multiple levels.** You can define what a concept means (conceptual), what to measure (operational), how to compute it (implementable), and how it connects to everything else (integrated). A dimension isn't "done" until all levels are addressed.
- K2: **The test for "good enough" is scenario coverage.** If you can take any realistic conversation scenario and the dimension's measurement produces a meaningful, non-ambiguous output — it's defined enough. If edge cases produce garbage, contradictions, or "it depends" — it's not.
- K3: **Traceability is the backbone.** "Energy is high" means nothing. "Energy is high BECAUSE Expressed Involvement micro-signals X, Y, Z fired on messages 4, 7, 12, aggregated over Topic 2 segment" — that's traceable. Every output must chain back to specific evidence.
- K4: **The real test is: can someone implement this from the spec alone?** If a developer needs to ask "but what do you mean by..." to build it, the definition is incomplete.

### Structural Points

- S1: A defined dimension has a clear path from raw conversation → atomic measurement → aggregation → output → downstream consumers
- S2: Each step in the path must be specified: what's computed, from what inputs, at what unit, producing what output
- S3: The definition must handle both typical cases and edge cases without special-casing

### Foundational Principles

- P1: Measurability — can you compute it?
- P2: Traceability — can you explain WHY it has this value?
- P3: Scenario coverage — does it produce sensible outputs across diverse cases?
- P4: Implementability — can a developer build it from the spec?
- P5: Integrability — does it connect to downstream consumers?

### Meaning-Nodes

- M1: The distinction between "understood" and "defined"
- M2: Scenario coverage as the validation method
- M3: The chain from atom to output to consumer


### SV2 — Anchor-Informed Understanding

"Defined" is not a binary. It has specific checkable properties. A dimension is concluded when it passes all of them. The properties are: measurability, traceability, scenario coverage, implementability, and integrability. Let's formalize these.

---

## Phase 2 — Perspective Checking

### Technical / Logical

From an engineering perspective, a dimension is defined when:

1. **The computation is specified end-to-end.** Input → processing → output, with no hand-waving steps.
2. **Each step has a clear unit of analysis.** Per-message, per-segment, per-exchange, per-conversation — explicitly stated, not assumed.
3. **Dependencies are explicit.** What other signals/systems does this dimension consume? (Topic Flow, Message Properties, Expressed Involvement, etc.)
4. **Output format is defined.** What does the output look like? A score? A classification? A trajectory? A profile?

**New anchor:** TA1 — The technical test: can you write a function signature for every step? If yes, it's defined. If any step requires "use judgment" or "it depends," it's not.

### Human / User

From a practitioner's perspective, a dimension is defined when:

1. **You can explain it in one sentence.** "Expressed Involvement measures how present and activated the speaker is in what they're saying." If the one-sentence version requires qualifications and exceptions, it's not clear.
2. **Examples are unambiguous.** Given a message, two practitioners would produce similar scores. If reasonable people disagree significantly, the definition is too vague.
3. **It maps to intuition.** Practitioners recognize what it's measuring — "oh, that's what I mean when I say this person has high energy." If the measurement produces results that contradict intuition in normal cases, the definition is wrong.

**New anchor:** TA2 — The practitioner test: do examples produce unambiguous, intuition-matching outputs?

### Risk / Failure

From a failure perspective, a dimension is defined when:

1. **Edge cases don't break it.** The definition handles unusual inputs (empty messages, emoji-only, sarcasm, copy-paste, multilingual) without producing nonsensical outputs.
2. **Failure modes are identified.** Where will this measurement be wrong? What kinds of conversations will produce unreliable scores? This should be known and documented, not discovered in production.
3. **Degradation is graceful.** If one input is missing (e.g., Topic Flow unavailable), does the dimension produce a partial result or crash?

**New anchor:** TA3 — The failure test: are failure modes known and documented?

### Strategic / Long-term

From a system perspective, a dimension is defined when:

1. **It feeds something.** The dimension's output is consumed by at least one downstream system (Behavioral Profiling, APT Inference, Dynamics Profile, Interpretation Layer).
2. **The feeding path is specified.** Not "this could be useful for APT" but "APT Inference consumes this dimension's per-topic-per-participant trajectory to infer charm."
3. **Aggregation is defined.** How does per-message data become per-segment, per-conversation, per-relationship, cross-conversation?

**New anchor:** TA4 — The integration test: is the full pipeline from atom to consumer specified?


### SV3 — Multi-Perspective Understanding

Four tests emerge, each checking a different aspect of "defined":

1. **Technical test** — can you write function signatures for every step?
2. **Practitioner test** — do examples produce unambiguous, intuition-matching outputs?
3. **Failure test** — are edge cases handled and failure modes documented?
4. **Integration test** — is the full pipeline from atom to consumer specified?

A dimension that passes all four is "concluded." A dimension that fails any one is still in progress.

---

## Phase 3 — Ambiguity Collapse

### Ambiguity 1: What does "measurable" actually require?

**Resolution:** A dimension is measurable when:
- The **atomic unit** is identified (what is measured at the smallest granularity)
- The **measurement method** is specified (mechanical, semantic, or computed from other signals)
- The **unit of analysis** is explicit (per-message, per-exchange, per-segment, per-conversation)
- The **output type** is defined (score, classification, trajectory, profile)

If any of these four are "to be determined," the dimension is not measurable yet.

**What is now fixed:** Measurability has 4 sub-requirements, all must be met.

### Ambiguity 2: What does "traceable" actually require?

**Resolution:** A dimension is traceable when any output value can be walked back through:
- Output value → aggregation step → per-segment/per-topic values → per-message measurements → specific messages → source text

Every link in this chain must be specified. If any link is "inferred" or "estimated" without explicit computation, traceability breaks.

**What is now fixed:** Traceability = complete evidence chain from output to source text.

### Ambiguity 3: What does "scenario coverage" actually require?

**Resolution:** The dimension must be tested against:
- **Common cases** (3-5 typical conversations) — produces expected, intuitive outputs
- **Edge cases** (5+ unusual situations) — produces sensible outputs or documented graceful failure
- **Adversarial cases** (2-3 deliberately tricky inputs) — doesn't produce misleading outputs

If the scenarios document exists and the measurement handles them, coverage is met. If scenarios reveal cases the measurement can't handle without special-casing, the definition needs revision.

**What is now fixed:** Scenario coverage has three levels (common, edge, adversarial), all must be addressed.


### SV4 — Clarified Understanding

"Defined" is now a checklist, not a feeling.

---

## Phase 4 — Degrees-of-Freedom Reduction

### The Definition Checklist

A CDA dimension is "concluded" when ALL of the following are met:

```
MEASURABILITY
├── [ ] Atomic unit identified
│       What is measured at the smallest granularity?
│       (e.g., 5 micro-signals for Expressed Involvement)
│       (e.g., redirect-response pairs for Control)
│       (e.g., "computable from existing signals" is also valid)
│
├── [ ] Measurement method specified
│       Mechanical (always-on) / Semantic (LLM, selective) / Computed?
│       What specific computation produces the value?
│
├── [ ] Unit of analysis explicit
│       Per-message / per-exchange / per-segment / per-conversation?
│       If multiple levels, each level specified.
│
└── [ ] Output type defined
        Score / classification / trajectory / vector / profile?
        What does a consumer receive?

TRACEABILITY
├── [ ] Evidence chain complete
│       Output → aggregation → per-segment → per-message → source text
│       Every link specified, no "inferred" gaps.
│
└── [ ] Aggregation hierarchy defined
        How does atomic measurement become segment-level,
        conversation-level, cross-conversation-level?
        Per-participant? Per-topic? Both?

SCENARIO COVERAGE
├── [ ] Common cases handled (3-5 typical conversations)
│       Produces expected, intuition-matching outputs.
│
├── [ ] Edge cases handled (5+ unusual situations)
│       Produces sensible outputs or documented graceful failure.
│
└── [ ] Adversarial cases addressed (2-3 tricky inputs)
        Doesn't produce misleading outputs.

IMPLEMENTABILITY
├── [ ] One-sentence definition exists
│       A developer can read it and understand what to build.
│
├── [ ] Dependencies explicit
│       What other signals/systems does this consume?
│       (Topic Flow, Message Properties, Expressed Involvement, etc.)
│
└── [ ] Function signatures writable
        Can you specify input → computation → output
        for every step without "use judgment"?

INTEGRABILITY
├── [ ] Downstream consumers identified
│       Who uses this? (Behavioral Profiling, APT, Interpretation Layer)
│
├── [ ] Feeding path specified
│       Not "could be useful" but "APT consumes X from this dimension."
│
└── [ ] Signal gaps computable
        Can this dimension's output be compared with other dimensions'
        outputs to produce diagnostic gaps?
```


### SV5 — Applying the Checklist

Let's grade what we have:

#### Energy (Expressed Involvement → Emotional Trajectory → Emotional Dynamics)

| Criterion | Status |
|---|---|
| Atomic unit | **PASS** — 5 micro-signals |
| Measurement method | **PASS** — Semantic (LLM), selective |
| Unit of analysis | **PASS** — Per-message (Level 1), per-segment (Level 2), per-topic-participant (Level 3), etc. |
| Output type | **PASS** — Involvement score → trajectory → dynamics label |
| Evidence chain | **PASS** — Output → aggregation → micro-signals → specific messages |
| Aggregation hierarchy | **PASS** — 5 levels fully defined |
| Common cases | **PASS** — handled in examples |
| Edge cases | **PARTIAL** — some addressed, not systematically documented |
| Adversarial cases | **NOT DONE** — sarcasm, copy-paste, multi-language not tested |
| One-sentence definition | **PASS** — "How present and activated is the speaker" |
| Dependencies | **PASS** — Topic Flow (for per-topic aggregation) |
| Function signatures | **PASS** — LLM extraction prompt structure defined |
| Downstream consumers | **PASS** — Behavioral Profiling, APT Inference, APT Profiling |
| Feeding path | **PASS** — Level 3 asymmetry → APT charm/hope/fear |
| Signal gaps | **PASS** — gap(involvement, control_effect) defined |

**Verdict: 13/15 PASS. Near-complete. Missing systematic edge case and adversarial testing.**

#### Control Distribution

| Criterion | Status |
|---|---|
| Atomic unit | **PASS** — 3 mechanisms (verbosity, topic direction, emotional register) + effect |
| Measurement method | **PASS** — Mechanical (verbosity, direction) + Computed (register from Expressed Involvement) |
| Unit of analysis | **PASS** — Per-exchange (redirect-response pairs), per-segment, per-conversation |
| Output type | **PASS** — Per-mechanism scores + success rates |
| Evidence chain | **PASS** — Output → mechanism success rates → specific exchanges → messages |
| Aggregation hierarchy | **PASS** — 5 levels defined |
| Common cases | **PASS** — handled in examples |
| Edge cases | **PARTIAL** — the dominance test example is one edge case, need more |
| Adversarial cases | **NOT DONE** |
| One-sentence definition | **PASS** — "Who determines what happens next, through what mechanism, and how successfully" |
| Dependencies | **PASS** — Topic Flow, Dialogic Function, Message Properties, Expressed Involvement |
| Function signatures | **MOSTLY** — mechanism detection clear, effect computation needs detail |
| Downstream consumers | **PASS** — APT Inference (primary), Behavioral Profiling |
| Feeding path | **PASS** — control patterns → charm/hope/fear type |
| Signal gaps | **PASS** — gap(verbosity, topic_control_effect) defined |

**Verdict: 12/15 PASS. Close. Missing edge/adversarial testing, effect computation detail.**

#### Information Density

| Criterion | Status |
|---|---|
| Atomic unit | **NOT DECIDED** — 6 axes identified but no atomic unit chosen. Is it "computable from existing signals" or does it need its own? |
| Measurement method | **PARTIALLY** — specificity + compression are mechanical. Novelty needs Topic Flow. Relevance needs Topic Flow. Type and impact are semantic. Not formally decided. |
| Unit of analysis | **PARTIALLY** — per-message for specificity, per-segment for novelty/relevance. Not formalized. |
| Output type | **NOT DEFINED** — vector of axes? Single score? Trajectory? |
| Evidence chain | **NOT DEFINED** — no aggregation path specified |
| Aggregation hierarchy | **NOT DEFINED** |
| Common cases | **PASS** — Scenario 1 (classic dense/sparse) |
| Edge cases | **PASS** — 13 additional scenarios explored |
| Adversarial cases | **PARTIAL** — Scenario 11 (emoji), 14 (cross-language) |
| One-sentence definition | **FAIL** — can't state it in one sentence without listing 6 axes |
| Dependencies | **PARTIALLY** — Topic Flow needed for relevance/novelty, but not formalized |
| Function signatures | **FAIL** — can't write function signatures yet |
| Downstream consumers | **PARTIALLY** — signal gaps identified but not formally connected |
| Feeding path | **NOT SPECIFIED** |
| Signal gaps | **PASS** — gap(density, relevance) defined |

**Verdict: 4/15 PASS, 5 PARTIAL, 6 FAIL. Explored but not concluded. Scenarios are strong but operational definition is missing.**

#### Conversational Intent

| Criterion | Status |
|---|---|
| All criteria | **NOT STARTED** — no scenarios, no atomic unit, no measurement method |

**Verdict: 0/15. Not explored.**


### SV5 — Constrained Understanding

The checklist reveals that "concluded" means passing 15 specific criteria across 5 categories. No dimension passes all 15 yet — even Energy has gaps in systematic edge case testing. But Energy and Control are close (12-13/15), Information Density is half-explored (4/15 with good scenarios), and Intent hasn't started.

The checklist also reveals that **scenario coverage is the easiest category to achieve** (we tend to write scenarios early) while **aggregation hierarchy and feeding path are the hardest** (they require full system thinking).

---

## Phase 5 — Conceptual Stabilization

### SV6 — Stabilized Model

**A CDA dimension is "concluded" when it passes 15 criteria across 5 categories: Measurability (4), Traceability (2), Scenario Coverage (3), Implementability (3), and Integrability (3).**

```
                    IS THIS DIMENSION DEFINED?

                         ┌───────────┐
                         │ Can you   │
                    ┌────│ MEASURE   │────┐
                    │    │ it?       │    │
                    │    └───────────┘    │
                    │                    │
                    ▼                    ▼
             ┌────────────┐      ┌────────────┐
             │ Atomic unit│      │ Output type│
             │ identified?│      │ defined?   │
             └────────────┘      └────────────┘
                    │                    │
                    ▼                    ▼
             ┌────────────┐      ┌────────────┐
             │ Method     │      │ Unit of    │
             │ specified? │      │ analysis?  │
             └────────────┘      └────────────┘

                         ┌───────────┐
                         │ Can you   │
                    ┌────│ TRACE     │────┐
                    │    │ it?       │    │
                    │    └───────────┘    │
                    │                    │
                    ▼                    ▼
             ┌────────────┐      ┌────────────┐
             │ Evidence   │      │ Aggregation│
             │ chain?     │      │ hierarchy? │
             └────────────┘      └────────────┘

                         ┌───────────┐
                         │ Does it   │
                    ┌────│ SURVIVE   │────┐
                    │    │ scenarios?│    │
                    │    └───────────┘    │
                    │         │          │
                    ▼         ▼          ▼
             ┌────────┐┌─────────┐┌───────────┐
             │Common  ││ Edge    ││Adversarial│
             │cases?  ││ cases?  ││ cases?    │
             └────────┘└─────────┘└───────────┘

                         ┌───────────┐
                         │ Can a dev │
                    ┌────│ BUILD     │────┐
                    │    │ it?       │    │
                    │    └───────────┘    │
                    │         │          │
                    ▼         ▼          ▼
             ┌────────┐┌─────────┐┌───────────┐
             │1-line  ││Deps     ││Function   │
             │def?    ││explicit?││sigs?      │
             └────────┘└─────────┘└───────────┘

                         ┌───────────┐
                         │ Does it   │
                    ┌────│ CONNECT   │────┐
                    │    │ to system?│    │
                    │    └───────────┘    │
                    │         │          │
                    ▼         ▼          ▼
             ┌────────┐┌─────────┐┌───────────┐
             │Consumers││Feeding ││Signal     │
             │known?  ││path?   ││gaps?      │
             └────────┘└─────────┘└───────────┘
```

### The Five Questions

| Question | Category | What it checks |
|---|---|---|
| **Can you MEASURE it?** | Measurability | Atomic unit, method, unit of analysis, output type |
| **Can you TRACE it?** | Traceability | Evidence chain from output to source, aggregation hierarchy |
| **Does it SURVIVE scenarios?** | Coverage | Common cases, edge cases, adversarial cases |
| **Can a dev BUILD it?** | Implementability | One-sentence def, explicit deps, writable function signatures |
| **Does it CONNECT to the system?** | Integrability | Downstream consumers, feeding paths, signal gaps |

A dimension is **concluded** when all five questions are answered YES with specific, documented evidence.

### How SV6 Differs from SV1

SV1 said "Energy is solved, Information Density is not." But didn't define what "solved" means.

SV6 provides a **15-criteria checklist** that makes "solved" verifiable. Applied to what we have:

- **Energy**: 13/15 — near-complete, needs systematic edge/adversarial testing
- **Control**: 12/15 — close, needs edge testing and effect computation detail
- **Information Density**: 4/15 with strong scenarios — explored but operationally undefined
- **Intent**: 0/15 — not started

The checklist also reveals a general pattern: **we're good at scenarios and conceptual clarity, weak on aggregation hierarchies and implementation specs.** The scenarios phase is natural and intuitive. The formalization phase (aggregation, function signatures, feeding paths) requires more disciplined engineering work.

This checklist should be applied to every dimension going forward. When all dimensions pass, CDA is defined.