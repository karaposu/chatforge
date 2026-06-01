# Branch: hope_sub_flavors

## Question

What are the significant sub-flavors of Hope as an APT attachment variable (Hope being the receiver's belief that interaction with the sender will yield future positive outcomes), what is the structural unifier that makes each sub-flavor *belong to* Hope (rather than to Charm, Fear, or Resonance), and what are the discriminating axes that *separate* the sub-flavors from each other while preserving Hope as a single additive variable in `f`?

## Goal

A taxonomy of significant Hope sub-flavors with four components:

1. **Named sub-flavors** — at least three, with concrete examples and worked vignettes for each.
2. **Structural unifier** — the precise property that makes something *be Hope* rather than be a different attachment variable (the "what's common between attention and exchange that makes them both Hope" question).
3. **Discriminating axes** — the dimensions along which Hope sub-flavors differ from each other (object of hope, time horizon, agent of fulfillment, specificity, etc.). The taxonomy should be a clean partition, not overlapping circles.
4. **Architectural status** — whether this sub-taxonomy is content within Hope (no formula change), a clarification of the iteration-3.3 Refinement 3 H_a/H_e distinction, or pressure toward splitting Hope into multiple variables.

The user should be able to: (a) classify any concrete Hope-instance into one of the named sub-flavors; (b) distinguish a Hope-flavor from a Charm- or Resonance-flavor that looks similar on the surface; (c) understand why splitting Hope into separate `f`-variables is or is not warranted; (d) update PRAGMA's Hope detection to flag which sub-flavor is dominant in a given interaction.

## Scope Check

Question covers goal — naming, unifying, distinguishing all addressed. Goal item 4 (architectural status) is implied by the question's "preserving Hope as a single additive variable" phrasing.

## Seeds

### Seed 1 — The existing H_a / H_e distinction (iteration-3.3 Refinement 3)

iteration-3.3 established two Hope sub-flavors as load-bearing for Refinement 3:
- *Exchange-Hope (H_e):* the receiver's hope about future positive exchanges with the sender ("we could collaborate / date / be friends").
- *Attention-Hope (H_a):* the receiver's hope that the sender will specifically continue to attend to them ("this person sees me, and will keep seeing me").

Refinement 3's coupling rule (g₁ display mode determines whether H_a is realized in `f`) depends on H_a being a distinct sub-component of Hope. iteration-3.3 names the distinction but does not provide a general framework — H_a was named because Refinement 3 needed it, not because the spec systematically partitions Hope.

### Seed 2 — The user's structural question

"What is common between attention and exchange that they are considered categories?" — the user is asking for the structural unifier of Hope itself. iteration-3.2 defined Hope informally as future-positive expectation; iteration-3.4's belief-frame defined Hope as "the receiver's belief that interaction with the sender will yield future positive outcomes." But what counts as a "future positive outcome"? Attention-receipt is one kind; exchange-value is another. The taxonomy needs to specify the structural shape that all Hope sub-flavors share.

### Seed 3 — Candidate additional sub-flavors to test

Beyond H_e and H_a, candidate Hope sub-flavors worth testing for inclusion:
- *Validation-Hope (H_v):* "this person will see me as I want to be seen" — hope about future validation/recognition of the receiver's self-image.
- *Continuity-Hope (H_c):* "this person will still be around / available" — hope about the relationship's persistence.
- *Generative-Hope (H_g):* "this person will help me grow / become more" — hope about the receiver's own development through the relationship.
- *Reciprocity-Hope (H_r):* "this person will reciprocate my care / investment" — hope about returns on what the receiver gives.
- *Status-Hope (H_s):* "this person will help me become higher-status / be associated with their status" — hope about status-elevation through the relationship.
- *Safety-Hope (H_safe):* "this person will protect me / be reliable" — hope about future protection or reliability.

Some of these may collapse into existing variables (e.g., H_s may be Charm-loading, not Hope; H_safe may overlap with Fear-absence, not Hope-presence; H_v may be a kind of Resonance). The exploration must test each for genuine Hope-membership.

### Seed 4 — The orthogonality test for Hope sub-flavors

Each candidate sub-flavor must:
- (a) share the structural shape that defines Hope (forward-orientation, positive-valence, sender-mediated outcome);
- (b) not be reducible to Charm (which is about *what the sender is*, not *what the future will bring*), Fear (about threat), or Resonance (about world-model match);
- (c) be PRAGMA-distinguishable from other Hope sub-flavors via observable signals.

If a candidate fails (a), it's not Hope. If it fails (b), it belongs to a different variable. If it fails (c), it's real but not operationally separable.

### Seed 5 — Discriminating axes between Hope sub-flavors

Possible axes along which Hope sub-flavors might differ:
- *Object of hope* — what is the receiver hoping for? (attention, exchange, validation, continuity, growth, reciprocity, ...)
- *Time horizon* — near-term vs long-term?
- *Agent of fulfillment* — the sender alone? the relationship? the receiver themselves through the relationship?
- *Specificity to this person* — could any person in this role fulfill the hope, or specifically this one?
- *Asymmetry of fulfillment* — does the receiver need to do something, or is the sender's action sufficient?

The taxonomy should identify which axes are load-bearing and which are derivative.

### Seed 6 — Why no formula split

iteration-3.2.1 established additive `f` with the four orthogonality test passes (Charm, Hope, Fear, Resonance can each generate attachment alone). Splitting Hope into multiple separate `f`-variables would either (a) violate parsimony (more variables for what was one) or (b) require each sub-flavor to pass orthogonality independently. The exploration should test whether any Hope sub-flavor passes the structural orthogonality test that would warrant variable-split — but the default expectation is that Hope sub-flavors are *partition-within-variable*, not *new variables*.

## Hypothesis Landscape (pre-exploration)

**Alpha — A small clean taxonomy (3-5 sub-flavors), partition-within-Hope.**
Hope's structural unifier is forward-positive-belief about the sender's effect on the receiver. Sub-flavors partition by *object of hope*. The taxonomy is clean (not overlapping); each sub-flavor has distinct PRAGMA signals; no variable split warranted. Output: a sub-taxonomy specified as content within Hope.

**Beta — Several candidate sub-flavors collapse into existing variables.**
Some candidates from Seed 3 (H_s, H_safe, H_v) actually belong to Charm, Fear-absence, or Resonance respectively rather than to Hope. The clean taxonomy is smaller than initially seeded; the exercise sharpens the boundary between Hope and its neighbors. Output: same as Alpha, plus boundary-clarification notes for the variables that absorbed candidates.

**Gamma — One candidate sub-flavor passes orthogonality and warrants variable split.**
One Hope sub-flavor (most likely H_a, given iteration-3.3 Refinement 3's reliance on its distinction from H_e) might pass the structural orthogonality test that would warrant making it a separate `f`-variable. Output: variable expansion from 4 to 5; iteration-label = 3.5 (structural change preserving ontology) or higher.

**Delta — The user's question is a different question than first reading suggests.**
The user may be asking not "what are Hope sub-flavors" but "what is the structural unifier of any APT variable category" — i.e., a meta-question about category-membership criteria. If so, the inquiry is meta and produces a category-membership procedure rather than a Hope-specific taxonomy. Output: a category-membership procedure that subsumes Hope sub-flavors as one application.

The exploration must discriminate among these. Default expectation: Alpha or Beta (a clean partition-within-Hope, possibly with boundary-clarifications). Gamma (variable split) requires an orthogonality pass, which is a high bar. Delta (meta-question) is unlikely given the user's specific examples but should be checked.
