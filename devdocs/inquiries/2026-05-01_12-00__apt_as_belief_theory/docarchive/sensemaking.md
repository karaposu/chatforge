---
status: active
discipline: sensemaking
inquiry: apt_as_belief_theory
iteration: 1
---
# Sensemaking: apt_as_belief_theory

## User Input

`devdocs/inquiries/2026-05-01_12-00__apt_as_belief_theory/_branch.md`

Inputs consumed: `_branch.md` (3 hypothesis candidates Alpha/Beta/Gamma + 5 seeds) and `exploration.md` (9 cycles converging on Alpha; Beta and Gamma ruled out; three load-bearing observations forwarded for sensemaking). Adjacent: iteration-3.3 finding (`apt_context_layer/finding.md`), iteration-3.2.1 finding (`attachment_variable_interactions/finding.md`), iteration-3.2 finding (`apt_modulator_landscape/finding.md`).

---

## Initial Sense Version (SV1 — Baseline Understanding)

The user noticed that iteration-3.3's Refinement 1 ("`f` is a cumulative belief state") implies something deeper: APT's variables and modulators are *all* receiver-side beliefs about the sender. Exploration confirmed this and concluded that the resulting belief-frame is a useful clarification (Alpha hypothesis), not a substrate-reframe (Beta) and not circular (Gamma, conditional on external anchoring). The remaining sensemaking job is to stabilize *what specifically* this frame is in the spec — a meta-section, an iteration-3.4 finding, or a companion document — and *how much external anchoring* it needs to avoid Self-Reference Collapse.

---

## Phase 1 — Cognitive Anchor Extraction

### Constraints (limits, requirements, boundaries)

- **C1 — Frame must not change the formula or any iteration-3.0–3.3 commitments.** Exploration confirmed it doesn't; this constraint must be preserved through the spec target choice.
- **C2 — Frame must be externally anchored to avoid Self-Reference Collapse.** Without anchoring to belief-formation cognitive theory, the frame becomes circular (Gamma).
- **C3 — Cluster 4 must remain not-triggered.** The frame is meta, not substrate. Any spec-placement choice that pushes it toward substrate territory is wrong.
- **C4 — Iteration label discipline (from iteration-3.3 sensemaking Ambiguity 5) must be honored.** 3.x.y = clarification; 3.x+1 = structural change preserving ontology; 4 = substrate reframe. The frame doesn't fit any of these cleanly — it's neither structural change nor clarification of relationships.
- **C5 — PRAGMA operationalizability.** Any new predictions the frame produces (multi-source independence, prior-strength, evidence-quality threshold) must be testable from PRAGMA's input scope.

### Key Insights (non-obvious implications)

- **K1 — The frame is a META-FRAME, not a structural-architecture change.** It explains *why* the existing architecture has the structure it does, without changing any component. This is a different kind of spec content than iterations 3.0–3.3 produced.

- **K2 — Iteration-3.3's iteration-label convention has a gap.** The convention covers structural changes (3.x+1), clarifications of existing relationships (3.x.y), and substrate reframes (4). It does NOT cover meta-frames — content that grounds the architecture without changing it. The frame either forces a new convention slot, or fits awkwardly into an existing one.

- **K3 — The property-vs-stance belief distinction (from exploration Cycle 3) is a genuinely new structural insight that the frame surfaces.** It explains *why* `f` combines additively while `g` combines multiplicatively: property-beliefs sum independently; stance-beliefs gate the product because any single stance-failure collapses attachment. This is content the existing iteration-3.3 spec does not state.

- **K4 — The frame's external-anchoring requirement parallels iteration-3.3's optional SDT theoretical-grounding pattern.** Both are external-vocabulary imports without full apparatus commitment. The pattern is now established (iteration-3.3 used it for Refinement 2's threshold model); this inquiry can reuse it for the belief-frame's anchoring.

- **K5 — Three new predictions (multi-source independence, prior-strength, evidence-quality threshold) become formula-level commitments if the frame ships in spec.** If the frame ships only as a companion document, the predictions stay informal. The spec-target choice has empirical consequences.

### Structural Points (core components, relationships)

- **S1 — Three candidate spec targets:**
  - *Meta-section in iteration-3.3 spec* — frame becomes part of 3.3's spec content, retroactively.
  - *Iteration-3.4 finding* — frame ships as a new iteration-numbered finding.
  - *Separate theoretical-grounding companion document* — frame ships as a companion (e.g., `apt_theoretical_grounding.md`) that does not change iteration numbering.

- **S2 — Three external-anchoring levels:**
  - *Vocabulary-only anchor* — one paragraph, importing terminology from belief-formation theory without committing to specific traditions.
  - *Single-tradition anchor* — explicit commitment to one tradition (e.g., Bayesian belief-update) as the canonical mechanism for belief-update in APT.
  - *Multi-section anchor* — explicit connection to multiple traditions (Bayesian, schema theory, attribution theory, Bowlby) as parallel anchors.

- **S3 — Three new predictions** the frame produces, each with different operational-cost profiles:
  - Multi-source independence (medium cost — requires PRAGMA to detect source-correlation across signals)
  - Prior-strength (low cost — extends iteration-3.3 Refinement 1's f_prior treatment)
  - Evidence-quality threshold (zero cost — already in iteration-3.3 Refinement 2; frame just grounds it)

- **S4 — Re-grounding effects on existing structures:** orthogonality test (gates Modulator Suite entry) becomes belief-category-distinctness test; receiver-state pre-condition becomes belief-about-self vs belief-about-sender categorization; Specificity + θ(context) become evidence-quality update-mechanism parameters.

### Foundational Principles (assumptions, rules, axioms)

- **P1 — Architectural minimalism (inherited from iteration-3.3).** Prefer the smallest sufficient change. Vocabulary-only anchor preferred over multi-section anchor unless evidence demands otherwise.
- **P2 — Cluster 4 discipline (inherited).** Frame is meta, not substrate; spec placement must not blur this distinction.
- **P3 — External grounding for self-referential evaluations.** Inherited from sensemaking failure mode #6 (Self-Reference Blindness): when a framework is used to evaluate something that shares its assumptions, external reference points are required.
- **P4 — Frame-load matches frame-content.** A frame that produces three new predictions, sharpens orthogonality test, sharpens scope, and re-grounds receiver-state placement is doing real work — should ship as spec content. A frame that produces only theoretical positioning without operational consequences could ship as companion.

### Meaning-Nodes (central concepts and themes)

- **M1 — Meta-frame as a content category.** The conceptual unifier. The spec needs a slot for content that grounds the architecture without changing it. Iteration-3.3's convention does not have this slot; either the convention extends, or the frame fits awkwardly.
- **M2 — External anchoring as the non-circularity guarantor.** Without it, Gamma materializes.
- **M3 — Property-vs-stance distinction as new structural content.** This is the "buy" component that distinguishes the frame from "merely renaming." Without it, the frame's load shrinks toward the upper bound of Gamma.
- **M4 — Iteration-label convention as a structural-communication channel.** Inherited from iteration-3.3. Maintaining it keeps spec history readable; collapsing it produces unnavigable findings.

### SV2 — Anchor-Informed Understanding

The frame's value is real and operational — at least three new predictions, a sharper orthogonality test, a sharper scope, and the property-vs-stance distinction as new structural content. This is not "merely renaming." But the frame's *kind* of value is meta-architectural: it grounds existing structure rather than adding new structure. The spec target should be chosen to match this kind: the frame should ship as content with iteration-label discipline that signals "meta-frame," not as a structural change (3.x+1) and not as mere clarification (3.x.y) and not as substrate-reframe (4). The convention may need extension to accommodate this. External anchoring is required to prevent Self-Reference Collapse; the level (vocabulary-only / single-tradition / multi-section) needs determination based on how committal the spec wants to be.

---

## Phase 2 — Perspective Checking

### Technical / Logical perspective

- The frame is consistent with iterations 3.0–3.3 (exploration confirmed). Logically, it makes a content claim ("APT specifies which receiver-side beliefs about another person, when held, generate attachment") that can be true or false. If true, three new predictions follow.
- New anchor: **Logical content of the frame.** It's not just a vocabulary swap; it's a content claim that has empirical consequences. Vocabulary swaps don't produce predictions; this does.

### Human / User perspective

- The user's question came from a felt sense that something deeper was happening at iteration-3.3's "f as cumulative belief state" statement. They didn't ask "is this a substrate reframe?" — they asked the meta-question: "is APT a theory of these specific beliefs?" The framing came naturally; it's the user's intuition pulling on a thread.
- New anchor: **The frame matches user intuition.** This is signal that the frame is communicating something real, not just academic. Pedagogical clarity (one of iteration-3.3's medium-weight critique dimensions) is high under the frame.

### Strategic / Long-term perspective

- The 3.x sequence is approaching maturity: iteration-3.0 → 3.1 (operational dynamics) → 3.2 (modulator suite + Resonance) → 3.2.1 (clarifications + Specificity + Double-Collapse + MAGNITUDE/TYPE) → 3.3 (three pre-content refinements). At some point a theoretical-grounding pass becomes valuable for spec consolidation.
- New anchor: **Spec consolidation pressure.** A theoretical-grounding meta-frame at this point in the sequence consolidates the architecture before further iterations build on it. Future inquiries (3.4, 3.5, ...) benefit from having the meta-frame stated.
- Risk: shipping a meta-frame *too early* (before architecture stabilizes) commits the spec to a grounding that may need revision. iteration-3.3's architecture is stable enough now that this risk is low.

### Risk / Failure perspective

- **Risk: Self-Reference Blindness.** Sensemaking failure mode #6 names exactly this case: using APT's concepts to evaluate an APT meta-frame. Mitigation: external anchoring (P3). The mitigation must be load-bearing in the final form, not just a footnote.
- **Risk: Premature substrate-reframe pressure.** If the meta-frame's external anchoring gets too committal (e.g., "APT is fundamentally a Bayesian belief-update model"), the frame slides toward substrate-reframe territory and Cluster 4 questions reopen. Mitigation: vocabulary-only anchoring (S2 first option).
- **Risk: Iteration-label discipline collapse.** If the frame ships as 3.x.y (clarification) when it has empirical content (three predictions), the convention's signal-meaning weakens. If it ships as 3.x+1 (structural change) when no formula component changes, the convention's signal-meaning weakens differently.
- New anchor: **The convention may need a new slot.** Meta-frames are a different content category. Adding a category (e.g., 3.x.M for meta-frame, or just calling it "iteration-3.4 (theoretical grounding)" with that subtitle) may be cleanest.

### Resource / Feasibility perspective

- Vocabulary-only anchoring (one paragraph importing terms like "belief-update," "evidence quality," "schema-match" without apparatus commitment) is low-cost. Multi-section anchoring is high-cost (requires writing up cross-discipline connections at length).
- Two of the three new predictions are PRAGMA-feasible at low cost (prior-strength, evidence-quality threshold — already in iteration-3.3). The third (multi-source independence) requires PRAGMA to detect source-correlation across signals; medium cost.
- New anchor: **Prediction-cost asymmetry.** Two of three predictions are nearly free; one is medium cost. The frame can ship with two-of-three operationalized and the third deferred to empirical agenda.

### Definitional / Consistency perspective

- Does the frame contradict any iteration-3.0–3.3 definition? Each was checked in exploration:
  - Modulator Suite (3 members): preserved.
  - Additive `f`: preserved.
  - Specificity formula: preserved (frame grounds it).
  - Sender-SP from message style: preserved (frame grounds it).
  - MAGNITUDE/TYPE outputs: preserved.
  - Receiver-state pre-condition: preserved (frame grounds it as belief-about-self).
  - Cluster 4 conditions: preserved (frame is meta, not substrate).
- No contradictions. The frame is consistent with all prior iterations.
- Does the frame contradict ITSELF? Test: are all the frame's claims internally consistent?
  - "f and g are receiver-side beliefs about sender" + "Specificity is not a belief; it's an evidence-quality property" + "θ(context) is not a belief; it's an update-mechanism parameter" + "receiver-availability is a belief-about-self, not belief-about-sender" — all consistent. The frame draws a clean line between belief-categories (formula inputs) and belief-update mechanisms (Specificity, θ) and pre-conditions (belief-about-self).
- New anchor: **Internal consistency confirmed.** No internal contradictions in the frame.

### Pedagogical / Onboarding perspective

- A new reader of the iteration-3.3 spec faces eight major architectural elements (4 attachment variables + 3 modulators + Specificity + θ(context) + display-mode coupling + MAGNITUDE/TYPE + Cluster 4 + the formula itself). Without a meta-frame, these read as a list of constructs to memorize. Under the belief-frame, they read as a structured belief-system: which beliefs about another person matter, how those beliefs combine, how those beliefs update.
- New anchor: **Pedagogical anchor is significant.** For a spec that has accumulated five iterations of complexity, a meta-frame that makes the architecture readable to a new reader is a real contribution.

### SV3 — Multi-Perspective Understanding

Major shifts from SV2:

1. **The frame's value is multi-dimensional, not single-purpose.** Logical content (three new predictions), pedagogical clarity (architecture-as-belief-system), strategic consolidation (spec-grounding before further iterations), risk mitigation (sharper orthogonality test, sharper scope, re-grounded receiver-state placement). All seven perspectives identify a distinct value vector.

2. **The iteration-label convention needs a meta-frame slot.** Current convention has three categories (clarification / structural-change-preserving-ontology / substrate-reframe). Meta-frames are a fourth category. Either the convention extends explicitly, or this iteration creates a new slot ad hoc and future inquiries inherit it.

3. **External anchoring should be vocabulary-only.** Resource cost, Cluster 4 risk, and architectural minimalism all point to vocabulary-only. Multi-section or single-tradition commits more than the frame's claim requires.

4. **The Self-Reference Blindness risk is real but well-understood.** The failure mode names exactly this case. Mitigation is in scope (external anchoring at vocabulary level). The mitigation must be load-bearing in the spec — a one-paragraph anchor that explicitly imports external belief-formation vocabulary and disclaims full-apparatus commitment.

5. **Prediction-cost asymmetry suggests staged operationalization.** Two of three predictions are PRAGMA-feasible at low cost; the third is medium cost. The frame can ship in spec with all three predictions named, two of three implementable now, and the third on the empirical agenda.

---

## Phase 3 — Ambiguity Collapse

### Ambiguity 1: Is this a meta-frame, a substrate-reframe, or something else?

**Strongest counter-interpretation:**
The belief-frame could be read as a substrate-reframe: "APT's surface taxonomy of C/H/F/R + g₁/g₂/g₃ is just a useful naming scheme for what is fundamentally Bayesian belief-update over signal evidence; the real substrate is the cognitive belief-formation mechanism." Under this reading, future iterations should formalize the Bayesian update mechanism and demote the variable+modulator ontology to surface taxonomy.

**Why the counter-interpretation fails (structural grounds):**
Exploration Cycle 5 performed the substrate test explicitly. Belief-formation mechanism does not, by itself, predict that exactly four property-belief categories and exactly three stance-belief categories matter for attachment. The ontology of C/H/F/R + g₁/g₂/g₃ is empirical content (these specific belief-categories are the ones humans use to compute attachment), not derivable from belief-formation mechanism alone. A substrate-reframe would need to derive the ontology from a deeper principle; the belief-frame does not do this and does not claim to. The frame is META (it grounds and explains the ontology) not SUBSTRATE (it would replace the ontology). Cluster 4 reopening conditions are documented; this frame does not satisfy them.

**Confidence:** HIGH (substrate test performed; ontology derivability check fails for substrate-reframe reading).

**Resolution:** The belief-frame is a META-FRAME. It grounds the architecture without replacing it. The variable + modulator + specificity ontology remains primary. Belief-formation mechanism is the *update mechanism* by which f and g values are populated, not a substitute for the ontology.

**What is now fixed:** Frame status = meta-frame. Cluster 4 = not triggered. Ontology = preserved.

**What is no longer allowed:** Spec content that demotes C/H/F/R + g₁/g₂/g₃ to "surface taxonomy" or treats Bayesian update as more fundamental than the variable+modulator structure.

**What now depends on this choice:** Spec target (next ambiguity) is chosen from meta-frame-appropriate options (meta-section / 3.4-titled-as-theoretical-grounding / companion document) rather than substrate-reframe options.

**What changed in the conceptual model:** The frame's status is locked as META. The remaining ambiguities are about how meta-frames fit in the spec, not whether this is one.

---

### Ambiguity 2: Where in the spec does the frame live? (Meta-section in 3.3 / Iteration-3.4 / Companion document)

**Strongest counter-interpretation:**
The frame should ship as a meta-section in the iteration-3.3 spec retroactively. Argument: the frame *grounds* iteration-3.3's three refinements (Refinement 1's "f as cumulative belief state" is a direct consequence; Refinements 2 and 3 have natural belief-theoretic readings); without the frame, the spec's grounding is asserted rather than explained. Putting the frame in 3.3 retroactively keeps the spec self-contained and avoids version-numbering inflation.

**Why the counter-interpretation fails (structural grounds):**
Three reasons. First, the frame produces three new predictions (multi-source independence, prior-strength, evidence-quality threshold) — this is empirical content, not just grounding. Embedding empirical content in iteration-3.3 retroactively rewrites that iteration's claims, which collapses iteration-label discipline (the same failure mode P5-C in iteration-3.3's critique was killed for). Second, the frame is qualitatively a different *kind* of content than 3.3's three refinements; combining them obscures both. Third, retroactive editing of iteration-3.3 — which has just been finalized — undermines the spec's history-of-decisions value.

**Confidence:** HIGH (iteration-label-discipline + content-kind-mixing both fail the retroactive option).

**Resolution:** The frame ships as **iteration-3.4** with a subtitle explicitly identifying it as a theoretical-grounding addition (e.g., "iteration-3.4 — Theoretical Grounding: APT as a Belief-Component Theory"). This:
- Preserves iteration-3.3's content as a complete record of the three pre-content refinements.
- Gives the frame its own iteration anchor that future inquiries can refer to.
- Establishes a new category in the iteration-label convention (theoretical-grounding additions are content-bearing iterations, not clarifications and not structural changes).
- Co-locates the three new predictions with the meta-frame that produces them.

**What is now fixed:** Spec target = iteration-3.4. Spec form = a finding document with the same template structure as 3.3.

**What is no longer allowed:** Retroactive embedding of the frame in iteration-3.3. Companion-document-only placement (which would understate the frame's empirical content).

**What now depends on this choice:** The convention extension is now a structural commitment — future iterations may produce theoretical-grounding additions with meta-frame status; iteration-3.4 sets the precedent.

**What changed in the conceptual model:** The frame is content-bearing (three predictions); content-bearing additions deserve their own iteration. The convention extends to include theoretical-grounding as a fourth category alongside clarification, structural-change-preserving-ontology, and substrate-reframe.

---

### Ambiguity 3: How much external anchoring? (Vocabulary-only / Single-tradition / Multi-section)

**Strongest counter-interpretation:**
A single-tradition anchor (e.g., "APT's belief-update is canonically Bayesian") would give the spec stronger theoretical commitment and clearer formal grounding. Vocabulary-only is too loose; multi-section is too dispersed; single-tradition is the principled middle.

**Why the counter-interpretation fails (structural grounds):**
Single-tradition commitment imports the tradition's full apparatus along with its vocabulary. Bayesian belief-update commits APT to specific computational claims about prior-likelihood updating, conjugacy, etc. — claims that may not survive empirical scrutiny in attachment contexts. The minimalism principle (P1) prefers the smallest sufficient anchor. The frame's claim is "APT specifies which beliefs generate attachment" — this requires that "belief" be externally meaningful, not that any specific update-mechanism be canonical. Vocabulary-only meets that requirement; single-tradition exceeds it.

Iteration-3.3 established the vocabulary-only-anchor pattern with optional Signal Detection Theory grounding for Refinement 2. The pattern works: vocabulary import, no apparatus commitment, easy to revise if a different tradition turns out more useful. This iteration should follow the same pattern.

**Confidence:** HIGH (minimalism principle + iteration-3.3 precedent + apparatus-import risk all point to vocabulary-only).

**Resolution:** **Vocabulary-only anchor.** One paragraph at the start of iteration-3.4's spec content imports vocabulary from belief-formation cognitive theory (broadly construed), explicitly disclaims commitment to any specific tradition's full apparatus, and notes that compatibility with multiple traditions (Bayesian, schema-theoretic, attribution-theoretic, Bowlby) is a feature, not a problem.

**What is now fixed:** Anchor level = vocabulary-only. Anchor form = single paragraph with explicit non-commitment disclaimer.

**What is no longer allowed:** Single-tradition commitment in the iteration-3.4 spec. Multi-section apparatus import. Treating any one tradition's update mechanism as canonical for APT.

**What now depends on this choice:** The Self-Reference Collapse risk is mitigated to acceptable level. The frame is non-circular by virtue of the vocabulary-only anchor without committing the spec to apparatus that may need later revision.

**What changed in the conceptual model:** External anchoring is at the vocabulary level only. Tradition-specific apparatus may be imported case-by-case (parallel to iteration-3.3's optional SDT grounding for Refinement 2) but no tradition is canonical.

---

### Ambiguity 4: What goes in iteration-3.4's spec? (Frame statement only / Frame + new predictions / Frame + new predictions + structural insights)

**Strongest counter-interpretation:**
Iteration-3.4 should contain only the frame statement plus external anchor; the three new predictions and the property-vs-stance belief distinction should be deferred to future empirical iterations. Argument: keep 3.4 tight and focused on theoretical-grounding; predictions and distinctions are content for separate iterations.

**Why the counter-interpretation fails (structural grounds):**
The three new predictions and the property-vs-stance belief distinction are *consequences of the frame*, not separate content. If they are deferred, the frame is empty (it produces nothing). The frame is content-bearing precisely because it produces these. Splitting them across iterations would either ship an empty frame in 3.4 (undermining the rationale for 3.4 existing) or ship the predictions/distinctions in some later iteration without their grounding (undermining their explanatory basis).

The frame, the property-vs-stance distinction, and the three predictions form a tight unit. They share derivation (all flow from the frame statement) and they share scope (all are theoretical-grounding content). Iteration-3.4's content should include all of them.

**Confidence:** HIGH (content-coherence test + derivation-coupling test both favor co-location).

**Resolution:** **Iteration-3.4 contains four content blocks:**
1. The frame statement (what APT structurally is, under the belief-frame).
2. The external vocabulary anchor (one paragraph; non-committal disclaimer).
3. The property-vs-stance belief distinction (new structural insight: why f combines additively and g multiplicatively).
4. The three new predictions (multi-source independence, prior-strength, evidence-quality threshold), each named with its operational-cost profile and PRAGMA implementability status.

Plus: re-grounding notes for orthogonality test, receiver-state placement, and Specificity/θ(context) — these are existing structures explained anew under the frame.

**What is now fixed:** Iteration-3.4's spec content scope.

**What is no longer allowed:** Empty-frame-only iteration-3.4 that defers predictions and distinction to later. Splitting the four content blocks across iterations.

**What now depends on this choice:** Decomposition will partition iteration-3.4's writing-work into pieces aligned with these content blocks.

**What changed in the conceptual model:** Iteration-3.4 is content-rich (frame + anchor + distinction + three predictions + re-grounding notes), not a thin grounding statement.

---

### Ambiguity 5: Does the convention need to extend explicitly, or is this implicit?

**Strongest counter-interpretation:**
Iteration-3.4's existence implicitly extends the convention; no explicit extension statement is needed in the spec. Future inquiries will read 3.4 and infer that theoretical-grounding additions are a valid iteration category.

**Why the counter-interpretation fails (structural grounds):**
Iteration-3.3 sensemaking Ambiguity 5 established the iteration-label convention as a structural-communication channel (3.x.y = clarification; 3.x+1 = structural change preserving ontology; 4 = substrate reframe). Implicit extension undermines the convention's signal-strength: a reader of iteration-3.4 may misread it as a structural change (what is the structural change?) or substrate-reframe (Cluster 4 triggered? — no, but this risks confusion). Explicit extension prevents misreading.

Conventions accumulate via explicit statements, not implicit examples. The discipline of stating "iteration-3.4 introduces a fourth iteration category — theoretical-grounding additions — defined as content-bearing meta-frames that ground the architecture without changing it" is small and pays back in future-iteration clarity.

**Confidence:** HIGH (convention-as-structural-communication-channel + explicit-statement-as-discipline both favor explicit extension).

**Resolution:** Iteration-3.4's spec **explicitly extends the iteration-label convention** with a fourth category: "theoretical-grounding additions — content-bearing meta-frames that ground the architecture without changing it." The convention statement appears once, in iteration-3.4's introduction, and is then available for future iterations to reference.

**What is now fixed:** Iteration-3.4 includes an explicit convention-extension paragraph.

**What is no longer allowed:** Implicit-precedent-only extension.

**What now depends on this choice:** Future iterations inherit the four-category convention. iteration-3.5 (if it exists) classifies as one of the four.

**What changed in the conceptual model:** The iteration-label convention now has four categories. Iteration-3.4 sets this in spec stone.

---

### SV4 — Clarified Understanding

After the five ambiguity collapses, the picture is fully resolved:

- **The frame is a META-FRAME**, not a substrate-reframe. Cluster 4 not triggered. Variable + modulator + specificity ontology preserved.

- **Spec target is iteration-3.4** (subtitle: "Theoretical Grounding: APT as a Belief-Component Theory"), with the same finding template as iteration-3.3.

- **External anchoring is vocabulary-only** — one paragraph importing belief-formation cognitive theory vocabulary, disclaiming full-apparatus commitment, parallel to iteration-3.3's optional SDT grounding pattern.

- **Iteration-3.4 contains four content blocks** plus re-grounding notes:
  1. Frame statement
  2. External vocabulary anchor
  3. Property-vs-stance belief distinction
  4. Three new predictions (multi-source independence, prior-strength, evidence-quality threshold)
  5. Re-grounding notes for orthogonality test, receiver-state placement, Specificity/θ(context)

- **The iteration-label convention extends explicitly** — iteration-3.4's spec adds a fourth category (theoretical-grounding additions) to the convention's three existing categories.

What is no longer viable:
- Substrate-reframe placement / Cluster 4 triggering
- Retroactive embedding of frame in iteration-3.3
- Companion-document-only placement (which would understate frame's empirical content)
- Single-tradition or multi-section anchoring (which exceed minimalism)
- Empty-frame-only iteration-3.4 (which defers predictions/distinction)
- Implicit-precedent-only convention extension (which weakens convention signal-strength)

---

## Phase 4 — Degrees-of-Freedom Reduction

### Variables now fixed

- Frame status: **meta-frame** (not substrate; not clarification; not structural-change)
- Spec target: **iteration-3.4** (titled as theoretical-grounding addition)
- Anchoring level: **vocabulary-only** (single paragraph, non-committal)
- Spec content scope: **four content blocks + re-grounding notes**
- Convention extension: **explicit four-category statement**
- Cluster 4 status: **not triggered** (preserved through frame status)
- Existing iterations 3.0–3.3: **all preserved unchanged**

### Options eliminated

- Substrate-reframe placement
- Retroactive iteration-3.3 embedding
- Companion-document-only placement
- Single-tradition apparatus commitment
- Multi-section apparatus import
- Empty-frame iteration-3.4
- Implicit convention extension

### Remaining viable paths (decomposition will pick among these)

1. **How to write the frame statement** — exact wording, how to disambiguate (per exploration Cycle 1) the user's two-claim phrasing into the precise frame statement.
2. **How to write the external vocabulary anchor** — one paragraph, what specific vocabulary to import, what non-commitment disclaimer to make.
3. **How to write the property-vs-stance belief distinction** — explanation, why it matters structurally (additive vs multiplicative combination), worked example.
4. **How to write each of the three new predictions** — wording, operational-cost profile, PRAGMA implementability status, empirical-test sketch.
5. **How to write the re-grounding notes** — for orthogonality test, receiver-state placement, Specificity/θ(context).
6. **How to write the convention-extension paragraph** — definition of the fourth category, integration with the existing three.
7. **Finding-document assembly** — structure, cross-references to iteration-3.2, 3.2.1, 3.3.

### SV5 — Constrained Understanding

The solution space is now bounded:

- The architectural answer is: **iteration-3.4 ships a META-FRAME with four content blocks plus re-grounding notes plus an explicit convention extension. External anchoring is vocabulary-only.**
- Decomposition's question-tree will partition along the seven viable paths above. Most pieces are content-writing; the convention-extension piece is structurally distinct (it touches the spec convention itself, not just iteration-3.4's content).
- Innovation will produce variants per piece — wording, tone, level of formality, anchor specificity.
- Critique will evaluate variants against: faithfulness to the meta-frame status, preservation of iteration-3.0–3.3 commitments, external-anchoring sufficiency (non-circularity), Cluster 4 discipline, PRAGMA-operationalizability of the three predictions, iteration-label convention discipline.

The iteration-3.4 finding's outline is now predictable: introduction (motivation from user's question + frame statement disambiguation), external vocabulary anchor, the four content blocks, re-grounding notes, convention-extension paragraph, predictions with PRAGMA-implementability table, Open Questions (mostly empirical agenda for the multi-source independence prediction).

---

## Phase 5 — Conceptual Stabilization

### SV6 — Stabilized Model

**Iteration-3.4 of APT theory is a theoretical-grounding addition that ships APT's first META-FRAME: a structural statement of which receiver-side beliefs about another person, when held, generate attachment. The frame grounds the existing iterations' architecture without replacing any component. It produces three new predictions (multi-source-independence, prior-strength, evidence-quality threshold), one new structural insight (the property-vs-stance belief distinction explaining why `f` combines additively and `g` multiplicatively), and re-grounding notes for orthogonality test, receiver-state placement, and Specificity/θ(context). External anchoring is vocabulary-only — a single paragraph importing belief-formation cognitive theory vocabulary with explicit non-commitment to any specific tradition's full apparatus.**

**Architectural status:**
- Meta-frame, not substrate-reframe.
- All iteration-3.0–3.3 commitments preserved.
- C/H/F/R + g₁/g₂/g₃ ontology unchanged; specificity formula unchanged; Modulator Suite at 3 members.
- Cluster 4 reopening conditions reviewed and not satisfied; Cluster 4 NOT triggered.

**Convention extension:**
- The iteration-label convention extends explicitly from three categories (clarification / structural-change-preserving-ontology / substrate-reframe) to four (adding theoretical-grounding additions as the fourth).
- Iteration-3.4 is the precedent-setter; future iterations classify as one of the four.

**Operational status:**
- Two of three new predictions are PRAGMA-feasible at low cost (prior-strength is an extension of iteration-3.3 Refinement 1's f_prior treatment; evidence-quality threshold is iteration-3.3 Refinement 2 re-grounded).
- One prediction is medium-cost (multi-source independence requires PRAGMA to detect source-correlation across signals).
- Vocabulary anchor is zero-cost (one paragraph, no apparatus implementation).

**What iteration-3.4 enables that 3.0–3.3 alone do not:**
- Theoretical grounding for the variable + modulator ontology (currently asserted as empirically derived; now connected to belief-formation cognitive theory).
- Sharper orthogonality test (re-grounded as belief-category-distinctness test).
- Sharper scope (beliefs about sender = in; beliefs about self = out; mechanism parameters = separate).
- Pedagogical clarity (architecture-as-belief-system framing for new readers).
- Three new empirical predictions.
- An explanation of why `f` is additive while `g` is multiplicative (property-vs-stance belief distinction).
- A theoretical positioning for APT (cognitive-theoretic tradition; in dialogue with Bowlby, adult attachment theories).

### How SV6 differs from SV1

SV1: a frame might be useful clarification, might be substrate-reframe, might be circular; spec target unclear; anchoring level unclear.

SV6: the frame is a META-FRAME ships as iteration-3.4 (theoretical-grounding addition) with vocabulary-only external anchor and four content blocks plus re-grounding notes; iteration-label convention extends explicitly to a fourth category; Cluster 4 not triggered; two of three new predictions PRAGMA-feasible at low cost.

---

## Saturation Indicators (Telemetry)

- **Perspective saturation:** 7 perspectives applied (Technical, Human, Strategic, Risk, Resource, Definitional, Pedagogical). The last two (Resource, Pedagogical) produced new anchors (prediction-cost asymmetry; pedagogical anchor significance) without changing the frame's status. **APPROACHING SATURATION.**
- **Ambiguity resolution ratio:** 5 ambiguities identified, 5 resolved with HIGH confidence and structural counter-arguments tested. **HIGH RATIO. No silent drops.**
- **SV delta:** SV1 ("frame might be Alpha/Beta/Gamma; spec target unclear") to SV6 ("META-frame; iteration-3.4 with four content blocks + convention extension; vocabulary-only anchor; Cluster 4 not triggered"). **HIGH DELTA.**
- **Anchor diversity:** 5 constraints, 5 key insights, 4 structural points, 4 foundational principles, 4 meaning-nodes. Multiple types from multiple perspectives. **DIVERSE.**
- **Failure-mode check:**
  - Status Quo Bias: avoided. The frame's content-bearing status (three predictions) was honestly acknowledged, even though it required extending the iteration convention rather than fitting an existing slot.
  - Premature Stabilization: avoided. SV2 did not stabilize; ambiguity collapse forced SV4 reconsideration of spec target, anchor level, content scope, and convention extension.
  - Anchor Dominance: avoided. The "meta-frame" anchor was tested against substrate-reframe and circularity readings; both alternatives ruled out on structural grounds, not by anchor inertia.
  - Perspective Blindness: Risk and Definitional perspectives both produced uncomfortable challenges (Self-Reference Blindness risk; convention-extension requirement). Not all friendly.
  - Clean Resolution Trap: Ambiguity 1's "elegant substrate-reframe" reading was tested with the strongest possible derivation argument and rejected on structural grounds (ontology not derivable from belief-formation mechanism alone). The clean answer lost.
  - Self-Reference Blindness: actively guarded against. The failure mode names exactly this case (using APT to evaluate an APT meta-frame). Mitigation (vocabulary-only external anchoring) is load-bearing in the final form, not a footnote.

**Overall: PROCEED to decomposition.** Sensemaking is at saturation. Frame status, spec target, anchoring level, content scope, and convention extension all stably resolved.
