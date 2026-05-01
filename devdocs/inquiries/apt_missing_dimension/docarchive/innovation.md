---
status: active
discipline: innovation
inquiry: apt_missing_dimension
iteration: 1
---
# Innovation: apt_missing_dimension

## User Input

`devdocs/inquiries/apt_missing_dimension/sensemaking.md`

## Seed

Integrate **Self-Positioning** (a modulator on APT's Domain 1 with dual character — internal *Self-Elevation* + external signalling; multiplicative mechanism; failure mode = devaluation) into the APT architecture. Sensemaking committed the structural role (modulator, not 4th variable, not premature full-domain, not just Internal frame) and left 4 items open for innovation:

- **OI1** — Sub-structure: does Self-Positioning have further axes that would upgrade it to a full domain?
- **OI2** — Final name: Self-Positioning vs Self-Elevation vs Frame-of-Regard vs Positioning-Posture vs alternatives.
- **OI3** — Concrete spec-surgery options for `apt_layer.md`.
- **OI4** — PRAGMA inference rules for detecting it.

Innovation's job: propose concrete options across these four, apply all 7 mechanisms, compare, assemble, test.

## Direction (intuition / valuation)

What matters here, grounded in the user's own framing:

- **Primary valuation:** The LinkedIn/Reddit pattern — high-potential contacts not converting — needs a diagnostic handle. Abstract beauty of the theory is secondary to whether the user can audit their own messages against it.
- **Secondary valuation:** The theory must stay internally consistent. APT is a working spec; surgery must not break existing outputs (Behavioral Profiling, APT Inference, APT Profiling).
- **Motivation:** The user has been developing APT iteratively. They don't want a replacement; they want the right *addition* that absorbs the transcript's insight without collateral damage.

This valuation sets the survival bar: outputs that merely sound novel but don't produce either (a) a diagnostic the user can apply or (b) a clean spec-surgery plan are deprioritized.

---

## Mechanism 1 — Lens Shifting

### 1.A Generic — Domain-of-relevance frame

Under different conversational contexts, Self-Positioning's weight varies:

- Low-stakes social chitchat → SP barely matters (nothing to devalue).
- High-stakes first-contact (LinkedIn DMs, networking, sales outreach) → SP dominates; the mechanism is raw.
- Intimate long-term relationships → too-high SP reads as coldness; devaluation protection stops mattering because the other party is already committed.
- Professional peer exchange → SP calibration is subtle; mis-calibration reads as either arrogance (too high) or supplication (too low).

**Implication:** Self-Positioning has a *domain of relevance*. Its modulating effect on attachment is strongest where value is still being established and weakest where it's stabilized or irrelevant.

### 1.B Focused — LinkedIn-specific operationalization

Reframe SP under the narrow frame: *asynchronous text-only first-contact*.

Under this frame, SP is encoded entirely through:

1. **Premise-framing** — does the opening position self as requesting permission ("I hope you don't mind me reaching out"), selecting the other ("I've been following your work and wanted to…"), or offering ("Noticed you're working on X — here's something relevant")?
2. **Self-justification density** — clauses explaining why you're writing, why you deserve attention, why you're qualified to ask. *Higher density → lower SP.*
3. **Elaboration gradient** — do you over-explain when a short signal would work? *Over-explaining → lower SP.*
4. **Response-trigger asymmetry** — does your message end with a question that obligates them or a statement that allows them to opt in?
5. **Stakes-acknowledgment** — do you acknowledge you might not get a response, or do you frame as if their response is assumed?

**Implication:** In text-first-contact, SP reduces to a *calibrated economy of words under the posture "you are free to ignore me."* The paradox: showing that you don't need the response is what makes the response likely.

### 1.C Contrarian — Maybe APT itself is the wrong frame

Shift to a frame where the whole "attachment via charm/hope/fear" model is questioned. Under this frame:

- People don't connect via the three. They connect via two fundamental forces: **RESONANCE** (shared world-model / genuine mutual recognition) and **RESPECT** (legitimacy of the other's claim to your attention — exactly what Self-Positioning gates).
- Charm/hope/fear are *downstream emergents*, not fundamentals. They're what resonance+respect produce when the interaction is transactional.
- Under this frame, Self-Positioning isn't a modulator — it's one of the two fundamental forces. APT is inverted: the "Attachment domain" becomes the surface and Positioning + Resonance become the substrate.

**Implication:** If true, the user should not be trying to integrate SP into APT but recognizing APT as a symptom-level theory that needs a substrate-level reframe. *Uncomfortable because it would invalidate sensemaking's entire surgical-update plan.*

---

## Mechanism 2 — Combination

### 2.A Generic — SP × Expressed Frame two-axis typology

Combining SP (self-elevation axis) with Expressed Frame (investment-asymmetry axis) produces a 2×2 typology of frames:

| | Low Investment (stepping back) | High Investment (leaning in) |
|---|---|---|
| **High Self-Elevation** | **Confident Selector** (classic high-status archetype) | **Respected Expert** (engaged AND big — rare, powerful) |
| **Low Self-Elevation** | **Disengaged / Avoidant** (stepping back from need, not self-regard) | **Try-Hard / Supplicating** (leaning in from need — the user's LinkedIn failure mode) |

**Implication:** The four-quadrant typology gives crisp diagnostic language. The user's LinkedIn pattern maps to *Try-Hard*. The target isn't *Confident Selector* (may read as cold) but *Respected Expert* — engaged but not supplicating.

### 2.B Focused — SP × PRAGMA signature

Operational definition by combining with existing PRAGMA dimensions:

**SP Signature** = Involvement (present) × Investment (calibrated-low, not zero) × Control-Distribution (symmetric or self-favoring) × Dialogic-Function (assertive without defensiveness) × Temporal (comfortable pauses, unhurried rhythm)

None alone detects SP. The *conjunction* does. The signal is the *pattern across five dimensions.*

**Implication:** PRAGMA inference for SP = second-order pattern-detector, not a new primary dimension. Spec change is small (inference rule in APT, no PRAGMA overhaul).

### 2.C Contrarian — SP as Costly Signal (economic framing)

Combine SP with the economic concept of *costly signaling* (Zahavi, signaling theory):

SP isn't a posture — it's a **cost paid** in each interaction. The cost is *willingness to lose the exchange.* High SP = high willingness to walk, challenge, say no, not reply, disagree. Low SP = every move is optimized to preserve the exchange at all costs.

Mechanism: others recognize the cost (your willingness to risk the exchange) and update respect accordingly. Costly signaling only works when the cost is real — fake SP (performed disinterest while desperate) is detectable because the cost isn't actually paid.

**Implication:** SP measurement reframes from "posture analysis" to "risk-taken analysis." New PRAGMA hook: *exit-willingness signals* — did the message risk the relationship? Did it include disagreement, challenge, selectivity, or plausible-last-message quality?

---

## Mechanism 3 — Inversion

### 3.A Generic — SP always helps attachment? Inverted: SP can REPEL

Invert "high SP → better attachment":

Sometimes high SP repels. When the other person is already very high-status, your elevation reads as competition or threat — they distance. When the other is insecure, your elevation triggers defensiveness. When there's power asymmetry in their favor, your elevation reads as insubordination.

**Implication:** SP is *relational, not absolute.* It must be calibrated against the other person's position. Optimal SP = slightly-elevated-relative-to-them. Too-low = supplication. Too-high-relative-to-them = threat/intrusion.

This means SP in APT Inference is always a *directional differential*, not a pair of absolute values.

### 3.B Focused — Devaluation comes from SP low? Inverted: maybe from visible-effort

Invert the causal claim "low SP causes devaluation":

What if devaluation is actually caused by **visible effort** (effort-to-please that the other sees), and SP is just *correlated* because high-SP people naturally conceal effort?

Test: could a skilled low-SP person still produce high attachment by concealing effort despite not feeling elevated? Plausible — actors, performers, negotiators do this.

Keep inverting (component → system):

- Component: "effort-concealment produces the effect"
- System: "the visibility of the *need-to-please* is what's devaluing." Hiding effort works because it hides need. The root variable is **visible-need**, not effort per se.

**Implication:** The real modulator might be *Visible-Need-Level*, with SP being a stable internal way of producing low visible-need. This changes the naming conversation — maybe the concept should be called *Non-Supplication* or *Need-Concealment* rather than Self-Positioning.

### 3.C Contrarian — SP is an internal trait? Inverted: it's relational-only

Deep inversion of sensemaking's dual-character claim.

What if SP isn't a property of a person at all, but a *dynamic that gets enacted moment-to-moment with this specific person*? You can't "have" SP; you can only produce it in a given exchange. Your SP with Person A may be entirely different from SP with Person B, not because of bearings but because the dynamic itself is what generates it.

Implications if true:

- APT *Profiling* (individual level) can't capture SP meaningfully — only APT *Inference* (relational) can.
- The "bearings" language sensemaking used would be a category error for SP specifically.
- SP becomes a property of the *dyad*, not of the individual.

Keep inverting (system-level):

- "Maybe ALL of APT is relational and individual profiling is the error." Charm, Hope, Fear might also be dyadic properties that APT Profiling only captures as approximations.

**Implication:** If accepted partially, SP is profiled as *tendencies* (how you tend to enact SP across dyads) not *levels.* APT Profiling entry would be "this person tends to enact high/calibrated/collapsed SP under conditions X" rather than "this person has SP level X."

---

## Mechanism 4 — Constraint Manipulation

### 4.A Generic — Add constraint: "must be detectable in text only"

Force SP to be measurable without body language, tone, pacing-in-real-time, facial expression. Under this constraint:

- Clothing-store example (mom's face) is excluded from operational definition — too off-channel.
- CV example (withholding) survives — it's a content-level signal.
- All operational correlates must be readable in text: word choice, premise, density, self-justification count, question-vs-statement closing, elaboration gradient.

**Implication:** Keeps SP actionable for the user's LinkedIn case. Spec should specify the text-only operationalization explicitly. Off-channel manifestations (tone, face) become a separate concern flagged for multi-modal PRAGMA extensions.

### 4.B Focused — Remove constraint: "must fit existing APT architecture"

If we let SP reshape APT rather than fitting in, what emerges?

Candidate: restructure to **three symmetric domains**:

1. **Attachment** (why stay) — Charm, Hope, Fear
2. **Positioning** (does this deserve respect) — Self-Elevation, Relative-Position, Investment-Asymmetry
3. **Presentation** (how it's transmitted) — Content, Style, Delivery (was "Expressed Frame"; renamed to avoid confusion)

Each domain answers a different question. Each has multiple axes. The spec gains symmetry.

Downside: sensemaking explicitly flagged this as premature (one axis not enough for a domain). But with *three candidate axes* (Self-Elevation + Relative-Position + Investment-Asymmetry — the last one relocated from Presentation), Positioning now has sub-structure.

**Implication:** A three-domain architecture is defensible IF we relocate Investment-Asymmetry into Positioning and let Self-Elevation + Relative-Position be the other two axes. This is a more invasive surgery but produces a cleaner architecture.

### 4.C Contrarian — Add constraint: "APT cannot grow in concept count"

Force SP to REPLACE something, not add. What can it replace?

Candidate: **Dissolve Expressed Frame entirely and replace with Self-Positioning** (with Investment-Asymmetry and Self-Elevation as its two axes). Expressed Frame in the current spec already bundles these; the replacement just names the bundle properly.

Presentation then becomes: Content, Style, *Self-Positioning* (replacing Expressed Frame).

Upside: no concept-count growth. The rename is honest about what Expressed Frame already tried to do.

Downside: "Self-Positioning" inside Presentation (external-only) contradicts sensemaking's commitment to dual character. The internal driver gets lost again.

**Implication:** A compromise. Works if we accept that "Self-Positioning" as a Presentation concept refers to the *expressed/signalled* layer, and separately note that it's backed by an internal bearing (mentioned as an aside, not a first-class element). Less clean than 4.B but less surgery.

---

## Mechanism 5 — Absence Recognition

### 5.A Generic — What else is missing from APT the transcript hints at?

Beyond SP, conspicuous absences in APT:

- **Resonance** — shared world-model / genuine mutual recognition. Not charm (looking up), not hope (wanting benefit), not fear (consequence). Just: "this person sees the world like I do, I feel understood." Conspicuously absent from APT. The transcript didn't raise it but the user's LinkedIn problem probably has a resonance component (high-potential contacts aren't just about status/benefit/fear; there's a mutual recognition element).
- **Timing Momentum** — when you show up in the other's life (crisis, boredom, windfall) affects attachment more than any of the three. APT is timeless; attachment is time-sensitive.
- **Stakes-level** — what's at risk in the exchange. Low-stakes exchanges have weaker attachment dynamics than high-stakes ones.

**Implication:** Innovation should flag these for future iterations. But *this* inquiry is scoped to SP. Don't scope-creep. Noting the absences is valuable; proposing they be added is out-of-scope.

### 5.B Focused — What PRAGMA signals are specifically missing to detect SP?

Current PRAGMA dimensions (Involvement, Investment, Control, Density, Intent, Function, Temporal) don't cleanly capture three SP-relevant signals:

1. **Withholding-Signal** — what the speaker *chose not to say* / *declined to elaborate* / *didn't defend.* The negative space in a message. High withholding (when the context invited more) is a Self-Elevation signal.
2. **Premise-Posture** — the opening premise's positioning: *requesting-permission* ("I hope you don't mind…") vs *selecting-the-other* ("Been following your work, thought you might appreciate…") vs *offering* ("Noticed X, here's Y") vs *asserting* (no premise at all, direct assertion of a shared object).
3. **Self-Justification-Density** — number of clauses-per-message devoted to explaining why the speaker is writing, why they're qualified, why they deserve attention. Directly inverse with SP.

**Implication:** These three are candidate additions to PRAGMA's dimension set, specifically to operationalize SP detection. Alternatively, they can live in a separate "SP inference signals" spec without extending PRAGMA.

### 5.C Contrarian — What's missing that would make APT unnecessary?

If the real unit of interest is *mutual shift in worldview per unit time* (not "who stays"), then:

- APT's entire attachment focus is too transactional — it explains who-stays-why but doesn't explain who-changes-whom.
- The missing concept is **Convergence Pressure** — how much the exchange is reshaping each party's model of the world. High-quality relationships have sustained convergence; low-quality ones don't even when both parties stay.

**Implication:** Self-Positioning protects convergence by preventing one party from collapsing into the other's model (supplication), which would be pseudo-convergence. Under this contrarian frame, SP's function is to *preserve the conditions for genuine mutual update.* This is a reframe that places SP in a larger theory APT doesn't contain.

*Out of scope for this inquiry but worth flagging.*

---

## Mechanism 6 — Domain Transfer

### 6.A Generic — Executive presence / brand aspirational distance

Leadership research has *Executive Presence*: a cluster of self-elevation + groundedness + economy-of-speech. Maps almost directly to Self-Positioning. Transfer: borrow the operational catalogs (physicality, gravitas, communication style from Sylvia Ann Hewlett's work) as candidate SP signals, adapted to text.

Brand research has *Aspirational Distance*: the gap between consumer and brand that creates desire. Transfer: SP creates aspirational distance in interpersonal exchanges. Brands manage this distance deliberately via scarcity, selectivity, pricing. Interpersonal SP has analogs: scarcity (of attention), selectivity (of engagement), pricing (effort-asking).

**Implication:** Gives a cross-domain vocabulary for SP. The "aspirational distance" framing is particularly useful for the user's LinkedIn case — treating each message as a brand touch helps diagnose what collapses the distance.

### 6.B Focused — Ethology (dominance signaling)

Transfer from animal-behavior research on dominance displays:

- *Stillness under scrutiny* (predator watching, not fidgeting) → comfortable-with-pause in text (no filler, no hedge, no over-elaboration when scrutinized)
- *Eye contact maintenance* → direct-assertion-without-hedging in text
- *Territory-taking posture* → premise-ownership in text (start with what you want to talk about, not permission-seeking)
- *Calm low-frequency vocalization* → measured sentence rhythm, not rushed clause stacks
- *Resource-confidence* (not guarding food) → not defending every word; letting some claims stand without justification

**Implication:** A concrete signal catalog. Each ethological pattern has a text-equivalent. This gives the spec operationalizable detectors.

### 6.C Contrarian — Gauge theory (physics)

In physics, *gauge* = an absolute-looking measurement that turns out to be frame-dependent. Same physics, different gauges → different apparent values.

Transfer: SP might be a gauge phenomenon. "He's elevated" vs "he's humble" could be measurement-artifact of the *observer's* frame, not a property of the person. What's gauge-invariant is the *asymmetry* between two parties' positioning, not either absolute level.

Implications if adopted:

- SP measurement is always a differential: SP(Person A relative to Person B), not SP(Person A).
- APT Inference captures the asymmetry directly; APT Profiling captures *tendencies to produce asymmetry* (i.e., the person reliably positions up/down/same vs others).
- This aligns with Inversion 3.A (SP is relational) but gives it a formal structure.

**Implication:** A rigorous framing for the relational/absolute tension. SP bearings in APT Profiling are *relative-position tendencies* not absolute levels.

---

## Mechanism 7 — Extrapolation

### 7.A Generic — Future modulator proliferation

If SP becomes accepted as a modulator on Domain 1, it sets a precedent. Future observations will reveal other modulators:

- **Tempo** (response latency, message cadence) as modulator
- **Affect** (emotional valence) as modulator
- **Coherence** (consistency of stance across time) as modulator

Extrapolated: APT's mature form is `Attachment(3 vars) × Modulator-Layer(n modulators) × Presentation(3 layers)`. The modulator layer grows over time.

**Implication:** The architectural decision now sets the template for future additions. Making Self-Positioning a *named first-class modulator* creates a clean slot for future ones. Making it a full third domain *doesn't* extend as naturally.

### 7.B Focused — SP in APT Profiling output: use cases

If APT Profiling includes SP bearings, these product-level use cases emerge:

1. **Chat history audit** — user feeds their LinkedIn DMs; system outputs per-message SP score and longitudinal trend.
2. **Feedback coaching** — "your last 10 DMs show Try-Hard pattern; specific suggestions: reduce self-justification clauses by X%, shift premise from requesting-permission to selecting-the-other."
3. **Relationship diagnostics** — "your SP with Person A trends high; with Person B, collapses. Here's what's different."
4. **Outreach pre-send analysis** — before sending, run the message through the SP detector and flag collapses.
5. **Persona coherence check** — detect when the user's SP is incoherent with their stated identity (e.g., writing as expert but supplicating).

**Implication:** SP integration has immediate downstream product value. This justifies the investment in getting the concept right.

### 7.C Contrarian — Modulator logic taken to the extreme

If SP modulates Charm/Hope/Fear, and other modulators exist, extrapolate: Charm/Hope/Fear may not be fundamental. They may be *emergent phenomena* at the intersection of deeper forces:

- Worldview-overlap (why this exchange is possible)
- Positioning-dynamics (respect/legitimacy)
- Stakes-structure (what's at risk)

Under this extrapolation, APT's "three attachment variables" are mid-level abstractions, not fundamentals. Self-Positioning isn't a modulator on fundamentals; it's a piece of a deeper framework that would eventually subsume APT.

**Implication:** Long-horizon threat to APT's framing. Worth flagging that the modulator concession is a first step on a path that *might* require rebuilding APT from deeper primitives. Not actionable now, but not deniable either.

---

## Testing Phase

Applying the five tests to each output.

### Survivors (passed novelty + scrutiny + fertility + actionability)

| ID | Output | Novelty | Survives scrutiny | Fertile | Actionable | Independent? |
|---|---|---|---|---|---|---|
| **1.B** | LinkedIn-specific operationalization (premise, self-justification density, elaboration gradient, response-trigger asymmetry, stakes-acknowledgment) | ✓ (concrete beyond sensemaking) | ✓ | ✓ (user can audit today) | ✓ direct | Partial — converges with 5.B, 6.B |
| **2.A** | 2×2 typology: Confident Selector / Respected Expert / Disengaged / Try-Hard | ✓ (names user's failure mode) | ✓ | ✓ (diagnostic language) | ✓ | Yes — unique output |
| **2.C** | SP as Costly Signal — willingness to risk the exchange | ✓ (reframes mechanism) | ✓ (explains why fake SP fails) | ✓ (new detection angle) | ✓ (detect exit-willingness in messages) | Partial — aligns with 3.B's effort-concealment |
| **3.A** | SP is RELATIVE, not absolute (optimal = slightly-elevated-vs-them) | ✓ (refines sensemaking's commitment) | ✓ (explains where SP repels) | ✓ | ✓ (asymmetry measurement) | Converges with 6.C — strong signal |
| **3.B** | Deeper mechanism: Visible-Need-Level (SP is stable way of producing low visible-need) | ✓ | ✓ (if visible-need hides, high-SP people are just skilled at this) | ✓ (renaming candidate: *Non-Supplication*) | ✓ | Partial — aligns with 2.C |
| **3.C** | SP is relational-only, not an individual property (dyadic) | ✓ (contrarian) | ✓ (in weakened form: profile tendencies not levels) | ✓ (reshapes APT Profiling) | Partial (abstract) | Converges with 6.C |
| **4.B** | Three-domain restructure: Attachment / Positioning / Presentation (relocates Investment-Asymmetry into Positioning) | ✓ (not in sensemaking) | Partial — sensemaking explicitly warned against premature new domain | ✓ (symmetric architecture) | ✓ (concrete spec surgery) | Standalone |
| **4.C** | Replace Expressed Frame with Self-Positioning (no concept growth) | ✓ | Partial — loses internal-driver layer | ✓ | ✓ (minimal surgery) | Standalone |
| **5.B** | Three new PRAGMA signals: Withholding, Premise-Posture, Self-Justification-Density | ✓ (concrete) | ✓ | ✓ (operationalizes SP detection) | ✓ direct | Converges with 1.B — strong signal |
| **6.B** | Ethology signal catalog (stillness, eye-contact, territory, rhythm, resource-confidence) | ✓ | ✓ | ✓ (cross-domain detector set) | ✓ | Converges with 1.B, 5.B |
| **6.C** | Gauge framing — SP is gauge-invariant only as asymmetry | ✓ (formal structure for relational claim) | ✓ | ✓ | Partial (needs formalization) | Converges with 3.A, 3.C |
| **7.A** | Modulator-layer precedent — SP sets template for future modulators | ✓ | ✓ | ✓ (shapes architectural decision) | ✓ (informs choice between 4.B and "named modulator") | Standalone |
| **7.B** | Product use cases (chat audit, coaching, diagnostics, pre-send, coherence) | Partial (follows from operationalization) | ✓ | ✓ | ✓ direct | Follows from 1.B, 5.B |

### Refined / Deferred

| ID | Output | Why deferred |
|---|---|---|
| 1.A | Domain-of-relevance frame | True but adds little operational value beyond noting. Folded into spec as a caveat, not a primary contribution. |
| 5.A | Other absences (Resonance, Timing Momentum, Stakes-level) | Valid but out-of-scope; flagged for future inquiries. |
| 1.C, 5.C, 7.C | "APT itself may need replacement" | Three contrarians converge on this. *That's a signal.* Too big for this iteration but must be flagged in the open-questions list. The user should be aware this family of doubts exists. |

### Killed

| ID | Output | Why |
|---|---|---|
| 2.B | PRAGMA signature operationalization | Already known from sensemaking; not novel enough at the innovation layer. Kept as implementation note, not counted as survivor. |
| 4.A | Text-only constraint | Too restrictive — excludes valid multi-modal applications (the clothing-store example). Kept as a mode-specific scoping note rather than a framework choice. |
| 6.A | Executive presence / brand distance | Vocabulary import only; no new operational content beyond 6.B. Absorbed into 6.B's catalog and 2.A's typology. |

### Convergence Signal

Three clusters of mechanisms pointed to the same core innovation:

- **Cluster 1 (Signal Catalog):** 1.B, 5.B, 6.B → three mechanisms independently produced an operational signal catalog. *High confidence.*
- **Cluster 2 (Relational/Gauge):** 3.A, 3.C, 6.C → three mechanisms independently produced the claim that SP is measured as asymmetry, not absolute value. *High confidence.*
- **Cluster 3 (Mechanism reframe):** 2.C, 3.B → two mechanisms pointed to a deeper mechanism (costly signal / visible-need). *Medium confidence — two is suggestive, not converged.*
- **Cluster 4 (APT-level doubt):** 1.C, 5.C, 7.C → three contrarian outputs converged on "APT itself may be insufficient." *High confidence that this doubt is real, but out-of-scope for resolution here.*

---

## Assembly Check

Combining survivors: does a larger architecture emerge?

**Yes.** The assembly produces a more complete proposal than any individual output:

### The Assembled Proposal

**1. Name**

Primary: **Self-Positioning** (umbrella).
Primary axis: **Self-Elevation** (internal bearing).
Secondary axis (from 4.B, 6.C): **Relative-Position** (asymmetry vs the other party).
Tertiary axis (from 2.A, relocated from Expressed Frame per 4.B): **Investment-Asymmetry** (who's chasing).

Alternative candidate from 3.B: **Non-Supplication** — emphasizes the mechanism (visible-need concealment) over the posture. Stronger mechanism name, weaker umbrella name. Reject as primary, note as mechanism-level description.

### 2. Architectural Placement

Two viable paths emerge from the survivors, *against* sensemaking's original preference:

**Path A (sensemaking's preferred): Named Modulator**
Insert Self-Positioning as a named modulator section between Domain 1 and Domain 2. Minimal surgery. Preserves existing architecture. Matches 7.A's precedent-setting argument: creates a clean slot for future modulators.

**Path B (innovation's assembly produces): Third Domain "Positioning"**
From 4.B + 3.A + 6.C + 2.A: Positioning now has three potential axes (Self-Elevation, Relative-Position, Investment-Asymmetry) — enough to justify a full domain. Invest-Asymmetry relocates from Expressed Frame to Positioning. Presentation's Expressed Frame is renamed/narrowed.

The assembly leans toward **Path B**. Sensemaking's "premature" warning was based on one axis; innovation found three. The third-domain structure is symmetric, clean, absorbs the transcript's insight, and is better-aligned with the Cluster 2 convergence (relational/gauge) because Positioning as a domain naturally carries axes that are measured relationally.

*This is a real tension with sensemaking's commitment.* Critique phase should resolve.

### 3. Mechanism

Multiplicative gating (from sensemaking) enriched by costly-signaling (2.C) and visible-need (3.B):

```
Attachment ≈ f(charm, hope, fear) × g(Positioning)
```

where `g(Positioning)` depends on:

- **Self-Elevation level** (relative to other)
- **Exit-willingness** (costly signal — willingness to risk the exchange)
- **Visible-need concealment** (low visible supplication)

Failure signature: devaluation ("this guy doesn't deserve this") when g → 0.

### 4. PRAGMA Inference

Three new inference signals (from 5.B) + ethological cross-check (from 6.B):

| Signal | Definition | High SP | Low SP |
|---|---|---|---|
| **Withholding-Signal** | negative space — what the speaker chose not to say | present (comfortable not-elaborating) | absent (over-elaborates everywhere) |
| **Premise-Posture** | opening positioning | selecting / offering / asserting | requesting-permission |
| **Self-Justification-Density** | clauses/msg explaining why I'm writing | low | high |
| **Exit-Willingness** | risk taken in the message | high (disagreement, selectivity, terminable-close) | low (safety-optimized, hedged, open-ended) |
| **Rhythm-Comfort** | comfort with silence/delay | present | rushed, filler-laden |

These are *inference signals*, not new PRAGMA primary dimensions. They compose from PRAGMA measurements and text-level features.

### 5. User-Facing Diagnostic (LinkedIn case)

From 7.B, 1.B, 2.A: concrete diagnostic the user can apply to their own messages today:

**Five-question audit** for any outgoing message:

1. Does my premise request permission or select/offer?
2. How many clauses explain why I'm writing?
3. Do I elaborate beyond what the point requires?
4. Does my close allow them to not reply?
5. Am I willing to not get a response? (And does that show?)

Map result to the 2×2: Confident Selector / Respected Expert / Disengaged / Try-Hard. If Try-Hard, the message is leaking low Self-Positioning regardless of how charming, hopeful, or consequential your content is.

---

## Concrete Options (for Critique)

The critique phase should adjudicate:

### Naming

- [Primary candidate] **Self-Positioning** (with Self-Elevation as axis)
- [Alternative] **Positioning** (if promoted to third domain per 4.B)
- [Alternative] **Non-Supplication** (mechanism-emphasizing per 3.B)
- [Alternative] **Standing** (captures both internal bearing and external perception)

### Architectural Placement

- [Option α] **Named Modulator** — minimal surgery; sensemaking's preferred path
- [Option β] **Third Domain "Positioning"** — invasive but symmetric; innovation assembly's emergent path
- [Option γ] **Replace Expressed Frame** — concept-count-neutral; loses internal-driver layer

### Mechanism Framing

- [Baseline] Multiplicative gating (from sensemaking)
- [Enriched] Multiplicative gating + costly-signaling + visible-need-concealment

### PRAGMA Inference

- Three-to-five new inference signals (Withholding, Premise-Posture, Self-Justification-Density, Exit-Willingness, Rhythm-Comfort)
- Implementation: new APT inference rule, not PRAGMA dimension extension

### Diagnostic

- Five-question audit mapped to 2×2 (Try-Hard / Disengaged / Confident Selector / Respected Expert)

---

## Open Items (forward to Critique)

- **O1** — Resolve Path α vs Path β (Named Modulator vs Third Domain). Innovation leans β; sensemaking committed α. The three-axis finding (Self-Elevation + Relative-Position + Investment-Asymmetry) materially changes sensemaking's "one axis, premature" reasoning. Critique should judge whether the three axes are distinct enough to justify a domain.
- **O2** — Final name choice. Innovation keeps Self-Positioning as primary; Critique should stress-test against Standing and Non-Supplication.
- **O3** — Relational-only (dyadic) vs individual-with-bearings (trait-like with relational expression). Innovation's Cluster 2 convergence leans relational; APT Profiling output shape depends on resolution.
- **O4** — APT-level doubt (Cluster 4): three contrarian mechanisms independently suggested APT itself may be insufficient. This is out-of-scope for resolution but needs to be surfaced honestly — it's not nothing.

---

## Mechanism Coverage (Telemetry)

- **Generators applied:** 4 / 4 (Combination, Absence Recognition, Domain Transfer, Extrapolation — all three variations each)
- **Framers applied:** 3 / 3 (Lens Shifting, Constraint Manipulation, Inversion — all three variations each)
- **Convergence:** YES
  - Cluster 1 (Signal Catalog) — 3 mechanisms converge — HIGH confidence
  - Cluster 2 (Relational/Gauge) — 3 mechanisms converge — HIGH confidence
  - Cluster 3 (Mechanism Reframe — costly signal / visible need) — 2 mechanisms — MEDIUM confidence
  - Cluster 4 (APT-level doubt) — 3 mechanisms — HIGH confidence, but out-of-scope
- **Survivors tested:** 13 surviving outputs, all passed novelty + fertility + actionability; scrutiny partial on 4.B (architectural tension with sensemaking — forwarded to Critique) and 4.C (loses internal layer — forwarded)
- **Failure modes observed:** none critically
  - Premature Evaluation: avoided (generation separated from testing)
  - Single-Mechanism Trap: avoided (all 7 mechanisms × 3 variations applied)
  - Early Frame Lock: avoided (did not accept first good output)
  - Innovation Without Grounding: avoided (all survivors tested)
  - Mechanism Exhaustion: not reached (strong convergence before exhaustion)
  - Survival Bias: *partial risk* — the three contrarian "APT is wrong" outputs (1.C, 5.C, 7.C) were deferred as "out of scope" rather than absorbed. This may be correct scoping OR comfortable dismissal. Flagging for Critique.
- **Overall:** **PROCEED** — sufficient coverage, strong convergence across three clusters, survivors tested, concrete options produced for Critique. One scope-creep flag (Cluster 4) forwarded honestly.
