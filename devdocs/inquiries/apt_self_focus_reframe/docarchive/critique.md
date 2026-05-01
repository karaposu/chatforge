---
status: active
discipline: td-critique
inquiry: apt_self_focus_reframe
iteration: 1
---
# Critique: apt_self_focus_reframe

## User Input

`devdocs/inquiries/apt_self_focus_reframe/`

Contents consumed:
- `_branch.md` — the question (adopt Self-Focus reframe? which of 4 paths?)
- `sensemaking.md` — committed Path (B) (axis swap with umbrella preserved); 5 open items forwarded
- `innovation.md` — 21 outputs, 14 survivors, 5 convergence clusters; one material challenge (label choice deserves rigorous evaluation, not sensemaking's working default)

---

## Phase 0 — Dimension Construction

### Dimensions Extracted From Sensemaking + Inherited from Iteration 1

This is iteration-2 refinement. Iteration-1 critique established 8 dimensions for the primary architectural decision. For iteration-2's scope (label refinement + spec additions within the committed Path α / Path B structure), the dimension set is tuned:

| # | Dimension | Success Criterion | Weight | Source |
|---|---|---|---|---|
| **D1** | **Explanatory Adequacy (causal clarity)** | The label + framing explains WHY the behaviors emerge (not just what state produces them) | **CRITICAL** | Sensemaking KI1, KI2 (causal > state principle) |
| **D2** | **Definitional Distinctness** | The label avoids collisions with existing psych-literature constructs (esp. "self-focused attention" public/private self-consciousness) and avoids misread as self-help/narcissism vocabulary | **CRITICAL** | Innovation 1.B (psych-literature collision flagged) |
| **D3** | **Operational Testability** | Maps to observable text/behavior features; concrete detection rules; user can compute from real messages | **CRITICAL** | Sensemaking OI2, Innovation Cluster B |
| **D4** | **User Actionability** | User can apply the diagnostic to a real LinkedIn message today and get a verdict | **CRITICAL** | User's primary valuation (preserved from iteration 1) |
| **D5** | **Structural Coherence with Iteration 1** | Respects iteration-1 commitments (Path α, multiplicative gating, trait-with-bearings, 5-signal catalog); doesn't require re-architecting what was already settled | **CRITICAL** | User's motivation (iterative refinement, not replacement) |
| **D6** | **Architectural Parsimony** | Minimum-viable additions; doesn't multiply concepts beyond what the evidence justifies | MEDIUM | FP of minimum complexity |
| **D7** | **Bilingual Compatibility** | Label lands cleanly in both Turkish (user's native) and English (spec language) | MEDIUM | Innovation 4.A |
| **D8** | **Honesty** | Acknowledges limits (alternatives not chosen, out-of-scope deeper reframes, context-scope caveats) without over-claiming closure | MEDIUM | Critique-framework foundational principle |

### Dimension Validation

Cross-reference against sensemaking's perspective coverage:

- Technical / Logical → D1, D3
- Human / User → D4
- Strategic / Long-term → D7 (label lifetime)
- Risk / Failure → D2, D8
- Resource / Feasibility → D6
- Definitional / Consistency → D2, D5
- Ethical / Systemic → D8 (scope honesty)

Coverage complete. No sensemaking perspective lacks a critique dimension.

### Stakes Assessment

Lower stakes than iteration 1:
- Architectural commitments are inherited; iteration 2 is label + spec-addition work
- Downstream impact is mostly cosmetic (vocabulary choice) and additive (new subsections)
- The one higher-stakes question: whether innovation's deeper-reframe signals (Cluster E) should be acted on or flagged

Burden of proof: balanced. For label choice, defense must demonstrate positive reasons (not just absence of problems). For spec additions, prosecution must demonstrate harm (not just over-engineering concern).

---

## Phase 1 — Fitness Landscape

**Viable region:** Passes all 5 critical dimensions, reasonable on medium.

**Dead region (fatal):**
- FAIL on D1 (doesn't explain causal chain — e.g., a label that describes outcome not cause)
- FAIL on D5 (breaks iteration-1 commitments — e.g., rewrites Path α)
- FAIL on D3 or D4 (unmeasurable / inapplicable)

**Boundary region:** passes critical, caveats on D2 (semantic collisions) or D6/D7 (clunkiness).

**Unexplored:** Cluster E territory (Outcome-Independence / Extractive-vs-Non-Extractive / Genuine-vs-Evaluative) — flagged by innovation as out-of-scope.

---

## Phase 2 — Adversarial Evaluation

### Cluster 1 — Architectural Path Verdict (confirming or challenging sensemaking's Path B)

Sensemaking committed Path (B): keep Self-Positioning umbrella, replace Self-Elevation axis with new label, add Displayed Self-Focus as external-correlate layer. Innovation did not materially challenge this at the structural level. Confirming:

- Path (A) — full replacement of umbrella: **KILLed** (loses structural-role signal of Self-Positioning)
- Path (C) — surface-only swap: **KILLed** (understates causal-clarity gain)
- Path (D) — reject: **KILLed** (ignores real theoretical advantage + alignment with iteration-1 supplementary theories)
- **Path (B) — SURVIVE** with refinements below

No re-adjudication needed. Path (B) holds.

---

### Cluster 2 — Axis Label Candidates

Innovation's major challenge: the final axis label deserves rigorous side-by-side evaluation, not defaulting to sensemaking's working "Self-Focus" label.

#### Candidate L1 — Self-Focus (user's Turkish-faithful label)

**Preview:** Likely viable with mitigations. User's preference carries weight.

**Prosecution:**

1. **Psychology-literature collision.** "Self-focused attention" is an established construct in psychology research (Buss 1980, Duval & Wicklund 1972) referring to awareness of self as object — public/private self-consciousness. Academic-adjacent users will import the wrong meaning. This is not a hypothetical — it's a guaranteed mis-read for any user with psych training.
2. **Narcissism connotation in self-help vocabulary.** "Self-focused" in casual English often implies "selfish." Self-help market routinely uses the vocabulary in the wrong sense. Users coming from that context will land wrong.
3. **Combined effect:** different user segments mis-land differently, making consistent adoption difficult.

**Defense:**

1. **User's native-language proposal.** The user proposed "kendine odaklanmak" after explicit reflection on what the concept is and what it is not (rejected Self-Regard, Investment-Control). The Turkish framing is authentic intuition; the English equivalent preserves the fidelity. User is the spec's author.
2. **Mitigations are strong.** A pro-social reframe in the spec introduction (Cluster C from innovation) explicitly disambiguates: "Self-Focus here is NOT narcissism or self-focused-attention research — it's a specific attention-direction that produces pro-social reliable behavior." This is one paragraph of disambiguation; any serious spec includes such disambiguations for technical terms.
3. **Alternatives have their own problems.** Each alternative either loses specificity (Grounded, Centered), introduces a different collision (Task-Focus), or becomes clunky (Unselfconscious Engagement, Own-Agenda-Focus). Trading one mitigable problem for an unmitigable one is a net loss.
4. **Directional content is preserved.** "Self-Focus" has specific positive content (attention on own priorities/agenda). Alternatives that avoid the "self" content (Centered, Grounded) lose this.

**Collision:**

Prosecution's strongest point (psych-literature collision) is specific enough to be mitigable: the spec's introduction explicitly disambiguates from the "self-focused attention" research construct. For users without that background, the collision doesn't trigger. For users with it, the disambiguation is one reading away.

Narcissism-connotation concern is softer and fully addressed by the pro-social reframe introduction.

Defense wins with mitigations.

**Position:**
- D1 Explanatory Adequacy: **PASS** (causal-directional)
- D2 Definitional Distinctness: **BOUNDARY** (collisions exist; mitigations work but require disambiguation work)
- D3 Operational Testability: **PASS** (via 5-signal catalog + 6 operational metrics)
- D4 User Actionability: **PASS (strong)** (user proposed the term; already internalized)
- D5 Structural Coherence: **PASS**
- D6 Parsimony: **PASS**
- D7 Bilingual Compatibility: **BOUNDARY** (Turkish clean, English has risks but mitigable)
- D8 Honesty: **PASS** (with explicit alternatives in Open Questions)

**Verdict: SURVIVE** — with required mitigations: (a) pro-social reframe in spec introduction, (b) explicit disambiguation from "self-focused attention" research construct, (c) alternatives listed in Open Questions so users who hit the mis-reads can substitute.

---

#### Candidate L2 — Own-Agenda-Focus

**Preview:** Clean on collisions, slightly clunky.

**Prosecution:**
1. "Agenda" carries political/strategic connotation in English ("hidden agenda," "political agenda") — may read as scheming or calculated.
2. Clunky phrasing — three words, hyphenated; harder to use in casual reference.
3. Turkish equivalent (*kendi gündemine odaklanma*) is grammatically clean but loses the directness of *kendine odaklanmak*.

**Defense:**
1. Specific and precise — names exactly what the attention is on.
2. Avoids narcissism landing entirely.
3. No collision with existing psych-literature constructs.

**Collision:** Avoidance of English collisions is real advantage, but "agenda" connotation is a new concern prosecution raises. Probably less impactful than Self-Focus's collisions but not zero.

**Position:**
- D1-D5 all PASS
- D6 Parsimony: BOUNDARY (clunk)
- D7 Bilingual Compatibility: PASS
- D2 Definitional Distinctness: PASS (stronger than Self-Focus)

**Verdict: SURVIVE as secondary/alternative.** Cleaner on collisions but loses user-preference and elegance. Best role: *formal synonym* or *Open-Questions alternative*, not primary label.

---

#### Candidate L3 — Task-Focus

**Preview:** Has performance-psychology pedigree; may have its own collision.

**Prosecution:**
1. "Task-focus" in cognitive/attention research refers to focus on a specific cognitive task — different construct than what APT needs. Collision.
2. Reads as purely functional/cognitive; misses the emotional/relational dimension of APT's modulator.
3. In casual usage, "task-focused" implies "not thinking about feelings" — wrong implication for an interpersonal modulator.

**Defense:**
1. Rich pedigree from performance psychology (athletes, musicians): importable pedagogy (pre-performance routines, process cues, body-scan grounding).
2. Captures the "genuine engagement with the matter at hand" quality.
3. Operationalizable via performance-psychology interventions.

**Collision:** Performance-psychology pedigree is valuable but the collision concern is structurally parallel to Self-Focus's collision — importing an existing construct that means something adjacent but not identical.

**Position:**
- D2 Definitional Distinctness: BOUNDARY (different collision but still a collision)
- Others: PASS

**Verdict: SURVIVE as alternative** with a caveat: it solves one collision (narcissism) while introducing another (cognitive-task literature). Net uncertain vs Self-Focus.

---

#### Candidate L4 — Grounded Attention

**Preview:** Presence-flavored, loses specificity.

**Prosecution:**
1. "Grounded" is diffuse — captures stability/presence but not the directional content.
2. No specific answer to "where is attention?" — which was the reframe's core insight (attention's direction matters).
3. Reads as meditation/mindfulness vocabulary; carries contemplative-tradition baggage.

**Defense:**
1. Clean on all English collisions.
2. Conveys the "stable, not volatile" quality of good self-positioning.
3. Avoids both narcissism and task-focus literature collisions.

**Collision:** Prosecution's "loses specificity" is the decisive point. The Self-Focus reframe's strength is the causal-directional insight. "Grounded" retreats from that.

**Position:**
- D1 Explanatory Adequacy: BOUNDARY (loses the direction content — "grounded attention on what?")
- D2 Definitional Distinctness: PASS
- Others: PASS

**Verdict: REFINE → hold as option if user explicitly prefers presence-flavored vocabulary.** Not the primary choice because it sacrifices the causal-directional insight.

---

#### Candidate L5 — Genuine Attention

**Preview:** Captures 3.A inversion insight; harder to measure.

**Prosecution:**
1. "Genuine" is evaluative — begs the question of what counts as genuine. Not operationally clean.
2. Doesn't distinguish between genuine self-focus (works) and genuine other-focus (also works) — loses the directional content entirely.
3. Hard to audit: "was my attention genuine?" is a self-judgment question, not an observable one.

**Defense:**
1. Reframes the axis insightfully — the real distinction may not be where attention is but whether it's evaluative or genuine.
2. Resolves the 3.A concern (other-focus can also work if genuine).

**Collision:** Prosecution's "operationally unclean" is the decisive point. The label creates evaluative-judgment problems.

**Position:**
- D3 Operational Testability: FAIL (self-judgment required)
- Others: PASS

**Verdict: KILL as label candidate.** The insight is valuable (genuine vs evaluative attention is a real axis) but not as the label — it belongs in the theoretical discussion of what makes Self-Focus work, not as the axis name. **Seed extracted:** the genuine-vs-evaluative frame can appear in the spec's explanation of what counts as productive Self-Focus, without being the label.

---

#### Candidate L6 — Unselfconscious Engagement

**Preview:** Accurate, clunky.

**Prosecution:**
1. Clunky phrase — three syllables, awkward to say.
2. "Unselfconscious" is a negative definition (named by what it isn't).
3. Academic-sounding; doesn't match the conversational feel of the rest of APT's vocabulary.

**Defense:**
1. Accurate — describes the target state precisely (attention on the exchange, unentangled with self-monitoring or reception-monitoring).
2. Captures the contemplative-tradition insight (ego-driven attention is the problem).

**Collision:** Accuracy vs elegance. Clunk is real.

**Position:**
- D6 Parsimony: FAIL (clunky)
- Others: PASS

**Verdict: KILL as primary label** — clunkiness makes it hostile to user-facing usage. **Seed:** the insight (unselfconscious engagement is the target) informs the spec's description of the state without being the label.

---

#### Candidate L7 — Centered-Attention / Merkezli Dikkat

**Preview:** Bilingual-clean, loses specificity.

**Prosecution:**
1. "Centered" is diffuse — similar critique to Grounded.
2. Meditation/self-help vocabulary; contemplative baggage.
3. No specific content about what "centered" means operationally.

**Defense:**
1. Clean in both Turkish and English.
2. Avoids narcissism landing.
3. Accessible — doesn't require disambiguation from psych-literature.

**Collision:** Same collision as Grounded Attention. Clean on risks, loses on specificity.

**Position:**
- D1 Explanatory Adequacy: BOUNDARY (diffuse)
- Others: PASS

**Verdict: REFINE → hold as option** if user prefers maximum safety over maximum specificity.

---

### Label Verdict Summary

| Label | Verdict | Role |
|---|---|---|
| **Self-Focus** | SURVIVE (with mitigations) | **Primary label** |
| Own-Agenda-Focus | SURVIVE (secondary) | Formal synonym / Open Questions alternative |
| Task-Focus | SURVIVE (secondary) | Alternative with different collision profile |
| Grounded Attention | REFINE | Option if user prefers presence-flavored |
| Centered-Attention | REFINE | Option if user prefers bilingual-max-safety |
| Genuine Attention | KILL as label; insight preserved in spec description | — |
| Unselfconscious Engagement | KILL as label; insight preserved in spec description | — |

**The decisive factor:** User's native-language proposal is authentic intuition. English risks are mitigable with explicit disambiguation. Alternatives either introduce their own collisions or sacrifice the causal-directional specificity that was the reframe's point.

**Recommended primary:** **Self-Focus** with required spec mitigations (pro-social introduction + psych-literature disambiguation + alternatives in Open Questions).

---

### Cluster 3 — Naming Convention (single-label vs dual-pole)

**Candidate N1 — Single-label axis:** axis named "Self-Focus" alone.

**Candidate N2 — Dual-pole axis:** axis named "Self-Focus (attention on own priorities) vs Supplication (attention on securing their response)."

**Prosecution of N1 (single-label):** The axis has two poles; naming only one hides the structure. Parallel with Expressed Frame (which is already bidirectional: "selector" vs "please like me") would favor dual.

**Prosecution of N2 (dual-pole):** Two labels to remember instead of one. Potentially over-specified for a spec that already has many concepts.

**Defense of N1:** Clean, simple, easy to refer to in casual discussion.

**Defense of N2:** Parallel with Expressed Frame is structurally consistent — if one frame-like axis is dual-poled, all should be. Names both failure modes explicitly, which aids diagnosis.

**Collision:** The parallel with Expressed Frame is the decisive structural argument. Both concepts are *frame-like* (named axes with two poles representing productive vs failure modes). Consistency matters.

**Position:**
- N1: all dimensions PASS, D5 BOUNDARY (inconsistent with Expressed Frame's convention)
- N2: all dimensions PASS

**Verdict: N2 SURVIVE — adopt dual-pole naming.** Parallel with Expressed Frame's existing convention.

---

### Cluster 4 — Operational Measurement Layer (6 text-feature metrics)

**Prosecution:**
1. Spec should stay at theoretical level; implementation details belong in a separate implementation doc.
2. Six metrics may be over-specified — some correlate (pronoun ratio and self-justification density both measure openings).
3. Text-feature metrics are too implementation-specific; the concept is multimodal and shouldn't be reduced to text features.

**Defense:**
1. User's primary valuation is LinkedIn-diagnostic actionability. Concrete metrics directly serve this.
2. Metrics don't replace the 5-signal catalog; they operationalize it for text-only contexts. Two levels of abstraction — principle (catalog) + implementation (metrics).
3. Correlation concern is empirical; the metrics are distinct in principle. Validation is downstream.
4. Multimodal generalization (voice, video) can have its own metric set; text-metrics are a text-specific instantiation.

**Collision:** Prosecution's "belongs in implementation doc" is valid methodologically, but the user's use case (LinkedIn DMs) is text-only. The metrics directly serve the valuation.

**Position:**
- D4 User Actionability: PASS (strong — direct operationalization)
- All other critical dimensions: PASS
- D6 Parsimony: BOUNDARY (six metrics vs the 5 already in the catalog)

**Verdict: SURVIVE — adopt as operational implementation layer** with explicit framing: "The 5-signal catalog defines inference signals; the 6 text-feature metrics operationalize the catalog for text-only conversations." Multimodal extensions (voice, video) can add parallel metric sets downstream.

---

### Cluster 5 — Pro-social Reframe in Introduction

**Prosecution:**
1. Defensive writing — spec shouldn't have to pre-empt misreads.
2. Adds length.
3. Implies the concept is weak enough to need protection.

**Defense:**
1. Technical vocabulary reliably gets mis-read when it has casual-usage connotations. Disambiguation is standard for specs (e.g., "authentication vs authorization" in security docs, "latency vs throughput" in systems docs).
2. Cluster A identified the narcissism misread as a real concern — the pro-social reframe directly addresses it.
3. Length cost is minimal (one paragraph); mis-adoption cost is larger.

**Collision:** Prosecution's "defensive" reads as an aesthetic preference; Defense's "disambiguation is standard" is substantive.

**Position:** All dimensions PASS.

**Verdict: SURVIVE — adopt.** Spec introduction should include the pro-social reframe explicitly.

---

### Cluster 6 — Appropriate-Low-Self-Focus Caveat

**Prosecution:**
1. Weakens the diagnostic — users may over-apply the caveat to justify Try-Hard patterns as "genuine vulnerability."
2. Adds complexity to the spec; the diagnostic should be sharp.

**Defense:**
1. Without it, the diagnostic over-applies to inappropriate contexts (intimate conversations, genuine asks, transparent-asymmetry situations). That's a failure mode.
2. Scoping clarity is strengthening, not weakening. A diagnostic that applies everywhere is actually weaker than one with a clear domain of relevance.
3. The risk of misuse is real but lower than the risk of over-application. Users who want to self-justify Try-Hard can do so without the caveat; users who want to calibrate correctly need it.

**Collision:** Prosecution's "weakens diagnostic" treats scoping as subtraction; Defense reframes scoping as precision. The second reading is structurally correct — unscoped tools are weaker than scoped ones.

**Position:** All dimensions PASS.

**Verdict: SURVIVE — adopt** as dedicated caveat subsection. Specific contexts noted: genuine vulnerability with authentic need, transparent power asymmetry (intern-to-CEO), intimate/warm conversations, ritual/ceremonial contexts.

---

### Cluster 7 — Displayed Self-Focus Layer Granularity

Two candidate interpretations of Displayed Self-Focus:

**Candidate 7.A:** Displayed Self-Focus *is* the 5-signal catalog (layer names equivalent).

**Candidate 7.B:** Displayed Self-Focus is a *principle* (the visibility commitment) that the 5-signal catalog *operationalizes*.

**Prosecution of 7.A:** Redundant — having two names for the same thing is concept bloat.

**Prosecution of 7.B:** Adds abstract layer without new content — the principle is implicit in the catalog.

**Defense of 7.A:** Minimalist; aligns with innovation 4.C (spec minimalism).

**Defense of 7.B:** Separating principle from operationalization is pedagogically useful — readers understand WHY the catalog matters (visibility requirement) separately from HOW it's computed. Parallels other APT structure (dimension definitions separate from operational measurements).

**Collision:** Defense of 7.B wins — the pedagogical separation is substantive. Principle-level explanations enable future operational extensions (voice, video, multimodal) without rewriting the theoretical commitment.

**Position:** Both PASS; 7.B provides more structural clarity.

**Verdict: 7.B SURVIVE — adopt principle-operationalization split.** Displayed Self-Focus is the visibility principle; the 5-signal catalog (plus 6 operational metrics) is the text-mode operationalization.

---

### Cluster 8 — Anxious-Distracted Edge Case Handling

Sensemaking argued the visibility requirement resolves this. Innovation didn't strongly challenge. Question: should the spec explicitly address it?

**Prosecution of explicit handling:** Over-engineering; the visibility principle is sufficient.

**Defense of explicit handling:** An edge case that could confuse users deserves one paragraph. Cheap to include; valuable to include.

**Verdict: SURVIVE with brief handling.** One paragraph in the spec explicitly noting: "Internal self-focus without visible manifestation doesn't produce the modulator effect. Anxious-distracted self-focus (attention on own anxiety rather than own agenda) is visible as distress signals, not as the 5-signal catalog. The catalog distinguishes productive self-focus from anxious look-alikes."

---

### Cluster 9 — Personal Pattern Subtypes (forward-looking)

Innovation's 7.B proposed: after sufficient data, each user's Try-Hard has a signature subtype (self-justification-dominant, over-elaboration-dominant, response-anxious, hedge-heavy, status-proving).

**Prosecution:** Speculative; depends on data not yet collected.

**Defense:** Forward-looking extension; flagging it as a future direction is honest and opens research agenda.

**Verdict: FLAG as forward-looking in Open Questions.** Don't commit to in spec; don't kill either.

---

### Cluster E — Deeper Reframe Signals (OUT OF SCOPE flag)

Innovation surfaced three inversion-family outputs (3.A genuine-vs-evaluative, 3.B extractive-vs-non-extractive, 3.C outcome-independence) converging on "the axis may be fundamentally about HOW attention is held, not WHERE directed." This parallels iteration-1's Cluster 4 (APT-level substrate reframe).

**Prosecution:**
1. Out of scope for this iteration. Scope was label refinement + spec additions, not substrate reframe.
2. User's valuation (iterative refinement, not replacement) argues against substrate-level changes.
3. Acting on these now forces premature restructure.

**Defense:**
1. Three mechanisms converging is signal, not noise.
2. Ignoring convergent signals is survival-bias territory.
3. The Cluster E outputs produce specific reopening conditions that can be added to Open Questions without committing to substrate reframe now.

**Collision:** Both sides are correct about different things. Out-of-scope NOW is correct; flag-with-reopening-conditions is also correct.

**Verdict: FLAG with reopening conditions** parallel to iteration-1's Cluster 4 protocol.

**Reopening conditions for Cluster E (in addition to iteration-1's Cluster 4 conditions):**
- If operationalization reveals that attention-direction metrics don't reliably distinguish productive from anxious self-focus → the deeper framing (how attention is held, not where) may need primary spec status.
- If the "genuine vs evaluative" distinction surfaces in user auditing as the decisive factor (more than self vs other) → same.
- If multiple future modulators are discovered and they're all attention-based → attention-substrate reframe becomes forced.

---

## Phase 3.5 — Assembly Check

Surviving candidates: Path (B) confirmed; Self-Focus as primary label with mitigations; dual-pole naming convention; operational measurement layer (6 metrics); pro-social reframe in introduction; appropriate-low-SF caveat subsection; Displayed Self-Focus as principle (7.B); anxious-distracted brief handling; subtypes flagged forward-looking; Cluster E flagged.

### The Assembled Proposal — Iteration-2 Update to `finding.md`

This is a **refinement** of iteration-1's finding, not a replacement. The existing `apt_missing_dimension/finding.md` should be updated in-place with the changes below. If the user prefers a separate iteration-2 finding document that supersedes the original, that's also workable — the architectural commitments remain identical; only the label and spec additions change.

**Changes to `finding.md`:**

1. **Axis label:** Self-Elevation → **Self-Focus** (primary), with "Self-Focus (*kendine odaklanmak*)" parenthetical at first use. Alternatives (Own-Agenda-Focus, Task-Focus, Grounded Attention, Centered-Attention) listed in Open Questions.

2. **Naming convention:** Convert to dual-pole: "Self-Focus (attention on own priorities) vs Supplication (attention on securing their response)." Parallel with Expressed Frame's existing convention.

3. **External correlate layer:** Rename to **Displayed Self-Focus** (*kendine odaklanmanın gözükmesi*) as the **visibility principle**. The 5-signal catalog (Withholding / Premise-Posture / Self-Justification-Density / Exit-Willingness / Rhythm-Comfort) operationalizes the principle for text-mode contexts.

4. **Operational measurement layer (new sub-section):**

| Operational metric | Computes | Links to inference signal |
|---|---|---|
| Opening verb class | Self-action vs other-request | Premise-Posture |
| Pronoun ratio (I-we vs you-your) | Balanced or you-heavy | Premise-Posture, Self-Justification-Density |
| Question-to-statement ratio | Structural openness | Self-Justification-Density |
| Self-justification clause count | Direct measurement | Self-Justification-Density |
| Elaboration gradient | Word count per point | Withholding-Signal |
| Closing assumption tone | "Take it or leave it" vs "waiting for response" | Exit-Willingness |

Note: these are text-mode metrics; multimodal extensions (voice, video) can add parallel metric sets downstream.

5. **Pro-social reframe (new paragraph in the Self-Positioning section introduction):**

> "Self-Focus as named here is neither narcissism (highly politically-optimized attention on being seen positively) nor the 'self-focused attention' construct from public/private self-consciousness research (awareness of self as object). It describes a specific attention-direction — on one's own priorities and agenda — that produces reliable pro-social behavior. Ironically, it's narcissism's opposite: narcissism is intensely attuned to others' reception; Self-Focus is not."

6. **Appropriate-low-Self-Focus caveat (new subsection):**

> "Low Self-Focus is a failure mode in contexts where value is being established (professional first-contact, networking, sales outreach, status-establishing exchanges). It is *appropriate and healthy* in other contexts:
>
> - **Genuine vulnerability / authentic need** — asking for help you actually need, expressed transparently. Performing Self-Focus while concealing real need is its own inauthenticity.
> - **Transparent power asymmetry** — intern-to-CEO, student-to-professor in domain. Appropriate humility is not Try-Hard.
> - **Intimate / high-warmth conversations** — deep conversations with close friends or partners. Mutual other-focus and shared vulnerability are the target here, not Self-Focus.
> - **Ritual / ceremonial contexts** — condolences, apologies, formal gratitude. Structured other-centering is the correct form.
>
> The modulator's relevance is context-scoped. The diagnostic is for value-establishing contexts, not universal."

7. **Anxious-distracted brief handling (one paragraph):**

> "Internal self-focus without visible manifestation doesn't produce the modulator effect — the 'gözükmesi' (displayed) requirement is load-bearing. Anxious-distracted self-focus (attention on own anxiety rather than on own agenda) is visible as distress signals (hedging, apologizing, over-explaining, rushed rhythm), not as the 5-signal catalog. The catalog distinguishes productive self-focus from anxious look-alikes on the behavioral surface."

8. **Reasoning section additions:**
   - Document that iteration-1 labeled the axis "Self-Elevation" (from the transcript's *kendini büyük görmek*); iteration-2 superseded with "Self-Focus" for causal-clarity reasons (attention-direction explains mechanism; state-posture only names the endpoint).
   - Document why Path (B) was chosen over Paths (A), (C), (D).
   - Document why Self-Focus was chosen over Own-Agenda-Focus / Task-Focus / Grounded Attention / Centered-Attention, preserving the alternatives in Open Questions.

9. **2×2 diagnostic axis label:** Self-Elevation → Self-Focus. Quadrant labels can optionally be refined (Selective Engager / Grounded Contributor) but iteration-1 labels (Confident Selector / Respected Expert / Disengaged / Try-Hard) remain viable.

10. **Open Questions additions:**
    - Alternative label candidates (Own-Agenda-Focus, Task-Focus, Grounded Attention, Centered-Attention) if user wants further deliberation.
    - Personal pattern subtypes (forward-looking — once user applies audit to 20-50 messages, Try-Hard subtypes should emerge).
    - Cluster E reopening conditions (attention-direction may be downstream of deeper framing: genuine-vs-evaluative, extractive-vs-non-extractive, outcome-independence).

**What doesn't change from iteration 1:**
- Path α architectural placement
- Multiplicative gating mechanism
- Trait-with-bearings structure
- Failure signature (devaluation)
- Confidence calibration structure
- APT-level doubt (Cluster 4) flag

### Assembly Evaluation (all 8 dimensions)

- D1 Explanatory Adequacy: **PASS** — causal-directional framing explains each signal's origin
- D2 Definitional Distinctness: **PASS** (with mitigations — pro-social reframe + psych-literature disambiguation)
- D3 Operational Testability: **PASS (strong)** — 6 text-feature metrics enable direct computation
- D4 User Actionability: **PASS (strong)** — user can apply today, more actionable than iteration-1 Self-Elevation framing
- D5 Structural Coherence with Iteration 1: **PASS** — refinement only, architectural commitments unchanged
- D6 Architectural Parsimony: **PASS** — additions are warranted (operational layer, caveat subsection, pro-social reframe); all have specific justification
- D7 Bilingual Compatibility: **BOUNDARY** — Self-Focus works in Turkish cleanly; English has mitigable risks
- D8 Honesty: **PASS** — alternatives documented, Cluster E flagged with reopening conditions, context-scope caveat explicit

**Assembly Verdict: SURVIVE — clean on all critical dimensions.** One BOUNDARY on D7 (English-language risks) addressed by required mitigations.

---

## Phase 4 — Coverage + Convergence

### Accumulator Update

| Candidate | Verdict | Primary reason |
|---|---|---|
| Path (A) / (C) / (D) from sensemaking | KILL | Iteration-1 reasoning applies (structural-role signal, causal clarity, real advantage) |
| Path (B) | SURVIVE | Confirmed; sensemaking's structural commitment holds |
| **Self-Focus** label | SURVIVE | Primary with required mitigations |
| Own-Agenda-Focus | SURVIVE (secondary) | Formal synonym / Open-Questions alternative |
| Task-Focus | SURVIVE (secondary) | Alternative with different collision profile |
| Grounded Attention | REFINE | Option for presence-flavored preference |
| Centered-Attention | REFINE | Option for bilingual-max-safety preference |
| Genuine Attention | KILL as label | Insight preserved in spec description (genuine vs evaluative distinction) |
| Unselfconscious Engagement | KILL as label | Clunky; insight preserved in spec description |
| Dual-pole naming convention | SURVIVE | Parallel with Expressed Frame |
| Operational measurement layer (6 metrics) | SURVIVE | Direct operationalization for LinkedIn case |
| Pro-social reframe in introduction | SURVIVE | Standard disambiguation for technical vocabulary |
| Appropriate-low-SF caveat | SURVIVE | Scoping clarity strengthens, not weakens, diagnostic |
| Displayed Self-Focus as principle | SURVIVE | 7.B wins on pedagogical separation |
| Anxious-distracted brief handling | SURVIVE | Cheap to include, valuable to include |
| Subtype profiling | FLAG forward-looking | Depends on future data |
| Cluster E (deeper reframes) | FLAG with reopening conditions | Out of scope; parallel with iteration-1 Cluster 4 |
| **Assembly (iteration-2 update to finding.md)** | **SURVIVE** | Clean across 8 dimensions with one BOUNDARY addressed by mitigations |

### Coverage Assessment

Regions evaluated:
- ✓ Label candidate space (7 candidates, including sensemaking default)
- ✓ Naming convention (single vs dual-pole)
- ✓ Spec addition candidates (operational layer, pro-social reframe, caveats, anxious-distracted)
- ✓ Granularity questions (Displayed Self-Focus as principle vs catalog-equivalent)
- ✓ Forward-looking extensions (subtype profiling)

Regions flagged:
- Cluster E (deeper reframes) — same scope-out as iteration-1 Cluster 4
- Multimodal PRAGMA (voice/video) — noted for downstream

No unexplored regions adjacent to viable regions. Coverage sufficient for the inquiry's scope.

### Convergence Assessment

- **Clean SURVIVE exists:** Yes — Assembly (iteration-2 update) with one BOUNDARY (English-language risk) addressed by required mitigations
- **Landscape stability:** Confirmed — label choice resolves to Self-Focus with alternatives in Open Questions; architectural commitments inherited unchanged
- **New-information rate:** Moderate — critique surfaced the label-choice adjudication work that innovation flagged; no new regions discovered
- **Rate of change:** Stable — iteration 2 is a refinement, not a restructure

### Signal: **TERMINATE**

Convergence criteria met:
- [x] At least one SURVIVE with no critical caveats (Assembly)
- [x] Landscape stable
- [x] No unexplored viable regions
- [x] Coverage sufficient for scope

Ready for MVL to write iteration-2 Finding (or update iteration-1 finding.md in place, per user preference).

---

## Convergence Telemetry

- **Dimensions evaluated:** 8 / 8. All 5 critical covered for every candidate. **YES**
- **Adversarial strength:** **STRONG**. Prosecutions on label candidates specifically identified structural concerns (psych-literature collision, narcissism connotation, operational testability issues) that forced either mitigations or kills. Self-Focus required defense on D2; Genuine Attention killed on D3; Unselfconscious Engagement killed on D6. Not rubber-stamping.
- **Landscape stability:** **STABLE** — architectural commitments inherited from iteration-1 unchanged; label and spec-addition decisions made cleanly within committed architecture.
- **Clean SURVIVE:** **YES** — Assembly (iteration-2 update) with one BOUNDARY on D7 addressed by required mitigations.
- **Failure modes observed:**
  - *Survival bias (risk partially present)* — Cluster E flagged as out-of-scope again (parallel with iteration-1 Cluster 4). Mitigated by explicit reopening conditions. Watch: if iteration-3 or iteration-4 also defers this, the pattern becomes comfortable dismissal. For iteration-2, flagging with conditions is appropriate scoping.
  - No other failure modes observed.
- **Overall: PROCEED** — sufficient dimension coverage + strong adversarial testing + clean SURVIVE candidate (Assembly). Ready for MVL to write Finding or update iteration-1 finding in place.

---

## The Answer (for MVL / Finding)

**Primary adjudications:**

1. **Path (B) confirmed** — axis swap with umbrella preserved; architectural commitments from iteration 1 unchanged.

2. **Self-Focus as primary axis label** — user's native-language proposal wins after rigorous evaluation against 6 alternatives. English-language risks (psych-literature collision, narcissism connotation) are mitigable with required spec additions: pro-social reframe in introduction + explicit disambiguation from "self-focused attention" research construct + alternatives in Open Questions.

3. **Dual-pole naming** — "Self-Focus (attention on own priorities) vs Supplication (attention on securing their response)" — parallel with Expressed Frame's existing convention.

4. **Displayed Self-Focus as principle** (visibility commitment) operationalized by the 5-signal catalog. Add a sub-layer of 6 text-feature operational metrics for text-mode contexts.

5. **Spec additions required:**
   - Pro-social reframe paragraph (pre-empting narcissism misread)
   - Appropriate-low-Self-Focus caveat subsection (scoping the diagnostic to value-establishing contexts)
   - Anxious-distracted brief handling (one paragraph)

6. **Open Questions additions:**
   - Alternative label candidates preserved for user re-evaluation
   - Subtype profiling flagged as forward-looking
   - Cluster E reopening conditions flagged (attention-direction may be downstream of deeper framing — parallel with iteration-1 Cluster 4)

**What doesn't change:** Path α, multiplicative gating, trait-with-bearings, failure signature, confidence calibration structure, iteration-1 Cluster 4 flag.
