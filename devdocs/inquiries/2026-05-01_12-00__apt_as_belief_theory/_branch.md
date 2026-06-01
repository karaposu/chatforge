# Branch: apt_as_belief_theory

## Question

Is APT (Attachment & Presentation Theory — the framework developed across iterations 3.0 → 3.1 → 3.2 → 3.2.1 → 3.3) structurally a theory of *which receiver-side beliefs about another person generate attachment when held*, and if so, what does that meta-frame enable that the current iteration-sequence framing does not?

## Goal

A diagnostic answer with three components:

1. **Is the belief-frame correct?** — Does APT, as currently specified, reduce structurally to "a theory of attachment-generating beliefs"? Does the existing variable + modulator + specificity architecture map cleanly onto belief-categories (the four `f`-variables = additive belief-categories; the three `g`-modulators = multiplicative belief-categories that gate or amplify)? Or does the mapping break in load-bearing ways?

2. **What does the belief-frame buy us?** — If correct, what specifically does this meta-frame enable that wasn't already enabled by iterations 3.0–3.3?
   - Theoretical grounding (connection to belief-formation cognitive theories)
   - Stronger orthogonality gatekeeping (a putative new variable that is just a recategorization of existing beliefs doesn't earn entry)
   - Sharper definition of what is in/out of APT's scope
   - New predictions
   - Pedagogical clarity

3. **What does the belief-frame cost us?** — Risks of self-reference collapse (theory evaluable only in its own terms), over-generalization (every social-cognitive phenomenon involves beliefs; what makes APT-beliefs special?), or substrate-reframe pressure (does this frame trigger Cluster 4?).

The user should be able to decide: ship the belief-frame as a meta-section in the iteration-3.3 spec, or open it as a parallel theoretical-grounding inquiry, or reject it as circular.

## Scope Check

**Question covers goal.** The question's three sub-parts (is it correct, what does it buy, what does it cost) map directly to the goal's three components. No widening needed.

## Seeds

### Seed 1 — The triggering observation

User pulled on Refinement 1 from iteration-3.3 (`apt_context_layer/finding.md`): "f is a cumulative belief state." User's response: "interesting ... so in the core of attachment there is belief? and apt is the component of significant beliefs??"

This frames APT as a theory of *which beliefs about another person generate attachment*. The four `f`-variables (Charm, Hope, Fear, Resonance) are receiver-side beliefs that, when held about another person, additively generate attachment. The three `g`-modulators (SP, Coherence, EC) are receiver-side reads of the sender's modulator state that multiplicatively gate or amplify the additive sum.

### Seed 2 — The orthogonality test re-grounded

The orthogonality test that gates Modulator Suite entry (developed in iteration-3.2 and applied in iteration-3.3 to kill P3-C g₄(Mode)) might be re-grounded under the belief-frame as: "a putative new variable must be a belief-category that is not a recategorization of existing belief-categories." This would give the test a structural basis it currently lacks.

### Seed 3 — The pre-condition placement

Iteration-3.3's pre-condition note (receiver availability is outside APT's formula scope, established in `apt_context_layer/exploration.md` Cycle 7) might be re-grounded under the belief-frame as: "APT models receiver-side beliefs *about the sender*; receiver availability is a meta-belief *about self* (am I open to forming attachments?), which is structurally a different belief category." This explains *why* the pre-condition placement is correct rather than asserting it.

### Seed 4 — The Resonance dyadic question

Resonance was added in iteration-3.2 as a 4th attachment variable, distinguished from g-modulators on the structural test that it can generate attachment alone (with Charm/Hope/Fear at zero — the shared-niche-interest case). Under the belief-frame, Resonance is the receiver's belief that "this person and I share world-models" — a relational belief, dyadic. This may interact with the belief-frame in interesting ways: are there other relational beliefs that should be in `f`?

### Seed 5 — Adjacent theories

Belief-formation cognitive theories (Bayesian belief-update, schema theory, attribution theory) are obvious adjacent fields. The belief-frame would connect APT to them. Domain Transfer candidate: Bayesian belief-update gives `f`-variable updating a formal mechanism; schema theory gives the Resonance variable theoretical anchoring; attribution theory gives g-modulator inference (SP-as-attribution-of-agency-direction) a basis.

## Hypothesis Landscape (pre-exploration)

Three candidate readings:

**Alpha — Belief-frame is a useful clarification (low-cost, low-risk).**
APT is structurally a belief-component theory; saying so explicitly grounds the architecture cognitively without changing it. Output: a meta-section in the iteration-3.3 spec or its own iteration-3.4 finding. No formula change.

**Beta — Belief-frame triggers a substrate reframe (Cluster 4).**
If APT reduces to a belief-component theory, then the "deeper substrate" of APT might be belief-formation mechanisms themselves (Bayesian update over signal evidence; schema-matching for Resonance). The current C/H/F/R + g₁/g₂/g₃ ontology becomes a useful surface taxonomy of belief categories, but the substrate is belief-formation theory. Output: an iteration-4 substrate reframe.

**Gamma — Belief-frame is circular and adds nothing (Self-Reference Collapse).**
Saying "APT is a theory of attachment-generating beliefs" is just renaming existing components ("variable" → "belief-category"). No new predictions, no new gatekeeping, no new connections. The frame is a bug, not a feature. Output: reject the frame; spec stays at iteration-3.3.

The exploration must discriminate between these three readings.
