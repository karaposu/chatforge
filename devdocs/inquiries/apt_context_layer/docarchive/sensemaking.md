---
status: active
discipline: sensemaking
inquiry: apt_context_layer
iteration: 1
---
# Sensemaking: apt_context_layer

## User Input

`devdocs/inquiries/apt_context_layer/_branch.md`

Inputs consumed: `_branch.md` (5 seeds, 3 pre-seeded hypotheses Alpha/Beta/Gamma, scope check), `exploration.md` (8 cycles, 3 confirmed structural gaps + 1 pre-condition clarification + 1 falsified candidate). Adjacent context: iteration-3.2 (`apt_modulator_landscape/finding.md` — formula `f(C,H,F,R) × g₁(SP) × g₂(Coherence) × g₃(EC)`) and iteration-3.2.1 (`attachment_variable_interactions/finding.md` — Double-Collapse, Signal Specificity, MAGNITUDE/TYPE).

---

## Initial Sense Version (SV1 — Baseline Understanding)

The exploration found three things that the current APT formula does not represent: (1) what the receiver already believes about the sender before the interaction starts, (2) how the channel/context determines whether a signal even registers, and (3) how the *mode* of Self-Positioning (selective engagement vs. withholding) gates whether Hope can exist at all. Plus a fourth, smaller item: receiver-availability is a precondition outside the formula. The exploration speculates these three gaps "may share a root" because the current theory is "interaction-centric." The sensemaking task is to convert this fuzzy intuition into a stable architectural model: are these one layer, three independent additions, or some mixture? And where does each piece sit relative to the existing f, g, and Specificity components?

---

## Phase 1 — Cognitive Anchor Extraction

### Constraints (limits, requirements, boundaries)

- **C1 — No new attachment variable.** Iteration-3.2.1 closed `f` to four members (C/H/F/R) on a strict orthogonality test. Anything new that fails the "can it generate attachment alone with all four others at zero?" test cannot enter `f` as a 5th variable.
- **C2 — Cluster 4 must be assessed, not assumed away.** Multiple architectural additions in a single iteration is the explicit Cluster 4 trigger from iteration-3.2. The sensemaking must check this honestly, not protect against it reflexively.
- **C3 — Iteration-3.2.1 is preserved.** The Double-Collapse, additive `f`, Signal Specificity, MAGNITUDE/TYPE — all stay. New work refines the surrounding architecture, not these.
- **C4 — Falsified mechanisms cannot be revived.** B1 (noise as indiscriminate signal attenuation) is confirmed-absent by Person A's specific Reddit message succeeding. Any architecture that depends on B1 being true is invalid.
- **C5 — Receiver-state is a pre-condition.** Cycle 7 determined this. Cannot be re-imported as a formula variable without overturning that finding.
- **C6 — PRAGMA operationalizability.** Whatever architectural elements are added must be detectable from message+channel+history evidence, not require psychological introspection of the receiver.

### Key Insights (non-obvious implications)

- **K1 — `f` was always a belief state, never a real-time signal stream.** This was implicit and never stated. The Reddit case looks like a "missing variable" problem only because the spec writes `f(C,H,F,R)` as if generated within the interaction. Once `f` is recognized as the receiver's *current belief* about C/H/F/R, social proof, reputation, and channel prior fall in naturally — they're sources that update belief, not new variables.
- **K2 — The threshold model wasn't wrong; its parameterization was wrong.** P2-C was killed in `attachment_variable_interactions` as "empirically underdetermined" because it treated θ as a single global constant. It survives once θ is parameterized by context. The killed candidate becomes valid under context-parameterization.
- **K3 — SP and H_a are not independent in approach contexts.** The current formula writes them as multiplicatively combined independent variables. But the *mode* of SP display determines whether H_a is expressible at all. Withholding-mode SP × any-H_a-input ≈ 0 because the input is structurally suppressed at source. This is non-independence, but at the *display channel* level, not at the construct level.
- **K4 — The approach act is not a "0th step" — it's a multi-variable signal event.** Selective initiation simultaneously signals f_Charm (initiation confidence), H_a (specific attention offered), and g₁ (acting from own evaluation). Specificity then realizes/dilutes all three at once. This is the Double-Collapse seen from the sender's side: the same lever (specificity of engagement) controls both layers.
- **K5 — Three gaps, one shared structural feature.** The current theory is interaction-centric. The three gaps each represent something that exists *prior to* or *around* the interaction-content channel: the receiver's prior beliefs (before), the context/channel filter (around), and the approach act (at the moment of contact, before content is processed).

### Structural Points (core components, relationships)

- **S1 — Three sources of `f`, currently conflated:**
  - `f_prior` (cumulative belief state at interaction start) ← social proof, reputation, channel default
  - `f_interaction` (signals generated within this specific interaction)
  - `f_approach` (signals from the approach act itself — a sub-component of f_interaction, but architecturally distinct)
- **S2 — Specificity gate sits BEFORE the f×g multiplication:**
  - `if specificity(signal) ≥ θ(context): effective_magnitude = nominal × specificity`
  - `else: effective_magnitude = 0`
  - θ is a function of context, not a global constant.
- **S3 — SP has two display modes with different downstream consequences:**
  - SP-as-selective-engagement → realizes H_a → g₁ amplifies f normally
  - SP-as-withholding → suppresses H_a at source → g₁ × (depleted f) → "not for me" read
- **S4 — Pre-condition layer (receiver-state) is outside the formula entirely.** Operating envelope, not a variable. Documented but not modeled.
- **S5 — The Double-Collapse, reframed.** The same root cause (non-engagement) drives F-layer failure (low specificity) and G-layer failure (Supplication structure) AND blocks the approach act from generating multi-variable signal. Three-layer collapse, not two — but with the same single upstream cause.

### Foundational Principles (assumptions, rules, axioms)

- **P1 — Architectural minimalism.** Prefer clarification over new structure. Prefer parameterization over new variables. Add only what cannot be expressed within existing architecture.
- **P2 — Structural orthogonality test for new elements.** A new component must be (a) impossible to express via clarification, (b) load-bearing under at least one decisive case, (c) operationally detectable.
- **P3 — `f` and `g` are separate architectural layers.** `f` = receiver's belief about sender's attachment-generators. `g` = receiver's read of sender's modulator state. Mixing them (treating modulator-mode as belief-input) is a category error.
- **P4 — Failure-signature distinctness.** Any new element must produce a distinguishable failure mode that the existing architecture cannot already explain. If existing failures cover it, the element is redundant.
- **P5 — Cluster 4 is honest, not protective.** A substrate reframe is triggered by genuine evidence, not avoided by definitional gymnastics. But it is also not invoked just because additions are non-trivial.

### Meaning-Nodes (central concepts and themes)

- **M1 — Belief state vs. signal stream.** The conceptual unification anchor for Gap 1.
- **M2 — Threshold-based registration.** The conceptual unification anchor for Gap 2.
- **M3 — Display-mode coupling.** The conceptual unification anchor for Gap 3.
- **M4 — Pre-content vs. content channels.** The candidate root concept for the "shared root" question. Three of the four findings (f_prior, θ_context, approach act) all operate before or around the message-content channel. Receiver-state is even earlier (pre-formula).
- **M5 — Iteration boundary.** Is this 3.2.2 (clarification), 3.3 (refinement with structural change), or 4 (substrate reframe)? Decisive for spec organization and cross-reference targets.

### SV2 — Anchor-Informed Understanding

The Reddit/friend/nightclub examples are not three separate problems demanding three separate fixes. They are three observable symptoms of one architectural under-specification: the current theory writes `f` and `g` as if both are computed strictly from in-interaction content. The exploration found that:

- `f` is a belief state, and beliefs include prior components that the formula never names (Gap 1).
- Signals don't enter `f` ungated — they pass a context-dependent threshold first (Gap 2).
- The approach act itself feeds both `f` (specifically H_a) and `g` (specifically g₁), and the *mode* of that approach determines whether one channel cannibalizes the other (Gap 3).

The decisive shift from SV1: the gaps are not "things missing from the formula" — they are **a missing pre-content layer that the formula tacitly assumes exists** but has never specified. This is closer to "missing scaffolding" than "missing components." Two of the three (`f_prior`, θ_context) are clarifications of what existing terms always implicitly meant. The third (approach act + display mode) is structurally newer because it identifies non-independence between previously-independent components in approach contexts.

---

## Phase 2 — Perspective Checking

### Technical / Logical perspective

- The shared-root claim ("interaction-centric theory") is a unifying frame, not a derivation. It doesn't logically entail that one architectural addition fixes all three. It could just describe what the three have in common after the fact.
- New anchor: **Existence-of-shared-frame ≠ unity-of-fix.** A single architectural element fixing all three would need to be load-bearing for each. f_prior is a pre-interaction concept. θ_context is a registration concept. Approach-mode is an interaction-moment concept. They share a *theme* but operate at different times.
- Logical structure of the additions:
  - Gap 1 = expanding the *domain* of `f` (it includes pre-loaded belief)
  - Gap 2 = adding a *gate* before specificity contributes (θ depends on context)
  - Gap 3 = adding a *coupling rule* between g₁ and a sub-component of f (H_a)
  Each is a different *kind* of structural change. They do not collapse into one.

### Human / User perspective

- The user's seed examples are intuitively coherent — they all "feel" like the same kind of missing thing (the theory ignores something obvious). This is a real signal but it's signal about the *experience* of the gap, not about the *structure* of the fix.
- The user's framing — "there is sth missing in our APT theory. lets try to diagnose it, even in fuzzy way" — explicitly invites possibility-space exploration. The user has not committed to one fix; they are diagnosing.
- New anchor: **The user is in diagnosis mode, not specification mode.** Sensemaking output should preserve the structural distinctness of the three gaps so that decomposition/innovation can take any of (a) three separate fixes, (b) one unified fix, (c) some hybrid.

### Strategic / Long-term perspective

- If treated as one layer ("Pre-Content Layer"): clean spec narrative, conceptual elegance, single named addition. Risk: hides the fact that the three sub-mechanisms are operationally independent and may evolve separately under empirical pressure.
- If treated as three separate additions: more accurate to actual structure, more spec surface area, but each can be independently validated/refined as evidence accumulates.
- New anchor: **Spec organization should follow operational independence, not narrative elegance.** The three gaps will likely receive different empirical treatments (f_prior is testable via social-proof manipulations; θ_context is testable via channel-controlled specificity studies; SP-display-mode is testable via approach-context experiments). They should be addressable separately in future iterations.
- Iteration label question: this is bigger than a clarification (3.2.2) because Gap 3 introduces a structural coupling not previously in the formula. It is smaller than a substrate reframe (4) because it doesn't require restructuring the C/H/F/R or g₁/g₂/g₃ ontology. Best fit: **iteration-3.3** (refinement with structural changes that preserve the existing variable/modulator ontology).

### Risk / Failure perspective

- **Risk: Anchor Dominance on "shared root."** The "interaction-centric theory" frame is seductive. It risks becoming the single anchor that resolves every question without each piece being independently tested. Corrective: require each gap to pass the structural orthogonality test on its own.
- **Risk: Status Quo Bias on `f` definition.** If the spec implicitly assumes `f` is in-interaction, then explicitly stating "`f` is a belief state including priors" might feel like a clarification. But for any reader who used `f` strictly as in-interaction signal, this is a re-scoping. The change is real even if framed as clarification.
- **Risk: Cluster 4 false negative.** Three additions in one iteration is the explicit trigger from iteration-3.2's Open Questions. The reflexive answer "no, these are clarifications" may protect against the genuine question.
- **Risk: Self-Reference Blindness.** Using APT's own concepts (f, g, Specificity) to evaluate whether APT needs a new layer is circular. The exploration's seeds (Reddit, friend, nightclub) are external grounding — but only if treated as constraints the architecture must explain, not as already-solved cases.
- New anchor: **The Cluster 4 question must be decided structurally, not narratively.** Decision rule: if all three gaps can be expressed using the existing variable+modulator+specificity architecture (with a new gate, a new coupling, and a clarified domain for f), the architecture survives. If any of the three forces re-defining what C/H/F/R or g₁/g₂/g₃ *are*, Cluster 4 triggers.

### Resource / Feasibility perspective

- f_prior: PRAGMA-detectable from channel metadata + social-proof markers (mutual connections, mentions, prior interaction history). Adds clarification, not new detection apparatus.
- θ(context): requires channel-classification taxonomy. PRAGMA already implicitly does some of this (template-detection is channel-aware in practice). Formalizable.
- SP-display-mode (selective-engagement vs withholding): more demanding. Detection requires distinguishing two SP states with similar surface "high SP" reading. This is a genuine new operational requirement — not infeasible, but a real lift.
- New anchor: **Gap 3 has the highest operationalization cost.** This is independent evidence that Gap 3 is structurally newer than 1 and 2.

### Definitional / Consistency perspective

- Does the proposed layer contradict iteration-3.2.1's commitments? Check each:
  - Additive `f`: preserved. f_prior + f_interaction is still additive.
  - Specificity formula: preserved, parameterized. `effective_magnitude = nominal × specificity (if ≥ θ_context)`.
  - Sender-SP from message style: preserved, refined. Display-mode adds a sub-distinction within SP-reading.
  - MAGNITUDE/TYPE: preserved. Could be enriched (TYPE may pick up an "available vs unavailable" sub-axis from the H_a mechanism) but not contradicted.
- Does iteration-3.2's Modulator Suite need to change? No new modulator (Gap 2's threshold is a parameter, not a modulator; Gap 3's coupling is within g₁, not a new g). The 3-member Suite is preserved.
- Does the iteration-3.2 narcissism reconciliation hold? Yes — narcissist mimicry produces selective-engagement-mode SP at first contact (high g₁ + present H_a), generating immediate attachment, with sustainability divergence happening over time. The display-mode distinction does not affect this temporal mechanism.
- New anchor: **All iteration-3.2 and -3.2.1 commitments are preserved.** No contradiction with established definitions. This is a clean refinement-not-rebuild.
- Internal consistency check on the *proposed* additions: do the three gaps' fixes cohere with each other?
  - f_prior is a domain-clarification of f.
  - θ(context) is a gate before specificity contributes to f.
  - SP-display-mode is a coupling rule between g₁ and a component (H_a) of f.
  - All three preserve the f×g architecture. No internal contradiction.

### SV3 — Multi-Perspective Understanding

Major shifts from SV2:

1. **The "shared root" is a thematic unifier, not a structural one.** All seven perspectives converge on this: the three gaps share a *theme* (everything outside the message-content channel) but operate at different architectural locations (domain expansion of f, gate before f, coupling within g). They should be specified as three separate refinements with one explanatory frame, not collapsed into one architectural element.
2. **The iteration label is 3.3, not 3.2.2 or 4.** Gap 3 is structurally new (introduces a coupling that didn't exist), but Cluster 4 is not triggered (no C/H/F/R or g-suite redefinition required). 3.3 is the right label.
3. **All iteration-3.2 and -3.2.1 commitments survive.** No contradiction. The new layer is purely additive scaffolding around the existing formula.
4. **Operational cost is uneven across the three gaps.** Gap 3 (SP-display-mode) has the highest detection cost. This argues for sequencing — get the cheaper Gaps 1 and 2 into the spec first; Gap 3 may need its own operationalization work.
5. **Cluster 4 must be answered structurally, not by reflex.** Decision rule articulated: if existing variable/modulator/specificity architecture can absorb the three gaps (with a domain-clarification, a parameter, and a coupling rule), the architecture survives. The check passes — Cluster 4 does not trigger.

---

## Phase 3 — Ambiguity Collapse

### Ambiguity 1: Is this one architectural layer or three separate additions?

**Strongest counter-interpretation:**
The "Pre-Content Layer" framing has real explanatory power. All three gaps share the property of being unmodeled-by-the-formula and existing outside or before the message-content channel. A single named layer ("everything before/around message content") would give the spec a clean unifying frame and make the additions easier to teach and remember. Treating them as three separate additions hides their conceptual unity behind operational distinctions that may or may not matter to readers.

**Why the counter-interpretation fails (structural grounds):**
Conceptual unity (shared theme) is not the same as architectural unity (single mechanism). Each gap operates at a different formula location: Gap 1 expands the *domain* of `f`; Gap 2 adds a *gate function* before specificity contributes; Gap 3 introduces a *coupling rule* between a modulator and a variable sub-component. A "single layer" framing would have to be either (a) so abstract it doesn't constrain anything, or (b) hiding three operationally distinct rules under one name. Each gap's fix is independently testable, independently falsifiable, and operates at a different timestep. Mechanism-level structural distinctness > narrative-level conceptual unity.

**Confidence:** HIGH (each gap has a different formula location and different operationalization profile; mechanistic structure overrides thematic unity).

**Resolution:** Three separate refinements, presented under one explanatory frame ("the theory was interaction-centric; these three refinements specify the pre-content scaffolding"). Spec gets three named refinements; the explanatory frame appears in the introduction/motivation, not as a structural element.

**What is now fixed:** Gaps 1, 2, 3 are independently specified, independently testable, and independently revisable in future iterations. The shared frame is descriptive, not load-bearing.

**What is no longer allowed:** Any treatment that collapses the three into a single named architectural element ("Pre-Content Layer," "Context Layer") in the spec. The frame is allowed in motivation/exposition; not in structure.

**What now depends on this choice:** Decomposition will produce three discrete pieces (one per gap), not one. Innovation will generate variants per gap. Critique will evaluate per gap. The finding will name three refinements.

**What changed in the conceptual model:** SV2's "missing scaffolding" frame stays as exposition; the structure underneath is three independent refinements.

---

### Ambiguity 2: Is `f_prior` a new term, or a clarification of what `f` always meant?

**Strongest counter-interpretation:**
Adding `f_total = f_prior + f_interaction` as an explicit decomposition makes the structure trackable and lets PRAGMA detect prior loading separately from interaction loading. Without explicit decomposition, `f_prior` is "what the receiver believed before this interaction" with no formal hook. Explicit decomposition is more precise and operationally useful.

**Why the counter-interpretation fails (structural grounds):**
The decomposition is operationally useful but structurally redundant. `f` was always the receiver's current belief about C/H/F/R. The receiver's belief at any moment is a function of all evidence accumulated so far — no formal split into "before" and "during" is needed; the formula already accommodates it because `f` is evaluated at any moment in the receiver's processing. Adding `f_prior + f_interaction` as a formal term commits the spec to tracking these separately, which forces every PRAGMA evaluation to attribute observed beliefs to source — an empirical question, not a definitional one. The clarification ("`f` is the receiver's cumulative belief state, including evidence from social proof, reputation, channel prior, and in-interaction signals") delivers all the explanatory power without committing to a decomposition the data may not support.

**Confidence:** HIGH (explicit decomposition adds bookkeeping cost without architectural gain; clarification suffices).

**Resolution:** Spec adds a clarification statement: "`f` represents the receiver's cumulative belief about the sender's C/H/F/R at any moment in the interaction. This belief is updated by all available evidence — in-interaction signals, prior direct experience, social proof from third parties, and channel/platform priors. The formula does not assume `f = 0` at interaction start." No new formal term.

**What is now fixed:** `f` is explicitly a belief-state variable. Pre-interaction loading is in-scope.

**What is no longer allowed:** Treating `f` as if it's reset to zero at the start of each interaction. PRAGMA cases involving social proof or channel priors are inside APT's scope, not adjacent to it.

**What now depends on this choice:** PRAGMA's input definition extends to include channel metadata and social-proof signals; these feed `f` directly, not a separate `f_prior` track.

**What changed in the conceptual model:** Gap 1 is a clarification (statement of what `f` always was), not a new term. The architecture doesn't grow; the spec's expressive precision does.

---

### Ambiguity 3: Is θ a global constant, a channel parameter, or a per-interaction variable?

**Strongest counter-interpretation:**
A per-interaction θ (varying within the same channel based on receiver-specific factors like attention available, mood, time of day) would be more flexible and could capture finer-grained variation. Global θ was killed; channel-θ rehabilitates it; per-interaction θ would be the most expressive form.

**Why the counter-interpretation fails (structural grounds):**
Per-interaction θ collapses into receiver-state, which Cycle 7 confirmed is a pre-condition outside APT's formula scope. Within-channel variation in θ is real but is governed by the receiver's availability — and APT explicitly doesn't model receiver availability. Channel/context-level θ is the highest resolution APT can specify without violating the receiver-state pre-condition boundary. Per-interaction θ is also empirically demanding — it would require detecting receiver mood/state from each interaction, which contradicts the "PRAGMA reads message+channel+history" operational frame.

**Confidence:** HIGH (per-interaction θ violates the pre-condition boundary established in Cycle 7).

**Resolution:** θ is a function of context/channel: `θ(context)`. Channel taxonomy is finite and operationalizable: cold-stranger-DM, warm-introduction, mutual-platform-match, existing-relationship, physical-proximity, etc. Each channel has a characteristic θ range. Within-channel variation due to receiver state is acknowledged as outside-formula (pre-condition).

**What is now fixed:** θ is parameterized at the channel/context level. Specificity formula becomes `effective_magnitude = nominal × specificity if specificity ≥ θ(context); else 0`.

**What is no longer allowed:** Treating θ as a global constant. Or treating within-channel variation as a formula matter (it's a pre-condition matter).

**What now depends on this choice:** Each channel needs a documented characteristic θ-range. PRAGMA's channel classifier becomes a load-bearing component (if channel is misclassified, θ is wrong).

**What changed in the conceptual model:** P2-C is rehabilitated as `θ(context)`. The threshold model survives — not as a fixed cutoff but as a context-parameterized gate.

---

### Ambiguity 4: Is SP-display-mode a structural property of g₁, or a new variable, or a clarification of g₁?

**Strongest counter-interpretation:**
SP-display-mode as a new modulator (g₄?) would explicitly model the selective-engagement-vs-withholding distinction as a separate dimension, with its own failure signature ("not for me" read = g₄ collapse). This would extend the Modulator Suite from 3 to 4 members.

**Why the counter-interpretation fails (structural grounds):**
A new modulator must pass the failure-signature distinctness test (P4): does it produce a failure mode existing modulators cannot already produce? Withholding-mode SP fails with the signature "the receiver concludes 'this person is not directing attention at me'" — but this signature operates by suppressing H_a in `f`, not by introducing a new gating product. The mechanism is *coupling between g₁ and H_a*, not a new independent gate. Calling it a new modulator double-counts: the failure already shows up as g₁ × (low-or-zero H_a) → small product, plus the receiver's interpretation of high g₁ with absent H_a as disqualification. A new modulator would also fail orthogonality: it cannot collapse independently of g₁ and H_a; its value is fully determined by their joint state.

Further: the existing g₁ definition (Self-Positioning as the modulator carrying SP signal) is preserved. What's new is the recognition that g₁ has two display modes that produce different effects on f's H_a sub-component. This is a property-of-g₁, not a new g.

**Confidence:** HIGH (orthogonality + failure-signature tests both fail for "new modulator" reading; coupling-rule reading passes both).

**Resolution:** SP-display-mode is a structural property of g₁ that determines the value of H_a in `f`. Specification: "g₁ has two display modes — selective-engagement and withholding. Selective-engagement realizes H_a; withholding suppresses it. In approach contexts, the display mode of g₁ is constrained by the requirement to generate at least minimum H_a for `f` to be non-trivially populated."

**What is now fixed:** g₁ has two specified display modes. The relationship between g₁'s mode and f's H_a is a coupling rule, not an independent variable.

**What is no longer allowed:** Treating g₁ × f_Hope as fully independent multiplication in approach contexts. The product is constrained by display-mode coupling.

**What now depends on this choice:** Iteration-3.2.1's Sender-SP-from-message-style addition gets refined: message style reads not just "high vs low SP" but also "selective-engagement-mode vs withholding-mode SP." PRAGMA needs operational signals for the mode distinction.

**What changed in the conceptual model:** Gap 3 is a coupling rule within the existing architecture, not a new modulator. The Modulator Suite stays at 3 members. Cluster 4 does not trigger.

---

### Ambiguity 5: Is this iteration 3.2.2, 3.3, or 4?

**Strongest counter-interpretation:**
Treating this as 3.2.2 (clarification) is defensible: Gap 1 is a clarification, Gap 2 is a parameter expansion of an existing formula component, Gap 3 is a coupling rule within an existing modulator. None of these introduce new variables or modulators. By the iteration-numbering convention used in iteration-3.2.1 (where four explicit additions still constituted "clarification"), three more refinements that don't add formula elements could also be "clarification." Calling it 3.3 inflates the perceived structural change.

**Why the counter-interpretation fails (structural grounds):**
3.2.1 added four *explicit statements* of things the spec already implicitly assumed (additive `f`, Specificity as factor, Sender-SP from style, MAGNITUDE/TYPE as outputs). None changed how the formula's components related to each other. Gap 3 in this inquiry *does* change a component relationship: it introduces a coupling between g₁ and H_a where the existing formula treated them as independent. That is a structural change, even if no new components are added. Convention from iteration-3.2's Open Questions: 3.x.y = clarifications; 3.x+1 = structural refinement preserving ontology; 4 = substrate reframe. Gap 3 is structural refinement. The label is 3.3.

**Confidence:** HIGH (convention is documented; Gap 3's coupling rule is genuinely structural; 3.2.2 understates the change).

**Resolution:** Iteration label is 3.3. Spec target document: a new file or a new section in the iteration-3 spec sequence, cross-referenced from `new_apt_layer.md` and the 3.2/3.2.1 finding documents.

**What is now fixed:** Iteration label 3.3. Gap 3's structural status (coupling rule, not just clarification).

**What is no longer allowed:** Treating Gap 3 as "just clarification" alongside Gaps 1 and 2.

**What now depends on this choice:** Spec organization: iteration-3.3 finding will document one structural refinement (Gap 3) plus two clarifications (Gaps 1 and 2). Cross-reference from iteration-3.2 and -3.2.1.

**What changed in the conceptual model:** The three gaps are not all of the same type. Gap 3 is structurally newer than Gaps 1 and 2.

---

### Ambiguity 6: Does this trigger Cluster 4?

**Strongest counter-interpretation:**
Three architectural additions in one iteration is the explicit trigger from iteration-3.2's Open Questions. The Reddit/friend/nightclub examples expose surfaces the existing architecture didn't model. If any of the three gaps reveals that C/H/F/R or g₁/g₂/g₃ are emergents from deeper variables, Cluster 4 should fire. The exploration's "shared root" observation could be early evidence of a deeper substrate that the C/H/F/R+g architecture is hiding.

**Why the counter-interpretation fails (structural grounds):**
Cluster 4 requires evidence that the existing variable+modulator+specificity architecture *cannot* express the new phenomena — that they are "real but unrepresentable" within the current ontology. The check: each gap's fix has been mapped to existing architecture: Gap 1 → clarified domain of `f`; Gap 2 → context-parameterized θ in the existing Specificity formula; Gap 3 → coupling rule within g₁ between display-mode and H_a. The existing C/H/F/R variables remain primary; g₁/g₂/g₃ remain primary; no substrate variables are needed to express the gaps. The "shared root" is thematic (all three operate outside the message-content channel) but does not require ontological restructure.

The decisive test: would moving to a substrate ontology (e.g., Resonance + Positioning as fundamentals; C/H/F as emergents) explain anything the current ontology cannot? The exploration found no such case. The friend's dates work fine within current ontology once `f_prior` is acknowledged. The Reddit failure works fine within current ontology + θ_context. The nightclub tension works fine within current ontology + display-mode coupling.

**Confidence:** HIGH (no decisive case requires substrate restructure; all three gaps absorbable within current ontology).

**Resolution:** Cluster 4 does NOT trigger. The current architecture survives. Three refinements within iteration-3.3.

**What is now fixed:** APT's variable+modulator+specificity ontology is preserved through iteration-3.3. Cluster 4 reopening conditions remain as documented in iteration-3.2's Open Questions; no new evidence in this inquiry triggers them.

**What is no longer allowed:** Invoking Cluster 4 reflexively because of "three additions." Cluster 4 requires structural evidence of ontological inadequacy, not quantitative count.

**What now depends on this choice:** Iteration-3.3 spec proceeds within current ontology. Any future inquiry that finds a phenomenon NOT absorbable via clarification + parameter + coupling rule would re-open the Cluster 4 question.

**What changed in the conceptual model:** Cluster 4 is honestly checked and confirmed not-triggered. The iteration-3.3 changes are real but bounded.

---

### SV4 — Clarified Understanding

After the six ambiguity collapses:

- **Three refinements, one explanatory frame, three different structural types.**
  - Gap 1 (`f_prior`): **clarification** of the domain of `f`. `f` is a cumulative belief state. No new term in the formula.
  - Gap 2 (θ_context): **parameter expansion** of the Specificity formula from iteration-3.2.1. θ becomes context-parameterized: `θ(context)`.
  - Gap 3 (SP-display-mode): **coupling rule** between g₁ and H_a. Two display modes specified; H_a availability depends on which mode g₁ is in.
- **One pre-condition statement** (receiver-state explicitly noted as outside formula scope).
- **Iteration label: 3.3.** Refinement preserving ontology, with one structural change (Gap 3).
- **Cluster 4 does not trigger.** Existing variable+modulator+specificity ontology absorbs all three gaps.
- **All iteration-3.2 and -3.2.1 commitments preserved.** Modulator Suite stays 3-member; `f` stays 4-variable additive; Specificity, Sender-SP-from-style, MAGNITUDE/TYPE all preserved (the last three with minor refinements).
- **Operational cost is uneven.** Gaps 1 and 2 are low-cost (PRAGMA already has channel awareness; social-proof/reputation detection is feasible). Gap 3 is higher-cost (distinguishing selective-engagement-mode vs withholding-mode SP requires new operational signals).

What is no longer viable:
- Single "Pre-Content Layer" architectural element (rejected as narrative-not-structural).
- `f_prior + f_interaction` as a formal decomposition (rejected as bookkeeping-overhead-without-gain).
- Per-interaction θ (rejected as receiver-state crossover).
- New g₄ modulator (rejected by orthogonality + failure-signature tests).
- Iteration-3.2.2 label (rejected as understating Gap 3's structural change).
- Cluster 4 substrate reframe (rejected — no decisive case forces it).

---

## Phase 4 — Degrees-of-Freedom Reduction

### Variables now fixed

- **Architectural location of each gap:**
  - Gap 1 = domain-of-`f` clarification
  - Gap 2 = parameter on Specificity formula
  - Gap 3 = coupling within g₁ (between display mode and H_a)
- **Iteration label:** 3.3
- **Ontology:** preserved (4 attachment variables, 3 modulators, Specificity gate)
- **Cluster 4 status:** not triggered
- **Existing commitments:** all preserved (3.2 and 3.2.1)
- **Receiver-state status:** explicitly out-of-formula (pre-condition)

### Options eliminated

- Single named "Pre-Content Layer" architectural element
- New attachment variable
- New modulator (no g₄)
- Formal `f_prior` term
- Global θ
- Per-interaction θ
- Cluster 4 substrate reframe
- Treating Gap 3 as mere clarification

### Remaining viable paths (decomposition will pick among these)

1. **How to specify `f` as belief state.** Wording, scope, how PRAGMA's input definition changes, what counts as "pre-interaction evidence," how to handle conflicting prior signals. *Open: empirical work on coefficient values for prior vs. in-interaction evidence.*
2. **How to taxonomize context for θ(context).** Channel taxonomy granularity, named channels with characteristic θ ranges, how θ is calibrated empirically, edge cases (mixed-channel interactions). *Open: how many distinct context categories the spec should commit to.*
3. **How to specify SP-display-mode operationally.** What signals distinguish selective-engagement vs withholding mode, how the H_a coupling rule is stated formally, integration with iteration-3.2.1's Sender-SP-from-message-style addition. *Open: operational signals for mode detection.*
4. **How to express the explanatory frame in the spec.** Where the "interaction-centric → pre-content scaffolding" narrative goes (introduction, motivation, or just inline), and how to keep it descriptive (not structural). *Closed-ish: the frame is exposition only.*
5. **Sequencing of empirical work.** Gaps 1 and 2 are cheaper; Gap 3 is harder. Whether to ship 3.3 with all three or stage them. *Open: sequencing decision belongs to innovation/critique.*

### SV5 — Constrained Understanding

The solution space is now bounded:

- The architectural answer is: **three refinements, three structural types, preserved ontology, iteration-3.3.**
- Decomposition's question-tree will partition along the four open paths above (#1, #2, #3, plus the optional sequencing question #5). The explanatory frame (#4) is closed enough to fold into spec exposition.
- Innovation will produce variants per open path: how to word the `f`-as-belief clarification, how to organize θ(context) channels, what operational signals identify SP display mode, sequencing options.
- Critique will evaluate variants against: faithfulness to the 3.3 architecture established here, preservation of 3.2 and 3.2.1 commitments, PRAGMA-operationalizability, structural orthogonality (no double-counting).

The shape of the iteration-3.3 finding is now predictable in outline: a brief recap of the three observed cases (Reddit / friend / nightclub), an "interaction-centric" framing as motivation, three named refinements with their architectural locations, an operationalization note that sequences Gap 3 separately if needed, and a Cluster 4 check that confirms non-trigger.

---

## Phase 5 — Conceptual Stabilization

### SV6 — Stabilized Model

**The current APT theory is interaction-centric: it specifies what happens once message-content signals are being processed but tacitly assumes — without stating — the scaffolding that determines whether processing happens at all and what the receiver brings into the processing. The Reddit stranger, the friend with many dates, and the nightclub SP/Hope tension are three observable symptoms of this single under-specification, but they have three distinct architectural fixes:**

1. **Gap 1 — `f` is a cumulative belief state (clarification).** The spec must state explicitly that `f` represents the receiver's current belief about the sender's C/H/F/R, formed from in-interaction signals AND from prior evidence (direct experience, social proof, channel prior). No new formula term. The spec was always implicitly true; this just says it.

2. **Gap 2 — θ is context-parameterized (parameter expansion).** The Specificity formula from iteration-3.2.1 gets a context-dependent threshold: `effective_magnitude = nominal × specificity if specificity ≥ θ(context); else 0`. This rehabilitates the previously-killed P2-C threshold model under a contextual parameterization. Channel taxonomy (cold DM, warm intro, mutual-match, existing relationship, physical proximity) gives θ characteristic ranges.

3. **Gap 3 — g₁ has two display modes coupled to H_a (structural refinement).** Self-Positioning displays in two modes: *selective-engagement* (realizes H_a — the receiver's hope of receiving specific attention) and *withholding* (suppresses H_a). In approach contexts, withholding-mode g₁ leaves SP nothing to multiply (g₁ × 0 = 0) and produces a "not for me" read that goes beyond simple low-attachment. The selective approach act is itself the minimum source of H_a. This is a coupling rule within the existing g₁, not a new modulator.

**Plus one pre-condition note:** Receiver availability/receptiveness is outside APT's formula scope. APT operates given a receiver who is processing the interaction. This is documentation, not addition.

**Architectural status:**
- All three gaps are absorbable within the existing variable+modulator+specificity ontology.
- No new attachment variable. No new modulator. No substrate reframe.
- All iteration-3.2 commitments preserved (Modulator Suite, 4-variable additive `f`, Resonance, narcissism reconciliation, Cluster 4 conditions).
- All iteration-3.2.1 commitments preserved (Specificity, Sender-SP-from-style, MAGNITUDE/TYPE, Double-Collapse).
- Iteration label: **3.3** — refinement with one structural change (Gap 3's coupling rule), preserving ontology.
- Cluster 4: **NOT triggered.** Honest check performed; ontology survives.

**Operational status:**
- Gap 1: low-cost (PRAGMA reads channel metadata + social-proof markers; no new apparatus).
- Gap 2: low-medium-cost (requires channel-classifier; PRAGMA already partly does this).
- Gap 3: medium-high-cost (requires distinguishing two SP display modes from message+behavior signals; new operational signals likely needed).

**Predictions the iteration-3.3 architecture makes that iteration-3.2.1 alone does not:**
- A high-specificity message via cold Reddit DM should still register (Person A) — but the same level of specificity via warm intro should produce noticeably more attachment, because lower θ_warm means more of the signal converts to effective magnitude.
- A friend with elevated f_prior from social proof should generate attachment in receivers before any direct interaction quality is established — and the in-interaction quality bar to maintain that attachment is lower than the bar to create it from zero.
- An approach in selective-engagement mode generates baseline attachment even with otherwise modest f_interaction (because the approach-act itself generates f_Charm + H_a + g₁ contributions). An approach in withholding mode generates the "not-for-me" read regardless of how high the sender's other f-loadings are — H_a sits at zero, suppressing the multiplicative product.

### How SV6 differs from SV1

SV1: three things are missing from APT, the exploration thinks they share a root.

SV6: the three observed phenomena are symptoms of one missing-scaffolding theme, but they have **three structurally distinct fixes at three different formula locations**. The architecture survives without a substrate reframe; the iteration label is 3.3; all prior commitments hold; and the operational lift is uneven across the three gaps. The shared root is descriptive, not structural — it goes into the spec's motivation, not its structure.

---

## Saturation Indicators (Telemetry)

- **Perspective saturation:** 7 perspectives applied (Technical, Human, Strategic, Risk, Resource, Definitional, plus the architecture-internal Risk lens). The last two (Resource, Definitional) produced refinements but no new architectural anchors. **APPROACHING SATURATION.**
- **Ambiguity resolution ratio:** 6 ambiguities identified, 6 resolved with HIGH confidence and structural counter-arguments tested. **HIGH RATIO. No silent drops.**
- **SV delta:** SV1 ("three missing things, possibly shared root, structure unclear") to SV6 ("three structurally distinct fixes at three formula locations, iteration-3.3, Cluster 4 not triggered, operational sequencing implied"). **HIGH DELTA.**
- **Anchor diversity:** 6 constraints, 5 key insights, 5 structural points, 5 foundational principles, 5 meaning-nodes. Multiple types from multiple perspectives. **DIVERSE.**
- **Failure-mode check:**
  - Status Quo Bias: avoided. The check on `f`-as-belief-state honestly re-scoped the existing variable; the Cluster 4 check was structural, not protective.
  - Premature Stabilization: avoided. SV2 did not stabilize; ambiguity collapse forced SV4 reconsideration.
  - Anchor Dominance: actively guarded against. The "shared root" anchor was tested in Ambiguity 1 and demoted from structural-unifier to descriptive-frame.
  - Perspective Blindness: Risk and Definitional perspectives produced uncomfortable challenges (Cluster 4 check, mode distinction operationalization cost). Not all friendly.
  - Clean Resolution Trap: Ambiguity 1's "elegant unifier" resolution was tested and rejected on structural grounds. The clean answer lost.
  - Self-Reference Blindness: external grounding via the user's three concrete cases (Reddit, friend, nightclub) was the structural test for each architectural choice. Not purely framework-internal.

**Overall: PROCEED to decomposition.** Sensemaking is at saturation. Three refinements, three architectural locations, iteration-3.3 label, Cluster 4 non-trigger — all stably resolved.
