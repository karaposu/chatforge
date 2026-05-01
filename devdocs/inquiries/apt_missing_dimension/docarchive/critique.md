---
status: active
discipline: td-critique
inquiry: apt_missing_dimension
iteration: 1
---
# Critique: apt_missing_dimension

## User Input

`devdocs/inquiries/apt_missing_dimension/`

Contents consumed:
- `_branch.md` — the question and goal (integrate Self-Positioning into APT)
- `sensemaking.md` — committed SP as multiplicative modulator on Domain 1; dual character; distinct from Expressed Frame and Internal Frame; 4 open items
- `innovation.md` — 21 outputs, 13 survivors, three high-confidence clusters; material challenge to sensemaking's "modulator not domain" commitment

---

## Phase 0 — Dimension Construction

### Dimensions Extracted From Sensemaking

Eight evaluation dimensions, weighted by the user's stated valuation (primary: LinkedIn actionability; secondary: APT internal consistency; motivation: iterative addition, not replacement).

| # | Dimension | Success Criterion | Weight | Extracted From |
|---|-----------|------------------|--------|----------------|
| **D1** | **Explanatory Adequacy** | Explains the devaluation failure mode ("this guy doesn't deserve this" despite high charm/hope/fear) and predicts when it occurs | **CRITICAL** | Sensemaking C1, KI4, SV6 mechanism section |
| **D2** | **Structural Integration** | Integrates into `apt_layer.md` without breaking downstream outputs (Behavioral Profiling, APT Inference, APT Profiling); existing Domain 1 → Domain 2 flow remains coherent (possibly with upstream modulator) | **CRITICAL** | Sensemaking C6, user valuation (iterative addition) |
| **D3** | **Definitional Distinctness** | Clearly different from Expressed Frame (investment-asymmetry, external-only) and Internal Frame (tool); survives boundary cases that separate them | **CRITICAL** | Sensemaking Ambiguities 3, 4; SV6 architectural-placement section |
| **D4** | **Operational Testability** | Concrete detection rules mapping to PRAGMA signals or text features; falsifiable, not post-hoc rationalizable-to-anything | **CRITICAL** | Sensemaking Ambiguity 6, OI4 |
| **D5** | **User Actionability** | User can audit a message today against explicit criteria and get a diagnostic verdict (Try-Hard / Respected Expert / etc.) | **CRITICAL** | User's primary valuation (LinkedIn pattern) |
| **D6** | **Architectural Parsimony** | Minimum-viable spec surgery; concept count grows only by what the evidence justifies | MEDIUM | User's motivation (iterative, not replacement); FP of minimum complexity |
| **D7** | **Extensibility** | Accommodates future additions (other modulators, other axes) without forcing another restructure | MEDIUM | Sensemaking OI1 (possible future axes); Innovation 7.A (modulator-layer precedent) |
| **D8** | **Honesty** | Acknowledges what's unresolved (supplementary mechanisms' confidence level, APT-level doubt, empirical validation gaps) without over-claiming closure | MEDIUM | Critique-framework foundational principle; innovation's survival-bias flag |

### Dimension Validation

Checked each dimension against sensemaking's perspective coverage (Technical, Human, Strategic, Risk, Resource, Definitional, Ethical):

- **Technical / Logical** → D1, D3 cover this
- **Human / User** → D5 covers this
- **Strategic / Long-term** → D7 covers this
- **Risk / Failure** → D2, D8 cover this
- **Resource / Feasibility** → D6 covers this
- **Definitional / Consistency** → D3 (strong coverage — the decisive sensemaking perspective)
- **Ethical / Systemic** → partially in D8 (honesty about limits; prescriptive-vs-descriptive flagged)

**Coverage complete.** No sensemaking perspective lacks a critique dimension. No dimensions are irrelevant.

### Stakes Assessment

Medium-to-high stakes:
- Downstream outputs (BP, Inf, Prof) will be modified based on this decision
- Architectural commitment persists across future iterations
- User's diagnostic tool depends on the operational layer

Burden of proof: lean toward "guilty until proven innocent" on critical dimensions — demand defense to demonstrate viability explicitly on D1-D5.

---

## Phase 1 — Fitness Landscape

**Viable region:** All 5 critical dimensions PASS; medium dimensions PASS or defensibly refinable.

**Dead region (fatal):**
- FAIL on D1 (can't explain devaluation)
- FAIL on D2 (breaks downstream specs)
- FAIL on D3 (collapses into Expressed Frame or Internal Frame)
- FAIL on D4 (unfalsifiable / vague operationalization)
- FAIL on D5 (user can't apply it)

**Boundary region:** passes critical, caveats on D6-D8 (e.g., too invasive, brittle extensibility, partial closure).

**Unexplored region going into critique:** The "APT-level doubt" region flagged by innovation's Cluster 4 (three contrarians converging on "APT itself may be inadequate"). Innovation deferred this as out-of-scope.

---

## Phase 2 — Adversarial Evaluation

Candidates to evaluate (extracted from `innovation.md`):

| ID | Candidate |
|----|-----------|
| **A** | Path α — **Named Modulator** (sensemaking's preferred) |
| **B-full** | Path β-full — **Third Domain "Positioning"** with 3 axes (Self-Elevation + Relative-Position + Investment-Asymmetry) |
| **B-soft** | Path β-soft — **Rename Expressed Frame to Positioning** containing Self-Elevation + Investment-Asymmetry (no new domain) |
| **C** | Path γ — **Replace Expressed Frame with Self-Positioning** |
| **D** | Enriched mechanism (costly signaling + visible-need concealment as supplementary theories) |
| **E** | Pure-relational framing (SP is dyadic, not a trait; only APT Inference captures) |
| **F** | Trait-with-bearings framing (SP bearings = central tendencies across dyads) |
| **G** | Signal Catalog (5 inference signals — Withholding, Premise-Posture, Self-Justification-Density, Exit-Willingness, Rhythm-Comfort) |
| **H** | 2×2 Diagnostic Typology (Confident Selector / Respected Expert / Disengaged / Try-Hard) |
| **I** | APT-level doubt (Cluster 4) — flagged but out-of-scope |
| **N1-N4** | Naming candidates: Self-Positioning / Positioning / Non-Supplication / Standing |

---

### Candidate A — Named Modulator (Path α)

**Preview:** Likely viable. Minimum surgery. Sensemaking's preferred commitment. Innovation's 3-axes finding pushes it toward boundary.

**Prosecution (strongest case against):**

1. Innovation independently surfaced THREE candidate axes (Self-Elevation + Relative-Position + Investment-Asymmetry). Sensemaking's "one axis insufficient for a domain" was the *only* reason it stayed a modulator. That reasoning is now obsolete. A modulator with internal axes is definitionally a domain — calling it a modulator hides structure to preserve minimum surgery. This buys convenience today and forces a rewrite in 2-3 iterations when the axes are operationalized separately.
2. Relative-Position is dyadic, not individual. Placing it inside an individual's Self-Positioning (a modulator on that individual's attachment signal) is a category mistake. If Relative-Position is a real axis, the "Self-Positioning is an individual property" framing breaks — pushing toward Path β or E.

**Defense (strongest case for):**

1. The three proposed axes are not equivalent. Self-Elevation is the dual-character property sensemaking established. **Relative-Position is a measurement property** (how Self-Elevation is assessed — against whom), not a separate axis. Investment-Asymmetry was already in Expressed Frame; innovation re-categorized it but did not *prove* relocation is forced. The honest count is ONE axis (Self-Elevation) + measurement refinement + a pre-existing concept. One axis is not a domain.
2. Structural Integration dominates. Path α preserves existing output specs (BP, Inf, Prof), preserves Domain 1 → Domain 2 flow as a downstream relation, and respects the user's stated valuation of iterative addition. Path β requires cascading edits across every output spec and the PRAGMA→APT mapping.
3. Extensibility: naming SP as a modulator creates a clean slot for future modulators (Tempo, Affect, Coherence per innovation 7.A). Tempo clearly doesn't belong in a "Positioning" domain — which means Path β requires yet another restructure when Tempo is added. Path α scales better.

**Collision:**

- Prosecution's "3-axes = domain" point: partially true IF all three are genuine. Defense contests: Relative-Position is measurement, not axis; Investment-Asymmetry relocation is not forced. I'll concede here: Relative-Position is genuinely ambiguous (could be measurement property OR could be a distinct calibration axis — "how well you adjust for the specific dyad's level"). Even granting that, we have *two* axes at most (Self-Elevation + Relative-Calibration), both answering the same question class ("does this deserve respect?") — which argues for keeping them under one concept, not for splitting into a domain.
- Defense wins on Extensibility decisively.
- Defense wins on Structural Integration decisively.
- Prosecution's strongest argument becomes a REFINEMENT signal: the spec surgery for Path α must explicitly address the axis question, framing Self-Elevation as the single axis with Relative-Calibration as a measurement/adjustment property, not as a second independent axis.

**Position:**

- D1 Explanatory Adequacy: **PASS** (multiplicative gating + devaluation mechanism)
- D2 Structural Integration: **PASS** (strong)
- D3 Definitional Distinctness: **PASS** (with explicit Expressed Frame narrowing)
- D4 Operational Testability: **PASS** (with Candidate G integration)
- D5 User Actionability: **PASS** (with Candidate H integration)
- D6 Architectural Parsimony: **PASS** (strong)
- D7 Extensibility: **PASS** (strong)
- D8 Honesty: **PASS** (with explicit acknowledgment that Relative-Calibration may eventually promote to a second axis)

**Verdict: SURVIVE** — with one refinement target: the spec surgery must explicitly address how Relative-Calibration fits (as measurement property of Self-Elevation, not as independent second axis), and must acknowledge this framing could be revisited if future cases force a second axis.

---

### Candidate B-full — Third Domain "Positioning" with 3 Axes

**Preview:** Boundary-to-dead. Innovation's assembly leaned here; sensemaking explicitly warned premature.

**Prosecution:**

1. Three-domain restructure cascades. APT's output specs (BP, Inf, Prof) are built on two-domain structure. Adding a third domain means every output schema needs a third slot, every mapping from PRAGMA needs a third branch, every example needs rewriting. User's valuation was explicit: iterative addition, not replacement. Path β-full violates that directly.
2. The three axes are not genuinely three. Investment-Asymmetry is a relocation (not a discovery) — already captured in Expressed Frame. Relative-Position is a measurement property of Self-Elevation. If we subtract relocations and measurement properties, we're at ONE axis. Manufacturing domain density by reshuffling labels is status-quo-bias territory — the three-axis story sounds rigorous but collapses under inspection.
3. Evidence base is Level-1 (single transcript + user's LinkedIn observation). Promoting to a full third domain requires Level-3 evidence (multiple converging cases with clearly distinguished axes).

**Defense:**

1. Path β-full resolves APT's current quiet contradictions (Expressed Frame "not internal" vs Internal Frame existing; Domain 1 → Domain 2 flow vs presentation moves causing attachment). Structural debt paid now prevents larger debt later.
2. Three question classes justify three domains: Attachment (why stay), Positioning (deserves respect), Presentation (how transmitted). The symmetry is not invented.
3. Iterative addition doesn't mean never refactor. This *is* a refactor.

**Collision:**

- Prosecution's "axes aren't really three" holds after dimensional test. Granting at most two axes (Self-Elevation + Relative-Calibration), both in the same question class — not enough for a domain.
- Defense's "resolves contradictions" is true but overkill. The contradictions can be resolved by narrowing Expressed Frame and promoting Self-Positioning as a modulator — cheaper surgery, same structural result.
- Defense's "iterative ≠ never refactor" is true but evidence threshold matters. Level-1 evidence ≠ grounds for Level-3 restructure.

**Position:**

- D1 Explanatory Adequacy: PASS
- D2 **Structural Integration: FAIL** (cascade breakage; user valuation violated)
- D3 Definitional Distinctness: PASS
- D4 Operational Testability: PASS
- D5 User Actionability: PASS
- D6 **Architectural Parsimony: FAIL** (invasive surgery on Level-1 evidence)
- D7 Extensibility: BOUNDARY (Positioning domain doesn't cleanly accommodate Tempo/Affect/Coherence)
- D8 Honesty: BOUNDARY (over-claims closure on axis count)

**Verdict: KILL** on D2 (Structural Integration, critical) and D6 (Architectural Parsimony, medium).

**Seed extracted:** The two-axis insight (Self-Elevation + Investment-Asymmetry as orthogonal dimensions producing 4 quadrants) is real structural value. It doesn't require a new domain to preserve — it's captured by the *cross-product* of Self-Positioning (Path α's new concept) and Expressed Frame (narrowed to investment-asymmetry). The 4-quadrant diagnostic (Candidate H) is this seed made concrete.

---

### Candidate B-soft — Rename Expressed Frame to "Positioning" (2 axes, no new domain)

**Preview:** Variant of Path α with a bundling choice. Neither clearly better nor worse than α structurally.

**Prosecution:** What does "Positioning" add that Expressed Frame didn't? If it covers Investment-Asymmetry and Self-Elevation, that's just "Expressed Frame with one more thing in it." Under Path α those two are separate concepts with a clear cross-product (the 2×2). Under β-soft they're bundled, losing the crispness of the typology.

**Defense:** Single bundle is conceptually clean — one "Positioning" layer instead of two concepts (SP and Expressed Frame) that only make sense together. "Positioning" as a layer name signals frame-setting has multiple dimensions.

**Collision:** Both preserve the same content. The difference is whether Self-Elevation and Investment-Asymmetry live in one bundle (β-soft) or as two related concepts (α). For user actionability (the 2×2 diagnostic), they're equivalent.

**Position:**

- All dimensions: PASS or equivalent to α
- D7 Extensibility: slight weakness — "Positioning" bundle is harder to extend than "modulator slot" (same Tempo-doesn't-fit concern as B-full but milder)

**Verdict: REFINE → subsume into α.** β-soft is α with a naming cosmetic. If the user prefers "Positioning" as the bundle label over "Self-Positioning as separate concept," that's a cosmetic choice not a structural one. Path α can adopt this naming without architectural change.

---

### Candidate C — Replace Expressed Frame with Self-Positioning (Path γ)

**Preview:** Likely dead on D3 (loses dual-character insight).

**Prosecution:**

1. Path γ puts Self-Positioning inside Presentation (external-only) — directly contradicting sensemaking's Ambiguity 4 resolution that Internal Frame's demotion was too aggressive. The internal-driver layer is dropped.
2. "No concept growth" constraint is artificial. APT already has many concepts; adding SP with clear mechanism is correct specification, not bloat.
3. Path γ regresses to the exact framing sensemaking rejected (SP as external-only perceptual property).

**Defense:** Occam — don't multiply entities. Merge Expressed Frame and Self-Positioning into one concept.

**Collision:**

- Prosecution's "loses internal-driver" is a direct contradiction of sensemaking. Defense's retreat ("note internal state in a paragraph") is exactly the demoted Internal Frame framing sensemaking explicitly rejected.
- The CV mechanism test is decisive: pure-external behaviors without internal state misfire (try-hard, hostile, weird). Path γ can't explain this because it lost the internal layer.

**Position:**

- D1 **Explanatory Adequacy: FAIL** (can't explain why external move requires internal backing per CV mechanism)
- D2 Structural Integration: PASS
- D3 **Definitional Distinctness: FAIL** (collapses dual character)
- D4 Operational Testability: PASS
- D5 User Actionability: PASS
- D6 Architectural Parsimony: PASS (but at cost of correctness)
- D7 Extensibility: FAIL (locks architecture against future internal-driver concepts)
- D8 Honesty: FAIL (pretends closure contradicting sensemaking)

**Verdict: KILL** on D1 + D3 (both critical) + D7 + D8.

**Seed extracted:** The economy motivation is valid but misdirected. The actual concept-count savings is *narrowing Expressed Frame's scope*, not *eliminating it*. That savings is already captured in Path α.

---

### Candidate D — Enriched Mechanism (costly signaling + visible-need concealment)

**Preview:** Supplementary-layer survival if framed correctly.

**Prosecution:**

1. Two different mechanism stories in one bundle. Costly signaling = signal-reliability theory. Visible-need concealment = information-asymmetry theory. Not the same mechanism. Claiming both simultaneously is hand-waving.
2. Innovation's Cluster 3 was MEDIUM confidence (only 2 mechanisms converged). Promoting MEDIUM-confidence theory into the spec as if HIGH-confidence is survival-bias territory.

**Defense:**

1. The two mechanisms are complementary at different levels. Costly signaling explains *why the signal is credible* (you can't fake paying the cost). Visible-need concealment explains *what specifically is signaled* (absence of supplication). One is meta-explanation; the other is content. Both can be true without redundancy.
2. Framing: adopt as *candidate explanatory theories* (supplementary layer), not primary mechanism. Multiplicative gating stays primary. These are the richer *why* theories.

**Collision:** Defense holds if these are explicitly framed as supplementary with MEDIUM-confidence flags. Prosecution wins if they're promoted to primary without stronger evidence.

**Position:**

- All critical dimensions: PASS (if supplementary)
- D8 Honesty: PASS with explicit confidence flag

**Verdict: REFINE** — adopt as supplementary explanatory layer with MEDIUM-confidence flag. Document under "candidate mechanism theories (downstream validation needed)" not in the core mechanism spec.

---

### Candidate E — Pure-relational (dyadic, not individual)

**Preview:** Contrarian inversion. Likely kills on Structural Integration.

**Prosecution:**

1. If SP is purely relational and has no individual trait component, APT Profiling can't capture it at all — a first-class output is eliminated unilaterally. Cascade consequences across the architecture.
2. Evidence is thin: three contrarian mechanisms (Inversion 3.C + Domain Transfer 6.C + aligned with 3.A). Contrarian inversions' purpose is to destabilize baseline, not prove alternative. Convergent challenge ≠ evidence of the challenge's correctness.
3. Empirically, people DO have bearings. Some are consistently supplicating across relationships; others consistently elevated. Pure-relational denies observable reality.

**Defense:**

1. A softer version: bearings predict tendencies, but the enactment is always relational. APT Profiling reports tendencies (not fixed levels); APT Inference reports realized asymmetry. This is more honest and more robust than claiming absolute levels.

**Collision:**

- Pure-relational fails Structural Integration and contradicts observable trait-level patterns.
- Soft version (bearings-as-tendencies) is functionally equivalent to Candidate F.

**Position (pure-relational):**

- D2 **Structural Integration: FAIL** (breaks APT Profiling)
- D8 Honesty: BOUNDARY (over-claims purely relational)

**Verdict: KILL** on pure-relational. Soft version (bearings-as-tendencies) folds into Candidate F.

**Seed extracted:** The gauge/asymmetric-measurement insight (Cluster 2 HIGH-confidence convergence) is real and must be preserved. SP is *measured* as A-relative-to-B, not as A-absolute. That doesn't require pure-relational commitment; it's absorbed into Candidate F's operational definition.

---

### Candidate F — Trait-with-bearings (relational-expression-of-bearings)

**Preview:** Likely viable. Sensemaking's implicit default, strengthened by Cluster 2 insight.

**Prosecution:**

1. Weak operational definition. What's a bearing vs a per-interaction calibration? Without criteria, "bearing" becomes a bucket for anything.
2. Cluster 2's relational-gauge insight says SP is measured as asymmetry. If measurement is asymmetric, what does "bearing level" mean outside a specific dyad?

**Defense:**

1. Operational definition: **bearing = central tendency of measured SP across multiple dyads.** Analog: Big Five Openness is a trait even though it manifests situationally. Asymmetric measurement doesn't negate trait; the trait is the distribution of dyad-positions the person tends toward.
2. APT Profiling purpose is stable tendencies. Trait-with-bearings is what makes Profiling produce meaningful individual-level output.

**Collision:** Defense wins with explicit operational definition. Prosecution's concern becomes a specification requirement, not a kill.

**Position:** All dimensions PASS.

**Verdict: SURVIVE** — adopt with operational definition: *bearing = central tendency of dyad-specific measured SP across multiple relationships, aggregated longitudinally.*

---

### Candidate G — Signal Catalog (5 inference signals)

**Preview:** Likely viable. HIGH-confidence convergence (Cluster 1).

**Prosecution:**

1. Five signals may not be independent. Self-Justification-Density and Premise-Posture both measure message openings — possibly correlated. Risk of double-counting.
2. Ethology catalog (innovation 6.B) overlaps with these. Two parallel catalogs may contradict at boundaries.
3. "Exit-Willingness" requires longitudinal context; single-message detection is ambiguous.

**Defense:**

1. In-principle independence: Withholding = negative space; Premise-Posture = opening framing; Self-Justification-Density = explanatory clauses; Exit-Willingness = risk-taking in the move; Rhythm-Comfort = temporal relaxation. Distinct conceptual dimensions. Correlations are empirical questions, not in-principle failures.
2. Conjunction detector framing: HIGH-confidence SP-collapse requires MULTIPLE signals, not any single one. This provides robustness without requiring any signal to be determinative.
3. Ethology catalog absorbs: Rhythm-Comfort matches calm-low-frequency-vocalization; Withholding matches resource-confidence; Premise-Posture matches territory-taking. Not a parallel catalog — one is grounding.

**Collision:** Defense wins with conjunction-detector framing. Prosecution's correlation concern is a downstream empirical validation need, not a kill.

**Position:** All dimensions PASS.

**Verdict: SURVIVE** — adopt as inference signal set using conjunction-detector framing. Flag empirical independence validation as downstream work.

---

### Candidate H — 2×2 Diagnostic Typology

**Preview:** Likely viable. Direct user actionability.

**Prosecution:**

1. 2×2 typologies hide variance. High SP + low Investment might not be Confident Selector; might be contextual choice. Flattening to 4 archetypes risks oversimplification.
2. Respected Expert quadrant has huge internal variation (engaged-elevated can be many things).

**Defense:**

1. Diagnostic utility > theoretical completeness. User needs coarse-grained map applicable today. 2×2 captures the real failure mode (Try-Hard) vs target (Respected Expert).
2. Sub-typologies can emerge from longitudinal use. Start coarse; refine as cases don't fit.

**Collision:** Defense wins on user actionability. Prosecution's variance concern is a refinement signal, not a kill.

**Position:**

- D5 User Actionability: **PASS (strong)** — this is the most directly actionable candidate
- All others: PASS

**Verdict: SURVIVE** — adopt as diagnostic scaffold. Revisit after user applies it to 20+ LinkedIn messages to see if variance exceeds the 4 archetypes.

---

### Candidate I — APT-level doubt (Cluster 4)

**Preview:** Not a solution candidate. A scope flag.

**Prosecution:**

1. Out of scope. Question was how to integrate SP into APT, not whether APT is correct.
2. APT-inadequacy claim is from contrarian mechanisms whose *job* was to challenge baseline. Convergent challenge ≠ evidence.
3. User's valuation is iterative addition, not replacement.

**Defense:**

1. Three independent mechanisms converging on APT-inadequacy is signal, not noise. Innovation self-flagged "partial survival-bias risk" — deferring as out-of-scope could be comfortable dismissal.
2. Flagging for future iteration is honest; ignoring is not.

**Collision:** Defense correct that the signal should be flagged. Prosecution correct it's not actionable now.

**Position:** Not evaluable as a solution. It's a coverage-map note.

**Verdict: FLAG, NOT KILL** — record in Open Questions and Coverage Map with explicit **reopening conditions:**
- If empirical cases emerge where SP collapse occurs *without* low charm/hope/fear → the substrate theory (Resonance + Positioning as fundamentals; Charm/Hope/Fear as emergents) may be needed.
- If the 5-signal catalog fails to detect SP in cases the user's intuition identifies clearly → underlying theory may be too thin.
- If future inquiries reveal additional modulators (Tempo, Affect, Coherence, Resonance) and their relationships become structurally constrained → a substrate reframe may be forced.

---

### Naming Candidates (N1-N4)

**N1 — Self-Positioning** (primary working name)

- Prosecution: Generic term, used in branding/career coaching. Semantic collision risk.
- Defense: Captures vertical (elevation) + stable-bearing quality. APT-specific definition disambiguates.
- **Verdict: SURVIVE** — keep as primary.

**N2 — Positioning** (umbrella if Path β adopted)

- Path β KILLed → N2 only survives as β-soft naming variant.
- **Verdict: REFINE** — available as alternative label if user prefers single-word bundle.

**N3 — Non-Supplication** (mechanism-emphasizing)

- Prosecution: Negative definition (named by absence). Doesn't capture positive dimension.
- Defense: Mechanism-accurate (visible-need concealment IS the mechanism).
- **Verdict: REFINE** — strong axis name but weak as umbrella. Could name the *mechanism* within SP, not the umbrella concept.

**N4 — Standing** (bearings + perception)

- Prosecution: Ambiguous with rank/legal usage. Less precise.
- Defense: One-word clean. Captures social-elevation without prescriptive tone.
- **Verdict: REFINE** — cleaner but less precise. Keep as alternative if user prefers one-word terms.

**Final naming verdict:** N1 (Self-Positioning) primary, N2 available as β-soft variant, N3/N4 as alternatives.

---

## Phase 3.5 — Assembly Check

Surviving/refined candidates: **A, D (supplementary), F, G, H, N1.**

Do they combine into an emergent architecture?

**Yes — they assemble into a complete specification.** Call it **ASPA: APT Self-Positioning Addition.**

### ASPA — The Assembled Proposal

**1. Name**
- **Self-Positioning** (primary; umbrella concept)
- **Self-Elevation** (the internal axis within Self-Positioning)
- Alternatives noted: Standing (one-word), Non-Supplication (mechanism-emphasizing)

**2. Architecture (Path α)**
- New section "Self-Positioning" inserted between Domain 1 and Domain 2 in `apt_layer.md`
- Expressed Frame narrowed to investment-asymmetry only, with cross-reference to Self-Positioning
- "What's Not a Domain But Matters" amended: Internal Frame's generic demotion stands, but Self-Elevation component is promoted to first-class under Self-Positioning
- Causal order updated: Self-Positioning sits upstream of both Domain 1 (in them) and Domain 2 (by you)
- Relative-Calibration framed as measurement property of Self-Elevation, not as independent second axis (open for revisit if future evidence forces separation)

**3. Mechanism**
- **Primary:** Multiplicative gating — `Attachment ≈ f(charm, hope, fear) × g(SP)`. Failure mode: devaluation ("this guy doesn't deserve this" despite high attachment values).
- **Supplementary (MEDIUM confidence, flagged):** Costly signaling (SP works because willingness-to-risk-exchange is a credible signal) + visible-need concealment (SP works because low visible-need prevents value-destroying neediness signals).

**4. Trait Structure**
- Individual-with-bearings
- Operational definition: *bearing = central tendency of measured SP across multiple dyads, aggregated longitudinally*
- APT Profiling reports bearings; APT Inference reports realized asymmetry in specific dyads
- Measurement is always asymmetric/relational (SP of A-relative-to-B, never absolute)

**5. PRAGMA Inference**
- Five-signal conjunction detector:
  1. **Withholding-Signal** — what was NOT said (negative space)
  2. **Premise-Posture** — opening framing (requesting-permission vs selecting vs offering vs asserting)
  3. **Self-Justification-Density** — clauses-per-message explaining why speaking / why qualified
  4. **Exit-Willingness** — risk-taken in the move (terminable-close, disagreement, selectivity)
  5. **Rhythm-Comfort** — unrushed temporal pattern
- Conjunction logic: HIGH-confidence SP detection requires multiple signals
- Empirical independence validation flagged as downstream work

**6. User-Facing Diagnostic (LinkedIn case)**
- **Five-question audit** for outgoing message:
  1. Does my premise request permission or select/offer?
  2. How many clauses explain why I'm writing?
  3. Do I elaborate beyond what the point requires?
  4. Does my close allow them to not reply?
  5. Am I willing to not get a response? (And does that show?)
- **2×2 mapping:**

| | Low Investment | High Investment |
|---|---|---|
| **High Self-Elevation** | Confident Selector | **Respected Expert** ← target |
| **Low Self-Elevation** | Disengaged | **Try-Hard** ← user's current failure mode |

**7. Acknowledged Limits (D8 Honesty)**
- Supplementary mechanisms (costly signaling, visible-need concealment) are MEDIUM-confidence; primary mechanism is multiplicative gating
- Signal independence is in-principle defensible but not empirically validated
- APT-level doubt (Cluster 4) is out-of-scope with explicit reopening conditions
- 2×2 typology may require sub-typologies after usage reveals variance
- Relative-Calibration is framed as measurement property; future evidence may force promotion to a second independent axis

### Assembly Evaluation (all 8 dimensions)

- D1 Explanatory Adequacy: **PASS** — multiplicative gating explains devaluation; supplementary mechanisms provide *why* the gating works
- D2 Structural Integration: **PASS** — minor surgery; no output spec breakage; Domain 1 → Domain 2 flow preserved with SP added upstream
- D3 Definitional Distinctness: **PASS** — distinct from narrowed Expressed Frame; distinct from Internal Frame (load-bearing not tool); cross-product produces the 2×2 typology
- D4 Operational Testability: **PASS** — 5-signal conjunction detector; empirical validation path specified
- D5 User Actionability: **PASS (strong)** — 5-question audit directly applicable to LinkedIn messages today
- D6 Architectural Parsimony: **PASS** — minimum viable addition; one new concept, one narrowing, one section amendment
- D7 Extensibility: **PASS** — modulator slot accommodates future Tempo/Affect/Coherence additions without restructure
- D8 Honesty: **PASS** — confidence levels flagged; reopening conditions specified; supplementary theories bounded

**Assembly Verdict: SURVIVE — clean, no critical-dimension caveats.**

---

## Phase 4 — Coverage + Convergence

### Accumulator Update

| Candidate | Verdict | Primary reason |
|-----------|---------|----------------|
| A (Path α) | SURVIVE | Passes all critical; refinement: Relative-Calibration framing |
| B-full (Path β 3-axis) | KILL | D2 Structural Integration + D6 Parsimony |
| B-soft (rename Expressed Frame) | REFINE → subsume into α | Cosmetic variant of α |
| C (Path γ replace Expressed Frame) | KILL | D1 Explanatory + D3 Distinctness + D7 Extensibility + D8 Honesty |
| D (enriched mechanism) | REFINE | Adopt as supplementary with MEDIUM-confidence flag |
| E (pure-relational) | KILL | D2 Structural Integration |
| F (trait-with-bearings) | SURVIVE | With operational definition (central tendency across dyads) |
| G (5-signal catalog) | SURVIVE | With conjunction-detector framing |
| H (2×2 diagnostic) | SURVIVE | User actionability |
| I (APT-level doubt) | FLAG | Not a candidate; coverage-map note with reopening conditions |
| N1 Self-Positioning | SURVIVE | Primary name |
| N2 Positioning | REFINE | Alternative label for β-soft naming variant |
| N3 Non-Supplication | REFINE | Axis-level mechanism name alternative |
| N4 Standing | REFINE | One-word alternative |
| **Assembly (ASPA)** | **SURVIVE** | **Clean across all 8 dimensions** |

### Coverage Assessment

Regions evaluated:
- ✓ Minimum-surgery modulator path (Path α)
- ✓ Invasive-domain path (Path β-full, β-soft)
- ✓ Replacement path (Path γ)
- ✓ Mechanism enrichment layer
- ✓ Trait-structure options (pure-relational vs bearings)
- ✓ Operational signal catalog
- ✓ User-facing diagnostic
- ✓ Naming variants

Regions flagged but not evaluated:
- APT-level restructure (Cluster 4) — explicitly out-of-scope with reopening conditions

Regions genuinely unexplored:
- Cross-modal PRAGMA signals (non-text SP signals like tone, facial expression in voice/video PRAGMA) — not relevant to user's LinkedIn scope
- Cultural variation in SP calibration — noted for future

No unexplored regions adjacent to viable regions. Coverage sufficient for the inquiry's scope.

### Convergence Assessment

- **Clean SURVIVE exists:** Yes — the Assembly (ASPA) with no critical-dimension caveats
- **Landscape stability:** Viable region clearly α+enrichments; dead regions clearly β-full/γ/pure-relational; boundary positions resolved via Assembly
- **New-information rate:** Adversarial testing surfaced one substantive refinement (Relative-Calibration framing in Path α); no new regions discovered
- **Rate of change:** Stable — iteration 1 produced a clean answer

### Signal: **TERMINATE**

Convergence criteria met:
- [x] At least one SURVIVE with no critical caveats (Assembly / ASPA)
- [x] Landscape stable across iteration
- [x] No viable unexplored regions
- [x] Coverage sufficient for the stated scope

The inquiry has a clean answer ready to go to Finding.

---

## Convergence Telemetry

- **Dimensions evaluated:** 8 / 8. All 5 critical covered for every candidate. **YES**
- **Adversarial strength:** **STRONG**. Every prosecution constructed would give the candidate's strongest advocate pause (e.g., the "3-axes = domain" challenge to Path α forced a substantive Relative-Calibration refinement; the "loses internal-driver" challenge to Path γ was a decisive KILL).
- **Landscape stability:** **CHANGED** on one dimension (Path α refined to explicitly address the axis question, not accepted as-written); **STABLE** on all others. The viable region is confirmed, not discovered.
- **Clean SURVIVE:** **YES** — Assembly (ASPA) has no critical-dimension caveats.
- **Failure modes observed:** None critical. Watch list:
  - *Survival bias* — partial risk acknowledged (Cluster 4 APT-level doubt deferred as out-of-scope). Mitigated by explicit reopening conditions and Open-Questions entry.
  - *False convergence* — ruled out: genuine clean SURVIVE exists; sensemaking's "premature new domain" warning was empirically confirmed by dimensional failure of Path β-full.
- **Overall: PROCEED** — sufficient dimension coverage + strong adversarial testing + clean SURVIVE candidate. Ready for MVL to write Finding.

---

## The Answer (for MVL / Finding)

**The concept:** Self-Positioning — a multiplicative modulator on APT's Domain 1 (Attachment), with Self-Elevation as its internal axis and five-signal external correlates. Dual-character. Upstream of both existing domains.

**The architecture:** Path α (Named Modulator between Domain 1 and Domain 2; Expressed Frame narrowed to investment-asymmetry; "What's Not a Domain" amended to promote Self-Elevation component specifically).

**The mechanism:** Primary — multiplicative gating producing devaluation when collapsed. Supplementary — costly signaling + visible-need concealment (MEDIUM confidence, flagged).

**The detection:** Five-signal conjunction detector (Withholding / Premise-Posture / Self-Justification-Density / Exit-Willingness / Rhythm-Comfort).

**The diagnostic:** Five-question audit → 2×2 typology. User's LinkedIn failure mode is Try-Hard; target is Respected Expert.

**What's open (honestly flagged):**
- Relative-Calibration framing (measurement property vs independent axis) — revisit if future evidence forces separation
- Signal independence — empirical validation needed
- Supplementary mechanisms — MEDIUM confidence until validated
- APT-level doubt (Cluster 4) — out-of-scope now with explicit reopening conditions
