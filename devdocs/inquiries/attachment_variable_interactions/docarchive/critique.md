---
status: active
discipline: critique
inquiry: attachment_variable_interactions
iteration: 1
---
# Critique: attachment_variable_interactions

## User Input

`devdocs/inquiries/attachment_variable_interactions/`

---

## Phase 0 — Dimension Construction

### Source: sensemaking constraints + principles

Extracted from sensemaking.md anchors (C1–C6, FP1–FP6, KI1–KI8, SP1–SP6):

| Dimension | Weight | Criterion | Source |
|---|---|---|---|
| **Architectural Coherence** | CRITICAL | Candidate preserves iteration-3.2's existing architecture. No new variables, no new modulators, no structural changes not evidenced by the inquiry's test cases. | C1, FP4, KI8, SP1-SP6 |
| **Definitional Distinctness** | CRITICAL | Candidate maintains clean conceptual separations: specificity ≠ 5th variable; TYPE ≠ magnitude; sender-SP-reading ≠ new mechanism; inner additive f ≠ outer multiplicative gating. | C3, FP2, KI2, D1–D5 |
| **Empirical Coverage** | CRITICAL | Candidate is consistent with all 6 test cases from exploration ($100K stranger, celebrity fandom, shared-niche, Reddit A/B, threat-only, standard-LinkedIn). Does not contradict well-attested real-world phenomena. | C2, FP1, KI1, R1–R3 |
| **Cluster 4 Integrity** | CRITICAL | Candidate does not introduce attention-interaction dynamics that would trigger substrate-reframe consideration. Cluster 4 status preserved unchanged from iteration-3.2. | C5, FP5, KI7 |
| **Operational Testability** | MEDIUM | Candidate's definitions are detectable by a signal-reading system (PRAGMA-level operationalization). Key for specificity and sender-SP. | KI4, KI5, F3, S3-S4 |
| **Pedagogical Clarity** | MEDIUM | Candidate honestly re-attributes user's intuitions ("Hope without Resonance fails"; "combinations unlock bigger locks"). Lands for a practitioner-reader. | C6, FP3, H1–H3, KI2–KI3 |
| **Scope Compliance** | MEDIUM | Candidate fits iteration-3.2.1 clarification scope. Doesn't make structural commitments that belong to iteration-3.3 empirical testing or later iterations. | FP6, KI8, S1 |

**Dimension validation:** All 7 dimensions map directly to sensemaking anchors. No irrelevant axes. If a candidate passes all 7, it correctly specifies content for iteration-3.2.1.

**Critical dimension note:** A single CRITICAL failure kills a candidate regardless of other dimensions' performance.

---

## Phase 1 — Fitness Landscape

### Viable region

Content that:
- States additive f with justification, without overstating (e.g., not committing to specific coefficient values)
- Defines specificity as magnitude factor per variable, with PRAGMA-readable operationalization
- Describes sender-SP-reading from message style using existing iteration-3.2 mechanism
- Introduces MAGNITUDE and TYPE as co-equal output dimensions with provisional TYPE taxonomy
- Re-attributes user's intuitions honestly

### Dead regions

- Any candidate claiming Resonance gates other variables (B1 was killed in exploration)
- Any candidate asserting specificity is a 5th attachment variable
- Any candidate that makes empirically underdetermined structural claims as settled spec
- Any candidate introducing attention-interaction dynamics that could reopen Cluster 4

### Boundary regions

- Specificity-as-threshold (P2-C): correct phenomenologically, underdetermined empirically — belongs in frontier flags, not spec assertions
- TYPE-primary reporting (P4-C): directionally correct, but exceeds clarification scope — belongs in practitioner guidance notes
- Display-IS-state (P3-C): philosophically stronger than needed, risks overclaiming ontology

### Unexplored regions (noted for later)

- Quantitative specificity scoring thresholds
- TYPE taxonomy empirical derivation (cross-cultural, cross-context)
- TYPE evolution over time (Hope-dominant → Resonance-dominant transitions)
- Dyadic specificity (mutual vs one-way)

---

## Phase 2–3 — Adversarial Evaluation by Piece

Candidates are grouped by piece since variants within each piece are alternatives for the same slot in the spec. The question per piece: which variant wins? Can variants be combined?

---

### P1 — Additive f Statement

#### P1-A (Generic)

**Preview:** Viable — correctly states the formula and outer-vs-inner distinction. Thin on justification.

**Prosecution:** Asserts additivity without engaging the alternatives. A sophisticated reader could ask: "Why is additivity the default? The user's observation suggests Resonance matters differently than the others — shouldn't that be addressed?" The outer-vs-inner distinction is noted but not explained. The effective-magnitude nuance (from P2) is not flagged, creating a gap when specificity is introduced later.

**Defense:** Concise. Formula stated correctly. The outer-vs-inner distinction is the key confusion point and it IS addressed.

**Collision:** Prosecution's "thin justification" concern holds. The spec's additive commitment will face pushback from practitioners who see the user's Reddit observation as strong evidence for gating. A reader who doesn't see the alternatives addressed will not be convinced.

**Verdict: REFINE** — insufficient justification. Success criteria not met on Empirical Coverage (doesn't show test-case basis) or Pedagogical Clarity (doesn't preempt the obvious challenge). Fix: incorporate P1-B's evidence ledger.

---

#### P1-B (Focused)

**Preview:** Strong viable. Evidence ledger, parsimony framing, effective-magnitude note.

**Prosecution:** The "burden of proof sits with future proposals" framing could be read as dismissive. A critic might say: "You're using parsimony as a shield rather than engaging with why the interaction-term intuition is wrong." The effective-magnitude note at the end ("additive in effective magnitudes, not nominal content") is necessary but may confuse readers who encounter it before the specificity section.

**Defense:** The evidence ledger is the critical strength. Three alternatives were explicitly tested and eliminated (B1 killed by $100K/celebrity; F1 reinterpreted as TYPE; I1 absorbed by Coherence at g₂). This isn't assertion — it's a record of inquiry. The parsimony framing is legitimate when backed by actual testing. The effective-magnitude note resolves the P1–P2 coupling issue identified in decomposition.

**Collision:** Prosecution's concern (parsimony as shield) is outweighed by the evidence ledger. The spec has tested the alternatives; parsimony is invoked AFTER testing, not instead of it. The effective-magnitude note's placement is addressable by cross-referencing "see Signal Specificity section."

**Verdict: SURVIVE** — passes all dimensions.
- Architectural Coherence ✓ (no new structure added)
- Definitional Distinctness ✓ (inner/outer distinction explicit; effective-magnitude nuance present)
- Empirical Coverage ✓ (three alternatives tested and cited)
- Cluster 4 ✓ (not affected)
- Operational Testability ✓ (formula is detectable)
- Pedagogical Clarity ✓ (evidence ledger preempts the main challenge)
- Scope Compliance ✓ (clarification, not structural change)

**Caveats:** Move effective-magnitude note to immediately precede or follow the Signal Specificity section to avoid confusion.

---

#### P1-C (Controversial)

**Preview:** Boundary region — positive structural claim that may overclaim.

**Prosecution:** The signal-detection-theory analogy is plausible but speculative. "Independent channels don't gate each other in SDT" doesn't prove the human attachment system works the same way. Claiming "there is no cue-interdependence in reading C/H/F/R" is an assertion about cognitive architecture not established in this inquiry's evidence base.

**Defense:** The positive-claim framing ("additivity is correct" rather than "additivity is our default") is epistemically stronger and more defensible in the long run. The SDT analogy is genuinely explanatory and gives readers an intuition pump.

**Collision:** Prosecution wins on the specific SDT claim. But the framing insight — "not defensive parsimony but a positive structural assertion about independent signal channels" — survives. The SDT grounding should be presented as analogical/explanatory, not as proof.

**Verdict: REFINE** — incorporate framing direction into P1-B. Specifically: add a sentence after the evidence ledger stating that additive f reflects genuine independence of signal channels (Charm/Hope/Fear/Resonance are drawn from distinct evidence classes), rather than merely being a parsimony default. Omit the SDT claim or soften to "analogously to how..."

---

### P2 — Signal Specificity

#### P2-A (Generic)

**Preview:** Viable but thin on two dimensions.

**Prosecution:** The "not a 5th variable" argument is asserted but thin. "Fails the orthogonality test" is stated without defining the test. A practitioner building PRAGMA could argue: "specificity correlates with attachment independently; it should be a 5th variable." The PRAGMA operationalization is absent.

**Defense:** Correct definition, good examples, formula stated.

**Collision:** Prosecution's concerns are real. Definitional Distinctness requires explaining WHY specificity fails the 5th-variable test. Operational Testability requires PRAGMA-readable indicators.

**Verdict: REFINE** — passes Architectural Coherence and Empirical Coverage but fails Definitional Distinctness (thin 5th-variable argument) and Operational Testability (no PRAGMA indicators). Incorporate P2-B's content.

---

#### P2-B (Focused)

**Preview:** Strong viable. Costly-signal grounding + PRAGMA operationalization + per-variable specificity.

**Prosecution:** The costly-signal theory (evolutionary psychology) is imported as the grounding for why receivers discount cheap signals. This is an analogy from a field with different empirical base — human signaling research supports it in social contexts but it isn't the same as APT's attachment mechanism. A critic could demand APT-native justification rather than evolutionary-psych import.

**Defense:** The costly-signal analogy isn't load-bearing — the definition works without it. "A message demonstrating specific knowledge could only have been generated by genuine engagement" is a logical claim, not an evolutionary one. The PRAGMA operationalization (template-match + rare-content-marker) is directly useful and doesn't depend on the evolutionary framing. Per-variable specificity (Resonance-specific vs Hope-specific) is the right granularity.

**Collision:** The evolutionary-psych framing is optional, not required. The core content (definition, formula, operationalization, per-variable model, why-not-5th-variable) survives without it. Solution: present costly-signal as an explanatory analogy ("analogous to costly signaling in...") rather than as theoretical grounding.

**Verdict: SURVIVE** — passes all dimensions with minor framing adjustment.
- Architectural Coherence ✓
- Definitional Distinctness ✓ (per-variable specificity; why-not-5th-variable with orthogonality test)
- Empirical Coverage ✓ (generic examples vs specific examples match all test cases)
- Cluster 4 ✓
- Operational Testability ✓ (template-match + rare-content-marker indicators named)
- Pedagogical Clarity ✓ (covers the practitioner's "why does my template fail" question)
- Scope Compliance ✓

**Caveats:** Soften costly-signal framing to explanatory analogy. Retain the orthogonality-test explanation for why specificity ≠ 5th variable.

---

#### P2-C (Controversial — Threshold Model)

**Preview:** Dead region for spec inclusion; viable as frontier flag.

**Prosecution:** The threshold model (`effective_magnitude = 0 if specificity < θ`) is a structurally different formula from the linear model. For it to be spec content in iteration-3.2.1, it must be supported by current evidence. The evidence is Person B's near-zero attachment — but a steep linear curve would also predict near-zero output for very low specificity. The empirical distinction between "threshold at low specificity" and "very-low-output on a linear curve" is not resolvable from the current data. Asserting a threshold commits the spec to a mathematical structure that may need revision when empirical data arrives.

**Defense:** The threshold model is phenomenologically accurate — generic templates feel categorically different (noise), not just weakly similar to real messages. The prescriptive clarity ("no optimization path below θ") is more useful for practitioners than a smooth gradient.

**Collision:** Prosecution wins. Empirically underdetermined structural claims cannot be asserted as spec content in a clarification pass. The threshold framing's phenomenological accuracy doesn't establish it as the correct mathematical structure.

**Verdict: KILL** — fails Empirical Coverage (underdetermined) and Scope Compliance (structural claim beyond 3.2.1 scope).

**Seed extracted:** The threshold-vs-linear distinction is a priority empirical question. In iteration-3.2.1 spec, flag: "The relationship between specificity and effective_magnitude may be threshold-gated rather than strictly linear — an empirical question for iteration-3.3 testing." This preserves the insight without committing to the structure.

---

### P3 — Sender-Side SP from Message Style

#### P3-A (Generic)

**Preview:** Viable but missing the g-layer failure explanation.

**Prosecution:** Correctly describes the mechanism for Self-Positioning reading but doesn't explain WHY Person B's attachment is near-zero (not just weak). Without the g-layer failure narrative, the mechanism looks like a minor add-on rather than a core explanation. A reader might think: "So Person B gets a slightly lower g — fine, but that alone doesn't explain zero attachment."

**Defense:** Accurate. Grounds in iteration-3.2. Makes the single-message case explicit.

**Collision:** Prosecution holds. The g-layer failure (g-product collapses entirely for Supplication-displaying messages) is what makes this mechanism matter. Without naming it, the mechanism feels like a footnote.

**Verdict: REFINE** — incorporate P3-B's double-collapse architecture. The g-collapse phenomenon must be made explicit.

---

#### P3-B (Focused — Double-Collapse)

**Preview:** Strong viable. Most important mechanism naming in the inquiry.

**Prosecution:** "The receiver applies their g-function to the sender" — is this stated in iteration-3.2 or is it a new claim? If the existing spec only says the receiver's attachment is modulated by the receiver's own g-values, then applying g to the sender is architecturally new.

**Defense:** This is the correct reading of the multiplicative-gating formula. The formula `Attachment ≈ f × g₁ × g₂ × g₃` describes the attachment experienced BY the receiver. All three modulators (SP, Coherence, EC) evaluate the SENDER as perceived by the receiver. `g₁(SP)` is not "the receiver's own SP" — it is the receiver's read of the sender's SP. This is how the formula was intended in iteration-3.2, and it's architecturally consistent with how Self-Positioning was defined (it's a displayed state, readable by others). P3-B makes this explicit, which is a clarification, not a new claim.

**Collision:** Prosecution's concern resolves on inspection. The "receiver applies g to sender" framing is the correct reading of existing architecture, not an addition. This is precisely what makes iteration-3.2.1 a clarification.

**The double-collapse framing survives as the key insight:** In a single generic message, low specificity suppresses f (all effective_magnitudes near-zero) AND Supplication-display collapses g₁ (sender-SP near-zero). Both suppress simultaneously. Person B doesn't generate weak attachment — Person B generates near-zero attachment because both channels are suppressed at once.

**Verdict: SURVIVE** — passes all dimensions. The double-collapse is the inquiry's most important named mechanism and should be explicitly titled in the spec.
- Architectural Coherence ✓ (clarification of existing formula)
- Definitional Distinctness ✓ (g-layer applies to sender, not receiver — clarified)
- Empirical Coverage ✓ (explains near-zero attachment; consistent with all test cases)
- Cluster 4 ✓
- Operational Testability ✓ (template-detection + SP-display-detection are both machine-readable)
- Pedagogical Clarity ✓ (double-collapse explains the categorical failure, not just gradient weakness)
- Scope Compliance ✓ (makes existing mechanism explicit for single-message case)

---

#### P3-C (Controversial — Display IS State)

**Preview:** Boundary region — philosophically overreaching.

**Prosecution:** "The display IS the Self-Positioning state, not evidence of it" commits APT to a behavioral ontology: there is no SP state independent of display. This is a substantive philosophical claim beyond the scope of a clarification. Counter-example: a person who is genuinely self-focused but writes a generic template under time pressure. Under display-IS-state, they would be classified as Supplication-displaying despite their actual state. The counter-example shows the claim is too strong.

**Defense:** For APT's purposes, only the display is observable and only the display generates attachment in the receiver. Whether an inner state exists independently is irrelevant to the mechanism. The practical prescription (genuine engagement is required because display determines outcome) is correct regardless of the philosophical framing.

**Collision:** Prosecution wins on the ontological claim. The practical conclusion survives but the "IS" framing overclaims. Solution: "For APT purposes, only the display is observable; the display is operationally equivalent to the state from the receiver's perspective."

**Verdict: REFINE** — correct practical implication, overclaims philosophical position. Fix: soften to "operationally equivalent" framing and incorporate the authenticity-as-structural-prediction conclusion into P5 as a practical note.

---

### P4 — Attachment MAGNITUDE vs TYPE

#### P4-A (Generic)

**Preview:** Viable. Introduces both dimensions with illustrative taxonomy. Needs stronger provisional language and independence argument.

**Prosecution:** The taxonomy may be read as definitive ("Charm-dominant → status/admiration" is stated flatly). The independence argument (same MAGNITUDE, different TYPE → different persistence) is the key insight but is understated. Missing the persistence-dynamics elaboration that makes TYPE diagnostically valuable.

**Defense:** Correctly introduces both dimensions. Provisional flag present. Readable.

**Collision:** Prosecution holds on depth. The provisional flag is present but the independence argument and persistence dynamics are what make TYPE clinically/strategically important. Without them, TYPE is just a label.

**Verdict: REFINE** — incorporate P4-B's persistence dynamics and independence argument. Strengthen provisional language on taxonomy.

---

#### P4-B (Focused — Persistence Dynamics)

**Preview:** Strong viable. Independence argument + persistence dynamics + architectural-elegance note.

**Prosecution:** The two-person comparison example uses `f×g = 0.6` — a specific number that implies false precision. The theory is qualitative at current development stage. Using 0.6 implies we can compute attachment to two decimal places, which we cannot.

**Defense:** The persistence dynamics are the single most important insight from the TYPE dimension. Fear-dominant attachment reverses on threat removal (relief, not loyalty); Hope-dominant dissolves when exchange ends; Resonance-dominant persists through absence. These are testable, practically consequential, and not in any prior iteration. The architectural-elegance note ("additive f gifts TYPE legibility for free") is genuinely elegant and worth preserving.

**Collision:** Prosecution's precision concern is easily fixed — replace "f×g = 0.6" with "assume equal total attachment score." The core content is unaffected.

**Verdict: SURVIVE** with minor edit — remove specific numerical value from comparative illustration. All other content passes.
- Architectural Coherence ✓
- Definitional Distinctness ✓ (TYPE and MAGNITUDE explicitly distinguished by independence argument)
- Empirical Coverage ✓ (persistence dynamics consistent with real-world attachment patterns)
- Cluster 4 ✓
- Operational Testability ✓ (persistence behavior is observable over time)
- Pedagogical Clarity ✓ (the same-score, different-type example is the clearest illustration)
- Scope Compliance ✓ (introduces TYPE dimension without structural change)

---

#### P4-C (Controversial — TYPE Primary)

**Preview:** Dead region for spec claims; viable as practitioner guidance note.

**Prosecution:** The claim that TYPE should be the "primary" output and MAGNITUDE "secondary" is a reporting-architecture decision, not a theoretical claim. Making this as a spec commitment in iteration-3.2.1 would require practitioners to change how they interpret outputs and how APT Profiling ranks its fields — a significant downstream change not supported by APT-internal evidence (only analogical imports from clinical attachment and sales). The scope of iteration-3.2.1 is to introduce both dimensions as explicit; priority ordering is a downstream practitioner-guidance question.

**Defense:** The evidence for TYPE's greater predictive utility is compelling and from adjacent well-studied domains.

**Collision:** Prosecution wins on scope. The insight is correct but belongs in practitioner guidance notes ("for strategic and relational applications, TYPE often provides more actionable information than MAGNITUDE") rather than as a formal spec commitment.

**Verdict: KILL** — fails Scope Compliance (reporting-architecture commitment exceeds clarification scope).

**Seed extracted:** Add a practitioner note in the MAGNITUDE/TYPE section: "For strategic or long-term relational contexts, TYPE is typically more actionable than MAGNITUDE; MAGNITUDE predicts current behavioral intensity while TYPE predicts trajectory and robustness under change." This captures the insight without making a formal priority commitment.

---

### P5 — Worked Example

#### P5-A (Generic)

**Preview:** Viable. Covers all 4 clarifications. Structure is sequential rather than comparative.

**Prosecution:** Person A and Person B are analyzed in separate blocks, making comparison difficult. The double-collapse mechanism is not named or highlighted — a reader could miss that BOTH f and g are collapsing simultaneously. The re-attributions are correct but lack the explanatory punch of the causal narrative.

**Defense:** Covers all 4 clarifications correctly. Re-attributions are honest.

**Verdict: REFINE** — restructure as comparative analysis (P5-B format) with double-collapse named explicitly.

---

#### P5-B (Focused — Table with Double-Collapse)

**Preview:** Strong viable. Table format + double-collapse callout + clean re-attributions.

**Prosecution:** A two-row comparative table in what will be a prose-heavy spec document. Could feel stylistically inconsistent.

**Defense:** The table is the clearest comparative presentation possible for a multi-variable analysis. It makes all 4 clarifications visible in a single glance: specificity, effective_magnitude across variables, sender-SP, resulting MAGNITUDE and TYPE. The double-collapse callout below the table names the key mechanism and distinguishes the double-failure from a single weak signal.

**Collision:** Prosecution's stylistic concern is minor and addressable (tables are standard in technical specs). The double-collapse callout is the critical addition — it names the mechanism that will be directly cited by practitioners explaining why generic templates fail.

**Verdict: SURVIVE** — passes all dimensions.
- Architectural Coherence ✓
- Definitional Distinctness ✓ (both f and g layers explicitly shown)
- Empirical Coverage ✓ (all 4 clarifications illustrated; re-attributions correct)
- Cluster 4 ✓
- Operational Testability ✓ (table structure maps directly to PRAGMA-detectable dimensions)
- Pedagogical Clarity ✓ (comparative format; double-collapse named)
- Scope Compliance ✓

---

#### P5-C (Controversial — Prescriptive Inverse)

**Preview:** Boundary region — different function from worked example, but valuable as follow-on.

**Prosecution:** P5-C changes the function of the worked example from illustrative (showing how the 4 clarifications apply) to prescriptive (deriving what to do). These are different purposes. The prescriptive inverse ("what would Person B need to write?") is more actionable but it's a SEPARATE piece of content, not a replacement for the analytical example.

**Defense:** The prescriptive conclusion — "there is no optimization path for the template; both the F-layer fix and the G-layer fix require genuine engagement" — is the most practically powerful output of the entire inquiry. If omitted, the spec remains purely descriptive and practitioners miss the single clearest action item.

**Collision:** Both are right. P5-B is the analytical worked example; P5-C's conclusion is the practical implication note. Structure: P5-B as the worked example, then a brief "Practical implication" paragraph containing P5-C's core insight (the template-optimization impossibility + authenticity-as-structural-prediction).

**Verdict: REFINE** — not a replacement for P5-B but a follow-on. Add P5-C's authenticity-as-structural-prediction conclusion as a "Practical Implication" note after the worked example table.

---

### P6 — Administrative Integration

#### P6-A (Generic)

**Preview:** Viable. Covers all required admin items. Placement decisions stated without rationale.

**Prosecution:** Placement decisions without rationale are unverifiable — a reader updating the spec doesn't know WHY each clarification goes where it goes. Cluster 4 statement is thin. Downstream flags are listed but not explained.

**Verdict: REFINE** — incorporate P6-B's rationale structure.

---

#### P6-B (Focused — Rationale-Based)

**Preview:** Strong viable. Placement-rationale table. Explicit 3.2.1 vs 3.3 criterion. Forward-looking sequence preserved.

**Prosecution:** The Cluster 4 statement says "monitoring active" — what does monitoring mean? This could imply active ongoing assessment is needed, which may create unnecessary overhead for practitioners.

**Defense:** The placement-rationale table directly addresses verifiability. The 3.2.1 labeling criterion (no new structural elements) is correctly applied. The forward-looking sequence preservation ensures the iteration development trail is coherent.

**Collision:** "Monitoring active" should be replaced with a specific statement about what conditions would trigger Cluster 4 re-evaluation — the same conditions already specified in iteration-3.2. Not "monitoring" as ongoing work but "conditions remain as specified in iteration-3.2."

**Verdict: SURVIVE** — minor wording fix on Cluster 4 statement.
- Architectural Coherence ✓
- Definitional Distinctness ✓
- Empirical Coverage ✓
- Cluster 4 ✓ (with wording fix)
- Operational Testability ✓
- Pedagogical Clarity ✓ (rationale makes decisions verifiable)
- Scope Compliance ✓

---

#### P6-C (Controversial — Finding.md Argument)

**Preview:** This is not actually controversial — it is the MVL+ protocol requirement.

**Prosecution:** The "finding.md argument" is presented as optional/controversial. It is not. Per MVL+ spec: "YES — the question is answered: Write finding.md in the inquiry folder." The finding.md is a protocol output, not a choice. Presenting it as controversial misrepresents its status.

**Defense:** The recommendation is correct. Both finding.md (reasoning for retrieval) and new_apt_layer.md update (integration into authoritative spec) are needed. They serve different functions and don't duplicate.

**Collision:** Prosecution wins on framing (it's not controversial, it's required), but the content recommendation is correct.

**Verdict: SURVIVE** — but reclassify: finding.md is a required output per MVL+ protocol, not an option. The content of P6-C's finding.md brief (question answered + 4 clarifications + B1 kill + F1 reinterpretation + double-collapse naming + Cluster 4 preserved + iteration label rationale) is the correct scope.

---

## Phase 3.5 — Assembly Check

### Survivors so far
- P1-B (with P1-C framing note added)
- P2-B (with evolutionary framing softened)
- P3-B (double-collapse architecture)
- P4-B (with numbers removed, P4-C practitioner note added)
- P5-B (with P5-C follow-on note)
- P6-B (with Cluster 4 wording fix)
- P6-C (finding.md required)

### Innovation's Assembly 1 — Double-Collapse Named Mechanism (P2-B + P3-B)

**Preview:** Strong viable — this is the inquiry's primary named insight.

**Prosecution:** "Double-collapse" as a named mechanism adds terminology to the theory. Practitioners need to learn a new term. Is the naming worth the terminological overhead?

**Defense:** The double-collapse is not a minor add-on — it is the complete causal explanation for why generic messages fail categorically, not just marginally. Without a name, the mechanism exists in prose but is not retrievable or citable. Named mechanisms are the currency of practical theory — "the double-collapse" is what a practitioner will cite when explaining to a colleague why Person B generated zero attachment. Naming it makes the insight durable.

More importantly: the double-collapse is what unifies the specificity mechanism (P2) and the sender-SP mechanism (P3) into a single coherent explanation. Without the assembly, readers may see two separate mechanisms and miss that they always fire together on generic messages.

**Collision:** Defense wins clearly. Terminological overhead is minimal (one term). The mechanism's importance — explaining near-zero generic-message attachment — justifies naming.

**Verdict: SURVIVE** — double-collapse should be explicitly named and defined in the spec as a mechanism that combines P2 (specificity failure at f-layer) and P3 (Supplication-display at g-layer). Add a named-mechanism paragraph in the worked example section.
- Architectural Coherence ✓ (uses existing f and g structure)
- Definitional Distinctness ✓ (f-layer failure and g-layer failure are distinct mechanisms)
- Empirical Coverage ✓ (explains near-zero attachment vs weak attachment)
- Cluster 4 ✓
- Operational Testability ✓ (both components are detectable)
- Pedagogical Clarity ✓ (most important practical insight of inquiry)
- Scope Compliance ✓ (names and combines existing mechanisms, adds no structure)

---

### Innovation's Assembly 2 — Threshold + TYPE-Primary (P2-C + P4-C)

**Preview:** Dead region — inherits both components' dimensional failures.

**Prosecution:** P2-C was killed (empirically underdetermined for spec). P4-C was killed (exceeds scope). Their combination inherits both failures. The assembly's conceptual elegance (below threshold → nothing registers; above threshold → TYPE determines) is attractive but doesn't resolve the evidence problem.

**Defense:** The assembly is phenomenologically accurate and may describe the correct structure.

**Collision:** Prosecution wins. Two killed candidates don't combine into a viable candidate when they're killed on independent grounds (one empirical, one scope).

**Verdict: KILL** — inherits component failures.

**Seed extracted:** This assembly is the priority test-design target for iteration-3.3. Specifically: design empirical tests that distinguish threshold-gated specificity from very-steep-linear, and test whether TYPE is a more reliable predictor of behavioral trajectory than MAGNITUDE. Document as two paired frontier questions in finding.md.

---

### Innovation's Assembly 3 — Authenticity as Structural Requirement (P5-C + P3-C)

**Preview:** Boundary region — practical conclusion survives, philosophical framing doesn't.

**Prosecution:** "Authenticity is a structural requirement" is prescriptive. APT is a descriptive theory — it describes what generates attachment, not what practitioners ought to do. The theory PREDICTS that inauthentic signals will tend to be low-specificity and Supplication-displaying, but it doesn't prescribe authenticity as required. The philosophical overclaim from P3-C is present in this assembly.

**Defense:** The practical conclusion — "the theory predicts that no optimization path exists for templates, and that genuine engagement is the path of least resistance to high-specificity + high-SP messages" — is correct and important. It's a prediction, not a prescription.

**Collision:** Both can be preserved by recasting: from "structural requirement" (prescriptive) to "structural prediction" (descriptive). The insight survives; the overclaiming doesn't.

**Verdict: REFINE** — reframe as "structural prediction" rather than "structural requirement." Content: the theory predicts that genuine engagement is the path of least resistance because it simultaneously produces specificity (f-layer) and Self-Focus-display (g-layer) without requiring separate optimization. Include as a practical implication note following P5-B.

---

## Phase 4 — Coverage + Convergence

### Accumulator

| Candidate | Verdict | Dimension that decided | Notes |
|---|---|---|---|
| P1-A | REFINE | Pedagogical Clarity, Empirical Coverage | Insufficient justification |
| P1-B | SURVIVE | All pass | Incorporate P1-C framing note |
| P1-C | REFINE | Empirical Coverage | SDT analogy speculative; framing direction valid |
| P2-A | REFINE | Definitional Distinctness, Operational Testability | 5th-variable argument thin; no PRAGMA indicators |
| P2-B | SURVIVE | All pass | Soften evolutionary framing to analogy |
| P2-C | KILL | Empirical Coverage, Scope Compliance | Threshold underdetermined; flag as frontier question |
| P3-A | REFINE | Pedagogical Clarity | Missing g-layer failure explanation |
| P3-B | SURVIVE | All pass | Double-collapse is the inquiry's key insight |
| P3-C | REFINE | Definitional Distinctness | Overclaims ontology; soften to "operationally equivalent" |
| P4-A | REFINE | Pedagogical Clarity | Independence argument understated; taxonomy too flat |
| P4-B | SURVIVE | All pass (minor edit) | Remove numerical precision from illustration |
| P4-C | KILL | Scope Compliance | Reporting-architecture commitment exceeds 3.2.1 scope |
| P5-A | REFINE | Pedagogical Clarity | Sequential format weaker than comparative |
| P5-B | SURVIVE | All pass | Strongest worked example |
| P5-C | REFINE | Scope Compliance | Follow-on note, not replacement |
| P6-A | REFINE | Pedagogical Clarity | Placement decisions without rationale |
| P6-B | SURVIVE | All pass (minor edit) | Fix Cluster 4 "monitoring" wording |
| P6-C | SURVIVE | All pass | Finding.md is protocol-required; scope is correct |
| Assembly 1 | SURVIVE | All pass | Double-collapse should be named in spec |
| Assembly 2 | KILL | Empirical Coverage, Scope Compliance | Inherits P2-C + P4-C failures |
| Assembly 3 | REFINE | Definitional Distinctness | Reframe to "structural prediction"; follow-on note |

### Coverage Assessment

- All 6 pieces evaluated: ✓
- All 3 innovation assemblies evaluated: ✓
- All 7 dimensions applied to all candidates: ✓
- Dead regions confirmed: Resonance-as-gate (B1), threshold-as-spec-content (P2-C), TYPE-primary-as-spec-commitment (P4-C), threshold+TYPE-primary combination (Assembly 2)
- Viable region populated: 7 survivors (P1-B, P2-B, P3-B, P4-B, P5-B, P6-B/C, Assembly 1)
- Boundary regions explored and assigned: P1-C, P3-C (framing), Assembly 3

No unexplored regions in the current candidate set.

### Convergence Signal: TERMINATE

All convergence criteria met:
1. Multiple clean SURVIVEs with no critical-dimension caveats ✓
2. All candidate landscape regions mapped ✓
3. Two kills with seeds extracted ✓
4. Refines have clear directions that don't require new innovation cycles ✓
5. The question ("how do the 4 variables in f interact?") is answered: **additive, with explicit justification, with three supporting mechanisms (specificity, sender-SP, double-collapse)**

---

## Final Deliverable

### Dimensions

| Dimension | Weight | Applied |
|---|---|---|
| Architectural Coherence | CRITICAL | All 21 candidates |
| Definitional Distinctness | CRITICAL | All 21 candidates |
| Empirical Coverage | CRITICAL | All 21 candidates |
| Cluster 4 Integrity | CRITICAL | All 21 candidates |
| Operational Testability | MEDIUM | All 21 candidates |
| Pedagogical Clarity | MEDIUM | All 21 candidates |
| Scope Compliance | MEDIUM | All 21 candidates |

### Fitness Landscape

**Viable region (occupied by survivors):**
P1-B, P2-B, P3-B, P4-B, P5-B, P6-B, P6-C, Assembly 1

**Dead regions (confirmed):**
- Resonance-as-credibility-gate: killed by $100K and celebrity cases (from exploration)
- Specificity-as-5th-variable: fails orthogonality (from P2 candidates)
- Threshold model as spec assertion: empirically underdetermined (P2-C killed)
- TYPE-primary as spec commitment: exceeds scope (P4-C killed)
- Threshold + TYPE-primary assembly: inherits both failures (Assembly 2 killed)

**Boundary regions (refined, not killed):**
- Signal detection theory grounding for additivity (P1-C): valid framing, speculative proof
- Display-IS-state ontological claim (P3-C): overclaims, soften to operational equivalence
- Prescriptive inverse (P5-C + Assembly 3): valid conclusion, wrong register — prediction not prescription

**Unexplored regions (for future iterations):**
- Threshold-vs-linear empirical test design (iteration-3.3)
- TYPE taxonomy empirical derivation
- TYPE evolution over time
- Dyadic specificity

### The Answer

**Iteration-3.2.1 content = 7 survivors assembled:**

1. **P1-B** (additive f with evidence ledger) + P1-C's framing note: f is additive by both parsimony default AND because C/H/F/R are independent signal channels. Three alternatives tested and eliminated (B1, F1, I1).

2. **P2-B** (signal specificity with PRAGMA operationalization): `effective_magnitude = nominal × specificity`, per variable, with template-match + rare-content-marker indicators. Costly-signal analogy presented as explanatory, not definitional.

3. **P3-B** (double-collapse architecture): The receiver applies their g-function to the sender. In single-message contexts, message style carries the sender's modulator signal. The Double-Collapse = generic messages suppress both f (via low specificity) and g (via Supplication-display) simultaneously.

4. **P4-B** (MAGNITUDE vs TYPE with persistence dynamics, numbers removed): Same attachment score, different variable mix → different behavioral trajectory. Persistence dynamics by TYPE established.

5. **P5-B** (comparative table with double-collapse callout) + P5-C follow-on note: Person A vs Person B as comparative analysis; "Practical Implication" note: the theory predicts genuine engagement is the path of least resistance — both fixes (specificity and SP-display) require authentic attention, which is a structural prediction, not a prescription.

6. **P6-B** (placement-rationale, Cluster 4 statement fixed): four placement decisions with reader-dependency rationale; iteration-3.2.1 labeled correctly; forward-looking sequence preserved; Cluster 4 status: unchanged.

7. **P6-C** (finding.md required per protocol): finding.md scope = question asked + 4 clarifications + B1 kill + F1 reinterpretation + double-collapse named + Cluster 4 status + iteration label rationale. Brief, not a full spec.

8. **Assembly 1** (Double-Collapse named in spec): explicitly define "The Double-Collapse" as a named mechanism combining the f-layer failure (specificity) and g-layer failure (Supplication-display) that together explain near-zero attachment from generic messages.

### Verdicts Summary

| Piece | Winner | Refinements applied |
|---|---|---|
| P1 | P1-B | + P1-C framing note ("not just parsimony; independent channels") |
| P2 | P2-B | + soften costly-signal to analogy |
| P3 | P3-B | double-collapse; g-layer explicit |
| P4 | P4-B | + remove numerical example + P4-C practitioner note |
| P5 | P5-B | + P5-C follow-on as "Practical Implication" |
| P6 | P6-B + P6-C | Cluster 4 wording fix; finding.md required |
| Assembly | Assembly 1 | Named mechanism "The Double-Collapse" |
| KILLED | P2-C, P4-C, Assembly 2 | Seeds: frontier question flags (iteration-3.3 agenda) |

### Signal: TERMINATE

**Ranked survivors:**
1. **Assembly 1 (Double-Collapse named mechanism)** — most important insight; explains near-zero vs weak attachment; should be the opening mechanism in the spec section
2. **P3-B (double-collapse architecture)** — foundation of the double-collapse; makes existing g-formula explicit for single-message case
3. **P4-B (MAGNITUDE vs TYPE with persistence dynamics)** — extends output dimensionality; persistence dynamics are the most practically powerful addition
4. **P2-B (signal specificity)** — operationalizes the magnitude factor; PRAGMA-ready
5. **P1-B (additive f with evidence ledger)** — explicit architectural commitment with justification trail
6. **P5-B + P5-C note (worked example + practical implication)** — integrates all 4 clarifications; delivers the authenticity-prediction conclusion
7. **P6-B + P6-C (admin + finding.md)** — administrative integration + protocol-required finding

---

## Convergence Telemetry

- **Dimensions evaluated:** 7 / 7, all critical covered: YES
- **Adversarial strength:** STRONG — prosecution on P2-C (threshold) would make advocates pause; prosecution on P4-C (scope) is unambiguous; prosecution on P3-C (ontological overclaim) identifies a real boundary. No rubber-stamping detected.
- **Landscape stability:** STABLE — critique confirmed the shape established by exploration + sensemaking. No new regions discovered. Three candidates killed on CRITICAL dimensions confirm the dead region boundaries.
- **Clean SURVIVE:** YES — P1-B, P2-B, P3-B, P4-B, P5-B, P6-B/C, Assembly 1 all pass critical dimensions with no critical-dimension caveats (only minor edits on medium-weight dimensions)
- **Failure modes observed:** None — no wrong dimensions (all extracted from sensemaking), no rubber-stamping (3 kills on critical dimensions), no nitpicking (medium-dimension failures produced REFINEs not KILLs), no dimension blindness (all sensemaking perspectives covered), no false convergence (landscape stable AND multiple clean SURVIVEs), no evaluation drift (dimensions fixed in Phase 0), no self-reference (external empirical and scope anchors used throughout)
- **Overall: PROCEED** — full dimension coverage, adversarial strength confirmed, multiple clean SURVIVEs, no failure modes, convergence criteria met
