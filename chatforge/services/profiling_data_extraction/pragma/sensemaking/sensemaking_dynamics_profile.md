# Sense-Making: Dynamics Profile

Structural sense-making analysis on the Dynamics Profile specification to identify gaps, missing details, and prompt design issues.


## SV1 — Baseline Understanding

The Dynamics Profile is a newly specified LLM composition layer that takes aggregated Signal Layer scores per topic segment and produces natural language descriptions. It sits between measurement (Signal Layer) and interpretation (Interpretation Layer). The core prompt instructs the LLM to "describe, don't interpret." The question is: what might we be missing, and how should the prompt be refined?


## Phase 1 — Cognitive Anchor Extraction

### Constraints
- C1: Must DESCRIBE, not INTERPRET. This is the hardest boundary to enforce.
- C2: Runs once per completed topic segment, not per message.
- C3: The Interpretation Layer is the primary consumer. It reads the `dynamics_profile` text.
- C4: Must handle the combinatorial space of 7 dimensions x 2+ participants.
- C5: Output must be concise (3-4 paragraphs).

### Key Insights
- K1: The Interpretation Layer prompts were written BEFORE the Dynamics Profile was conceived. They currently read raw dimension outputs, not the Dynamics Profile description. Consistency gap.
- K2: The example output already contains interpretation. "suggesting obligation or routine rather than genuine engagement" in notable_gaps.description is interpretation, not description.
- K3: The describe/interpret boundary is genuinely ambiguous. "B's involvement-investment gap is 0.38" is description. "The gap suggests obligation" is interpretation. But "gap between investment and involvement" already implies they SHOULD correlate, which is a theoretical claim.
- K4: Temporal Structure (dimension 7) is per-conversation, not per-segment. The Dynamics Profile is per-segment. Where does Temporal Structure show up?
- K5: The prompt includes raw numbers ("specificity 0.7"). This aids validation and precision.

### Structural Points
- S1: Three outputs: dynamics_profile (text), headline (summary), notable_gaps (structured).
- S2: Multiple downstream consumers with different needs.
- S3: The signal gaps are already computed mechanically before the DP runs. The DP describes them in context.

### Foundational Principles
- F1: Each layer has a different epistemological status. Facts, Measurements, Descriptions, Interpretations.
- F2: The Dynamics Profile is a REASONING STEP (chain-of-thought) that prepares data for interpretation.
- F3: Information should flow DOWN (aggregated) not UP (disaggregated) through layers.

### SV2

Three critical issues: (1) the Interpretation Layer prompts don't consume the DP yet, (2) the describe/interpret boundary leaks in the example, and (3) the DP is a lossy bottleneck — what it drops is lost to interpretation.


## Phase 2 — Perspective Checking

### Technical
- T1: The DP is lossy compression. Whatever the LLM doesn't mention is LOST to the Interpretation Layer. If the DP misses a subtle gap, interpretation can't find it.
- T2: The notable_gaps structured output partially mitigates T1. But only gaps > 0.3 are included.
- T3: Timing mismatch. Per-message tension checks run on raw signals (before DP exists). Per-segment checks should read the DP. But current per-segment prompt reads raw aggregations.

### Human / User
- H1: For human analysts, the headline + dynamics_profile IS the product. Readability and accuracy matter equally.
- H2: Including some numbers aids validation. Humans can check against raw data.

### Strategic
- ST1: Behavioral Profiling aggregates DPs across conversations. Descriptions need consistency across segments.
- ST2: Pure free-text is hard to aggregate programmatically. Semi-structured might be better for downstream.

### Risk
- R1: The describe/interpret boundary WILL leak. Every description implies interpretation. "B rehashes" implies repetition rather than thoroughness.
- R2: LLM might hallucinate dynamics not in the data. Need grounding instructions.
- R3: Short segments (2-3 messages) make trajectories meaningless. Prompt must handle this.

### SV3

Three major shifts: (1) lossy compression risk needs mitigation, (2) consistency for aggregation matters, (3) Interpretation Layer prompts need updating to consume the DP.


## Phase 3 — Ambiguity Collapse

### Ambiguity 1: Should the Interpretation Layer read the DP or raw signals?

**Resolution:** Both. The DP text is PRIMARY input for per-segment queries. The structured notable_gaps provides key numerical values. Per-message tension checks continue on raw signals (DP doesn't exist at message time).

**What is now fixed:** Per-segment Interpretation Layer prompt must consume the DP text.
**What is no longer allowed:** Per-segment interpretation reading raw JSON aggregations directly.
**What depends on this:** interpretation_layer_prompts.md per-segment prompt needs rewriting.

### Ambiguity 2: Does the DP describe or interpret?

**Resolution:** The boundary is a spectrum. The DP makes compositional observations (noting divergence) without causal claims (explaining why).

Allowed: "A's involvement is increasing while investment is decreasing. Gap magnitude: 0.38."
Allowed: "B's density is high but novelty is low, meaning prior points are being repeated with added detail."
Not allowed: "B appears to be performing engagement." (motive attribution)
Not allowed: "A is testing B's commitment." (strategic inference)

**What is now fixed:** "Indicating" factual consequences = description. "Suggesting" motives = interpretation.
**What depends on this:** The example output and prompt need fixing.

### Ambiguity 3: Should output include raw numbers?

**Resolution:** Yes, selectively. Key magnitudes, asymmetry scores, trajectory labels in prose. Not a data dump.

### Ambiguity 4: How to handle short segments?

**Resolution:** Segments with < 4 messages: trajectories are not computed. Focus on per-message signals. Note the limitation.

### SV4

The DP is a lossy but intentional compression. It produces the canonical description of segment dynamics. Interpretation Layer per-segment prompt must be rewritten to consume it. The describe/interpret boundary is enforced via compositional-yes, causal-no. Numbers included selectively. Short segments handled.


## Phase 4 — Degrees-of-Freedom Reduction

**Fixed:**
- DP is canonical input for per-segment Interpretation Layer queries
- Per-message tension checks continue to read raw signals
- Compositional observations allowed, causal claims not
- Key numbers included in prose
- Short segments (< 4 messages) get simplified treatment

**Eliminated:**
- Interpretation Layer reading raw JSON for per-segment analysis
- Pure free-text with no numerical grounding
- Motivational language in the DP

**Open:**
- Whether DP should have consistent sections for cross-segment aggregation
- How Temporal Structure (per-conversation) relates to per-segment DPs
- Whether notable_gaps stays structured JSON or folds into text

### SV5

Four concrete updates needed: (1) fix example output, (2) add short-segment handling, (3) add grounding instructions, (4) rewrite Interpretation Layer per-segment prompt. Plus add describe-vs-interpret examples to the prompt.


## SV6 — Stabilized Model

The Dynamics Profile is a **lossy, intentional, compositional compression** of Signal Layer aggregations. It is the canonical representation of "what happened in this segment" and the primary input for all per-segment interpretation.

### What changed from SV1

1. **A bottleneck with consequences.** What it drops is lost to interpretation. The prompt must be comprehensive about gaps and asymmetries.
2. **A boundary enforcer with leaky edges.** Perfect boundary is impossible. Fix is clear examples: compositional observations yes, causal claims no.
3. **A document with multiple consumers.** Structured notable_gaps serves machines, prose serves humans and interpretation.
4. **A trigger for upstream revision.** Interpretation Layer prompts must be updated to consume the DP.

### Action Items

| # | What | Where |
|---|---|---|
| 1 | Fix example output: remove interpretive language from notable_gaps | dynamics_profile.md |
| 2 | Add describe-vs-interpret examples to prompt | dynamics_profile.md prompt section |
| 3 | Add short-segment handling instruction | dynamics_profile.md prompt section |
| 4 | Add grounding instruction (only describe what data shows) | dynamics_profile.md prompt section |
| 5 | Update per-segment Interpretation Layer prompt to read DP text | interpretation_layer_prompts.md |
| 6 | Note that Temporal Structure feeds per-conversation summary, not per-segment DP | dynamics_profile.md |