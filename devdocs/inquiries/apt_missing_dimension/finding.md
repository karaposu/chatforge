---
status: active
---
# Finding: apt_missing_dimension

## Question

The APT (Attachment & Presentation Theory) layer document models interpersonal attachment dynamics via two domains:

- **Domain 1 (Attachment):** Charm, Hope, Fear — why the other party stays.
- **Domain 2 (Presentation):** Content, Style, Expressed Frame — how attachment is transmitted.

A transcript conversation (and the user's own observation about LinkedIn/Reddit high-potential conversations not converting) surfaced a *fourth* dimension the two-domain model doesn't name. It clusters around cues like "holding yourself as big" (Turkish: *kendini büyük görmek*), slight disregard, not over-helping, freely-shown displeasure, comfortable withholding. Two concrete examples illustrated it:

1. **CV incident:** A subordinate asked a senior for career advice. When the senior did too much of the work, the advice became worthless ("çabuk ulaştı çünkü" — because he got it too easily). When the senior only edited one heading and withheld the rest, the value was preserved.
2. **Clothing store:** A mother's face-making disregard toward an eager salesperson *generated* the salesperson's effort toward her.

Without this fourth thing, high Charm + high Hope + high Fear produces a specific failure mode: the other party engages but *discounts* you post-hoc ("this guy doesn't deserve this"). This is different from the failure mode of low Charm/Hope/Fear (no attachment at all).

**The question:** What is this new dimension, and where does it fit in APT's architecture — as a fourth attachment variable, a modulator of the three, a new third domain, or something already subsumed by Expressed Frame?

**The goal:** A clear name + definition + mechanism + surgical update to `apt_layer.md`. Plus a practical diagnostic the user can apply to their own asynchronous messages (LinkedIn DMs, Reddit), where the pattern shows up as "high-potential conversations don't convert."

---

## Finding

**The new dimension is Self-Positioning.**

It is a **multiplicative modulator on Domain 1 (Attachment)**, not a fourth attachment variable and not a new domain. It has **dual character** — an irreducibly internal axis (*Self-Elevation* — the stable bearing of holding yourself big) that emits external behavioral correlates (withholding, freely-shown displeasure, calibrated terseness, unhurried rhythm, absence of status-seeking moves in the exchange).

Architecturally it sits **upstream** of both existing domains: it causes both the other party's attachment response AND your own presentation, rather than being caused by either.

### Mechanism

Self-Positioning modulates attachment multiplicatively:

```
Attachment ≈ f(charm, hope, fear) × g(self-positioning)
```

When `g(self-positioning)` collapses, even high `f(charm, hope, fear)` produces near-zero real attachment. The failure signature is **devaluation** — the other party registers your charm, your offered benefit, and the power asymmetry, but discounts them post-hoc. High attachment values without the modulator convert at a steep discount, often to nothing.

Each of the three attachment variables is individually modulated:

- **Charm** without Self-Positioning reads as shiny-but-hollow → charm is devalued.
- **Hope** without Self-Positioning reads as desperate-to-please → the offered benefit loses perceived value (the CV mechanism generalized).
- **Fear** without Self-Positioning reads as bluster → fear fails to consolidate into respect.

Two **supplementary mechanism theories** (MEDIUM confidence, flagged for downstream validation):

1. **Costly signaling** — Self-Positioning works because willingness-to-risk-the-exchange is a credible signal (you can't fake paying the cost). Fake Self-Positioning (performed disinterest while desperate) is detectable because the cost isn't actually paid.
2. **Visible-need concealment** — Self-Positioning works because low visible-need prevents value-destroying supplication signals. The deeper variable may be the *visibility* of need, with Self-Elevation being a stable way of producing low visible-need.

These two are complementary at different levels (signal reliability vs signal content), not competing primary mechanisms.

### Trait structure

Individual-with-bearings, expressed relationally.

**Operational definition of bearing:** central tendency of measured Self-Positioning across multiple dyads, aggregated longitudinally.

- **APT Profiling** reports bearings (how a person tends to self-position across relationships).
- **APT Inference** reports realized Self-Positioning asymmetry in a specific dyad.

**Measurement is always asymmetric/relational** — Self-Positioning is measured as Person-A-relative-to-Person-B, never as an absolute level. The four-quadrant diagnostic space (below) emerges from this asymmetric measurement combined with the investment-asymmetry axis.

### Distinctness

Self-Positioning is **not**:

- **Not a 4th attachment variable.** Charm/Hope/Fear answer "why would I stay?" Self-Positioning answers "does what they offer deserve respect?" Different question class. Also mathematically different: the devaluation failure mode produces near-zero collapse (multiplicative), not a linear discount (additive).
- **Not the existing Expressed Frame.** Expressed Frame tracks *investment asymmetry* ("I'm the selector vs please like me") and is defined as "not internal — only matters as perceived." Self-Positioning has an internal driver that is *load-bearing* — external behaviors without the internal state misfire as try-hard, weird, or hostile.
- **Not a full new domain.** The evidence surfaces one primary axis (Self-Elevation) with Relative-Calibration as a measurement property. That's not enough sub-structure to justify a third peer domain alongside Attachment and Presentation. If future evidence forces Relative-Calibration into an independent axis, the modulator framing can be revisited.
- **Not the existing Internal Frame as "tool."** APT's current spec demotes Internal Frame to "a tool that makes correct expressed frame natural and sustainable." The CV mechanism falsifies the implicit claim that internal state is pure tool — the internal posture is causally load-bearing on the attachment outcome.

### Surgical update to `apt_layer.md`

Four specific edits:

1. **New section "Self-Positioning"** inserted between Domain 1 and Domain 2. Specifies:
   - Modulator role (multiplicative on Domain 1, upstream of Domain 2)
   - Dual character (internal Self-Elevation axis + external signalling correlates)
   - Distinctness from Expressed Frame and Internal Frame
   - Failure signature (devaluation)
   - PRAGMA inference approach (conjunction of signals, not single measurement)

2. **Domain 2 revision** — Narrow "Expressed Frame" definition to investment-asymmetry only. Add cross-reference: "Self-Positioning is orthogonal — it covers the self-elevation dimension that Expressed Frame previously conflated with investment dynamics. The two form a cross-product (see the four-quadrant diagnostic)."

3. **"What's Not a Domain But Matters" amendment** — Internal Frame's generic demotion to "tool" stands for the broad concept; one component (Self-Elevation) is promoted to first-class status as the internal axis of Self-Positioning. The original demotion rested on the claim that internal state is pure tool; the devaluation failure mode refutes this for Self-Elevation specifically.

4. **Causal order update** — Add that Self-Positioning sits upstream of both Domain 1 (in them) and Domain 2 (by you). The existing Domain 1 → Domain 2 flow holds downstream of Self-Positioning as a modulating prior cause.

### PRAGMA inference — Signal Catalog

Five inference signals composed into a **conjunction detector** (no single signal is determinative; high-confidence Self-Positioning detection requires multiple):

| Signal | Definition | High SP | Low SP |
|---|---|---|---|
| **Withholding-Signal** | Negative space — what the speaker chose not to say / declined to elaborate / didn't defend | Present (comfortable not-elaborating when invited) | Absent (over-elaborates everywhere) |
| **Premise-Posture** | Opening frame | Selecting / offering / asserting | Requesting-permission |
| **Self-Justification-Density** | Clauses-per-message explaining why speaking / why qualified | Low | High |
| **Exit-Willingness** | Risk taken in the move | High (disagreement, selectivity, terminable-close) | Low (safety-optimized, hedged, open-ended) |
| **Rhythm-Comfort** | Comfort with silence/delay | Present (unrushed) | Rushed, filler-laden |

These are **second-order PRAGMA inference signals**, composed from existing PRAGMA measurements and text-level features. No change to PRAGMA's primary dimension set is required. Empirical independence validation is downstream work.

### User-facing diagnostic — LinkedIn case

Self-Positioning × Expressed Frame (Investment-Asymmetry) produces a **2×2 typology**:

| | Low Investment (stepping back) | High Investment (leaning in) |
|---|---|---|
| **High Self-Elevation** | **Confident Selector** (classic high-status) | **Respected Expert** (engaged AND big — the target) |
| **Low Self-Elevation** | **Disengaged / Avoidant** (stepping back from need) | **Try-Hard / Supplicating** (leaning in from need — the user's LinkedIn failure mode) |

**Five-question audit** applicable to any outgoing message:

1. Does my premise request permission or select/offer?
2. How many clauses explain why I'm writing?
3. Do I elaborate beyond what the point requires?
4. Does my close allow them to not reply?
5. Am I willing to not get a response? (And does that show?)

Diagnosis: The user's LinkedIn failure mode is **Try-Hard**. Fix is not "add more charm" but "calibrate the posture from which charm is delivered" — reduce self-justification clauses, shift premise from requesting-permission to selecting/offering/asserting, comfortable pauses, terminable close, minimum viable word count.

### What's asserted and with what confidence

- **HIGH confidence:** The concept exists; the multiplicative mechanism holds; the devaluation failure mode is the signature; Path α (Named Modulator) is the correct architectural placement; the 2×2 typology and 5-question audit are diagnostically useful.
- **MEDIUM confidence:** The supplementary mechanism theories (costly signaling + visible-need concealment); the empirical independence of the five-signal catalog; the choice of "Self-Positioning" as the final name (vs Standing, Non-Supplication, Positioning).
- **LOW confidence / flagged:** Relative-Calibration as measurement property vs independent axis; whether APT itself may eventually need substrate reframing (Cluster 4 APT-level doubt — flagged with explicit reopening conditions).

---

## Reasoning

This finding survived adversarial critique across 8 weighted dimensions (5 critical: Explanatory Adequacy, Structural Integration, Definitional Distinctness, Operational Testability, User Actionability; 3 medium: Architectural Parsimony, Extensibility, Honesty). The reasoning below documents what was considered and why each rejected option was rejected.

### Why Self-Positioning as a modulator, not a 4th attachment variable

**Proposed:** Add Self-Positioning as a peer of Charm, Hope, and Fear inside Domain 1.

**Rejected because:**

1. *Different question class.* Charm/Hope/Fear answer "why stay?" Self-Positioning answers "does this deserve respect?" Forcing it into the same slot flattens a real distinction.
2. *Different mathematical shape.* The CV example shows the failure mode is near-zero collapse when Self-Positioning breaks despite high Charm/Hope/Fear. That's multiplicative behavior, not additive. A 4th peer variable would predict linear discount (high, high, high, low → moderate). Reality shows catastrophic collapse.

### Why Self-Positioning is not subsumed by Expressed Frame

**Proposed:** Expand Expressed Frame to cover both investment-asymmetry and self-elevation (current definition bundles them implicitly).

**Rejected because:**

1. *Internal-character test fails.* APT's current Expressed Frame is explicitly defined as "not internal — only matters as perceived." Self-Positioning has an irreducibly internal driver (the CV mechanism is decisive — performed Self-Positioning without internal backing misfires as try-hard). Expanding Expressed Frame to include an internal-driven dimension requires rewriting its core "not internal" claim, which ripples through the causal-order section and the Internal Frame demotion section.
2. *Orthogonality test passes.* A four-quadrant test proves investment-asymmetry and self-elevation are genuinely orthogonal: *Respected Expert* (high Investment + high Self-Elevation) and *Try-Hard* (high Investment + low Self-Elevation) are distinguishable and real. So these are two axes, not one axis with variants.
3. *Cleaner cut:* narrow Expressed Frame to investment-asymmetry (its original intent) and introduce Self-Positioning as a separate concept. The 2×2 typology emerges as a cross-product rather than a single multi-dimensional frame.

### Why Self-Positioning is not just Internal Frame upgraded

**Proposed:** Promote the existing Internal Frame concept (currently demoted to "tool") to first-class and call it done.

**Partially accepted.** Self-Elevation IS the load-bearing component of what Internal Frame gestured at. But Internal Frame in APT was a generic concept covering any internal state backing presentation. Self-Positioning is specifically about self-elevation with its multiplicative modulation mechanism on attachment — more specified, more testable. The amendment keeps Internal Frame's generic demotion (it was *partly* correct — internal frame for pure presentation-execution IS a tool) while promoting the specific Self-Elevation component that the CV mechanism shows is causally load-bearing.

### Why Path α (Named Modulator) over Path β (Third Domain) [KILL of β-full]

**Proposed (Path β-full):** Promote Self-Positioning to a full third domain "Positioning" with three axes (Self-Elevation + Relative-Position + Investment-Asymmetry), relocating Investment-Asymmetry from Expressed Frame.

**Rejected because:**

1. *The "three axes" collapse under inspection.* Relative-Position is a measurement property of Self-Elevation (how it's assessed — against whom), not an independent axis. Investment-Asymmetry was already in Expressed Frame; relocation is not forced by evidence, only re-categorized. The honest count is one axis (Self-Elevation) + a measurement refinement + a pre-existing concept. One axis is insufficient to justify a peer domain alongside Attachment and Presentation.
2. *Structural Integration fails.* Three-domain restructure cascades across every downstream spec (Behavioral Profiling, APT Inference, APT Profiling). Every output schema needs a third slot, every PRAGMA-to-APT mapping needs a third branch. User's valuation was explicit: iterative addition, not replacement.
3. *Extensibility is weaker, not stronger.* A "Positioning" domain doesn't cleanly accommodate future modulators (Tempo, Affect, Coherence) — Tempo isn't a Positioning thing. Path α's "named modulator slot" scales more cleanly: Tempo becomes another modulator alongside Self-Positioning without restructure.
4. *Evidence level mismatch.* Evidence base is Level-1 (single transcript + user's LinkedIn observation). Promoting to a full third domain requires Level-3 evidence (multiple converging cases with clearly distinguished axes).

The softer variant (β-soft: rename Expressed Frame to "Positioning" containing both axes, no new domain) is cosmetically different from Path α but structurally the same; it's available as a naming choice if the user prefers a single bundle label.

### Why Path α over Path γ (Replace Expressed Frame) [KILL of γ]

**Proposed (Path γ):** Dissolve Expressed Frame entirely; replace with Self-Positioning, which contains both investment-asymmetry and self-elevation. Concept-count-neutral.

**Rejected because:** This puts Self-Positioning *inside* Presentation (external-only), directly contradicting the dual-character insight. The internal-driver layer is dropped — exactly the demoted Internal Frame framing that sensemaking explicitly rejected. Path γ regresses. The cost-saving motivation (don't multiply concepts) is valid but misdirected — the actual savings opportunity is *narrowing* Expressed Frame's scope, not *eliminating* it.

### Why trait-with-bearings over pure-relational [KILL of pure-relational]

**Proposed (pure-relational):** Self-Positioning is a dyadic dynamic only; no individual trait component. APT Profiling cannot capture it meaningfully.

**Rejected because:**

1. *Empirical falsification.* People DO have observable bearings. Some are consistently supplicating across relationships; others consistently elevated. Pure-relational denies this observable reality.
2. *Structural Integration fails.* APT Profiling is a first-class output. Claiming it cannot capture Self-Positioning unilaterally removes it. Cascade consequences.
3. *Evidence is thin.* Three contrarian mechanisms in innovation converged on pure-relational, but their *purpose* was to destabilize baseline. Convergent challenge is not the same as evidence of the challenge's correctness.

**Accepted variant:** Bearings-as-tendencies — individuals have trait-level central tendencies that manifest through per-dyad enactment. Operational definition: *bearing = central tendency of measured Self-Positioning across multiple dyads, aggregated longitudinally.* This preserves APT Profiling's output validity while honoring the asymmetric-measurement insight.

### Why the five-signal catalog is used as a conjunction detector [REFINE]

**Proposed:** Five inference signals (Withholding / Premise-Posture / Self-Justification-Density / Exit-Willingness / Rhythm-Comfort) as independent primary dimensions.

**Refined because:** The signals may be empirically correlated in practice (e.g., Premise-Posture and Self-Justification-Density both measure openings). Treating them as independent primary dimensions risks double-counting. Framing them as a *conjunction detector* preserves the benefits (multi-signal robustness, no single determinative signal) while sidestepping the independence question. Empirical independence validation is flagged as downstream work.

### Why the enriched mechanism theories are supplementary, not primary [REFINE]

**Proposed:** Adopt costly-signaling and visible-need-concealment as primary mechanism explanations alongside (or instead of) multiplicative gating.

**Refined because:** These are complementary theories at different levels — costly signaling explains signal *reliability*; visible-need concealment explains signal *content*. Both can be true simultaneously without redundancy. But they carry MEDIUM confidence (innovation's Cluster 3 had only 2 mechanisms converge). Multiplicative gating is the primary mechanism (HIGH confidence from sensemaking + innovation convergence); the enriched theories become candidate explanatory layers flagged for downstream validation.

### Why the 2×2 diagnostic survives despite variance concerns [SURVIVE]

**Objected:** 2×2 typologies hide variance. High Self-Elevation + high Investment is not one thing (Respected Expert) — it's many things.

**Survived because:** Diagnostic utility outweighs theoretical completeness. The user needs a coarse-grained map applicable today. 2×2 captures the real failure mode (Try-Hard) vs target (Respected Expert). Sub-typologies can emerge from longitudinal use — start coarse, refine as cases don't fit.

### Why APT-level doubt is flagged, not killed [FLAG]

**Concerned:** Three contrarian mechanisms in innovation converged on "APT itself may be inadequate — substrate reframe needed (Resonance + Positioning as fundamentals; Charm/Hope/Fear as emergents)." Innovation flagged this as partial survival-bias risk.

**Result:** Not a solution candidate (doesn't answer the scoped question). Not dismissed either. Recorded in Open Questions with explicit reopening conditions:

- If empirical cases emerge where Self-Positioning collapse occurs without low Charm/Hope/Fear → substrate theory may be needed.
- If the 5-signal catalog fails to detect Self-Positioning in cases the user's intuition identifies clearly → underlying theory may be too thin.
- If future inquiries reveal additional modulators (Tempo, Affect, Coherence, Resonance) and their relationships become structurally constrained → substrate reframe may be forced.

---

## Open Questions

1. **Relative-Calibration: measurement property or independent axis?** Currently framed as a measurement property of Self-Elevation (how SP is assessed against the other party's position). Could be promoted to an independent second axis ("how well you adjust for the specific dyad's level") if future evidence shows cases where absolute Self-Elevation and dyad-calibration dissociate — e.g., someone who maintains the same internal posture with everyone versus someone who reads and adjusts per dyad.

2. **Final name choice.** Working name is Self-Positioning (primary) with Self-Elevation as the axis. Alternatives:
   - **Standing** — one-word, captures bearing + perception, but ambiguous with rank/legal usage.
   - **Non-Supplication** — mechanism-accurate (the visible-need-concealment theory), but negative definition; could name the *axis mechanism* rather than the umbrella concept.
   - **Positioning** (without "Self-") — bundle label, available if the β-soft naming variant is preferred.

3. **Signal independence empirical validation.** The 5-signal catalog is defensible in principle (each targets a distinct message feature) but correlations in practice may reduce effective dimensionality. Downstream empirical work: apply the catalog to 50+ annotated conversations; measure inter-signal correlation; if high correlation emerges, reduce to 2-3 composite signals.

4. **PRAGMA inference rules specification.** The signal catalog is defined conceptually; the exact detection rules (what counts as Withholding vs just brevity? what's the threshold for Self-Justification-Density?) need an implementation spec. Flagged for downstream work (separate from this inquiry).

5. **2×2 typology variance.** The four archetypes (Confident Selector / Respected Expert / Disengaged / Try-Hard) capture the primary failure and target modes. Longitudinal use may reveal sub-typologies within quadrants that deserve their own names. Revisit after the user applies the audit to 20+ real messages.

6. **Cross-modal signals (voice, video).** The signal catalog and diagnostic are text-focused (aligned with the user's LinkedIn use case). Self-Positioning has off-channel manifestations (tone, pacing-in-real-time, facial expression in voice/video) that are not captured. If APT extends to multi-modal PRAGMA in the future, the catalog needs corresponding extensions.

7. **Cultural calibration.** What reads as Self-Positioning in one cultural context (direct assertion, terse close) may read as rudeness or incompetence in another. The current spec is culture-neutral in its abstract framing but the diagnostic signals may vary by conversational norm context. Not explored in this inquiry.

8. **APT-level doubt (Cluster 4).** Flagged with reopening conditions above. Three contrarian mechanisms in innovation converged on "APT itself may need a substrate reframe." Not resolved here; reopening conditions specified. If multiple future inquiries surface additional modulators or discover that Charm/Hope/Fear are better modeled as emergents from deeper variables (Resonance + Positioning + Stakes), an APT-level restructure inquiry should be opened.

9. **Domain-of-relevance calibration.** The transcript examples (CV, clothing store) and the user's LinkedIn case are all contexts where value is still being established. In intimate long-term relationships, very high Self-Positioning may read as coldness — the modulator may have optimal ranges that vary by relationship stage. Not fully specified in this iteration.

10. **Prescriptive vs descriptive tension.** APT is a descriptive theory. The user's LinkedIn application is prescriptive. The finding scopes Self-Positioning descriptively; prescriptive use (how to *produce* calibrated Self-Positioning) is a downstream concern that the 5-question audit partially addresses but doesn't resolve — genuine internal Self-Elevation comes from a different source than verbal calibration tricks.

11. **Other absences flagged but out-of-scope.** Innovation's 5.A flagged additional concepts conspicuously absent from APT: **Resonance** (shared world-model / genuine mutual recognition), **Timing Momentum** (when you show up in the other's life), **Stakes-level** (what's at risk in the exchange). Out of scope for this inquiry. Candidates for future inquiries if/when they surface in user observations.
