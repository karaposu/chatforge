---
status: active
discipline: innovation
inquiry: apt_self_focus_reframe
iteration: 1
---
# Innovation: apt_self_focus_reframe

## User Input

`devdocs/inquiries/apt_self_focus_reframe/sensemaking.md`

## Seed

Sensemaking committed **Path (B)**: keep Self-Positioning umbrella, replace Self-Elevation axis with **Self-Focus** (causal-directional framing), add **Displayed Self-Focus** as named external-correlate layer. Five open items forwarded:

- **OI1** — Final English label for the axis (Self-Focus carries narcissism-connotation risk in English; alternatives: Centered-Attention, Self-Prioritization, Own-Agenda-Focus, etc.)
- **OI2** — 2×2 quadrant label refinements (Selective Engager vs Confident Selector; Grounded Contributor vs Respected Expert)
- **OI3** — How much Self-Elevation language to retain as historical reference
- **OI4** — Whether the visibility requirement ("gözükmesi") fully resolves the anxious-distracted edge case or explicit handling is needed
- **OI5** — What counts as "displayed" in Displayed Self-Focus (the 5-signal catalog = Displayed Self-Focus, or a more abstract layer above it?)

Innovation's job: propose concrete options across these + test whether sensemaking's structural commitment (Path B) is really right or if mechanisms surface a better alternative.

## Direction (intuition / valuation)

The user's motivating valuation, preserved from iteration 1:

- **Primary:** The LinkedIn diagnostic must remain actionable. Whatever the axis ends up named, the user should be able to audit a message against it today.
- **Secondary:** Internal consistency of APT. This is iteration-2 refinement of a spec the user is developing iteratively — absorb the Self-Focus insight without collateral damage.
- **Motivation:** Precision over cosmetics. The user explicitly framed "not perfect but better" — invites rigorous evaluation, doesn't demand adoption.

Specific valuation signals from the user's Turkish proposal:

- User cared about *causal* over *state* framing (invoked it explicitly as "it's the actual state, others get limited investment BECAUSE attention is genuinely elsewhere")
- User flagged semantic mis-landings ("Self-Regard" = ego; "Investment Control" = strategic)
- User insisted on *gözükmesi* (visibility) as part of the concept, not an implementation detail

These shape what mechanism outputs count as valuable: outputs that give cleaner operational purchase, avoid semantic mis-landings, and honor the visibility requirement.

---

## Mechanism 1 — Lens Shifting

### 1.A Generic — Context domains of relevance

Evaluate Self-Focus under different conversational contexts:

- **Cold first-contact (LinkedIn, cold email, pitch meetings):** Self-Focus framing lands cleanly — user easily recognizes "I'm attending to getting their response" as their failure mode.
- **Ongoing professional relationship:** Framing holds; Self-Focus here means attending to one's own contribution/agenda rather than to status maintenance.
- **Intimate/therapeutic conversation:** "Self-Focus" reads awkwardly — in therapy contexts, the target is often *not* self-focus but relational presence. The label mis-lands.
- **Public speaking / performance:** Framing becomes task-focus (performance psychology literature) — not exactly self-focus but adjacent.

**Implication:** Self-Focus is a contextually-appropriate label (clean in most APT use cases) but has a weak spot in intimate/therapeutic contexts. Not a dealbreaker — APT's primary use case is professional/networking/conversational, not therapeutic.

### 1.B Focused — English-language semantic risk

Frame: "What does an English-speaking APT user hear when they see 'Self-Focus' for the first time, out of spec context?"

- Tech/professional crowd: reads as "concentration on one's own goals" — neutral-to-positive.
- HR / organizational behavior crowd: reads as individual-development framing — neutral.
- Self-help / therapy-adjacent crowd: reads as "selfish" or pathologizing — negative landing.
- Academic psychology crowd: may conflate with "self-focused attention" literature (Buss, Duval & Wicklund) which is a DIFFERENT construct (awareness of self as object).

**Implication:** Self-Focus has a naming collision with an existing psychology literature construct ("self-focused attention" = public/private self-consciousness). This is a real concern — APT users with a psych background may import the wrong meaning. Alternatives that sidestep this collision are worth canvassing.

### 1.C Contrarian — Prescriptive vs Descriptive

Under the frame "APT will be used as a self-improvement / coaching tool" (prescriptive), the Self-Focus reframe may be *worse*, not better:

- "Hold yourself as big" (Self-Elevation) is harder to misuse toward selfishness — the imagined target is an esteemed character, not an inward-turned one.
- "Focus on your own priorities" (Self-Focus) can be read as license for neglecting others — slippery toward actual narcissism.

Under the frame "APT is a descriptive psychology framework" (used by profilers to understand patterns), Self-Focus wins cleanly — it's mechanism-accurate and doesn't need to be "safe."

**Implication:** Dual-labeling might be warranted: **Self-Focus** as the internal theory label (used in spec, in APT Inference/Profiling outputs) and **Self-Elevation** or a softened alternative as the user-facing diagnostic label (used in coaching products, prescriptive applications). Adds complexity; need to weigh against the clarity gained.

---

## Mechanism 2 — Combination

### 2.A Generic — Self-Focus × existing APT elements

- **Self-Focus × Trajectory:** Does attention-direction predict trajectory stability? Hypothesis: consistent self-focused attention produces stable trajectory; oscillating attention (flips between self and other) produces volatile trajectory.
- **Self-Focus × Charm/Hope/Fear:** Each attachment variable has an attention correlate. Charm-signaling with self-focus = "here's what I'm working on" (attention on self); charm-signaling with other-focus = "here's what I can do for you" (attention on their value-reception). Both deliver charm; first reads grounded, second reads performative.
- **Self-Focus × Expressed Frame (Investment-Asymmetry):** The 2×2 that iteration 1 established gains cleaner semantics under Self-Focus.

**Implication:** Self-Focus is cross-compatible with APT's existing structure. Not a novel insight but a coherence check — passes.

### 2.B Focused — Operational metrics from text features

For the LinkedIn case specifically, derive concrete text-level measurements that operationalize Self-Focus:

| Text feature | What it measures | High Self-Focus | Low Self-Focus |
|---|---|---|---|
| **Opening verb class** | What the first sentence describes | Self-action ("I've been working on…") | Other-request ("I wanted to ask you…") |
| **Pronoun ratio** | I/we vs you/your per message | Balanced or I-leaning | You-heavy |
| **Question-to-statement ratio** | Structural openness | Low Q, high S (you're asserting, not harvesting) | High Q, low S (you're structuring around their answer) |
| **Self-justification clause count** | Clauses explaining "why I'm writing" | Low | High |
| **Elaboration gradient** | Word count per point | Flat or terse (you stop when point is made) | Expanding (you keep adding because you're tracking their reaction) |
| **Closing assumption** | Implicit closing tone | "Take it or leave it" | "Waiting for your response" |

**Implication:** These are computable from text. Any automated PRAGMA pipeline can calculate them without human interpretation. Worth specifying as an *operational implementation layer* sitting below the 5-signal catalog.

### 2.C Contrarian — Self-Focus × contemplative-tradition framing

In Buddhist / contemplative psychology, "self-focus" is typically identified as the *problem* (ego-driven attention), not the solution. The target state in those traditions is **present-moment attention unentangled with self-reference** — attention that's on the exchange itself, not on "what am I doing" or "what are they thinking of me."

This produces a radical reframe candidate: the target is neither self-focus nor other-focus, but **unselfconscious engagement**. Attention is on *the matter at hand* without reflexive self-monitoring or reception-monitoring.

Names this suggests:

- **Unselfconscious Engagement** — accurate mechanism, clunky phrase
- **Presence** — clean, general, maybe too abstract
- **Grounded Attention** — captures both presence and stability
- **Task-Focus** — performance psychology's term (below) converges here
- **Agenda-Focus** — specific to what's being pursued, sidesteps narcissism risk

**Implication:** The user's "Self-Focus" label might be pointing at something slightly different from what they name it. The deep concept may be closer to "unselfconscious presence with one's own agenda" than to "focus on self." Worth stress-testing whether the alternative labels land better.

---

## Mechanism 3 — Inversion

### 3.A Generic — Invert "Self-Focus produces the effect"

**What if Other-Focus also produces the effect?**

Deep listening, genuine curiosity about someone's worldview, real interest in what they're saying — these can produce attachment without the neediness pattern. A person who's genuinely curious about you (not evaluating you, not angling for response) produces positive attachment the same way a self-focused person does.

This suggests the axis may not be self-vs-other but **genuine-attention vs evaluative-attention**:

- Genuine self-attention (your priorities, your responses) — works
- Genuine other-attention (their worldview, their thinking) — also works
- Evaluative self-attention (monitoring how you're landing) — fails (try-hard)
- Evaluative other-attention (measuring their reaction for approval-harvesting) — fails (supplicating)

**Implication:** The axis might be "genuine vs evaluative" or "engaged vs harvesting" rather than self vs other. This is a Level-2 inversion (goes up one abstraction).

### 3.B Focused — Invert the positive framing to negative

**Name the axis by what it isn't.** Iteration 1 already surfaced "Non-Supplication" as a mechanism-accurate label, but rejected as umbrella because negative definitions are weaker. Revisiting under Self-Focus framing:

- **Non-Evaluative Attention** — captures what 3.A surfaced
- **Non-Supplicating Presence** — captures the visibility requirement + the mechanism
- **Un-Harvesting Attention** — captures the contrast with approval-harvesting

The deeper inversion (system-level): **the axis is not about WHAT attention is on, but about WHETHER it's extractive or non-extractive.** Self-Focus and genuine Other-Focus both count as non-extractive. Try-Hard and Supplication are extractive modes of attention.

**Implication:** At the system level, the real axis may be **extractive vs non-extractive attention** — whether the interaction is being used to harvest something from the other (approval, information, commitment) or whether it's engaged non-extractively. This is a more fundamental reframe than Self-Focus.

### 3.C Contrarian — Invert "the root is attention"

**What if the root isn't attention at all, but EXPECTATION?**

Candidate: the modulator's deep variable is **whether you expect the other to stay or expect them to leave**. If you assume they'll stay (not-caring-about-keeping-them), you don't optimize for keeping them → Self-Focus behaviors emerge naturally. If you assume they'll leave (caring-about-keeping-them), you optimize → needy behaviors emerge.

Under this inversion:
- Attention-direction is *downstream* of expectation-stance
- Self-Focus is a *symptom* of assumed-stay
- "Displayed Self-Focus" maps onto *observable assumed-stay behavior*
- The fundamental question shifts from "where is your attention?" to "what are you assuming about how this exchange will end?"

Keep inverting:
- System level: **the modulator is about your felt relationship to the exchange's outcome.** Assumed-stay = outcome-independence; Assumed-leave = outcome-dependence.
- Reframes as **Outcome-Independence** vs **Outcome-Dependence**.

**Implication:** This is a genuinely deeper framing — attention-direction might be a downstream signal of outcome-independence. If accepted, the axis name shifts to Outcome-Independence or Outcome-Detachment. This would be a significant change to sensemaking's Path (B).

*Out-of-scope risk flag:* this might reopen Cluster 4 territory (APT-level substrate reframing). Noting, not pursuing further here.

---

## Mechanism 4 — Constraint Manipulation

### 4.A Generic — Bilingual-compatibility constraint

Add the constraint: "Label must land cleanly in both Turkish (user's native) and English (spec's primary language)."

- **Self-Focus / Kendine Odaklanmak** — Turkish clean, English has psych-literature collision + narcissism risk
- **Centered-Attention / Merkezli Dikkat** — Both clean, loses the "self" content
- **Own-Agenda-Focus / Kendi Gündemine Odaklanma** — Both clean, specific, slightly clunky in English
- **Grounded Attention / Topraklanmış Dikkat** — Both clean, Turkish less natural
- **Unselfconscious Engagement / Benliksiz Bağlılık** — English clean, Turkish clunky

**Implication:** "Own-Agenda-Focus" or "Centered-Attention" are the bilingual winners. User decides between the two based on Turkish naturalness preference.

### 4.B Focused — Remove "axis must be a single-concept name" constraint

Allow the axis to be named with *two explicit aspects*:

**Self-Focus (positive pole) + Non-Supplication (negative pole)** — together define the axis. The spec names the concept by BOTH what it is (attention on own priorities) AND what it isn't (not harvesting approval). Each aspect is clearer than either alone.

Analog: APT's Expressed Frame is already defined bidirectionally ("I'm the selector" vs "please like me"). Applying the same approach to this axis is consistent.

**Implication:** Dual-pole naming may clarify better than single-label naming. Expand the spec to name both poles explicitly: "the internal axis is attention-direction, with Self-Focus (on own priorities / agenda) as the high-modulator pole and Supplication (attention on securing their response) as the low-modulator pole."

### 4.C Contrarian — Add the constraint "no new top-level concept"

What if sensemaking's Path (B) is too much surgery? Add the constraint: axis name change only, no new "Displayed Self-Focus" layer — that layer collapses into the 5-signal catalog.

Under this: the 5-signal catalog IS Displayed Self-Focus. No need to name the layer separately. The spec reads: "Self-Positioning has one axis (Self-Focus) and is detected via a 5-signal catalog."

**Implication:** This saves a concept (sensemaking's OI5 becomes moot — the catalog *is* the display). Trades abstract clarity (named layer) for spec minimalism. Worth considering if the user prefers less structure.

---

## Mechanism 5 — Absence Recognition

### 5.A Generic — What's still missing in the Self-Focus framing?

- **Temporal dynamics** — Self-Focus is not static; it oscillates during an interaction. The spec currently treats it as a state, but real interactions involve repeated shifts. When and how Self-Focus can *recover* after a slip matters for coaching applications.
- **Relational context** — Self-Focus with someone who shares your world-model feels categorically different from Self-Focus with a stranger. A resonance component is conspicuously absent from APT entirely (noted in iteration 1 as out-of-scope).
- **Stakes-asymmetry** — Self-Focus is easier when stakes are symmetric. In asymmetric-stakes situations (you need something they have; they don't need you), sustained Self-Focus is structurally harder.

**Implication:** These are real gaps but scope-bound. Flag for future iterations. Current iteration should not attempt them.

### 5.B Focused — Missing diagnostic tooling layer

The 5-question audit is manual. What's missing between "the spec" and "the user applying it daily"?

- **Message-level pre-send check:** A lightweight utility that flags low-Self-Focus patterns in a drafted message before sending. Maps each of the 6 operational metrics (from 2.B) to a score.
- **Post-hoc reviewer:** Analyzes sent messages in aggregate, produces personal pattern trends ("you trend Try-Hard in messages to senior people, but Respected Expert with peers").
- **Live conversation annotation:** Real-time flagging during chat ("you just used three self-justifying clauses in a row").
- **Pattern subtypes:** After sufficient data, identify each user's specific Try-Hard subtype (self-justification-dominant, over-elaboration-dominant, response-anxious, etc.).

**Implication:** These are product/tooling layers, not spec. But the *spec should enable them.* Including the operational metrics (from 2.B) in the spec enables all of these.

### 5.C Contrarian — Missing: the "low Self-Focus is sometimes appropriate" caveat

The spec currently implies low-Self-Focus is always bad. That's false.

Genuine cases where low Self-Focus is appropriate and productive:

- **Genuine vulnerability / asking for help you actually need.** Pretending not to need help when you do is its own inauthenticity — a performance of Self-Focus that masks actual need. The other person detects it.
- **Transparent power asymmetry.** When you're clearly in a subordinate role (intern-to-CEO, student-to-professor in their domain), performing Self-Focus reads as inappropriate. Appropriate humility is NOT Try-Hard.
- **High-warmth / intimate contexts.** Deep conversations with close friends or partners benefit from other-focus, genuine listening, shared vulnerability. Self-Focus here reads as cold.
- **Ritual/ceremonial contexts.** Condolences, apologies, formal gratitude — these require structured other-centering. Self-Focus misfires entirely.

**Implication:** The spec needs a caveat section: *low Self-Focus is a failure mode under specific conditions (status-establishing contexts, asymmetric-stakes interactions) but is appropriate and healthy in others (genuine vulnerability, transparent asymmetry, intimate warmth, ceremonial occasions). The modulator's relevance is context-scoped.*

This is important because otherwise users will over-apply the diagnostic and discount legitimate human warmth as "supplicating."

---

## Mechanism 6 — Domain Transfer

### 6.A Generic — Attention research (cognitive science)

William James on attention: we focus on what we choose to attend to; attention is a form of will. The attention economy (Herbert Simon): attention scarcity creates value.

Transfer:
- Attention CAN be redirected through practice → Self-Focus is trainable, not fixed. Good news for coaching applications.
- Attention is finite → when you're attending to their response, you're *not* attending to your own priorities. Zero-sum framing.

**Implication:** Supports the trainability of the modulator. Minor theoretical grounding; not a new operational insight.

### 6.B Focused — Performance psychology (athletes, musicians)

Performance literature distinguishes **task-focus** (attention on the action itself) from **outcome-focus** (attention on the judge's reaction / the score / the audience). Elite performers train into task-focus; under pressure, novice performers drift into outcome-focus, which degrades performance.

Direct transfer to APT:
- **Self-Focus ≈ Task-Focus** — attention on the actual exchange content, not on how you're being received.
- **Try-Hard ≈ Outcome-Focus** — attention on securing the audience's approval, which degrades the performance.

Performance literature provides concrete protocols for shifting from outcome-focus to task-focus:
- **Pre-performance routines** (priming the task-attention state before the interaction)
- **Body-scan grounding** (using physical sensation as task-content to anchor)
- **Process cues** ("what's my task here?" reorientation questions)
- **Acceptance of pre-performance anxiety** (reframing arousal as useful energy rather than a signal of incompetence)

**Implication:** This is a rich transfer. APT's Self-Focus gains an entire pedagogy by importing from performance psychology. The user can use pre-send protocols: "before writing this DM, name the task (share X, ask Y), not the outcome (get them to respond)."

### 6.C Contrarian — Social ethology (group-benefit through apparent self-focus)

In social mammals (wolves, primates), individuals who respond to their own perception rather than to politics are more valuable to the group. Reliable individuals (who alarm-call when they see danger, not when politics incentivize alarm-calling) get respected and followed.

This inverts the "Self-Focus = selfish" association: apparent self-focus can be the best contribution to the group, because it's honest-responsive-to-reality rather than politically-optimized.

Transfer to APT:
- The **Respected Expert** quadrant is respected precisely because they don't optimize for social approval — they're trustworthy. Their Self-Focus is a *pro-social* feature, not an anti-social one.
- The counter-intuition: being less focused on the social others around you makes you *more valuable* to them.

**Implication:** This is a useful reframe against the "Self-Focus = narcissism" misread. The spec's introduction can note: apparent self-focus in this sense is pro-social because it creates reliable, trustworthy, politics-independent behavior. This is not narcissism; it's the opposite — narcissism is highly politically-optimized.

---

## Mechanism 7 — Extrapolation

### 7.A Generic — Label lifetime and terminology drift

If "Self-Focus" is adopted as the canonical APT label, extrapolate 2-3 years forward:

- Gets conflated with "self-care" / "self-help" vocabulary in mainstream usage.
- Gets misused by advice-industry ("self-focus your way to the life you want!").
- Semantic drift softens the technical meaning.
- APT users have to constantly re-disambiguate the term.

**Implication:** Precise internal labels age better than intuitive ones. "Own-Agenda-Focus" or "Task-Focus Orientation" drift less because they're less appropriable by the self-help market. May be worth the slight clunk.

### 7.B Focused — Extrapolate the diagnostic to personal pattern profiling

After the user applies the 5-question audit to 20-50 LinkedIn messages, patterns emerge beyond the coarse 2×2:

- **Try-Hard subtypes:** self-justification-dominant / over-elaboration-dominant / response-anxious / hedge-heavy / status-proving. Each has different fixes.
- **Respected Expert subtypes:** terse-authoritative / warm-grounded / selective-engaged / expert-depth. Each is a sub-pattern of the target.
- **Transition patterns:** how a user moves from Try-Hard to Respected Expert over time — does one signal stabilize first? Do others lag?

This extends the diagnostic from a coarse-grained map to a **personal pattern profile** — each user's signature mode with specific subtype.

**Implication:** The 2×2 is the coarse-grained first layer; subtype profiling is the refined second layer. Worth including in the spec as a forward-looking extension ("as data accumulates, subtypes emerge within each quadrant; the 2×2 is the minimum-viable scaffold").

### 7.C Contrarian — Extrapolate attention-based framing beyond this modulator

If Self-Focus as a modulator is causally-attention-based, other APT components may also be attention-based at root:

- **Charm:** attention on your strengths / value signals
- **Hope:** attention on what you're offering (shareable-with-them)
- **Fear:** attention on your leverage / consequence-of-losing-you
- **Content:** attention on what's being communicated
- **Style:** attention on how it's being delivered

Extrapolate: APT may be re-derivable as an attention-allocation theory. The three attachment variables become *where the other party's attention is drawn by you*; the presentation layer becomes *where your attention is during the signaling*; Self-Positioning becomes *where your attention is at the meta level (on exchange vs on their response)*.

**Implication:** This is the Cluster-4 territory from iteration 1 — APT-level reframing. The Self-Focus insight might be the first signal that attention-as-substrate could eventually restructure APT itself. *Out of scope for this iteration; flag honestly with reopening conditions.*

---

## Testing Phase

Applying the 5 tests to each output.

### Survivors (pass all 5)

| ID | Output | Novelty | Scrutiny | Fertility | Actionable | Independent |
|---|---|---|---|---|---|---|
| **1.B** | English psych-literature collision + narcissism risk is real | ✓ | ✓ | ✓ (informs label choice) | ✓ | Partial — links with 4.A |
| **1.C** | Prescriptive vs descriptive dual-labeling | ✓ | ✓ (if dual-labeling) | Partial | Partial | Standalone |
| **2.B** | Operational text-feature metrics (6 measurements) | ✓ (concrete) | ✓ | ✓ (enables tooling) | ✓ direct | Converges with 5.B, 6.B |
| **2.C** | "Unselfconscious Engagement / Grounded Attention / Presence" as axis labels | ✓ | ✓ | ✓ (opens label space) | ✓ | Converges with 3.A, 6.B |
| **3.A** | Genuine-vs-evaluative as deeper axis | ✓ | ✓ | ✓ (opens reframe space) | ✓ | Converges with 2.C, 3.B |
| **3.B** | Extractive vs non-extractive attention (system-level) | ✓ | ✓ | ✓ | Partial (needs operationalization) | Converges with 3.A |
| **3.C** | Outcome-Independence as deeper root | ✓ | ✓ | ✓ | Partial | Standalone, flagged for scope |
| **4.A** | Bilingual-compatibility label filter | ✓ | ✓ | ✓ | ✓ | Converges with 1.B |
| **4.B** | Dual-pole naming (Self-Focus positive + Supplication negative) | ✓ | ✓ | ✓ | ✓ | Standalone |
| **5.B** | Operational tooling layer (pre-send, post-hoc, live, subtypes) | ✓ | ✓ | ✓ | ✓ direct | Converges with 2.B, 7.B |
| **5.C** | Caveat: "low Self-Focus is sometimes appropriate" | ✓ | ✓ (strong) | ✓ | ✓ | Standalone — important |
| **6.B** | Performance psychology task-focus transfer | ✓ | ✓ | ✓ | ✓ (concrete protocols) | Converges with 2.C, 3.A |
| **6.C** | Pro-social reframe against narcissism read | ✓ | ✓ | ✓ | ✓ (spec introduction) | Standalone |
| **7.B** | Personal pattern profile / subtypes | ✓ | ✓ | ✓ | ✓ | Extends 2×2 |

### Refined / Deferred

| ID | Output | Why deferred |
|---|---|---|
| 1.A | Context-domain of relevance | Already in iteration-1 finding's Open Questions; noting, not re-proposing |
| 3.C | Outcome-Independence | Genuinely interesting but reopens Cluster 4 (APT-level reframe). Out of scope for this iteration. Flag with reopening conditions. |
| 4.C | Spec minimalism (collapse Displayed Self-Focus into catalog) | Possible but loses abstract clarity; user preference call |
| 5.A | Temporal / relational / stakes gaps | Out of scope (iteration-1 flagged similar items) |
| 7.A | Label lifetime drift | Abstract advice; rolled into label-choice considerations |
| 7.C | Attention-substrate for all of APT | Cluster 4 territory; out of scope |

### Killed

| ID | Output | Why |
|---|---|---|
| 2.A | Self-Focus × existing APT (cross-compatibility) | Coherence check, not novel insight |
| 6.A | William James / attention research | Loose, not actionable beyond noting trainability |

### Convergence Clusters

**Cluster A — Label refinement beyond "Self-Focus"** (1.B + 2.C + 3.A + 4.A + 6.B)

Five mechanisms converge on the insight that "Self-Focus" as the final English label has issues (narcissism risk, psych-literature collision) and that **alternative labels emphasizing presence / task-orientation / genuine-attention / own-agenda-focus may land better.** Candidate labels that emerged:

- **Own-Agenda-Focus** (specific, bilingual-clean, avoids narcissism)
- **Task-Focus** (from performance psychology — rich pedigree)
- **Grounded Attention** (presence-flavored, clean)
- **Genuine Attention** (3.A's inversion — genuine vs evaluative)
- **Unselfconscious Engagement** (contemplative-adjacent, clunky)
- **Centered-Attention** (bilingual-clean, loses self-content)

*HIGH confidence that label deliberation is warranted. MEDIUM confidence on which wins.*

**Cluster B — Operational measurement layer** (2.B + 5.B + 7.B)

Three mechanisms converge on specifying concrete text-level measurements (opening verb class, pronoun ratio, question-statement ratio, self-justification count, elaboration gradient, closing assumption) as the *operational implementation* of the 5-signal catalog for text conversations. Plus the forward extension to personal pattern profiling.

*HIGH confidence that an operational layer should be added to the spec.*

**Cluster C — Pro-social reframe against narcissism read** (6.C alone; supported by 1.C and 1.B contextually)

The "Self-Focus looks narcissistic" concern is refuted by the social-ethology insight: apparent self-focus is *pro-social* because it creates reliable-honest-responsive-to-reality behavior. Narcissism is highly politically-optimized, which is the opposite.

*MEDIUM confidence — one mechanism, but strong structural argument.* Should be in the spec's introduction to preempt the misread.

**Cluster D — Caveat for genuine low-Self-Focus cases** (5.C alone)

The spec needs explicit acknowledgment that low Self-Focus is appropriate and healthy in specific contexts (genuine vulnerability, transparent asymmetry, intimate warmth, ceremonial occasions). Otherwise the diagnostic gets over-applied.

*MEDIUM confidence — one mechanism but clearly important for spec completeness.*

**Cluster E — Deeper reframing signals (out of scope for this iteration)** (3.A → extractive/non-extractive; 3.B → genuine/evaluative; 3.C → outcome-independence)

Three inversion-family outputs independently surface deeper reframings. These converge on "the axis may be fundamentally about HOW attention is held (extractive vs non-extractive / evaluative vs genuine / outcome-dependent vs outcome-independent), not about WHERE it's directed (self vs other)."

*Important signal. Out of scope for this iteration. Flag with reopening conditions.*

---

## Assembly Check

Combining survivors: what architecture emerges?

**Yes — an enriched Path (B) with four additions.**

### Enriched Self-Focus Integration Proposal

**1. Axis name — reconsider beyond "Self-Focus"**

Sensemaking committed to "Self-Focus" as working label. Innovation found five mechanisms converging on concerns. Candidate alternatives for Critique to adjudicate:

- **Self-Focus** (user's original; narcissism risk in English, psych-literature collision)
- **Own-Agenda-Focus** (specific, bilingual-clean, slight clunk)
- **Task-Focus** (performance-psychology pedigree; may conflate with cognitive-task usage)
- **Grounded Attention** (presence-flavored, clean)
- **Genuine Attention** (genuine-vs-evaluative framing from 3.A)
- **Centered-Attention / Merkezli Dikkat** (bilingual-clean)

Critique should adjudicate which wins; innovation confirms that the naming deserves explicit stress-test rather than defaulting to sensemaking's working label.

**2. Dual-pole naming convention (from 4.B)**

Consider naming the axis with both poles explicitly rather than a single label:

- **Positive pole:** Self-Focus / Own-Agenda-Focus / chosen label
- **Negative pole:** Supplication / Approval-Harvesting

Parallel with Expressed Frame ("I'm the selector" vs "please like me"), which is already bidirectional. Clearer than single-label for spec readers.

**3. Operational measurement layer (from 2.B + 5.B)**

Add to the spec an explicit measurement layer below the 5-signal catalog:

| Operational metric | Computes | Links to signal |
|---|---|---|
| Opening verb class | Self-action vs other-request | Premise-Posture |
| Pronoun ratio (I-we vs you-your) | Balanced or you-heavy | Self-Justification-Density, Premise-Posture |
| Question-to-statement ratio | Structural openness | Self-Justification-Density |
| Self-justification clause count | Direct measurement | Self-Justification-Density |
| Elaboration gradient | Word count per point | Withholding-Signal |
| Closing assumption tone | "Take it or leave it" vs "waiting for response" | Exit-Willingness |

This enables automated PRAGMA computation for text-only contexts and supports downstream product tooling (pre-send check, post-hoc review, live annotation, subtype profiling per 7.B).

**4. Pro-social reframe + appropriate-low-Self-Focus caveat (from 6.C + 5.C)**

Two spec-level additions:

- **Pro-social introduction** — at the Self-Positioning section's introduction, clarify: "Self-Focus as named here is not the narcissism construct from self-help literature nor the self-focused-attention construct from public/private self-consciousness research. It describes a particular attention-direction that produces reliable pro-social behavior — ironically, it's narcissism's opposite, because narcissism is highly politically-optimized (attention intensely on others' perception)."
- **Context-appropriate caveat** — dedicated subsection noting that low Self-Focus is *appropriate* in: genuine vulnerability (asking for help you actually need), transparent power asymmetry, intimate/high-warmth conversations, ritual/ceremonial contexts. The modulator's relevance is context-scoped; the diagnostic is for contexts where value is being established (professional first-contact, networking, sales outreach).

### Assembly Evaluation

The enriched proposal:

- Respects sensemaking's Path (B) structural commitment
- Adds concrete operational measurement
- Adds necessary caveats to prevent misapplication
- Opens label choice for Critique adjudication rather than defaulting
- Flags deeper-reframe signals (Cluster E) honestly as out-of-scope

No critical dimension failures introduced. Extends, doesn't rewrite.

### Real Tension Forward to Critique

**Innovation introduces one genuine tension with sensemaking:** sensemaking committed to "Self-Focus" as the working label. Innovation's Cluster A finding suggests this default should be treated as *a candidate*, not a commitment, with alternatives rigorously evaluated. Critique should adjudicate the label choice explicitly rather than accepting sensemaking's working default.

---

## Concrete Options (for Critique)

Critique should adjudicate:

### Axis Label

- **Self-Focus** (sensemaking's default; faithful to user's Turkish but English issues)
- **Own-Agenda-Focus** (specific, bilingual-clean)
- **Task-Focus** (performance-psychology pedigree)
- **Grounded Attention** (presence-flavored)
- **Genuine Attention** (genuine-vs-evaluative)
- **Centered-Attention** (bilingual-clean, loses self-content)

### Naming Convention

- Single-label axis (sensemaking default)
- Dual-pole axis (Self-Focus + Supplication, parallel with Expressed Frame)

### Operational Layer

- Add 6 concrete text-feature metrics as implementation layer below 5-signal catalog
- Skip (stay at catalog level, implementation left to downstream specs)

### Pro-social Framing

- Include pro-social reframe in introduction (against narcissism misread)
- Skip (let readers infer)

### Appropriate-Low-Self-Focus Caveat

- Add dedicated caveat subsection
- Include as a bullet in Open Questions
- Skip (imply through context-of-use)

### Personal Pattern Profiling (subtypes)

- Include in spec as forward-looking extension
- Flag only in Open Questions

### Deeper Reframing (Cluster E — Outcome-Independence / Extractive vs Non-Extractive / Genuine vs Evaluative)

- Flag with reopening conditions (align with iteration-1 Cluster 4 flag)
- Skip entirely

---

## Open Items (forward to Critique)

- **O1** — Final axis label. Innovation's Cluster A found five mechanisms concerned about Self-Focus; alternatives warrant rigorous side-by-side evaluation. Critique adjudicates.
- **O2** — Dual-pole naming convention. Innovation proposes it as a clarity improvement; Critique judges whether it's parsimony-violating or parsimony-restoring.
- **O3** — Operational measurement layer. Innovation proposes 6 concrete text-feature metrics; Critique judges whether they should live in the spec or in a separate implementation doc.
- **O4** — Cluster C pro-social reframe: include in spec introduction, yes/no?
- **O5** — Cluster D caveat subsection: include, yes/no, and how specifically?
- **O6** — Cluster E deeper reframe signals (Outcome-Independence, Extractive/Non-Extractive, Genuine/Evaluative): flag with reopening conditions, aligning with iteration-1 Cluster 4 protocol?
- **O7** — Anxious-distracted edge case: is the visibility requirement sufficient without explicit spec handling, or is a mini-subsection needed?
- **O8** — Displayed Self-Focus layer granularity: is the 5-signal catalog *identical* to Displayed Self-Focus, or is Displayed Self-Focus a more abstract layer above it?

---

## Mechanism Coverage (Telemetry)

- **Generators applied:** 4 / 4 (Combination, Absence Recognition, Domain Transfer, Extrapolation) — all 3 variations each
- **Framers applied:** 3 / 3 (Lens Shifting, Constraint Manipulation, Inversion) — all 3 variations each
- **Total outputs:** 21
- **Convergence:** YES
  - Cluster A (label refinement beyond Self-Focus) — 5 mechanisms — HIGH confidence
  - Cluster B (operational measurement layer) — 3 mechanisms — HIGH confidence
  - Cluster C (pro-social reframe) — 1 mechanism + supporting context — MEDIUM confidence
  - Cluster D (appropriate-low-SF caveat) — 1 mechanism — MEDIUM confidence but clearly important
  - Cluster E (deeper reframings — out of scope) — 3 mechanisms — HIGH confidence the signal is real, explicit scope-out
- **Survivors tested:** 14 survivors, all passed novelty + fertility + actionability; scrutiny strong for Cluster A/B outputs, partial on Cluster E outputs (out-of-scope)
- **Failure modes observed:** none critical
  - Premature Evaluation: avoided (all 21 outputs generated before testing)
  - Single-Mechanism Trap: avoided (7 × 3 = 21 outputs across all mechanisms)
  - Early Frame Lock: avoided (Cluster A explicitly challenges sensemaking's working label default)
  - Innovation Without Grounding: avoided (all survivors tested with the 5 criteria)
  - Mechanism Exhaustion: not reached
  - Survival Bias: *flagged* — Cluster E (deeper reframings) was deferred as out-of-scope; same pattern as iteration 1's Cluster 4 deferral. This is appropriate scoping if done transparently with reopening conditions — not appropriate if it's comfortable dismissal. Critique should verify.
- **Overall: PROCEED** — Coverage full, convergence strong across five clusters (three in-scope + two flagged out-of-scope), survivors tested, concrete options produced. One material challenge to sensemaking (label choice) and one scope-flag (Cluster E) forwarded honestly.
