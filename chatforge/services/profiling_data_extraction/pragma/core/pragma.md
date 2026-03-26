# PRAGMA: Conversational Act Analysis

Analyzing what people DO in conversation. Their involvement, control moves, substance, and intent. Revealing both the visible dynamics and the invisible conversation beneath.


## The Problem We're Solving

Every day, billions of conversations happen in homes, offices, online forums, and chat interfaces. Yet despite their centrality to human experience, we lack a systematic way to understand what's actually happening in these exchanges.

Current approaches fall short:
- **Sentiment analysis** tells you "positive" or "negative" but not who controls, who's hiding intent, or why the energy shifted
- **Keyword extraction** captures what's mentioned but not what's being done with those mentions
- **Content extraction** (like CPDE-7) tells you what people say about themselves but not how the conversation itself unfolds
- **Human intuition** recognizes dynamics but can't quantify, compare, or scale them

What's missing: a system that reads what people **DO** in conversation, their behavioral moves, strategies, and relational dynamics, separately from what they **SAY**.


## What PRAGMA Is

In linguistics, the study of what people DO with language (as opposed to what the language literally means) is called **pragmatics**. The Greek root is **πρᾶγμα (pragma)**, meaning "deed, act, a thing done."

PRAGMA analyzes the conversational acts performed by each participant. Not the content of what's said, but the behavioral dynamics of HOW the exchange unfolds.

Every utterance in a conversation IS an act. It informs, challenges, deflects, supports, controls, tests, reveals, or conceals. PRAGMA measures these acts across multiple dimensions and reveals both what's happening on the surface and what's really going on underneath.

**The core distinction:**

| System | What it reads | Analogy |
|--------|-------------|---------|
| CPDE-7 (Content Extraction) | What people say about themselves: facts, opinions, desires | Reading a diary |
| PRAGMA (Conversational Act Analysis) | What people DO in conversation: involvement, control, substance, intent | Watching a dance |

Same conversation, orthogonal analyses:

```
Message: "I'm a 34-year-old engineer, and I've been 
          thinking about this nonstop since we talked."

CPDE-7 extracts (what they SAY about themselves):
  → Core Identity: age=34, profession=engineer
  → Temporal Involvement: "thinking about this nonstop"
  → Life Narrative: engineering background

PRAGMA measures (what they DO in the conversation):
  → Expressed Involvement: HIGH
      Self-Reference Intensity: invested
        ("I'm a 34-year-old engineer" = identity at stake,
         "I've been thinking" = personal experience shared)
      Evaluative Force: absent
        (describes self and state but doesn't judge anything
         as good/bad/great/terrible. Sharing, not evaluating)
      Temporal Involvement: consuming
        ("nonstop since we talked" = this topic occupies them
         beyond this message, extending into past days)
      Reactive Disruption: absent
        (not being surprised or changed by the conversation
         right now. Reporting an existing state, not reacting
         to something new)
      Urgency Signal: absent
        (no time pressure, no imperative, no "we need to")
  → Dialogic Function: [sharing experience, transmitting, affirming]
      sharing: "I've been thinking about this nonstop"
      transmitting: "I'm a 34-year-old engineer" (factual info)
      affirming: "nonstop since we talked" (validates prior exchange)
  → Intent: inform (confidence 0.8)
      explanation: "Sharing personal background + signaling 
      deep engagement with the topic"
  → Investment: high (elaboration, self-disclosure, unsolicited detail)
  → Information Density (single LLM call):
      Specificity:
        entity: high ("engineer" = profession named)
        temporal: absent (no time references)
        quantitative: moderate ("34" = one number)
        action: absent (no concrete actions described)
        combined: moderate
      Novelty: requires prior messages in segment
      Relevance: requires active topic context
      Compression: low (moderate specificity across 15 words) [derived]
  → Control signals: no redirect attempt, no verbosity dominance
```


## The Two Conversations

Every conversation has two layers:

**The visible conversation** is what observably happened. Who said what, when, how much, what topics were discussed, what functions each message performed. Measurable, factual, verifiable.

**The invisible conversation** is what was really going on. Who was actually controlling the exchange, whose intent was hidden, where the emotional dynamics were heading, what strategic moves were being made. Interpretive, composed from patterns, confidence-scored.

PRAGMA separates these architecturally. The Signal Layer measures the visible. The Interpretation Layer reveals the invisible. They have different epistemological statuses (facts vs interpretations) and should never be confused.


## Architecture

PRAGMA has three internal layers, consuming from two external inputs:

```
┌─────────────────────────────────────────────────────────────┐
│                     RAW CONVERSATION                        │
│                (messages, timestamps, metadata)              │
└─────────────────────────────────────────────────────────────┘
       │              │                       │
       ▼              ▼                       ▼
┌────────────┐  ┌───────────┐          ┌───────────┐
│  MESSAGE   │  │  TOPIC    │          │  CPDE-7   │
│ PROPERTIES │  │  FLOW     │          │ (content  │
│ (preprocess│  │ (shared   │          │ extraction│
│  metadata) │  │  infra)   │          │ separate) │
└─────┬──────┘  └─────┬─────┘          └───────────┘
      │               │
      └───────┬───────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                        PRAGMA                               │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              SIGNAL LAYER                             │  │
│  │              (the visible conversation)               │  │
│  │                                                       │  │
│  │  Per-message signals + per-segment computations       │  │
│  │  Epistemological status: MEASUREMENT                  │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              DYNAMICS PROFILE                         │  │
│  │              (LLM-composed per segment)               │  │
│  │                                                       │  │
│  │  Composes Signal Layer aggregations into natural      │  │
│  │  language descriptions of what's happening            │  │
│  │  Epistemological status: DESCRIPTION                  │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              INTERPRETATION LAYER                     │  │
│  │              (the invisible conversation)             │  │
│  │                                                       │  │
│  │  Query-driven, confidence-scored, on-demand           │  │
│  │  Epistemological status: INTERPRETATION               │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
      Behavioral          APT               APT
      Profiling         Inference          Profiling
```

**Facts are verifiable. Measurements are scorable. Descriptions are composable. Interpretations are debatable.** Each layer depends on the layers below it. Each has a different confidence level.


## External Inputs

### Message Properties

Preprocessing step that extracts and computes raw properties from each message. No interpretation.

- Extracted: sender, timestamp, text, word count
- Computed: response latency, position in conversation, gap since own last message, silence detection

Cost: Zero (arithmetic on message fields).

### Topic Flow

Shared infrastructure that tracks what is being discussed: how topics bloom, persist, interleave, fade, and return. Sits beneath both PRAGMA and CPDE-7 as a foundational service.

PRAGMA consumes from Topic Flow:
- Segment boundaries (where dominant topics change)
- Topic attribution (who introduced, continued, shifted, abandoned each topic)
- Per-participant topic behavior

Topic Flow is defined separately. It is not a PRAGMA dimension. It is infrastructure.


## The Seven Dimensions

PRAGMA measures seven dimensions, each answering a different question about what participants are DOING in conversation.

### 1. Dialogic Function: What is this message doing?

The action performed by each message: Challenging, Co-creating, Explaining, Sharing, Affirming, Transmitting, Querying, Echoing.

A message can blend functions. The system preserves this richness rather than forcing single classification.

**Unit:** Per message.
**Method:** LLM multi-label classification.
**Key insight:** The only dimension that was always well-defined from the original framework.

### 2. Expressed Involvement (Energy): How present is the speaker?

The degree to which the speaker's self is present and activated in what they're saying. Not word count, not punctuation. The semantic reality of how much the speaker is IN the message.

**Atomic unit:** Five micro-signals: Self-Reference Intensity, Evaluative Force, Temporal Involvement, Reactive Disruption, Urgency Signal.

**Unit:** Per message (5 micro-signals), aggregated per topic segment per participant.
**Method:** LLM extraction (5 micro-signals per message).
**Key insight:** Energy is not a primitive. It's emergent from involvement trajectory. "High energy" was vague because it collapsed intensity and direction. Involvement is the atomic measurement; energy is the trajectory computed from it.

### 3. Control Distribution: Who determines what happens next?

Who controls the conversation, through what mechanism, and how successfully.

**Three independent mechanisms:**
- **Verbosity control**: who takes space (how much)
- **Topic direction control**: who steers what's discussed (what)
- **Emotional register control**: who sets the mood (how it feels)

Each mechanism has a measurable **effect** (success rate). Did the other participant follow or resist?

**Unit:** Per exchange (redirect-response pairs) and per segment.
**Method:** Computed from Topic Flow + Dialogic Function + Message Properties + Expressed Involvement. No additional extraction needed.
**Key insight:** Dominance is not control. The person talking most may have the least control. The system distinguishes observable dominance (verbosity) from actual control (effect of control attempts).

### 4. Information Density: How much substance is here?

How much new, relevant substance is in a message, measured through three core axes.

**Three axes (all LLM assessed per message, per participant):**
- **Specificity**: how concrete (entity, temporal, quantitative, action sub-dimensions)
- **Novelty**: how new within the topic segment
- **Relevance**: how on-topic relative to the active discussion

Plus **compression** (specificity per word, computed mechanically from LLM specificity output + word count).

**Unit:** Per message, per participant.
**Method:** Single LLM call per message assesses all three axes together. Specificity requires semantic judgment (action concreteness, entity reference quality), not just counting. Novelty requires paraphrase detection. Relevance requires contextual understanding.
**Key insight:** All three axes are semantic judgments. The diagnostic power is in **signal gaps**: high density + low relevance = deflection; high specificity + low novelty = repetition disguised as substance.

### 5. Conversational Intent: Why are they here?

What each participant is trying to accomplish, classified per message, tracked as trajectory.

**12 goal-based categories:** Inform, Discover, Convince, Connect, Request, Process, Perform, Control, Support, Avoid, Test, Co-create.

Categories are **goals**, not methods or qualities. "Teach" is a method of Inform. "Manipulate" is a quality detectable through signal gaps. "Vent" is a subtype of Process captured in the freestyle explanation.

**Unit:** Per message (classification), per segment (intent arc), per conversation (intent profile).
**Method:** LLM classification piggybacked on the Expressed Involvement call (near-zero marginal cost). Plus mechanical computations for hidden intent, shift detection, mismatch, and avoidance.
**Key insight:** Intent is the WHY dimension, the only one that tells you what the conversation is FOR. It's dual-layer: classification at Signal Layer, arcs and strategic readings at Interpretation Layer.

### 6. Investment: How much effort is being put in?

How much the participant is investing in this message, assessed semantically.

Investment measures whether the response exceeds, meets, or falls short of what the conversational moment called for. A copy-paste of 500 words is mechanically "high effort" but semantically zero. A carefully crafted 10-word answer to a complex question is mechanically "low effort" but semantically high.

Replaces the original framework's separate "Engagement Level" and "Interest Level." The observable signals are the same for both.

**Unit:** Per message.
**Method:** LLM semantic assessment.
**Key insight:** Investment is effort. Involvement is activation. They can diverge: high investment + low involvement = obligation (going through motions with effort). This gap is one of the most diagnostic signal gaps.

### 7. Temporal Structure: What shape does the conversation take?

How the conversation flows through topics over time. The narrative architecture of the exchange.

- Linear (A to B to C, progressive)
- Circular (returning to previous topics)
- Branching (multiple parallel threads)
- Fragmented (disconnected jumps)

**Unit:** Per conversation.
**Method:** Directly computed from Topic Flow (topic continuity graph shape).
**Key insight:** Structure reveals thinking patterns. Linear suggests goal-orientation. Circular may indicate processing or avoidance. Branching shows associative thinking.

### Context (input, not a dimension)

Environmental and relational metadata: setting (formal/informal), relationship type, mode (synchronous/asynchronous), modality (text/voice). Provided as input, not measured from conversation content.


## Signal Gaps: Where Dimensions Interact

Individual dimensions are informative. The **gaps between dimensions** are diagnostic.

A signal gap is the computed distance between two axes that should correlate but don't. The Signal Layer computes gaps mechanically. The Interpretation Layer reads what they mean.

| Signal Gap | High value means | Interpretation Layer reads as |
|---|---|---|
| `gap(density, relevance)` | Dense but off-topic | Deflection, impression management, avoidance |
| `gap(specificity, novelty)` | Specific but repetitive | Repetition disguised as substance |
| `gap(investment, involvement)` | High effort, low activation | Obligation, going through motions |
| `gap(verbosity, control_effect)` | Talking a lot but not controlling | Performing, not leading |
| `gap(involvement, control_effect)` | Highly activated but not controlling | Following with energy (charm signal) |
| `gap(classified_intent, behavioral_signals)` | Says one thing, signals say another | Hidden intent |


## The Interpretation Layer: The Invisible Conversation

The Interpretation Layer reads the Dynamics Profile (not raw scores) and reveals things no single dimension shows. It is query-driven, confidence-scored, and on-demand.

The Dynamics Profile provides the "what's happening" description. The Interpretation Layer provides the "what does it mean" reading. This separation matters: the Dynamics Profile LLM does comprehension (composing scores into descriptions). The Interpretation Layer LLM does interpretation (reading descriptions for subtext, strategy, and hidden dynamics).

**What it answers:**
- **Strategic dynamics:** "Who is actually controlling this conversation?" (The Dynamics Profile describes control patterns. The Interpretation Layer reads: "A guided B to this topic.")
- **Subtext:** "What's being communicated beneath the words?" (The Dynamics Profile describes topic shifts + involvement changes + dialogic patterns. The Interpretation Layer reads the subtext.)
- **Authenticity:** "Is this exchange genuine or performative?" (The Dynamics Profile describes investment/involvement gaps. The Interpretation Layer reads: "performative engagement.")
- **Hidden intent:** "What is this person really trying to accomplish?" (The Dynamics Profile describes intent classification + behavioral signals. The Interpretation Layer reads the contradiction.)

**Key principle: the Signal Layer measures, the Dynamics Profile describes, the Interpretation Layer interprets. Don't mix them.** Topic Flow correctly says "B introduced topic X." That's a fact. The Dynamics Profile says "B drives topic direction while A dominates verbosity." That's a composed description. The Interpretation Layer says "A guided B there." That's an interpretation. Each layer has a different confidence level.

APT (Attachment & Presentation Theory) lives in the Interpretation Layer as one specific interpretive framework, not the only one.


## Three Downstream Outputs

PRAGMA feeds three parallel outputs:

```
                   PRAGMA
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼

 BEHAVIORAL      APT            APT
 PROFILING     INFERENCE      PROFILING

 Individual     Relational     Individual
 (direct)       (per pair)    (aggregated)

 "How does      "What's       "What moves
  this person    happening     this person?"
  communicate?"  between
                 these two?"
```

**Behavioral Profiling.** Individual communication signatures. "This person consistently operates from high investment, asks qualifying questions, maintains symmetric control, escalates slowly." Aggregated across conversations. Changes slowly.

**APT Inference.** Relational dynamics between a specific pair. Uses Attachment & Presentation Theory (Attachment: charm, hope, fear. Presentation: content, style, expressed frame). Changes dynamically within a conversation.

**APT Profiling.** Individual attachment bearings and presentation tendencies aggregated from APT Inference observations across many relationships. "Gets charmed by expertise, hopes for mentorship, fears rejection. Frame collapses when challenged." Changes slowly.

All three feed into **Profile Grains** (the FOP pipeline), combining with CPDE-7's content-based profiles to produce comprehensive user understanding.


## How PRAGMA Relates to CPDE-7

They run in parallel on the same conversation. Different extractions, different purposes, same raw data:

```
                 RAW CONVERSATION
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
    ┌───────────┐ ┌──────────┐ ┌──────────┐
    │  CPDE-7   │ │  TOPIC   │ │  PRAGMA  │
    │           │ │  FLOW    │ │          │
    │  WHAT they│ │  (shared │ │  WHAT    │
    │  SAY about│ │  infra)  │ │  they DO │
    │  themselves│ │         │ │  in convo│
    └─────┬─────┘ └──────────┘ └─────┬────┘
          │                          │
          ▼                          ▼
    Context-based               Behavioral
    Profiling                   Profiling
    (domain clusters)           + APT
          │                          │
          └──────────┬───────────────┘
                     ▼
              Profile Grains
              (FOP pipeline)
```


## Implementation Feasibility

PRAGMA was designed with implementation feasibility as a core constraint. Every dimension has a specified measurement method, and the system is architected to minimize cost while maximizing signal.

### The Cost Model

| Component | What it does | Cost | When |
|---|---|---|---|
| **Message Properties** | Preprocessing: timestamps, lengths, sender | Zero | Every message |
| **Topic Flow** | Topic detection via LLM (three window sizes) | LLM call | Immediate: every message. Medium/Long: periodic |
| **Dialogic Function** | Multi-label classification via LLM | LLM call | Every message |
| **Investment** | Semantic effort assessment via LLM | LLM call | Every message |
| **Information Density** | All 3 axes (specificity, novelty, relevance) LLM assessed | LLM call | Every message |
| **Expressed Involvement** | 5 micro-signals via LLM | LLM call | Every message |
| **Intent** | 12-category classification via LLM | LLM call | Every message |
| **Control Distribution** | Computed from all above signals | Zero | Per segment |
| **Dynamics Profile** | LLM-composed description from aggregated signals | LLM call | Per segment |

Topic Flow runs first as separate infrastructure. PRAGMA dimensions consume its output.

### LLM Calls

The system needs **five LLM calls per message** at the Signal Layer, plus **one LLM call per segment** at the Dynamics Profile layer:

**Per message (Signal Layer):**
1. **Topic Flow** (separate infrastructure): what topic is this message about? Same, subtopic shift, or new? Runs first, produces segment boundaries and active topic identity.
2. **Expressed Involvement + Intent** (PRAGMA Signal Layer): 5 micro-signals + 12-category classification + explanations. Contextualized by Topic Flow output.
3. **Information Density** (PRAGMA Signal Layer): specificity + novelty + relevance, all three axes assessed together per message per participant.
4. **Investment** (PRAGMA Signal Layer): semantic effort assessment. How much effort went into this message relative to what the conversational moment called for.
5. **Dialogic Function** (PRAGMA Signal Layer): multi-label classification of what this message does (challenging, explaining, sharing, querying, etc.).

**Per segment (Dynamics Profile):**
6. **Dynamics Profile composition**: takes aggregated Signal Layer outputs for a segment (scores, trajectories, asymmetries, signal gaps) and composes a natural language description of what's happening. This description is what the Interpretation Layer reads.

Everything else (compression, control, temporal structure, aggregation, signal gaps) is computed mechanically from existing signals.

### The Aggregation Pipeline

Every dimension follows the same aggregation pattern:

```
Level 1: Per message, per participant → raw signals
Level 2: Per topic segment, per participant → trajectories, patterns
Level 3: Per topic segment, dyadic → asymmetries, mismatches
Level 4: Per conversation, per participant → cross-topic profiles
Level 5: Cross-conversation, per participant → behavioral signatures
```

Each level is computed from the level below. No level requires new extraction, only aggregation. This makes the system scalable: extract once (Level 1), compute everything else.

### Signal Gaps Are Cheap

Signal gaps (the most diagnostic outputs) are computed from existing dimension outputs. They require no additional extraction. The gap values feed into the Interpretation Layer as LLM queries that semantically identify inconsistencies between dimension readings. They produce the highest-value signals for APT.

### What This Means Practically

To run PRAGMA on a conversation:

1. **Preprocess**: compute Message Properties (zero cost)
2. **Topic Flow**: detect topics via LLM calls at three window sizes (separate infrastructure, runs first)
3. **EI + Intent**: one LLM call per message for Expressed Involvement (5 micro-signals) + Intent classification (12 categories), contextualized by Topic Flow output
4. **Density**: one LLM call per message for specificity + novelty + relevance, using Topic Flow segment context and prior messages
5. **Investment**: one LLM call per message for semantic effort assessment
6. **Dialogic Function**: one LLM call per message for multi-label function classification
7. **Mechanical computation**: compression, control mechanisms (from above signals, zero cost)
8. **Aggregate**: compute trajectories, arcs, asymmetries, signal gaps (zero cost, arithmetic)
9. **Dynamics Profile**: one LLM call per segment, composing aggregated signals into natural language description
10. **Interpret** (on-demand): query the Interpretation Layer for specific readings, reading the Dynamics Profile description (LLM, only when asked)

Steps 1 and 7-8 are cheap/free. Steps 2-6 are LLM calls per message. Step 9 is one LLM call per segment. Step 10 is on-demand.


## Dimension Summary

| # | Dimension | Question it answers | Method | Cost |
|---|---|---|---|---|
| 1 | **Dialogic Function** | What is this message doing? | LLM (multi-label classification) | LLM call |
| 2 | **Expressed Involvement** | How present is the speaker? | LLM (5 micro-signals) | LLM call |
| 3 | **Control Distribution** | Who determines what happens next? | Computed from signals | Zero |
| 4 | **Information Density** | How much substance is here? | LLM (3 axes in one call) | LLM call |
| 5 | **Conversational Intent** | Why are they here? | LLM (piggybacked on #2) | LLM call (shared) |
| 6 | **Investment** | How much effort is being put in? | LLM (semantic assessment) | LLM call |
| 7 | **Temporal Structure** | What shape does the conversation take? | Computed from Topic Flow | Zero |
| . | **Context** | What's the setting? | Input metadata | N/A |

**Signal Layer: 5 LLM calls per message (Topic Flow, EI + Intent, Density, Investment, Dialogic Function).**
**Dynamics Profile: 1 LLM call per segment (composition).**
**Interpretation Layer: on-demand LLM queries.**
**Control + Temporal Structure + compression: mechanical computation on existing signals.**


## Evolution From CAF

PRAGMA evolved from the Conversation Anatomy Framework (CAF) through systematic stress-testing and refinement:

| What changed | CAF (original) | PRAGMA (current) |
|---|---|---|
| **Dimensions** | 9 (most vague) | 7 computed + 1 input (all defined with measurement specs) |
| **Measurability** | 1 of 9 well-defined | All 7 have full definitions, test cases, and implementation logic |
| **Architecture** | Flat (all dimensions treated the same) | Three layers with different epistemological status |
| **Energy** | Vague scalar | Expressed Involvement (5 micro-signals) → trajectory |
| **Power** | Vague ("who controls") | Control Distribution (3 mechanisms + effect + silence) |
| **Information Density** | Vague ("depth of content") | Specificity + Novelty + Relevance (all computable) |
| **Intent** | Unaddressed | 12 goal categories + hidden intent + arcs + mismatch |
| **Engagement + Interest** | Two vague, overlapping dimensions | Merged into Investment (observable signals are the same) |
| **Contextual Dimensions** | Treated as measured dimension | Reclassified as input metadata |
| **Visible/invisible distinction** | Not recognized | Core architectural principle |
| **Topic Flow** | Implicitly needed but not identified | Extracted as shared infrastructure |
| **Signal gaps** | Not conceived | General diagnostic mechanism across all dimensions |
| **Cost model** | Not considered | 5 LLM calls per message (Topic Flow, EI+Intent, Density, Investment, Dialogic Function). Control, compression, temporal structure, aggregation mechanical |
| **Implementation spec** | None | Full measurement logic with code for every dimension |


## Learn More

All core specifications live in this directory (`devdocs/pragma/core/`). Topic Flow lives in `devdocs/topicflow/`.

### Signal Layer (7 Dimensions)

- **Expressed Involvement (Energy)**: `dimensions/energy/` (desc, testcases, measurement logic)
- **Control Distribution**: `dimensions/control/` (desc, testcases, measurement logic)
- **Information Density**: `dimensions/density/` (desc, testcases, measurement logic)
- **Conversational Intent**: `dimensions/intent/` (desc, testcases, measurement logic)
- **Investment**: `dimensions/investment/` (desc, testcases, measurement logic)
- **Dialogic Function**: `dimensions/dialogic_function/` (desc, testcases, measurement logic)
- **Temporal Structure**: computed from Topic Flow (no separate spec needed)

### Layers

- **Dynamics Profile**: `dynamics_profile.md` (LLM composition spec, prompt, output structure)
- **Interpretation Layer**: `interpretation_layer_prompts.md` (per-message + per-segment tension prompts)
- **Interpretation Layer Test Cases**: `interpretation_layer_testcases.md` (12 test scenarios)

### Downstream Outputs

- **APT Inference**: `apt_inference.md` (attachment reading, prompt, directional 5-level categorical output)
- **APT Profiling**: `apt_profiling.md` (individual profile schema, update prompt, trigger/blocker aggregation)
- **Behavioral Profiling**: `behavioral_profiling.md` (communication signature, mechanical aggregation + LLM composition)

### Theory and Infrastructure

- **APT Theory**: `apt_layer.md` (attachment & presentation theory, two domains, causal vs analytical order)
- **Topic Flow**: `devdocs/topicflow/` (desc, calculation_logic with three window prompts, topic definition, testcases)
- **Signal Gaps**: described within dimension docs and Interpretation Layer prompts