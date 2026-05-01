---
status: active
supersedes: devdocs/inquiries/apt_missing_dimension/finding.md
---
# Finding: apt_self_focus_reframe

**This finding supersedes** `devdocs/inquiries/apt_missing_dimension/finding.md` at the **vocabulary and spec-additions level.** The architectural commitments from the prior finding (Path α — Named Modulator between Domain 1 and Domain 2; multiplicative gating mechanism; trait-with-bearings; devaluation failure signature; 5-signal catalog; 2×2 diagnostic structure; Cluster 4 reopening conditions) are **inherited unchanged.** What changes is the axis label, the naming convention, the external-correlate layer's framing, plus several spec additions.

## Question

The prior inquiry (`apt_missing_dimension`) established that APT (Charm/Hope/Fear × Content/Style/Expressed-Frame) was missing a dimension — a meta-pattern surfacing in a Turkish transcript as *kendini büyük görmek* (holding yourself as big), slight disregard, not over-helping. The prior finding integrated this as **Self-Positioning** with **Self-Elevation** as its internal axis (a stable-bearing state description) and five external behavioral correlates (withholding, freely-shown displeasure, calibrated terseness, unhurried rhythm, absence of status-seeking moves).

The user then proposed a reframe: the root concept is not Self-Elevation (a *state*) but **Self-Focus** (*kendine odaklanmak*) — where your attention genuinely lives — with **Displayed Self-Focus** (*kendine odaklanmanın gözükmesi*) as the visibility requirement. Self-Focus is *causal*: attention genuinely on your own priorities *produces* the scarce investment, the unmanaged reactions, the absence of over-giving, and the amplified charm/hope/fear signals. Self-Elevation only *labels* the posture without naming the mechanism.

**The inquiry question:** Is the Self-Focus reframe materially better than the Self-Positioning / Self-Elevation framing — and if so, which of four integration paths wins:

- **(A)** Full replacement (umbrella + axis)
- **(B)** Swap axis while keeping Self-Positioning umbrella
- **(C)** Surface vocabulary swap only
- **(D)** Reject as downstream proxy for visible-need-concealment already captured in iteration 1

**The goal:** Verdict precise enough to either edit specific lines in the iteration-1 finding.md, or treat this iteration-2 finding as the superseding document.

---

## Finding

**The Self-Focus reframe is adopted via Path (B).** Architectural commitments inherited; vocabulary refined at the axis level; external-correlate layer given an explicit name; several spec additions required.

### The Decision Structure

```
Self-Positioning         ← umbrella (preserved — structural-role label in APT)
├── Self-Focus           ← internal axis (causal-directional framing —
│                          attention on own priorities vs on their response)
│   │
│   └── [dual-pole: Self-Focus (positive) ↔ Supplication (negative)]
│
└── Displayed Self-Focus ← external correlate layer (visibility principle —
                            the internal state must be observable in behavior)
    │
    └── Operationalized by:
         • 5-signal catalog (inference layer)
         • 6 text-feature metrics (implementation layer, text-mode)
```

### Primary Decisions

#### 1. Axis label: **Self-Focus** (primary)

- Turkish: *kendine odaklanmak*
- Selected after rigorous comparison against six alternatives (Own-Agenda-Focus, Task-Focus, Grounded Attention, Centered-Attention, Genuine Attention, Unselfconscious Engagement)
- **Required mitigations:**
  - **Pro-social reframe in the spec introduction** — explicitly disambiguates Self-Focus from: (a) narcissism (highly politically-optimized attention on being seen positively) and (b) the "self-focused attention" construct from public/private self-consciousness research (Buss 1980; Duval & Wicklund 1972 — awareness of self as object). Self-Focus here is narcissism's *opposite* — narcissism is intensely attuned to others' reception; Self-Focus is not.
  - **Alternative labels listed in Open Questions** — so users for whom Self-Focus reliably mis-lands can substitute (Own-Agenda-Focus, Task-Focus, Grounded Attention, Centered-Attention).

#### 2. Naming convention: dual-pole

The axis is named by both poles explicitly, parallel with APT's Expressed Frame convention ("I'm the selector" vs "please like me"):

- **Positive pole — Self-Focus:** attention genuinely on own priorities / agenda
- **Negative pole — Supplication:** attention on securing the other's response / approval

#### 3. External correlate layer: **Displayed Self-Focus** as principle

*Kendine odaklanmanın gözükmesi* — the visibility commitment. Internal self-focus without observable manifestation doesn't produce the modulator effect. Performed self-focus (trying to appear self-focused while desperate) produces distress signals, not modulator signals — the two are distinguishable on the behavioral surface.

Displayed Self-Focus is **the principle** (visibility requirement); the **5-signal catalog** operationalizes it at the inference level; the **6 text-feature metrics** operationalize the catalog at the implementation level for text-mode contexts.

#### 4. Causal mechanism (replaces iteration-1's state-level description)

When your attention in an interaction is genuinely on your own priorities (your agenda, your reactions, your sense of what matters) — not on securing the other's response or approval — the following emerge naturally:

- **Investment is calibrated low** — you don't over-give because the exchange isn't your priority
- **Reactions show freely** — you're not managing their feelings; your reactions are your information, not their experience
- **Over-giving is absent** — the exchange isn't where your attention is
- **Charm, hope, fear signals amplify** — when present, they carry the credibility of a person attending to their own life rather than auditioning for this one

**Multiplicative gating mechanism (unchanged from iteration 1):**

```
Attachment ≈ f(charm, hope, fear) × g(self-positioning)
```

where g(self-positioning) is driven by the Self-Focus axis. When g collapses (attention flips to securing-their-response), high f(charm, hope, fear) still produces near-zero real attachment. The failure signature is **devaluation** — "this guy doesn't deserve this" — triggered by the other party perceiving asymmetric-need.

Each of the three attachment variables is individually modulated:

- **Charm** under low Self-Focus reads as shiny-but-hollow → devalued
- **Hope** under low Self-Focus reads as desperate-to-please → offer loses perceived value
- **Fear** under low Self-Focus reads as bluster → fails to consolidate into respect

### PRAGMA Inference — Two Operational Layers

**Layer 1 — 5-signal catalog (inference level, unchanged from iteration 1):**

| Signal | Definition | High Self-Focus | Low Self-Focus |
|---|---|---|---|
| **Withholding-Signal** | Negative space — what the speaker chose not to say | Present (comfortable not-elaborating when invited) | Absent (over-elaborates everywhere) |
| **Premise-Posture** | Opening frame | Selecting / offering / asserting | Requesting-permission |
| **Self-Justification-Density** | Clauses-per-message explaining why speaking | Low | High |
| **Exit-Willingness** | Risk taken in the move | High (disagreement, selectivity, terminable-close) | Low (safety-optimized, hedged, open-ended) |
| **Rhythm-Comfort** | Comfort with silence / delay | Present (unrushed) | Rushed, filler-laden |

Each signal is now *causally derivable* from the Self-Focus framing — a consequence of where attention lives — rather than a separate behavioral correlate of an "elevated posture."

**Layer 2 — 6 text-feature operational metrics (implementation level, new in iteration 2):**

| Metric | Computes | Links to signal |
|---|---|---|
| **Opening verb class** | Self-action vs other-request | Premise-Posture |
| **Pronoun ratio** (I/we vs you/your) | Balanced or you-heavy | Premise-Posture, Self-Justification-Density |
| **Question-to-statement ratio** | Structural openness | Self-Justification-Density |
| **Self-justification clause count** | Direct measurement | Self-Justification-Density |
| **Elaboration gradient** | Word count per point | Withholding-Signal |
| **Closing assumption tone** | "Take it or leave it" vs "waiting for response" | Exit-Willingness |

These are text-mode metrics. Multimodal extensions (voice, video) can add parallel metric sets downstream without re-architecting the spec.

### User-Facing Diagnostic

**2×2 typology (Self-Focus × Investment-Asymmetry):**

| | Low Investment (stepping back) | High Investment (leaning in) |
|---|---|---|
| **High Self-Focus** | **Selective Engager / Confident Selector** — attention on own priorities, not leaning in | **Grounded Contributor / Respected Expert** — leaning in from own agenda (target) |
| **Low Self-Focus** | **Disengaged / Avoidant** — attention on them but not leaning in (defensive) | **Try-Hard / Supplicating** — attention on them, leaning in from need (user's LinkedIn failure mode) |

(Quadrant names — iteration-1 labels remain viable; iteration-2 alternatives optional.)

**Five-question audit** (refined wording under Self-Focus framing):

1. Does my premise reflect my priorities (selecting, offering, asserting) or their approval (requesting-permission, justifying my right to write)?
2. How many clauses explain why I'm writing / why I'm qualified / why I deserve attention?
3. Do I elaborate beyond what the point requires — because I'm tracking their reaction?
4. Does my close allow them to not reply, or does it extract a response?
5. Is my attention genuinely on my own agenda, or on securing their response? (And does that show?)

**Diagnosis of the user's concrete LinkedIn case:** Failure mode is **Try-Hard / Supplicating** — attention has drifted from own priorities to securing the response. Fix is not "add more charm" but "shift the attention direction that the message is written from" — reduce self-justification clauses, shift premise from permission-requesting to selecting/offering, comfortable pauses, terminable close, minimum viable word count. This is trainable (performance-psychology pre-performance protocols adapt cleanly).

### Appropriate-Low-Self-Focus Caveat (new in iteration 2)

Low Self-Focus is a failure mode in **value-establishing contexts** (professional first-contact, networking, sales outreach, status-establishing exchanges). It is *appropriate and healthy* in other contexts:

- **Genuine vulnerability / authentic need** — asking for help you actually need, expressed transparently. Performing Self-Focus while concealing real need is its own inauthenticity.
- **Transparent power asymmetry** — intern-to-CEO, student-to-professor in domain. Appropriate humility is not Try-Hard.
- **Intimate / high-warmth conversations** — deep conversations with close friends or partners. Mutual other-focus, shared vulnerability, and deep listening are the target here, not Self-Focus.
- **Ritual / ceremonial contexts** — condolences, apologies, formal gratitude. Structured other-centering is the correct form.

The modulator's relevance is **context-scoped.** The diagnostic is for value-establishing contexts, not universal.

### Anxious-Distracted Edge Case (new in iteration 2)

Internal self-focus without visible manifestation doesn't produce the modulator effect — the *gözükmesi* requirement is load-bearing. **Anxious-distracted self-focus** (attention on own anxiety / embarrassment / need-to-succeed) is visible as distress signals — hedging, apologizing, rushed rhythm, over-explaining — not as the 5-signal catalog. The catalog distinguishes productive self-focus from anxious look-alikes on the behavioral surface. No additional spec qualifier needed; the visibility requirement does the disambiguation.

### Confidence

- **HIGH:** Path (B) is correct; Self-Focus is the causal-mechanism framing of the phenomenon iteration-1 named Self-Elevation; 5-signal catalog structure; 2×2 diagnostic; multiplicative gating; trait-with-bearings; devaluation failure signature.
- **MEDIUM:** Final English label choice (Self-Focus has narcissism-connotation and psych-literature-collision risks — mitigated by pro-social reframe introduction + disambiguation + alternatives in Open Questions); 6 operational metrics' empirical independence (need validation against annotated conversations).
- **LOW / flagged:** Whether attention-direction framing is itself downstream of a deeper framing (genuine-vs-evaluative, extractive-vs-non-extractive, outcome-independence — Cluster E convergence signal; parallel with iteration-1 Cluster 4 APT-level doubt).

---

## Reasoning

### Why Path (B) over (A), (C), (D)

**Path (A) — Full replacement of umbrella with Self-Focus:** KILLed. Losing "Self-Positioning" as the umbrella removes the structural-role signal that the concept is a modulator at the positioning level within APT. The name parallel with Attachment / Presentation domain-level names weakens. Future modulators (Tempo, Affect, Coherence) would need their own umbrella names; Self-Positioning establishes the pattern that modulators get position/role labels.

**Path (C) — Surface-only swap:** KILLed. This treats Self-Focus and Self-Elevation as equivalent vocabulary for the same concept. They are not. Self-Focus is the *causal-mechanism* framing; Self-Elevation is the *state* framing. The change is theoretical, not cosmetic — causal descriptions are stronger than state descriptions because they explain WHY and generate testable predictions. Calling this a surface swap understates the gain.

**Path (D) — Reject the reframe entirely:** KILLed. The reframe aligns with iteration-1's innovation Cluster 3 (visible-need-concealment as potentially deeper than Self-Elevation — accepted as MEDIUM-confidence supplementary theory). Rejecting now would contradict that acceptance. Additionally, the causal-mechanism framing gives each of the 5 signals a derivable origin, which is theoretically valuable.

**Path (B) — Axis swap with umbrella preserved:** SURVIVED. Keeps structural-role signal (Self-Positioning) clear; gains causal-mechanism clarity (Self-Focus). Minimum surgery; iteration-1 architecture inherited.

### Why Self-Focus over six alternative labels

The final label was contested. Seven candidates evaluated against 8 dimensions with adversarial testing.

**Genuine Attention** — KILLed on D3 (Operational Testability). "Genuine" is evaluative; auditing "was my attention genuine?" requires self-judgment, not observation. The insight (genuine vs evaluative attention may be the deeper axis) is preserved in the spec's description of what makes Self-Focus work, but not as the label.

**Unselfconscious Engagement** — KILLed on D6 (Parsimony). Clunky three-word phrase; hostile to user-facing usage. The insight (the target is attention unentangled with self-monitoring) is preserved in the spec's description.

**Own-Agenda-Focus** — SURVIVED as secondary. Clean on psych-literature collision; avoids narcissism landing. But "agenda" carries political/strategic connotation in English ("hidden agenda"), and the three-word phrase is slightly clunky. Best role: formal synonym in Open Questions.

**Task-Focus** — SURVIVED as secondary. Performance-psychology pedigree (importable pedagogy: pre-performance routines, process cues, body-scan grounding). But has its own collision: "task-focus" in cognitive/attention research means focus on a specific cognitive task — different construct. Solves narcissism collision, introduces task-literature collision. Net uncertain vs Self-Focus.

**Grounded Attention** — REFINEd to option for presence-preference. Clean on English collisions but "grounded" is diffuse — loses the specific directional content (attention on WHAT?). Sacrifices the causal-directional specificity that was the reframe's point.

**Centered-Attention** — REFINEd to option for bilingual-max-safety preference. Similar to Grounded Attention — clean but diffuse.

**Self-Focus** — SURVIVED as primary with mitigations. Faithful to user's native Turkish proposal; preserves causal-directional specificity. English risks (psych-literature collision with "self-focused attention" research construct; narcissism connotation in self-help vocabulary) are real but *mitigable* with one paragraph of disambiguation in the spec introduction — standard practice for technical vocabulary. Alternatives each sacrifice either specificity or introduce their own collisions.

The decisive factor: **user's native-language proposal is authentic intuition.** The user rejected Self-Regard (ego) and Investment-Control (strategic) and landed on *kendine odaklanmak* for reasons that matter. Adopting the English equivalent with disambiguation is the honest path. Alternatives are recorded for users who hit the mis-reads.

### Why dual-pole naming

APT's Expressed Frame is already named bidirectionally ("I'm the selector" vs "please like me"). Applying the same naming convention to Self-Focus ("Self-Focus (attention on own priorities) vs Supplication (attention on securing their response)") is structurally consistent and names both failure modes explicitly — which aids diagnosis.

### Why operational measurement layer

The user's primary valuation is LinkedIn-diagnostic actionability. Concrete text-feature metrics directly serve this. They don't replace the 5-signal catalog; they operationalize it for text-mode contexts. Having both principle (catalog) and implementation (metrics) in the spec enables automated tooling (pre-send checkers, post-hoc reviewers, live conversation annotators) without rewriting the theoretical commitments.

### Why pro-social reframe in introduction

"Self-Focus" in casual English often implies "selfish" and collides with the public/private self-consciousness literature. Users coming from either context will mis-land. Disambiguation in one paragraph is cheap; mis-adoption cost is larger. Standard practice for technical vocabulary.

The reframe's content: apparent Self-Focus is *pro-social* because it produces reliable, honest, politics-independent behavior. Narcissism is the opposite — highly politically-optimized, constantly monitoring others' reception.

### Why appropriate-low-Self-Focus caveat

Without it, the diagnostic over-applies. Users would pathologize appropriate humility, authentic vulnerability, intimate warmth, and ceremonial other-centering. Scoping clarity *strengthens* the diagnostic rather than weakening it. The diagnostic is for value-establishing contexts, not universal.

### Why Displayed Self-Focus as principle (not catalog-equivalent)

Two readings considered:
- Displayed Self-Focus *is* the 5-signal catalog (layer names equivalent — minimalist)
- Displayed Self-Focus is a *principle* that the 5-signal catalog *operationalizes* (pedagogical separation)

The principle-operationalization split wins: readers understand WHY the catalog matters (the visibility commitment) separately from HOW it's computed. This parallels other APT structure and enables multimodal extensions (voice, video metric sets) without re-writing the theoretical commitment.

### What iteration-1 called Self-Elevation, iteration-2 calls Self-Focus

The transcript that seeded the original inquiry used *kendini büyük görmek* — literally "seeing yourself as big." Iteration 1 translated this into **Self-Elevation** at the axis level. That was accurate to the transcript's vocabulary but named the *state* (how big you hold yourself) rather than the *mechanism* (where your attention lives).

Iteration 2 recognizes that the user's subsequent refinement (*kendine odaklanmak* — where your attention actually lives) is the *causal upstream* of Self-Elevation. The state of "holding yourself big" is what results when attention is genuinely on your own priorities. Naming the cause (Self-Focus) is theoretically stronger than naming the state (Self-Elevation) because causal descriptions generate predictions and explain mechanisms.

The change is refinement, not retraction. The transcript's original insight (the dimension exists; it's distinct from the three attachment variables; it modulates them multiplicatively) stands. What shifts is the name we give it and the abstraction level of that name.

### Cluster E flagged with reopening conditions

Three of innovation's inversion outputs (3.A, 3.B, 3.C) independently converged on a deeper reframing: the axis may be fundamentally about HOW attention is held (genuine-vs-evaluative, extractive-vs-non-extractive, outcome-dependent-vs-independent) — not about WHERE it's directed (self vs other). This parallels iteration-1's Cluster 4 (APT-level substrate doubt).

Not acted on in iteration 2 — scope was label refinement + spec additions, not substrate reframing. Flagged with explicit reopening conditions:

- If operationalization reveals that attention-direction metrics don't reliably distinguish productive from anxious self-focus → the deeper framing (how attention is held) may need primary spec status.
- If the "genuine vs evaluative" distinction surfaces in user auditing as the decisive factor (more than self vs other) → same.
- If multiple future modulators are discovered and they're all attention-based → attention-substrate reframe becomes forced.
- If iteration 3+ also defers this without engaging, the pattern becomes comfortable dismissal — at that point, an explicit substrate-reframe inquiry should be opened.

---

## Open Questions

1. **Alternative label candidates** — for users who hit the English-language mis-reads of Self-Focus despite the pro-social reframe:
   - **Own-Agenda-Focus** — cleanest on collisions, slightly clunky
   - **Task-Focus** — performance-psychology pedigree, cognitive-task-literature collision risk
   - **Grounded Attention** — clean but diffuse
   - **Centered-Attention** — clean but diffuse
   Users may substitute based on semantic preference; spec describes the concept, not the label-as-such.

2. **Final quadrant labels in the 2×2.** Iteration-1 labels (Confident Selector / Respected Expert / Disengaged / Try-Hard) remain viable. Iteration-2 alternatives (Selective Engager / Grounded Contributor) adopt the Self-Focus framing more explicitly. User preference.

3. **Empirical independence of the 6 operational metrics.** Defensible in principle (each targets a distinct text feature) but practical correlations may reduce effective dimensionality. Downstream empirical work: apply the metric set to 50+ annotated conversations; measure inter-metric correlation; if high correlation emerges, consolidate to 2-3 composite metrics.

4. **Personal pattern subtype profiling** (forward-looking). After the user applies the 5-question audit to 20-50 LinkedIn messages, subtypes within each quadrant likely emerge: Try-Hard via self-justification-dominant / over-elaboration-dominant / response-anxious / hedge-heavy / status-proving. Respected Expert via terse-authoritative / warm-grounded / selective-engaged / expert-depth. Extends the 2×2 from coarse-grained to personal-pattern tracker. Revisit after data accumulates.

5. **Anxious-distracted edge case: robust enough?** The spec currently resolves this via the visibility requirement (anxious self-focus shows as distress, not as the modulator signals). If user auditing reveals cases where the catalog misclassifies anxious-distracted as productive self-focus, explicit qualifier language may be needed.

6. **Cross-modal signals (voice, video).** The operational metrics are text-focused (aligned with the user's LinkedIn use case). Self-Focus has off-channel manifestations (tone, pacing-in-real-time, facial expression in voice/video) that the text metrics don't capture. Multimodal PRAGMA extensions can add parallel metric sets downstream without re-architecting the theoretical commitment.

7. **Cultural calibration.** What reads as productive Self-Focus in one cultural context (direct assertion, terse close, comfort with silence) may read as rudeness or incompetence in another. The spec is culture-neutral at the abstract framing level; operational metrics may vary by conversational norm context. Not explored in this iteration.

8. **Prescriptive vs descriptive tension.** APT is a descriptive theory. The user's LinkedIn application is prescriptive (how to *produce* Self-Focus in outgoing messages). The performance-psychology pedagogy (pre-performance routines, process cues, body-scan grounding) is a natural downstream import. Not fully specified here; flagged for future coaching-focused inquiry.

9. **Cluster E — attention-direction may be downstream of a deeper framing.** Three contrarian mechanisms in innovation converged on: "How attention is held (genuine/evaluative, extractive/non-extractive, outcome-independent) may be the deeper axis; Where it's directed (self/other) may be downstream." Out of scope for iteration 2 with explicit reopening conditions above. Parallel with iteration-1's Cluster 4 APT-level doubt flag.

10. **APT-level doubt (Cluster 4, iteration 1).** Still flagged. Three iteration-1 contrarian mechanisms converged on "APT itself may need substrate reframe (Resonance + Positioning as fundamentals; Charm/Hope/Fear as emergents)." Unchanged in iteration 2. Reopening conditions stand.

11. **Other absences noted but out-of-scope.** Resonance (shared world-model / genuine mutual recognition), Timing Momentum (when you appear in the other's life), Stakes-level (what's at risk). Unchanged from iteration 1. Candidates for future inquiries.

---

## Applying Iteration-2 to Iteration-1's `finding.md`

Two options for the user:

**Option A — Treat this document as the current finding.** The iteration-1 finding (`apt_missing_dimension/finding.md`) remains as historical context. This document is the current specification. Update the surgical plan for `apt_layer.md` to reflect the Self-Focus vocabulary.

**Option B — Update `apt_missing_dimension/finding.md` in place** with these iteration-2 changes:

1. Rename **Self-Elevation → Self-Focus** throughout (with *kendine odaklanmak* parenthetical at first use).
2. Adopt dual-pole axis naming: "Self-Focus vs Supplication."
3. Rename external-correlate layer to **Displayed Self-Focus** (*kendine odaklanmanın gözükmesi*).
4. Add the 6 text-feature operational metrics as implementation sub-layer beneath the 5-signal catalog.
5. Add the pro-social reframe paragraph to the Self-Positioning section introduction.
6. Add the appropriate-low-Self-Focus caveat subsection.
7. Add the anxious-distracted edge-case handling paragraph.
8. Update the causal-mechanism description — each signal derives from Self-Focus's causal chain (not from "elevated posture").
9. Swap 2×2 vertical axis label (Self-Elevation → Self-Focus); quadrant labels optional.
10. Update the Reasoning section with the iteration-2 adjudication (why Self-Focus wins over the six alternatives; why Cluster E is flagged).
11. Update the Open Questions section — alternative labels, empirical metric validation, subtype profiling, cross-modal signals, cultural calibration, Cluster E reopening conditions.

Either option is architecturally equivalent. Option A preserves iteration history; Option B consolidates into a single current document. User choice.
