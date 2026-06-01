---
status: active
discipline: innovation
inquiry: apt_context_layer
iteration: 1
---
# Innovation: apt_context_layer

## User Input

`devdocs/inquiries/apt_context_layer/`

Inputs consumed: `_branch.md`, `exploration.md`, `sensemaking.md`, `decomposition.md`. Adjacent: iteration-3.2 (`apt_modulator_landscape/finding.md`), iteration-3.2.1 (`attachment_variable_interactions/finding.md`).

---

## Direction (Intuition Component)

**Context (proximate concepts):** APT formula architecture (`f × g₁ × g₂ × g₃`); iteration-3.2.1 commitments (additive `f`, Signal Specificity, Sender-SP-from-style, MAGNITUDE/TYPE, Double-Collapse); iteration-3.2 Modulator Suite + Resonance + Cluster 4 conditions; killed candidates (P2-C threshold, B1 noise-attenuation); user's seed examples (Reddit stranger, friend with dates, nightclub SP/Hope tension).

**Valuation:** The structural refinements at three formula locations matter because they convert the user's lived intuition (something is missing in APT) into precise spec wording. Getting Gap 3's coupling rule right is the highest-stakes piece — it decides whether the spec stays at 3 modulators or expands. Getting Gap 1's framing right preserves the architectural minimalism that has held through five prior iterations. Getting Gap 2's threshold right rehabilitates a previously-killed candidate without reopening that kill's grounds.

**Motivation:** Iteration-3.3 should be tight and load-bearing. Each refinement should pull empirical weight (produce predictions 3.2.1 cannot make) and operationally hand off to PRAGMA. The output should be specifiable in one finding without spawning sub-iterations.

---

## Seeds (one per piece)

- **P1 seed (gap):** "`f` is implicitly a belief state but the spec writes it like a real-time signal stream. The Reddit/friend contrast forced this gap into view."
- **P2 seed (failure→reframe):** "P2-C threshold model was killed in 3.2.1 as empirically underdetermined. The Reddit case requires it; the right move is context-parameterization."
- **P3 seed (collision):** "Self-Positioning + Hope channel availability + approach act mode collide in approach contexts in a way the formula treats as independent multiplication."
- **P4 seed (question):** "What does iteration-3.3 predict that 3.2.1 cannot, and is the architecture still safe from Cluster 4 once all three refinements land together?"
- **P5 seed (constraint):** "How does this finding integrate with five prior iterations' worth of spec content without breaking established cross-references?"

---

## Phase 2 — Generate (mechanisms × pieces)

15 candidates total: 3 variants × 5 pieces. Mechanism distribution covers all 7.

### P1 — `f` as cumulative belief state

#### P1-A (generic) — "Definition-only clarification" [Constraint Manipulation]

**Mechanism:** Constraint Manipulation. Add the constraint "no new formal term may enter the formula." The clarification becomes a definitional sentence in the spec.

**Output:**
> "`f` represents the receiver's cumulative belief about the sender's Charm/Hope/Fear/Resonance at any moment in the interaction. This belief is updated by all available evidence — in-interaction signals, prior direct experience, third-party social proof, and channel/platform priors. The formula does not assume `f = 0` at interaction start. PRAGMA reads channel metadata and social-proof markers as additional inputs to the existing C/H/F/R variables; no formula change."

Plus an enumeration of the four evidence sources and a worked example (friend-with-many-dates: girls' f_Hope and f_Charm pre-loaded by social proof before any direct interaction).

#### P1-B (focused) — "Evidence ledger model" [Combination]

**Mechanism:** Combination. Belief-state + evidence-classes-as-ledger.

**Output:** Each f-variable functions as a ledger that aggregates signals from four evidence classes:
- *Interaction evidence* — current message + behavior in the live interaction
- *Prior-experience evidence* — history of past interactions with this sender
- *Social-proof evidence* — third-party signals (mutual friends' opinions, public reputation)
- *Channel-prior evidence* — default expectations from the platform context

Each class contributes additively to the variable's current value. The formula's `f(C,H,F,R)` is unchanged; the ledger is an explanatory model of HOW the variables get their values, exposed for PRAGMA implementation. PRAGMA's input pipeline becomes a four-source aggregator.

**Why combination:** "Belief state" + "evidence sources" + "ledger pattern" combine to produce a structure that's neither a formal decomposition nor a plain definition.

#### P1-C (contrarian) — "Reify f_prior as formal term" [Inversion]

**Mechanism:** Inversion. Invert sensemaking's claim that no new term is needed.

**Output:** Add `f_total = f_prior + f_interaction` as an explicit additive decomposition. The argument: without explicit decomposition, every PRAGMA evaluation silently aggregates prior-loaded and in-interaction evidence into one number, which makes attribution impossible. Bookkeeping cost is the price of trackability.

**Inversion depth check:** First-level inversion (component-level). Could go deeper: invert "f is generated from evidence" → "f is a static property updated by evidence" — but that doesn't fit attachment dynamics. Stay at first level.

---

### P2 — θ(context) parameter expansion

#### P2-A (generic) — "Channel taxonomy + qualitative θ ordering" [Lens Shifting]

**Mechanism:** Lens Shifting. Reframe killed P2-C under context-parameterization conditions.

**Output:**
- Updated specificity formula: `effective_magnitude = nominal × specificity if specificity ≥ θ(context); else 0`
- Channel taxonomy: cold-stranger-DM, warm-introduction, mutual-platform-match, existing-relationship, physical-proximity, public-figure-to-stranger
- Qualitative θ ordering: `θ_cold_DM > θ_warm_intro > θ_mutual_match > θ_existing_relationship > θ_physical_proximity`
- No quantitative ranges (deferred to empirical work; calibration methodology stated)
- Mixed-channel edge case: θ inherits from current channel; channel-shift mid-interaction triggers θ recalculation
- Worked example: Person A's specificity clearing θ_cold_DM; Person B's failing it
- Explicit P2-C rehabilitation note: previously-killed threshold model survives under context-parameterization

#### P2-B (focused) — "Signal-detection-theory port" [Domain Transfer]

**Mechanism:** Domain Transfer from Signal Detection Theory.

**Output:** Port SDT's four primitives:
- *Signal strength* = `nominal × specificity` (specificity-weighted signal already in 3.2.1)
- *Noise level* = a function of channel; cold DM = high noise (many similar messages); warm intro = low noise (single curated message)
- *Threshold* = receiver's discrimination threshold, set adaptively to noise level — this IS θ(context)
- *Bias* = receiver's prior willingness to engage — confirmed outside-formula (Cycle 7 pre-condition)

This grounds θ(context) in adjacent theory rather than treating it as ad-hoc. PRAGMA's channel classifier estimates noise-level; θ follows. Worked example uses ROC-style analysis: specificity must clear noise-level to register; warm-intro receivers operate at lower threshold because noise is lower.

**Why domain transfer:** SDT has 70+ years of formalism for the threshold + noise + signal triple. Importing the structure (not the binary classifier) gives APT's threshold model theoretical credibility instead of stipulation.

#### P2-C (contrarian) — "θ is per-receiver, not per-channel" [Inversion]

**Mechanism:** Inversion. Invert "θ is a channel parameter" → "θ is a receiver parameter."

**Output:** θ is a property of the receiver: each receiver has a personal noise floor that depends on attentional load, channel familiarity, saturation. Channel-level θ is just an empirical average across many receivers. The "right" model is per-receiver θ; channel taxonomy is a coarse aggregation.

**Inversion depth check:** Component-level inversion. Going deeper: "θ exists per-receiver" → "θ doesn't exist; receivers process signals continuously and the apparent threshold is an artifact of measurement." The deeper inversion contradicts both the friend-vs-Reddit empirical pattern and Person A's success on Reddit. Stays at component level.

---

### P3 — SP display mode + H_a coupling

#### P3-A (generic) — "Two named modes + coupling rule" [Combination]

**Mechanism:** Combination. Mode-state + H_a-availability.

**Output:**
- *Selective-engagement mode:* g₁ display through specific attention directed at this counterparty from the sender's own evaluation. Realizes H_a in `f` (by directing specific attention).
- *Withholding mode:* g₁ display through visible non-engagement / occupation with own-things / non-selective approach. Suppresses H_a in `f`.
- *Coupling rule:* In approach contexts, H_a in `f` is gated by g₁'s mode. Mode = withholding ⇒ H_a → 0 regardless of other H_a inputs. Mode = selective-engagement ⇒ H_a is realized at the level supported by other inputs.
- *Failure signature:* High g₁ × suppressed H_a → "not for me" read (active disqualification, structurally distinct from generic low-attachment).
- *Architectural status:* Coupling rule within g₁; NOT a new modulator; Modulator Suite stays 3-member.
- Worked example: nightclub case (withholding mode) + Reddit selective-vs-template case.

#### P3-B (focused) — "Approach act as multi-variable signal source" [Absence Recognition]

**Mechanism:** Absence Recognition. What was never explicitly named in prior iterations: the approach act itself is a signal-event with simultaneous f and g contributions.

**Output:** A new spec subsection "The Approach Act":
> "Selective initiation is itself a signal event. A specific approach contributes simultaneously to:
> - f_Charm (the sender displays initiation confidence — perceived self-worth)
> - H_a (the sender offers the possibility of specific continued attention)
> - g₁ (the sender acts from their own evaluation, not waiting for permission)
>
> Message specificity then determines how much of each contribution is realized. High specificity amplifies all three. Low specificity dilutes all three simultaneously — this is the Double-Collapse from the sender's perspective: one lever (specificity of engagement) controls both `f` and `g` layers."

This connects 3.2.1's Sender-SP-from-message-style and Double-Collapse mechanism with Gap 3's mode coupling, resolving the question of where H_a comes from baseline.

**Why absence recognition:** The phenomenon was visible in 3.2.1 but never named. This output names it.

#### P3-C (contrarian) — "Make it g₄: a new Mode modulator" [System-level Inversion]

**Mechanism:** System-level Inversion. Invert sensemaking's coupling-rule decision.

**Output:** Add g₄(Mode) to the Modulator Suite as a 4th member:
- g₁ becomes "SP-magnitude" (how much SP is displayed)
- g₄ becomes "SP-mode" (how SP is displayed: selective-engagement vs withholding)
- g₄ × f_Hope → realized H_a contribution
- Modulator Suite expands to 4: g₁(SP-magnitude), g₂(Coherence), g₃(EC), g₄(Mode)

**Inversion depth check:** First-level inversion (component → modulator). Could go deeper: "Mode is itself a property of the entire interaction-frame, not of g₁" — but that pushes toward substrate reframe, which Cluster 4 says is not warranted by current evidence.

---

### P4 — Synthesis: predictions + Cluster 4 + sequencing

#### P4-A (generic) — "Predictions table + Cluster 4 verdict + sequencing" [Extrapolation]

**Mechanism:** Extrapolation. Forward-project the architecture.

**Output:**

*Predictions iteration-3.3 makes that 3.2.1 cannot:*
| Gap | Prediction | Test |
|---|---|---|
| 1 | Elevated f_prior generates pre-interaction attachment; in-interaction quality bar to maintain is lower than to create | Social-proof manipulation: introduce sender via warm reputation vs cold; compare receiver's attachment formation curve |
| 2 | Identical-content message on cold DM fails where same content on warm intro succeeds | Channel-controlled specificity study: hold specificity constant, vary channel, observe registration |
| 3 | Selective-engagement-mode approach generates baseline attachment with modest other f-loadings; withholding-mode approach generates "not-for-me" read regardless of how high other f-loadings are | Approach-mode manipulation: hold f-loadings high, vary mode, observe receiver disqualification rate |

*Cluster 4 re-check:* Each Gap maps to existing architecture (Gap 1 → domain clarification of `f`; Gap 2 → context parameter on Specificity; Gap 3 → coupling rule within g₁). No C/H/F/R or g₁/g₂/g₃ ontological restructure required. Iteration-3.2 reopening conditions reviewed: no additional modulators identified; no decisive cases requiring substrate reframe. **Cluster 4 NOT triggered.**

*Sequencing recommendation:* Ship Gaps 1 and 2 in iteration-3.3 finding (low-medium operational cost, PRAGMA already partly supports). Gap 3 may stage separately if mode-distinction operational signals don't complete in this iteration's timeline.

#### P4-B (focused) — "Cross-Gap interaction matrix" [Combination]

**Mechanism:** Combination. Three Gaps × three Gaps interaction matrix.

**Output:** Make the interaction matrix an explicit deliverable:
| | Gap 1 (f_prior) | Gap 2 (θ_context) | Gap 3 (display-mode) |
|---|---|---|---|
| **Gap 1** | — | Does f_prior interact with θ_context? **HYPOTHESIS:** Yes — high f_prior may lower the effective specificity needed to clear θ (a known sender on cold-DM channel registers at lower specificity than an unknown sender). **STATUS:** Open Question. | Does f_prior compensate for withholding-suppressed H_a? **HYPOTHESIS:** Partially — elevated H_a from prior reputation (e.g., the sender is known to be specifically interested in this counterparty) can offset withholding-mode H_a suppression in current interaction. **STATUS:** Open Question. |
| **Gap 2** | (mirror) | — | Does θ_context interact with display mode? **HYPOTHESIS:** No — they operate on different aspects (specificity gating at f-input vs H_a availability within `f`). **STATUS:** Tentative. |
| **Gap 3** | (mirror) | (mirror) | — |

The matrix is published as Open Questions, not as commitments. Each cell becomes a future empirical agenda item.

**Why combination:** The three Gaps individually are independent fixes; their pairwise interactions are emergent and worth exposing.

#### P4-C (contrarian) — "Cluster 4 IS triggered by quantitative pressure" [Inversion]

**Mechanism:** Inversion. Invert sensemaking's "Cluster 4 not triggered" verdict.

**Output:** Three architectural elements added in one iteration is qualitatively the same kind of pressure as "additional modulators" — the documented Cluster 4 trigger from iteration-3.2's Open Questions. Even if each Gap individually is structurally absorbable, the cumulative pressure indicates the architecture is straining. Open a substrate-reframe inquiry: are C/H/F/R + g₁/g₂/g₃ better understood as emergents from deeper variables (e.g., Resonance + Positioning + Stakes from iteration-3.2's Open Question 11)?

**Inversion depth check:** Component-level inversion. Goes against sensemaking's structural test, on grounds that quantitative pressure should override structural absorption when the quantity reaches a threshold. The contrarian case is weak because iteration-3.2's documented trigger was specifically "additional modulators" — this iteration adds zero modulators.

---

### P5 — Assembly: finding + spec integration

#### P5-A (generic) — "Standard MVL+ template + extend new_apt_layer.md" [Constraint Manipulation]

**Mechanism:** Constraint Manipulation. Constraint: "use existing finding template + minimum-disruption to existing spec."

**Output:**
- finding.md follows MVL+ extended template (Question, Finding Summary, Finding, Reasoning, Open Questions; Next Actions if changes proposed)
- Spec integration: extend `pragma/core/new_apt_layer.md` with new sections (no new file)
- 3.2 and 3.2.1 finding documents updated with brief forward-reference notes
- Receiver-state pre-condition note in a "Scope and Pre-conditions" subsection of `new_apt_layer.md`
- Frontmatter: status, refines (3.2.1 finding's specific commitments preserved/refined), iteration label = 3.3

#### P5-B (focused) — "Dedicated new spec file `apt_iteration_3_3.md`" [Combination]

**Mechanism:** Combination. New file pattern + explicit cross-reference structure + 3.3-specific organization.

**Output:**
- Create `pragma/core/apt_iteration_3_3.md` with sections:
  1. *Motivation* — interaction-centric framing (descriptive, not structural per sensemaking Ambiguity 1)
  2. *Three Refinements* — Gap 1, Gap 2, Gap 3 each with location, statement, worked example, PRAGMA implication
  3. *Predictions* — three predictions iteration-3.3 makes that 3.2.1 cannot
  4. *Cross-Gap Interactions* — interaction matrix as Open Questions (from P4-B)
  5. *Cluster 4 Re-Check* — explicit verdict with structural reasoning
  6. *Scope and Pre-Conditions* — receiver-state out-of-formula note
  7. *Open Questions* — calibration of θ values, operational signals for mode distinction, cross-Gap interactions
- Frontmatter: `refines: pragma/core/apt_iteration_3_2_1.md` (or equivalent existing spec target); iteration label 3.3
- Cross-references: backward to 3.2 and 3.2.1 in finding.md and spec; 3.2/3.2.1 documents updated with forward-reference notes pointing to 3.3
- finding.md mirrors structure but is positioned in `devdocs/inquiries/apt_context_layer/`

#### P5-C (contrarian) — "Update 3.2.1 in place; don't increment iteration" [Inversion]

**Mechanism:** Inversion. Invert iteration-numbering decision.

**Output:** Don't ship as iteration-3.3. Instead, update the iteration-3.2.1 finding in place — add the three refinements as Additions 5, 6, 7. Argument: 3.2.1 already added four clarifications including a structurally novel one (MAGNITUDE/TYPE as new output dimension); adding three more isn't qualitatively different. Avoids version-numbering inflation; keeps the 3.x series tight.

**Inversion depth check:** Component-level inversion. The structural counter (Gap 3 introduces a coupling between previously-independent components, which 3.2.1 did not do) was already established in sensemaking Ambiguity 5.

---

## Phase 3 — Test (per candidate)

Five tests: novelty, scrutiny survival, fertility, actionability, mechanism independence.

### P1 verdicts

| | Novelty | Scrutiny | Fertility | Actionability | Mech. Independence | Verdict |
|---|---|---|---|---|---|---|
| **P1-A** | LOW (restatement of implicit) | HIGH (sensemaking-validated) | MEDIUM (opens PRAGMA input expansion) | HIGH | HIGH (multiple mechanisms converge) | **SURVIVE** |
| **P1-B** | MEDIUM (ledger framing new) | NEEDS CHECK (does it violate sensemaking's "no formal decomposition" verdict?) | HIGH (PRAGMA architecture) | HIGH | MEDIUM | **SURVIVE-with-clarification** |
| **P1-C** | HIGH (rehabilitates killed alternative) | NEEDS HARD CHECK | MEDIUM | HIGH | LOW (only inversion) | **REFINE-or-KILL** (critique to decide) |

P1-B clarification: the evidence-ledger is an *internal accounting model for PRAGMA's input pipeline*, not a formal additive split in `f`. The formula stays `f(C,H,F,R)`; the ledger is exposition. This preserves sensemaking's commitment.

P1-C scrutiny: sensemaking explicitly rejected `f_prior + f_interaction` on grounds of "bookkeeping cost without architectural gain." The contrarian case offers attribution-trackability as the gain. Critique decides whether attribution-trackability is worth the bookkeeping cost. Strongest objection: PRAGMA can attribute-via-ledger (P1-B) without committing to formal terms. Counter-objection: a ledger is itself a formal model. The dispute is real.

### P2 verdicts

| | Novelty | Scrutiny | Fertility | Actionability | Mech. Independence | Verdict |
|---|---|---|---|---|---|---|
| **P2-A** | MEDIUM (rehabilitation of P2-C) | HIGH | HIGH (calibration agenda) | HIGH | HIGH | **SURVIVE** |
| **P2-B** | HIGH (no SDT import in APT) | NEEDS CHECK (SDT/APT fit) | HIGH (cross-discipline grounding) | MEDIUM (theoretical, doesn't change spec content beyond P2-A) | MEDIUM | **SURVIVE-as-grounding** |
| **P2-C** | MEDIUM (alternative parameterization) | FAILS (per-receiver = receiver-state crossover, ruled out Cycle 7) | MEDIUM | LOW (not PRAGMA-detectable) | LOW | **KILL** |

P2-B scrutiny: SDT primarily addresses binary discrimination; APT signals are graded. Counter: SDT has graded-signal extensions (ROC, d′ measures); the import is the structure (signal+noise+threshold+bias), not the binary classifier. Holds with adaptation note.

P2-C kill: per-receiver θ requires PRAGMA to access receiver attentional load, channel familiarity, saturation — exactly the receiver-state pre-condition variables ruled outside-formula in exploration Cycle 7. Not operationally feasible within APT's scope.

**Seed extracted from P2-C kill:** "θ may have a per-receiver component that PRAGMA cannot access; this is what receiver-state pre-condition is doing for us." Confirms the pre-condition placement.

### P3 verdicts

| | Novelty | Scrutiny | Fertility | Actionability | Mech. Independence | Verdict |
|---|---|---|---|---|---|---|
| **P3-A** | HIGH (mode distinction not in prior iterations) | HIGH (sensemaking-validated) | HIGH (display-mode as new diagnostic axis) | HIGH | HIGH (combination + absence both find it) | **SURVIVE** |
| **P3-B** | HIGH (new naming of phenomenon) | HIGH (consistent with Double-Collapse + 3.2.1 Sender-SP) | HIGH (refines 3.2.1 Addition 2) | HIGH | MEDIUM-HIGH | **SURVIVE** |
| **P3-C** | HIGH (architectural change) | FAILS (orthogonality + failure-signature tests fail per sensemaking Ambiguity 4) | (would be high if survived) | HIGH | LOW | **KILL** |

P3-C kill: g₄(Mode) has no value independent of g₁ × context. Selective-engagement mode IS high g₁ in approach contexts; withholding mode IS high g₁ in non-approach contexts. Mode cannot collapse independently of the joint state. Fails orthogonality cleanly. Sensemaking's Ambiguity 4 verdict holds.

**Seed extracted from P3-C kill:** "The phenomenon is real but its architectural location is the coupling rule within g₁, not a new modulator. The orthogonality test gates entry to the Modulator Suite tightly — this protects the Suite from inflation."

### P4 verdicts

| | Novelty | Scrutiny | Fertility | Actionability | Mech. Independence | Verdict |
|---|---|---|---|---|---|---|
| **P4-A** | MEDIUM (extrapolation) | HIGH | HIGH (empirical agenda) | HIGH | HIGH | **SURVIVE** |
| **P4-B** | HIGH (interaction matrix) | NEEDS CHECK (interactions speculative) | HIGH | MEDIUM (Open Questions) | MEDIUM | **SURVIVE-as-Open-Question** |
| **P4-C** | MEDIUM (challenges sensemaking) | FAILS (quantitative count contradicts iteration-3.2's specific trigger; structural test passed) | MISLEADING if accepted | HIGH | LOW | **KILL** |

P4-B: interactions are speculative without empirical grounding, but framing them as Open Questions (not commitments) makes scrutiny acceptable. Survives in the Open Questions section.

P4-C kill: iteration-3.2's documented Cluster 4 trigger names "additional modulators" specifically. This iteration adds zero modulators. The quantitative-pressure heuristic does not override the structural test; sensemaking's Ambiguity 6 verdict holds.

**Seed extracted from P4-C kill:** "Cluster 4 reopening conditions are documented; honest checks should reference them by their specific criteria, not invoke them on quantitative count alone. This protects the substrate-reframe inquiry from premature triggering."

### P5 verdicts

| | Novelty | Scrutiny | Fertility | Actionability | Mech. Independence | Verdict |
|---|---|---|---|---|---|---|
| **P5-A** | LOW (template-driven) | HIGH | LOW (preserves structure) | HIGH | MEDIUM | **SURVIVE** |
| **P5-B** | MEDIUM (new file pattern) | HIGH (gives 3.3 clean home; preserves 3.2/3.2.1 as anchors) | HIGH (establishes pattern) | HIGH | MEDIUM-HIGH | **SURVIVE** |
| **P5-C** | MEDIUM (challenges convention) | FAILS (structural test from sensemaking Ambiguity 5 holds: Gap 3 is qualitatively newer than 3.2.1 clarifications) | MEDIUM | HIGH | LOW | **KILL** |

P5-A vs P5-B: both survive; choice between them is a presentation question. P5-B is preferred because Gap 3's structural status warrants its own iteration anchor — extending `new_apt_layer.md` in place buries the structural change.

P5-C kill: 3.2.1's MAGNITUDE/TYPE addition introduced a new output dimension but did not change component relationships; Gap 3 introduces a coupling between previously-independent components (g₁ mode and H_a). That difference is qualitatively significant; iteration label 3.3 reflects it.

**Seed extracted from P5-C kill:** "Iteration label discipline (3.x.y vs 3.x+1) tracks structural-vs-clarificatory change. Maintaining the discipline keeps the spec's history readable; collapsing it produces a single big finding that can't be navigated."

---

## Phase 3 — Assembly Check

Looking at SURVIVE candidates across all five pieces:

**Primary survivor set (one per piece, strongest):**
P1-A or P1-B (both viable; P1-B is richer), P2-A (with optional P2-B as theoretical grounding), P3-A + P3-B (these two combine — modes + approach act), P4-A + P4-B (predictions + interaction matrix), P5-B (new file).

### Assembly 1 — "Channel-Aware Belief Ledger + Display-Mode Spec"

**Components:** P1-B + P2-A + P3-A + P3-B + P4-A + P4-B + P5-B.

**Emergent architecture:** The evidence ledger from P1-B naturally encodes channel-prior as one of its four sources. This connects directly to θ(context)'s channel taxonomy from P2-A — they share the channel concept. The PRAGMA pipeline becomes:

```
1. Read channel metadata + signals → distribute across f's evidence-ledger sources
   (interaction / prior-experience / social-proof / channel-prior)
2. Apply channel-specific θ from P2-A to specificity-gated signals
3. Read sender-SP from message style + behavior; classify display mode (P3-A) +
   approach-act contributions (P3-B) → determine H_a availability in f
4. Aggregate evidence per ledger; apply specificity formula with θ(context);
   evaluate g₁(mode) × g₂(Coherence) × g₃(EC) × f
5. Output MAGNITUDE and TYPE per 3.2.1
```

This unifies the three Gaps under a PRAGMA pipeline view. The finding ships as iteration-3.3 with the unified pipeline as a worked illustration.

**Emergent value:** None of P1-B, P2-A, P3-A alone produces this pipeline. Their assembly does. The pipeline is the testable, operationalizable instantiation of the three refinements together.

**Assembly tests:**
- *Novelty:* HIGH (no prior PRAGMA pipeline view in spec).
- *Scrutiny survival:* HIGH (each component independently survives; assembly is consistent).
- *Fertility:* HIGH (gives PRAGMA implementation a concrete blueprint).
- *Actionability:* HIGH (direct PRAGMA development guide).
- *Mechanism independence:* HIGH (assembly emerges from combination of independently-derived components).

**Verdict on Assembly 1: STRONG SURVIVE — primary candidate for iteration-3.3 finding.**

### Assembly 2 — "SDT-Grounded Variant"

**Components:** P1-A (minimal) + P2-B (SDT port) + P3-A + P3-B + P4-A + P4-B + P5-B.

**Emergent architecture:** SDT grounds θ(context) in adjacent theory; the rest of the architecture stays as in Assembly 1. The signal+noise+threshold+bias frame becomes a section in the iteration-3.3 spec.

**Emergent value:** Theoretical credibility. Appeals to readers from signal-processing or perceptual-psychology backgrounds. Provides structural language for how PRAGMA's channel classifier should work.

**Assembly tests:** Same as Assembly 1 except SDT integration adds theoretical-grounding section.

**Verdict on Assembly 2: SURVIVE — alternative theoretical framing, can be merged with Assembly 1 as an optional Theoretical Grounding section.**

### Assembly 3 — "Substrate Reframe" (if P4-C had survived)

P4-C killed → assembly does not exist. Cluster 4 stays cold for iteration-3.3.

---

## Mechanism Coverage (Telemetry)

* **Generators applied: 4/4** — Combination (P1-B, P3-A, P4-B, P5-B), Absence Recognition (P3-B), Domain Transfer (P2-B), Extrapolation (P4-A)
* **Framers applied: 3/3** — Lens Shifting (P2-A), Constraint Manipulation (P1-A, P5-A), Inversion (P1-C, P2-C, P3-C, P4-C, P5-C)
* **Convergence:** YES on all three core refinements (Gap 1: P1-A and P1-B converge on "f-as-belief-state with PRAGMA input expansion"; Gap 2: P2-A and P2-B converge on "context-parameterized θ with channel taxonomy"; Gap 3: P3-A and P3-B converge on "two modes + coupling rule + approach-act contribution"). Assembly 1 emerges from this convergence.
* **Survivors tested:** 15/15 (all variants tested against all 5 criteria).
* **Failure modes observed:**
  - *Premature evaluation:* avoided — each candidate generated before testing
  - *Single-mechanism trap:* avoided — 7/7 mechanisms applied
  - *Early frame lock:* avoided — multiple mechanisms applied per piece, including contrarian variants
  - *Innovation without grounding:* avoided — all candidates tested
  - *Mechanism exhaustion:* not observed — every mechanism produced viable output
  - *Survival bias:* actively guarded against — contrarian variants (P1-C, P2-C, P3-C, P4-C, P5-C) given strongest possible framing; killed on structural grounds, not comfort
* **Overall: PROCEED** — full coverage, strong convergence, all candidates tested, no failure modes detected. Assembly 1 is the primary finding-target candidate; Assembly 2 is an optional theoretical-grounding overlay.
