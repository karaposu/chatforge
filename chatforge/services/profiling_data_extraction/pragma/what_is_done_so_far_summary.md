# What Is Done So Far

Summary of everything produced in this design session. From the original CAF framework through sensemaking, stress testing, and refinement to PRAGMA.


## The Journey

Started with: **CAF (Conversation Anatomy Framework)**, 9 vague dimensions, no measurement specs, no implementation detail.

Ended with: **PRAGMA (Conversational Act Analysis)**, 7 well-defined dimensions, full measurement logic with code, stress-tested, named, and architecturally specified.


## Final Artifacts

### PRAGMA (the framework)

| File | What it is |
|---|---|
| `devdocs/pragma/pragma.md` | The main framework document. Architecture, 7 dimensions, two-tier cost model, implementation feasibility, evolution from CAF |
| `devdocs/pragma/missing_next_steps.md` | What's solid, what's missing, prioritized next steps |

### Topic Flow (shared infrastructure)

| File | What it is |
|---|---|
| `devdocs/topicflow/desc.md` | Topic Flow definition. Polyphonic music + river delta analogies. Identity/focus/state model, hierarchy, two-tier detection, upstream ordering |
| `devdocs/topicflow/sensemaking.md` | Why embeddings aren't enough, LLM detection needed, topic evolution, processing order |

### Dimension Full Definitions

Each dimension has three files: description, test cases, and detailed measurement logic with code.

**Energy (Expressed Involvement)**

| File | What it is |
|---|---|
| `devdocs/caf/new/full_definitions/energy/desc.md` | Full definition. 5 micro-signals, aggregation hierarchy, dependencies, consumers, APT connection |
| `devdocs/caf/new/full_definitions/energy/testcases.md` | 19 test cases (6 common, 8 edge, 3 adversarial, 2 aggregation) |
| `devdocs/caf/new/full_definitions/energy/detailed_measurement_logic.md` | 7-step pipeline with Python code. Mechanical proxies, triggers, LLM prompt, scoring, trajectory, asymmetry, output formats |
| `devdocs/caf/new/stress-test/energy/v1.md` | 9 stress tests (6 edge + 3 adversarial). Sarcasm, copy-paste, quoting, formulaic, emoji, passive-aggressive, performed involvement, strategic disengagement |
| `devdocs/caf/new/expressed_involvement.md` | Original concept document (updated with aggregation hierarchy and prompt refinements) |

**Control Distribution**

| File | What it is |
|---|---|
| `devdocs/caf/new/full_definitions/control/desc.md` | Full definition. 3 mechanisms (verbosity, topic direction, emotional register) + effect, silence as control, multi-party |
| `devdocs/caf/new/full_definitions/control/testcases.md` | 14 test cases (3 common, 5 edge, 3 adversarial, 2 aggregation) |
| `devdocs/caf/new/full_definitions/control/detailed_measurement_logic.md` | 6-step pipeline with code. Per-exchange detection, effect computation, silence detection, dyadic comparison, multi-party extension |
| `devdocs/caf/new/stress-test/control/v1.md` | 12 stress tests. Filibuster, silent treatment, question trap, emotional hijack, multi-party, performed submission, gaslighting, crowd pressure |
| `devdocs/caf/new/control_power_distribution.md` | Original sensemaking document (updated with 3 mechanisms + stress test refinements) |

**Information Density**

| File | What it is |
|---|---|
| `devdocs/caf/new/full_definitions/density/desc.md` | Full definition. 3 axes (specificity, novelty, relevance) + compression. No atomic semantic unit needed, fully mechanical |
| `devdocs/caf/new/full_definitions/density/testcases.md` | 14 test cases (3 common, 5 edge, 3 adversarial, 2 aggregation) |
| `devdocs/caf/new/full_definitions/density/detailed_measurement_logic.md` | 8-step pipeline with code. Specificity vector, novelty via embeddings, relevance via topic centroid, compression, aggregation |
| `devdocs/caf/new/information_density_scenarios.md` | 14 scenarios exploring what density means. Including signal gaps mechanism |
| `devdocs/caf/new/density_sensemaking.md` | Resolution: no atomic unit needed, 6 axes collapsed to 3+1, type and impact removed |

**Conversational Intent**

| File | What it is |
|---|---|
| `devdocs/caf/new/full_definitions/intent/desc.md` | Full definition. 12 goal-based categories, dual-layer (Signal + Interpretation), hidden intent via contradiction matrix, intent arcs (11 patterns), shift significance |
| `devdocs/caf/new/full_definitions/intent/testcases.md` | 24 test cases (10 classification, 4 hidden intent, 8 arc patterns, 5 mismatch, 2 aggregation) |
| `devdocs/caf/new/full_definitions/intent/detailed_measurement_logic.md` | 7-step pipeline with code. Piggybacked on EI call, contradiction matrix, transition significance, arc classification, mismatch computation, avoidance detection |
| `devdocs/caf/new/intent_scenarios.md` | 19 scenarios exploring intent. Updated with category mapping, methods/qualities/subtypes distinction |
| `devdocs/caf/new/intent_sensemaking.md` | Resolution: dual-layer, piggybacked on EI call, 12 categories with eligibility principle |
| `devdocs/caf/new/intent_cat_sensemaking.md` | Category eligibility: goals vs methods vs qualities. 6-question test |
| `devdocs/caf/new/sense_making_for_intent_definition_missing_parts.md` | Hidden intent (contradiction matrix), intent arcs (11 patterns), shift significance (transition weights) |


### Sensemaking and Design Documents

| File | What it covers |
|---|---|
| `devdocs/caf/old_def.md` | Original CAF: 9 dimensions, the starting point |
| `devdocs/caf/discussion.md` | Original CAF + APT discussion (the seed of everything) |
| `devdocs/caf/new/apt_layer.md` | APT theory: Attachment (charm, hope, fear) + Presentation (content, style, expressed frame). Three outputs |
| `devdocs/caf/new/caf_outputs.md` | Three parallel outputs: Behavioral Profiling, APT Inference, APT Profiling |
| `devdocs/caf/new/on_the_way_of_new_caf.md` | CAF dimension audit. 1 solid, 2 workable, 1 misplaced, 5 need rework |
| `devdocs/caf/new/topic_flow.md` | Original Topic Flow spec (pre-sensemaking) |
| `devdocs/caf/sensemaking.md` | CAF measurement problem sensemaking. Two-layer, multi-level, two-tier architecture |
| `devdocs/caf/sensemaking_topic_flow.md` | Topic Flow as missing foundation. Unlocks 5+ dimensions |
| `devdocs/caf/sensemaking_missing_foundations.md` | Other missing foundations: Turn-Taking, Valence, Referential Structure |
| `devdocs/caf/sensemaking_visible_invisible.md` | Visible vs invisible conversation. Four-layer architecture |
| `devdocs/caf/new/what_it_means_to_define_good.md` | 15-criterion checklist for dimension definition quality |
| `devdocs/caf/new/what_is_missing.md` | Status of each dimension (pre-full-definitions). Hypothesis: EI is the only atomic semantic unit needed |
| `devdocs/caf/new/cda_draft_v1.md` | First draft of renamed framework (CDA). Architecture, naming |
| `devdocs/caf/new/cda_draft_v2.md` | Second draft. Topic Flow extracted, Conversation Ground removed, Expressed Involvement + aggregation hierarchy |
| `devdocs/caf/new/naming_sensemaking.md` | Naming analysis v1: CDA, DICE, CODA, Conversation Cartography |
| `devdocs/caf/new/naming_sensemaking_v2.md` | Naming analysis v2: PRAGMA chosen. Goals vs methods vs qualities |


## Key Design Decisions Made

| Decision | What was chosen | Why |
|---|---|---|
| **Name** | PRAGMA (from Greek pragma, "deed, act") | Captures the action-focus: what people DO in conversation |
| **Architecture** | Three layers: Signal Layer, Dynamics Profile, Interpretation Layer | Different epistemological statuses (measurement, description, interpretation) |
| **Topic Flow** | Upstream shared infrastructure, not a PRAGMA dimension | Multiple systems (PRAGMA, CPDE-7) depend on it. Runs FIRST |
| **Energy atomic unit** | Expressed Involvement (5 micro-signals) | Energy is emergent from involvement trajectory, not directly measurable |
| **Control model** | 3 mechanisms (verbosity, direction, register) + effect | Independent mechanisms. Dominance is not control |
| **Density model** | 3 axes (specificity, novelty, relevance), no LLM needed | Fully mechanical. Signal gaps are the diagnostic output |
| **Intent model** | 12 goal categories, dual-layer, piggybacked on EI call | Goals not methods/qualities. Near-zero marginal cost |
| **Engagement + Interest** | Merged into Investment | Observable signals are the same for both |
| **Contextual Dimensions** | Reclassified as input metadata | Known before analysis, not measured from content |
| **Cost model** | One LLM call with three sequential outputs (Topic + EI + Intent) | Topic resolves first, PRAGMA uses context. Everything else mechanical |
| **Signal gaps** | General mechanism, not named individual gaps | Extensible, composable, non-interpretive |
| **Visible/invisible** | Architectural separation: Signal Layer measures visible, Interpretation Layer reveals invisible | Different confidence levels. Don't mix facts with interpretations |
| **Topic detection** | LLM required, not just embeddings | Embeddings catch breaks. LLM catches evolution |
| **Definition quality** | 15-criterion checklist across 5 categories | Measurability, traceability, scenario coverage, implementability, integrability |


## Numbers

| Metric | Count |
|---|---|
| Documents created | ~40 |
| Dimensions fully defined (desc + testcases + measurement logic) | 4 (Energy, Control, Density, Intent) |
| Dimensions with full stress tests | 2 (Energy, Control) |
| Total test cases across all dimensions | ~70 |
| Sensemaking analyses | ~10 |
| Intent scenarios | 19 |
| Information density scenarios | 14 |
| Named intent categories | 12 |
| Expressed Involvement micro-signals | 5 |
| Control mechanisms | 3 |
| Information Density axes | 3 + 1 supplementary |
| Intent arc patterns | 11 |
| LLM calls needed per message | 1 (three outputs sequentially) |
| Dimensions requiring LLM | 2 (EI + Intent, shared call) |
| Dimensions fully mechanical | 4 (Control, Density, Investment, Dialogic Function) |
| Dimensions computed from Topic Flow | 1 (Temporal Structure) |


## What Remains

See `missing_next_steps.md` for the full breakdown. In summary:

**Phase 1 (Complete Signal Layer):** Topic Flow implementation, Investment + Dialogic Function full definitions, unified LLM prompt, signal gaps spec.

**Phase 2 (Specify Upper Layers):** Interpretation Layer spec, APT Inference implementation, APT/Behavioral Profiling schemas.

**Phase 3 (Integration):** End-to-end example through full pipeline, integration stress test, output validation.

The foundation is solid. The signal layer is implementation-ready. The upper layers (composition, interpretation, profiling) need the same rigor applied next.