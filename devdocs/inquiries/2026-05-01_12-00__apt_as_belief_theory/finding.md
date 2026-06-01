---
status: active
refines: devdocs/inquiries/apt_context_layer/finding.md
---
# Finding: apt_as_belief_theory

## Changes from Prior

**Prior path:** devdocs/inquiries/apt_context_layer/finding.md (iteration-3.3)

This finding ships **iteration-3.4** of APT theory. It is a *theoretical-grounding addition* — a new fourth category in the iteration-label convention. iteration-3.4 does not change any formula component, does not add a variable or modulator, does not trigger Cluster 4 (the documented condition under which APT's variable + modulator + specificity ontology would need to be replaced by a deeper substrate).

**Revision trigger:** User question. After completing iteration-3.3 (the `apt_context_layer` inquiry), the user pulled on Refinement 1's framing — "`f` is a cumulative belief state" — and asked: "in the core of attachment there is belief? and apt is the component of significant beliefs?" That observation surfaced something the existing iterations had implicitly assumed but never said.

**What's preserved:** All commitments from iterations 3.0 through 3.3. The Modulator Suite stays at three modulators (Self-Positioning, Coherence, Emotional Composure). The four attachment variables (Charm, Hope, Fear, Resonance) stay additive in `f`. Specificity stays as the magnitude factor; θ(context) stays as its context-dependent threshold. Sender-SP-from-message-style stays. MAGNITUDE/TYPE outputs stay. The Double-Collapse mechanism stays. iteration-3.3's three refinements (`f` as cumulative belief state; θ context-parameterized; g₁ display-mode coupled to Attention-Hope) stay. The receiver-state pre-condition stays outside formula scope.

**What's changed:** Nothing structural. iteration-3.4 *grounds* the existing architecture rather than changing it.

**What's new:**
1. The frame statement: APT is structurally a theory of *which receiver-side beliefs about another person, when held, generate attachment*. The four `f`-variables are additive *property-belief* categories. The three `g`-modulators are multiplicative *stance-belief* categories. The formula is the structural claim about how these belief-categories combine to produce a behavioral disposition (attachment).
2. The property-vs-stance belief distinction — a structural insight that explains *why* `f` combines additively while `g` combines multiplicatively. iteration-3.2 made the architectural decision empirically; iteration-3.4 explains it.
3. Three new predictions: multi-source independence (genuinely new), prior-strength (re-grounding of iteration-3.3 Refinement 1), evidence-quality threshold (re-grounding of iteration-3.3 Refinement 2).
4. Re-grounding notes for three existing structures (orthogonality test, receiver-state pre-condition placement, Specificity + θ(context)) — each previously stipulated; now structurally explained.
5. An explicit four-category extension of the iteration-label convention. The fourth category is *theoretical-grounding additions* — content-bearing meta-frames that ground the architecture without changing it. iteration-3.4 is the precedent-setter.

**Migration:** No PRAGMA implementation changes. iteration-3.4's predictions are testable; two of three are already implementable from iteration-3.3 capability (prior-strength is an extension of iteration-3.3 Refinement 1's f_prior treatment; evidence-quality threshold is iteration-3.3 Refinement 2 re-grounded). The genuinely new prediction (multi-source independence) requires PRAGMA to detect source-correlation across signals — medium operational cost, parallel to iteration-3.3 Refinement 3's mode-distinction work.

---

## Question

From `_branch.md`:

> "Is APT (Attachment & Presentation Theory — the framework developed across iterations 3.0 → 3.1 → 3.2 → 3.2.1 → 3.3) structurally a theory of *which receiver-side beliefs about another person generate attachment when held*, and if so, what does that meta-frame enable that the current iteration-sequence framing does not?"

Goal: a diagnostic answer with three components — is the belief-frame correct; what does it buy us; what does it cost us. The user should be able to decide between three readings (Alpha: useful clarification; Beta: substrate-reframe trigger; Gamma: circular self-reference).

---

## Finding Summary

- **The belief-frame is correct.** APT is structurally a theory of which receiver-side beliefs about another person, when held, generate attachment. All four `f`-variables (Charm, Hope, Fear, Resonance) map cleanly onto property-beliefs about the sender. All three `g`-modulators (Self-Positioning, Coherence, Emotional Composure) map cleanly onto stance/state-beliefs about the sender. The mapping is not strained; it does not contradict any iteration-3.0–3.3 commitment; and it explains things the existing architecture asserted without grounding.

- **The belief-frame is a META-FRAME, not a substrate-reframe.** It grounds the architecture without replacing it. Belief-formation cognitive theory (broadly construed: Bayesian update, schema theory, attribution theory, Bowlby's working models) supplies the *vocabulary* for how belief-categories update; it does not derive the C/H/F/R + g₁/g₂/g₃ taxonomy. Cluster 4 is honestly checked and not triggered.

- **The belief-frame is non-circular when externally anchored.** A vocabulary-only anchor — one paragraph importing belief-formation cognitive theory terms with explicit non-commitment to any specific tradition's full apparatus — is sufficient to prevent Self-Reference Collapse. APT does not define "belief" by what APT happens to count as a belief; it borrows the term from external cognitive theory.

- **What the frame buys: theoretical grounding.** The variable + modulator + specificity ontology was previously asserted as empirically derived. Under the frame, the ontology connects to belief-formation cognitive theory, which provides the vocabulary for *how* the variables update.

- **What the frame buys: the property-vs-stance belief distinction.** This is a new structural insight. Property-beliefs (what a person is — their status, threat, future-promise, world-model match) sum independently because each property contributes to attachment-generation independently of the others. Stance/state-beliefs (how a person is — their agency-direction, internal coherence, emotional regulation) gate the product because any single stance-failure destroys the receiver's ability to form a stable belief about the sender. The distinction explains *why* iteration-3.2's architectural decision (additive `f` vs multiplicative `g`) was structurally correct rather than just empirically observed.

- **What the frame buys: three new predictions.** *Multi-source independence* (genuinely new): if PRAGMA detects multiple independent evidence sources signaling the same f-variable direction, the f-update is faster than if a single source signals or sources are correlated. *Prior-strength* (re-grounding of iteration-3.3 Refinement 1): strong f_prior is slow to update by single in-interaction signals. *Evidence-quality threshold* (re-grounding of iteration-3.3 Refinement 2): low-specificity evidence does not update beliefs even if frequent.

- **What the frame buys: sharper orthogonality test.** iteration-3.2 introduced the orthogonality test as the gatekeeping criterion for Modulator Suite entry; iteration-3.3 applied it to kill a proposed g₄(Mode) modulator. Under the frame, the test re-reads as belief-category-distinctness — a putative new variable or modulator must be a belief-category that is not a recategorization of existing belief-categories. The test now has a structural basis.

- **What the frame buys: explained pre-condition placement.** iteration-3.3 noted receiver availability is outside APT's formula scope. Under the frame, this is explained: APT models receiver-side beliefs *about the sender*; receiver availability is a meta-belief *about self*, structurally a different belief category. The placement is no longer stipulated; it follows from the frame's scope of sender-directed beliefs.

- **What the frame costs: a real Self-Reference Collapse risk that is mitigated by external anchoring.** Without anchoring to external belief-formation cognitive theory, the frame becomes circular ("APT defines beliefs by what APT counts as beliefs"). The mitigation is a one-paragraph vocabulary anchor parallel to iteration-3.3's optional Signal Detection Theory grounding for Refinement 2. The cost is well-understood and bounded.

- **What the frame costs: a fourth iteration-label category.** The convention established in iteration-3.3 (clarification / structural-change-preserving-ontology / substrate-reframe) extends to four categories. Iteration-3.4 is the precedent-setter for *theoretical-grounding additions*. Future iterations classify against the four-category convention.

- **The user's three candidate readings — Alpha (useful clarification), Beta (substrate-reframe trigger), Gamma (circular self-reference).** Alpha is supported. Beta is ruled out (frame is meta, not substrate; Cluster 4 not triggered). Gamma is ruled out conditionally (frame is non-circular if externally anchored, which iteration-3.4 ensures via the vocabulary-only anchor).

---

## Finding

### 1. The belief-frame, stated precisely

APT specifies which receiver-side beliefs about another person, when held, generate attachment. The four `f`-variables (Charm, Hope, Fear, Resonance) are additive *property-belief* categories. The three `g`-modulators (Self-Positioning, Coherence, Emotional Composure) are multiplicative *stance-belief* categories. The formula `Attachment ≈ f(C, H, F, R) × g₁(SP) × g₂(Coherence) × g₃(EC)` is the structural claim about how these belief-categories combine to produce attachment as a behavioral disposition.

Two readings of the user's framing must be disambiguated. First reading: "attachment IS belief." Second reading: "attachment is GENERATED BY beliefs." APT says the second. Attachment is a behavioral disposition — the receiver's tendency to engage with, persist toward, return to the sender. APT computes this disposition from receiver-side beliefs about the sender. APT does not list specific beliefs (it does not say "believe X about person Y"); it specifies which *categories* of belief about another person are load-bearing for attachment-generation.

**External vocabulary anchor.** APT's account of how f-values and g-values are populated borrows vocabulary from belief-formation cognitive theory broadly construed — Bayesian belief-update (prior, likelihood, posterior, independence-of-evidence), schema theory (schema-matching for Resonance), attribution theory (agency-direction inference for Self-Positioning), and the working-models tradition descending from Bowlby (relational availability schemas). APT does not commit to any specific tradition's full apparatus; compatibility with multiple traditions is treated as a feature, not a problem to resolve. Tradition-specific apparatus may be imported case-by-case (parallel to iteration-3.3's optional Signal Detection Theory grounding for the context-dependent threshold) but no tradition is canonical for APT.

**Theoretical positioning.** APT belongs to the cognitive-theoretic tradition of relationship modeling (Bowlby's parent-child attachment theory; adult attachment theory's anxious/avoidant/secure styles; schema-based approaches to relational understanding) rather than the decision-theoretic tradition (rational choice theory of partner selection, match theory in marriage markets, utility-maximization models of relationship investment). Within the cognitive-theoretic tradition, APT's specific contribution is structural: a particular set of belief-categories (4 property + 3 stance) with a particular combination structure (additive `f` × multiplicative `g`) that produces attachment as output.

A note on the negative-space framing: most beliefs about another person — their hair color, height, ZIP code, favorite music — do not generate attachment. APT names a small set that does and explains why others do not. The frame's claim is structural (closure-via-combinatorial-structure of seven belief-categories), not enumerative (a list of inclusions or exclusions).

### 2. The property-vs-stance belief distinction

APT's belief-categories split into two kinds.

*Property-beliefs* about the sender — beliefs about what the sender is — populate the `f`-variables:
- Charm = "this person is high-status / competent / impressive"
- Hope = "interaction with this person will yield future positive outcomes"
- Fear = "this person can harm me / poses threat"
- Resonance = "this person shares world-models / values / ways of seeing with me"

*Stance/state-beliefs* about the sender — beliefs about how the sender is — populate the `g`-modulators:
- Self-Positioning = "this person acts from their own evaluation; agency-direction toward self"
- Coherence = "this person presents a stable, alignable mental model over time"
- Emotional Composure = "this person regulates their affective state; not contagious-disregulating"

**Why this distinction explains additive `f` vs multiplicative `g`.** Property-beliefs sum independently because each property contributes to attachment-generation independently of the others — being high-status, being a future-positive prospect, being a threat to navigate, sharing world-models, are independent attachment generators that add. iteration-3.2 confirmed this empirically: Resonance can generate attachment alone (the shared-niche-interest case, with Charm/Hope/Fear at zero). High-status alone (the celebrity case) can generate Charm-dominated attachment without other variables. Each property-belief is independently sufficient for partial attachment.

Stance-beliefs gate the product because any single stance-failure destroys the receiver's ability to form a stable belief about the sender. A Coherence-collapse (the receiver cannot form a stable mental model of the sender because their behavior is contradictory across time) means the receiver cannot consolidate attachment regardless of how favorable the property-beliefs are — there is no consistent person to attach to. An Emotional Composure failure (contagious disregulation) destroys engagement at the affective level. A Self-Positioning collapse (Supplication-display) means the sender's agency-direction is read as deferring entirely to the receiver, which removes the sender as an independent center of agency the receiver could attach to.

**Worked example demonstrating multiplicative gating.** A sender with high property-beliefs across the board (genuine Charm + Hope + Resonance from a long acquaintance) but a single stance-failure (Coherence collapse from contradictory behavior over time) generates attachment that decays — even as the property-beliefs remain favorable on snapshot evaluation, the receiver loses the ability to consolidate them into a stable belief about the sender, and attachment cannot persist.

**Worked example demonstrating additive sum.** A sender with one strong property-belief (Resonance only — the shared niche interest case) and minimal Charm/Hope/Fear, with all g-modulators clean (the sender displays consistent agency-direction, coherent self-presentation, regulated emotional state), generates real attachment. A single property-belief is sufficient when stance-beliefs don't gate it down.

**What iteration-3.2 noticed but did not name.** iteration-3.2's classification (Resonance as 4th attachment variable, additive in f; Modulator Suite, multiplicative in g) was driven by the orthogonality test (can it generate attachment alone? can its failure collapse attachment alone?). The test was implicitly distinguishing property-beliefs (which generate independently) from stance-beliefs (which gate the whole). The belief-frame names what the orthogonality test was implicitly tracking.

### 3. Three predictions the frame produces

The frame produces three predictions. *Honesty flag:* one of the three is genuinely new content; two are re-groundings of existing iteration-3.3 predictions, connecting them to belief-update mechanisms. The spec explicitly labels which is which.

**Prediction 1 — Multi-source independence (genuinely new).** If PRAGMA detects multiple independent evidence sources signaling the same f-variable direction (e.g., social proof + reputation + warm-intro all signaling high Charm), the f-update is faster than if a single source signals or if multiple sources are correlated. Independent evidence sources update belief multiplicatively (in the Bayesian-update sense — combining likelihoods independently); correlated evidence updates less than its raw count would suggest because the sources are not providing independent information. *PRAGMA implementability:* medium cost. Requires a new classifier for source-independence assessment (detecting whether multiple signals come from genuinely independent observers vs from correlated sources within a network). *Empirical test sketch:* hold f_prior at zero; vary number-and-independence of evidence sources signaling the same direction; measure update rate.

**Prediction 2 — Prior-strength (re-grounding of iteration-3.3 Refinement 1).** Strong f_prior (well-established prior belief from rich history of evidence) is slow to update by single in-interaction signals; weak f_prior is fast. *PRAGMA implementability:* low cost — extends iteration-3.3 Refinement 1's f_prior treatment with update-rate predictions. *Empirical test sketch:* establish f_prior at high vs zero via warm-intro + social-proof manipulation; deliver same single in-interaction signal; compare attachment-formation rate.

**Prediction 3 — Evidence-quality threshold (re-grounding of iteration-3.3 Refinement 2).** Low-specificity evidence (specificity below θ(context)) does not update beliefs even if frequent. iteration-3.3's Refinement 2 had this implicit; the frame makes it explicit by reading θ(context) as the channel-specific cutoff below which evidence does not count for update. *PRAGMA implementability:* zero cost — re-grounding only. The prediction is already in iteration-3.3.

| Prediction | Genuinely new? | PRAGMA cost |
|---|---|---|
| Multi-source independence | Yes | Medium |
| Prior-strength | No (re-grounding) | Low |
| Evidence-quality threshold | No (re-grounding) | Zero |

*Optional theoretical-grounding overlay (Bayesian belief-update vocabulary).* The three predictions can be expressed in Bayesian belief-update vocabulary: multi-source independence corresponds to Bayes' assumption that independent evidence updates posterior multiplicatively; prior-strength corresponds to the strength of the prior in Bayes' update; evidence-quality threshold corresponds to a likelihood-cutoff. This vocabulary is one of several tradition-specific anchors APT may draw on (per the vocabulary-only commitment); Bayesian apparatus is not canonical for APT. The overlay is provided for readers from quantitative cognitive science backgrounds who can use the recognizable formal shapes.

### 4. How the frame re-grounds existing structures

iteration-3.4's frame does more than name what was implicit; it re-grounds three existing structures from prior iterations, replacing stipulations with explanations.

**Orthogonality test re-grounding.** iteration-3.2 introduced the orthogonality test as the gatekeeping criterion for Modulator Suite entry: a putative new modulator must have value independent of existing modulators. iteration-3.3 applied this test to kill a proposed g₄(Mode) modulator (g₄ had no value independent of g₁ × context, so it failed orthogonality). Under the belief-frame, the test re-reads as belief-category-distinctness: a putative new variable or modulator must be a belief-category that is not a recategorization of existing belief-categories (C/H/F/R as property-beliefs; SP/Coherence/EC as stance-beliefs). The test had a structural basis it had not previously made explicit.

**Receiver-state pre-condition re-grounding.** iteration-3.3 noted that receiver availability/receptiveness is outside APT's formula scope (a pre-condition, not a variable). Under the belief-frame, this placement is explained: APT models receiver-side beliefs *about the sender*; receiver availability is a meta-belief *about self* (am I open to forming attachments?), structurally a different belief category. The pre-condition is no longer stipulated — it follows from the frame's scope of sender-directed beliefs.

**Specificity + θ(context) re-grounding.** iteration-3.2.1 introduced Signal Specificity as a magnitude factor; iteration-3.3 added a context-dependent threshold θ(context) in Refinement 2. Under the belief-frame, Specificity is the evidence-quality measure for belief-update; θ(context) is the channel-specific cutoff below which evidence does not count for update. iteration-3.3's Refinement 2 had this implicit; the frame makes it explicit: signals below θ are discarded as non-informative evidence rather than weighted-but-low evidence.

**The pattern.** Existing iterations made empirically correct architectural decisions on grounds the spec did not formalize. The frame formalizes the grounds. No iteration content changes; the spec's explanatory depth increases.

### 5. Architectural status of iteration-3.4

**Iteration-label convention extension.** iteration-3.3 sensemaking established the iteration-label convention as a structural-communication channel: 3.x.y for clarifications of existing relationships; 3.x+1 for structural changes preserving ontology; 4 for substrate reframes. iteration-3.4 fits none of these. It is not a clarification (it produces three new predictions and a new structural insight). It is not a structural change (no formula component changes). It is not a substrate reframe (Cluster 4 explicitly not triggered).

The convention extends explicitly to a fourth category: **theoretical-grounding additions** — content-bearing meta-frames that ground the architecture without changing it. The criteria for this category are:
- *Content-bearing:* produces new predictions, new structural insights, or new explanatory depth (not pure relabeling).
- *Meta-architectural:* grounds rather than changes (no formula component is added, removed, or relationally restructured).
- *Externally anchored:* not circular (vocabulary anchored to external cognitive theory, with explicit non-commitment to specific apparatus).
- *Preserves all prior iterations:* every prior iteration's commitments survive.

iteration-3.4 is the precedent-setter for this category. Future iterations classify against the four-category convention.

**Cluster 4 explicit re-check.** Each of iteration-3.4's content blocks examined for substrate-reframe pressure:
- *Frame statement:* meta-architectural; grounds the existing variable + modulator + specificity ontology; does not replace it. Belief-formation cognitive theory supplies the *vocabulary* for how categories update; it does not *derive* the C/H/F/R + g₁/g₂/g₃ taxonomy. The taxonomy remains primary; the frame explains rather than restructures.
- *Property-vs-stance distinction:* explains the existing additive-vs-multiplicative combination structure; does not change it.
- *Three predictions:* operate within the existing variable structure (one new, two re-groundings).
- *Three re-grounding notes:* apply the frame to existing structures; do not change them.
- *Convention extension:* adds a category; does not replace any existing category or introduce a substrate.

**Cluster 4 verdict: NOT TRIGGERED.** The reopening conditions documented in iteration-3.2 (additional modulators OR ontological inadequacy) reviewed and confirmed not satisfied: zero modulators added; ontology absorbs all iteration-3.4 content blocks.

---

## Next Actions

### MUST

- **What:** Integrate iteration-3.4 spec content into a dedicated spec file at `chatforge/services/profiling_data_extraction/pragma/core/apt_iteration_3_4.md` (parallel to iteration-3.3's pattern).
  **Who:** spec maintainer.
  **Gate:** before any future iteration-3.5 inquiry, or before downstream PRAGMA work that would benefit from the property-vs-stance distinction or the multi-source independence prediction, whichever is sooner.
  **Why:** without a dedicated spec file, iteration-3.4's belief-frame is finding-only and the spec itself doesn't reflect the theoretical grounding. Future PRAGMA work would build against iteration-3.3 alone and miss the frame's predictions and gatekeeping content.

- **What:** Add forward-reference notes to the iteration-3.3 finding (`apt_context_layer/finding.md`) and to the iteration-3.3 spec file (when it exists) pointing to iteration-3.4 as their successor.
  **Who:** spec maintainer.
  **Gate:** at the same time as the dedicated spec file is created.
  **Why:** keeps the iteration history navigable; future readers landing on 3.3 can find the theoretical grounding.

### COULD

- **What:** Develop an optional "Theoretical Grounding" companion section that imports Bayesian belief-update vocabulary as a cross-discipline anchor for the three predictions.
  **Who:** spec maintainer; optional based on audience.
  **Gate:** if the iteration-3.4 spec is being read by audiences with quantitative cognitive science / computational modeling backgrounds and would benefit from the recognizable Bayesian formal shapes.
  **Why:** gives the predictions a vocabulary that connects to a mature adjacent field. The grounding is informal and explicitly framed as external grounding (parallel to iteration-3.3's optional SDT grounding for Refinement 2), not architectural commitment to Bayesian apparatus.

- **What:** Develop PRAGMA's source-independence classifier for the multi-source independence prediction.
  **Who:** PRAGMA detection layer development.
  **Gate:** when source-correlation detection becomes feasible from PRAGMA's existing input scope (channel metadata, social-proof markers, mutual-connection graph data) — likely after iteration-3.3 Refinements 1 and 2 are operationally complete.
  **Why:** the multi-source independence prediction is the genuinely new prediction iteration-3.4 produces; without source-correlation detection, the prediction cannot be tested empirically.

### DEFERRED

- **What:** Empirical validation of the multi-source independence prediction.
  **Gate:** when controlled comparison studies become feasible — paired observations holding f_prior at zero, varying the number-and-independence of evidence sources signaling the same direction, with ≥ 30 paired observations.
  **Why if revived:** confirms or falsifies the genuinely-new prediction the frame produces. Confirmation strengthens the frame's claim to be content-bearing; falsification would require the frame's prediction-generation mechanism to be re-examined.

- **What:** Re-evaluate killed Assembly 2 (canonical-Bayesian apparatus commitment).
  **Gate:** observable trigger — if a future inquiry empirically validates Bayesian update for APT's f-variable formation specifically (e.g., parameter-fit studies show that Bayesian update accurately predicts f-variable update rates across a wide range of contexts).
  **Why if revived:** apparatus-level commitment becomes worth its reversal-cost only if the apparatus is empirically validated for APT's domain.

- **What:** Investigate the temporal dimension implicit in stance-beliefs (the killed P2-C contrarian's seed).
  **Gate:** condition-bound — if PRAGMA's temporal-pattern-detection produces signals not currently classified by the property-vs-stance distinction (e.g., a phenomenon where the temporal pattern of belief-update matters in a way the current distinction doesn't capture).
  **Why if revived:** the temporal dimension may reveal a sub-axis of the property-vs-stance distinction that warrants spec content.

---

## Reasoning

### Why the frame is a META-FRAME, not a substrate-reframe

Sensemaking Ambiguity 1 examined whether the belief-frame should be read as a substrate-reframe — "APT's surface taxonomy of C/H/F/R + g₁/g₂/g₃ is just useful naming for what is fundamentally Bayesian belief-update over signal evidence; the real substrate is the cognitive belief-formation mechanism." This reading was tested with the strongest possible argument and rejected on structural grounds.

The substrate test: belief-formation mechanism, by itself, does not predict that exactly four property-belief categories and exactly three stance-belief categories matter for attachment. The ontology of C/H/F/R + g₁/g₂/g₃ is empirical content (these specific belief-categories are the ones humans actually use to compute attachment), not derivable from belief-formation mechanism alone. A substrate-reframe would need to derive the ontology from a deeper principle; the belief-frame does not do this and does not claim to.

The frame is META: it grounds the architecture (explains why the variables are belief-categories and how they update) and explains the architecture (why `f` is additive and `g` multiplicative). The frame is not SUBSTRATE: it does not replace the variable + modulator + specificity ontology with belief-formation mechanisms. Cluster 4 reopening conditions from iteration-3.2 (additional modulators OR ontological inadequacy) reviewed; zero modulators added; ontology adequate. Cluster 4 NOT triggered.

### Why iteration label is 3.4 (not 3.3.1 or 4 or implicit)

Sensemaking Ambiguity 5 examined the iteration-label decision. iteration-3.3 sensemaking had established the convention with three categories. iteration-3.4 fits none of them.

The candidate of folding iteration-3.4 into iteration-3.3 retroactively (Sensemaking Ambiguity 2's strongest counter-interpretation) was rejected because: iteration-3.4 produces empirical content (three predictions); embedding empirical content in iteration-3.3 retroactively rewrites that iteration's claims, which collapses iteration-label discipline (the same failure pattern that killed iteration-3.3's P5-C 'update 3.2.1 in place'). iteration-3.4 is qualitatively different content (meta-frame) than 3.3's three pre-content refinements; combining them obscures both.

The candidate of substrate-reframe placement (Cluster 4 triggered, iteration label = 4) was rejected for the substrate-test reasons above.

The candidate of implicit-only convention extension (the killed P5-C contrarian) was rejected because conventions accumulate via explicit statements, not implicit examples; implicit extension undermines the convention's signal-strength.

The fourth category (theoretical-grounding additions) is the right slot. iteration-3.4 is the precedent-setter; the convention extends explicitly.

### Why external anchoring is vocabulary-only

Sensemaking Ambiguity 3 examined three anchoring levels. The candidate of single-tradition apparatus commitment ("APT's belief-update is canonically Bayesian") was rejected because it imports the tradition's full apparatus along with vocabulary; specific computational claims (priors, conjugacy, evidence-independence assumption strength) may not survive empirical scrutiny in attachment contexts.

The candidate of multi-section apparatus import (Bayesian + schema + attribution + Bowlby all developed at length) was rejected on architectural minimalism — the frame's claim ("APT specifies which beliefs generate attachment") requires that "belief" be externally meaningful, not that any specific update-mechanism be canonical.

Vocabulary-only meets the requirement; single-tradition exceeds it. iteration-3.3's optional SDT grounding pattern (vocabulary import, no apparatus commitment, easy to revise) is the precedent. iteration-3.4 follows the same pattern.

### Why Self-Reference Collapse risk is mitigated

Sensemaking failure mode #6 names exactly this case: using APT's concepts to evaluate an APT meta-frame is circular if "belief" is defined by what APT happens to count as a belief.

The mitigation is the vocabulary-only external anchor: "belief" is borrowed from external belief-formation cognitive theory (Bayesian, schema, attribution, Bowlby), each of which has an empirically-grounded definition independent of APT. APT's claim that C/H/F/R + g₁/g₂/g₃ are the belief-categories that generate attachment is then an empirical claim, not a definitional one — falsifiable in principle by showing that a belief-category outside this set generates attachment, or that one of these categories does not.

The mitigation is load-bearing in iteration-3.4's spec. The vocabulary anchor appears as content (one paragraph, prominent placement in P1's frame foundation), not as a footnote. Critique D2 (Self-Reference Avoidance / External Anchoring) is a critical-weight dimension; Assembly 2 (canonical-Bayesian apparatus commitment) was killed precisely on the apparatus-commitment risk that would have triggered Self-Reference Collapse — apparatus-level commitments are circular if apparatus is not empirically validated for APT's domain, while vocabulary-level commitments are not.

### Killed candidates and what was learned

- **P1-C — negative-space framing as primary frame.** REFINED to one-sentence aside. The system-level inversion converged back to the positive frame because the structural claim is closure-via-combinatorial-structure of seven belief-categories, not enumeration. The negative-space framing has rhetorical didactic value (foregrounding that APT names a small set; most beliefs are attachment-irrelevant) but cannot deliver precision as primary framing. *Seed:* the rhetorical aside is preserved in the iteration-3.4 spec.

- **P2-C — object-vs-process axis.** KILLED on architectural minimalism + content-bearing-ness. Object-vs-process is plausible vocabulary but does not better explain additive-vs-multiplicative; it requires extra reasoning to recover the same structural justification. The simpler, more aligned distinction (property-vs-stance) wins. *Seed:* the temporal dimension implicit in stance-beliefs may be a future inquiry candidate if PRAGMA's temporal-pattern-detection produces signals not classified by the current distinction.

- **P3-C — predictions are circular.** REFINED to honesty-flag. The contrarian's partial truth (predictions 2 and 3 are re-groundings of iteration-3.3 content) was acknowledged honestly via explicit labeling. Prediction 1 (multi-source independence) is genuinely new content with its own PRAGMA classifier requirement; not circular. The honesty-flag is folded into the predictions section.

- **P4-C — cut re-grounding notes.** KILLED on content-bearing-ness. Re-grounding notes are forward-looking gatekeeping content (they document why existing structures have their form so future inquiries can argue against alternatives the frame already rejects). The orthogonality test re-grounding, in particular, sharpens future Modulator Suite gatekeeping. *Seed:* the spec-inflation concern is bounded; iteration-3.4 keeps re-grounding notes concise (one paragraph each).

- **P5-C — implicit convention extension.** KILLED on iteration discipline. Conventions accumulate via explicit statements, not implicit examples; implicit-only extension undermines convention signal-strength. Inherits the same structural pattern as iteration-3.3's killed P5-C ('update 3.2.1 in place'). *Seed (already extracted in iteration-3.3):* iteration label discipline tracks structural-vs-clarificatory change; explicit statements maintain navigability.

- **P6-C — retroactive embedding.** KILLED on iteration discipline + architectural coherence. Inherits the same structural pattern. Sensemaking Ambiguity 2 explicitly rejected this on three grounds: empirical content embedding rewrites finalized iteration; content-kind mixing obscures both; retroactive editing undermines spec history.

- **Assembly 2 — canonical-Bayesian apparatus commitment.** KILLED on architectural minimalism + Self-Reference Avoidance. Apparatus-level commitments commit APT to specific computational claims (priors, conjugacy, evidence-independence) that may not survive empirical scrutiny in attachment contexts. Vocabulary-only is reversible cheaply; apparatus commitment is not. *Seed:* re-evaluate if Bayesian update is empirically validated for APT's f-variable formation specifically.

### What survived and why

The eight clean SURVIVE verdicts and three refined-folded-in candidates all addressed dimensions iteration-3.4 had to satisfy: preserving prior commitments, honoring orthogonality discipline, honoring Cluster 4 discipline, staying PRAGMA-operationalizable, staying architecturally minimal (vocabulary-only anchor), faithfully addressing the user's three sub-questions, choosing the right iteration label (4-category convention extension), staying content-bearing (at least one genuinely new prediction + the property-vs-stance distinction + the convention extension + the re-grounding pattern), and reading clearly. Assembly 1 emerged because the eight content blocks cohere under a single argumentative arc (frame → distinction → predictions → re-grounding → architectural status → assembly).

### Contradictions reconciled across exploration / sensemaking / decomposition

- The exploration's three candidate readings (Alpha: useful clarification; Beta: substrate-reframe trigger; Gamma: circular self-reference) were tested in cycles 5 and 6: Beta ruled out by substrate test; Gamma ruled out conditionally on external anchoring. Sensemaking and critique both honored these falsifications.

- Sensemaking initially considered whether the three Gap fixes from iteration-3.3 should be re-examined under the belief-frame (since the frame would have streamlined some of their analysis). Decomposition and critique confirmed: iteration-3.3 stays as it is; iteration-3.4 *grounds* iteration-3.3's content rather than rewriting it. No drift across disciplines.

- Innovation produced a Bayesian-anchored variant (Assembly 2) that critique killed, in alignment with sensemaking Ambiguity 3's vocabulary-only commitment. The kill confirms sensemaking's verdict; the seed (re-evaluate if Bayesian is empirically validated for APT) preserves the option for future empirical work.

---

## Open Questions

### Monitoring

- **Multi-source independence prediction empirical test outcome.** Observable when paired-observation infrastructure exists for source-correlation manipulations (≥ 30 controlled-comparison observations). Confirms or falsifies the genuinely-new prediction iteration-3.4 produces.

### Blocked

- **Empirical validation of Bayesian belief-update mechanism for APT's f-variable formation specifically.** Cannot be answered until controlled belief-update studies become feasible. Until then, Bayesian remains one of several optional vocabulary anchors; not canonical.

### Research Frontiers

- **Whether the temporal dimension implicit in stance-beliefs warrants a sub-axis of the property-vs-stance distinction.** No known path; requires investigation if PRAGMA's temporal-pattern-detection produces signals not currently classified.
- **Whether multiple cognitive-theoretic traditions (Bayesian, schema, attribution, Bowlby) can in principle be unified into a single belief-update meta-mechanism for APT.** No known path; vocabulary-only commitment defers this question; substantive work would require apparatus comparison across traditions in attachment-formation contexts specifically.

### Refinement Triggers

- **If a future inquiry surfaces a belief-category that appears to generate attachment but is not a recategorization of existing C/H/F/R + g₁/g₂/g₃**, the orthogonality test (re-grounded in iteration-3.4's P4) re-opens. This is the strict gatekeeping condition for Modulator Suite or attachment-variable expansion.
- **If two or more PRAGMA implementations of the multi-source independence prediction diverge in source-correlation detection**, the prediction's operational specification needs review and potentially formalization.
- **If a future inquiry empirically validates Bayesian update for APT's f-variable formation**, Assembly 2 (canonical-Bayesian apparatus commitment) re-opens and may become spec content.
- **If a Modulator Suite proposal arrives where the put modulator is ambiguous between property-belief and stance-belief categories**, the property-vs-stance distinction needs a sharper diagnostic and the temporal-dimension sub-axis question may need to be addressed (P2-C seed).

---

## Source Input

<details>
<summary>Raw user input that triggered this inquiry</summary>

```text
Refinement 1 — f is a cumulative belief state. The four attachment variables (Charm, Hope, Fear, Resonance) represent the receiver's current belief about the sender, formed from in-interaction signals AND from prior evidence (direct experience, third-party social proof, channel/platform default). This is a clarification, not a new formula term.

interesting ... so in the core of attachment there is belief ? and apt is the componenet of significatn beliefs ??
```

Followed by the assistant's exploratory reply identifying APT as structurally a theory of attachment-generating beliefs, with property-vs-stance distinction and Self-Reference Collapse risk noted, after which the user invoked /MVL+ to run the full extended cognitive loop.

</details>
