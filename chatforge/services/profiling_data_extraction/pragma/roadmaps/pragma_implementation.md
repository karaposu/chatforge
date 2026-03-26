# Roadmap: PRAGMA Design Specs → Usable Service in Chatforge

From fully specified design documentation to an importable, configurable Python service at `chatforge/services/profiling_data_extraction/pragma/`, following the same architectural patterns as CPDE-7.


## ASCII Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. Study     │     │ 2. Models    │     │ 3. Topic     │
│    CPDE-7    │────▶│    + Config  │────▶│    Flow Svc  │
│   DONE ✓     │     │   DONE ✓     │     │              │
│ ○ clear | S  │     │ ○ clear | M  │     │ ○ clear | M  │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │ 4. Signal    │     │ 5. Signal    │
                     │    Prompts   │────▶│    Service   │
                     │              │     │              │
                     │ ○ clear | M  │     │ ○ clear | L  │
                     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │ 6. Upper     │
                                          │    Layers    │
                                          │              │
                                          │ ○ clear | L  │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │ 7. End-to-   │
                                          │    End Test  │
                                          │              │
                                          │ ◐ foggy | M  │
                                          └──────────────┘
```


## Detailed Nodes


### Node 1: Study CPDE-7 Architecture Patterns

**Description:** Read the CPDE-7 implementation fully: `models.py`, `prompts.py`, `batch_prompts.py`, `batch_prompts_targeted.py`, `config.py`, `cpde7llmservice.py`, `__init__.py`. Understand how it structures prompts, handles configuration (which domains to extract), manages batch vs targeted extraction, and integrates with chatforge's service layer. Document the patterns PRAGMA must follow.

**Fuzziness:** clear
**Depends on:** none
**Produces:** understanding of the implementation patterns, file structure conventions, configuration approach, and service interface that PRAGMA must replicate
**Effort:** small
**Why this order:** Cannot build PRAGMA service without understanding the architecture it must fit into. Foundation.


### Node 2: PRAGMA Models + Config

**Description:** Create `pragma/models.py` with Pydantic models for all PRAGMA outputs: per-message signals (EI micro-signals, intent classification, density axes, investment score, dialogic function labels), per-segment aggregations, Dynamics Profile output, Interpretation Layer tension output, APT Inference output. Create `pragma/config.py` with configurable dimension selection (which of the 5 LLM calls to run, like CPDE-7's domain targeting).

**Fuzziness:** clear
**Depends on:** Node 1
**Produces:** `pragma/models.py` + `pragma/config.py` — the data structures and configuration that everything else builds on
**Effort:** medium
**Why this order:** Models define the shape of all data flowing through the system. Prompts produce these models. Services orchestrate around them. Must exist first.


### Node 3: Topic Flow Service

**Description:** Implement Topic Flow as a separate service or module. Translate the three-window LLM prompts from `devdocs/topicflow/calculation_logic.md` into Python. Handle the sliding window logic (immediate: every message, medium: every ~5, long: every ~10). Output: topic identity, segment boundaries, active topic per message. Topic Flow runs upstream of PRAGMA — PRAGMA consumes its output.

**Fuzziness:** foggy
**Depends on:** Node 1, Node 2
**Produces:** Topic Flow service that PRAGMA can call to get segment context for each message
**Effort:** medium
**Why this order:** Topic Flow runs FIRST in the pipeline. PRAGMA dimensions consume its output (segment boundaries, active topic). Must exist before Signal Layer can be tested meaningfully.

**What's foggy:** Should Topic Flow be a separate service or a module within PRAGMA? How does it persist segment state across messages? How does the sliding window interact with chatforge's message processing pipeline?


### Node 4: Signal Layer Prompts

**Description:** Translate all PRAGMA prompts from the design specs into Python prompt classes/functions, following CPDE-7's prompt patterns. Five prompt modules: EI+Intent (`detailed_measurement_logic.md`), Density (`detailed_measurement_logic.md`), Investment (`detailed_measurement_logic.md`), Dialogic Function (`detailed_measurement_logic.md`). Each prompt takes a message + context and produces structured output matching the models from Node 2.

**Fuzziness:** clear
**Depends on:** Node 2
**Produces:** `pragma/prompts.py` or `pragma/prompts/` directory with all Signal Layer prompts as Python code
**Effort:** medium
**Why this order:** Prompts are the core logic. They're fully specified in the design docs. This is translation, not design. Can be done in parallel with Node 3 since prompts don't depend on Topic Flow code, only on models.


### Node 5: Signal Layer Service

**Description:** Create the main PRAGMA service class (`pragma/pragma_service.py` or similar). Orchestrates: receive message → call Topic Flow → run configured LLM calls (up to 5) → compute mechanical dimensions (Control, Temporal Structure, compression) → aggregate per-segment → compute signal gaps → output combined Signal Layer result. Handles configuration (which dimensions to run). Handles the aggregation pipeline (Level 1-5).

**Fuzziness:** foggy
**Depends on:** Node 2, Node 3, Node 4
**Produces:** working Signal Layer that takes a message and produces dimension readings
**Effort:** large
**Why this order:** This is where everything comes together. Requires models (Node 2), Topic Flow (Node 3), and prompts (Node 4) to all exist. The largest and most complex node.

**What's foggy:** How to handle the aggregation state across messages (segment-level accumulation). How to manage the 5 parallel/sequential LLM calls efficiently. How to handle the configurable dimension selection at the service orchestration level.


### Node 6: Upper Layers (Dynamics Profile + Interpretation + APT)

**Description:** Implement the three upper layers: Dynamics Profile (LLM composition per segment), Interpretation Layer (per-message + per-segment tension checks), APT Inference (directional attachment reading). Each reads the Signal Layer output and produces its own output. These run after segment completion (not per-message). Include Behavioral Profiling and APT Profiling update logic.

**Fuzziness:** foggy
**Depends on:** Node 5
**Produces:** complete PRAGMA pipeline from raw message to APT Inference output
**Effort:** large
**Why this order:** Upper layers consume Signal Layer output. Cannot be built or tested without a working Signal Layer.

**What's foggy:** When exactly do upper layers trigger in chatforge's message processing lifecycle? How are segment completion events detected and propagated? How is cross-conversation profile state (Behavioral Profiling, APT Profiling) stored and retrieved?


### Node 7: End-to-End Integration Test

**Description:** Take a real multi-message conversation and run it through the complete pipeline: messages → Topic Flow → Signal Layer → aggregation → Dynamics Profile → Interpretation Layer → APT Inference. Verify: outputs match expected structure, dimensions produce sensible readings, the Dynamics Profile describes accurately, tensions are identified correctly, APT readings are grounded. Compare against the test cases in the design specs.

**Fuzziness:** foggy
**Depends on:** Node 5, Node 6
**Produces:** validated, working PRAGMA service ready for integration into chatforge's production pipeline
**Effort:** medium
**Why this order:** Integration testing must come last — it requires all components to exist.

**What's foggy:** What test conversation to use? How to evaluate "sensible readings" without human judgment? How to automate validation against the 12 Interpretation Layer test cases?


## Roadmap Summary

**Total nodes:** 7
**Clear:** 3 (Node 1, 2, 4 — study patterns, create models, translate prompts)
**Foggy:** 4 (Node 3, 5, 6, 7 — Topic Flow service, Signal Layer service, upper layers, testing)
**Unknown:** 0

**Recommended next action:** Node 1 (Study CPDE-7 patterns). It's clear, small effort, and everything depends on it. Then Node 2 + Node 4 can proceed in parallel.

**Biggest risk:** The foggy nodes (3, 5, 6) all involve integration with chatforge's service architecture, which we haven't studied yet. Node 1 may reveal constraints that reshape nodes 3-7. Run Node 1 first and re-assess.