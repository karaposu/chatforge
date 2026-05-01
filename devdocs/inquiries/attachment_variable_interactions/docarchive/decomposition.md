---
status: active
discipline: decomposition
inquiry: attachment_variable_interactions
iteration: 1
---
# Decomposition: attachment_variable_interactions

## Input Consumed

- `_branch.md` — inquiry question on f's internal interaction dynamics
- `exploration.md` — 11 candidates probed; 2 CONFIRMED (A1 additive + C1 sender-SP), 1 CONFIRMED ABSENT (B1), 1 CONFIRMED as magnitude-factor (D1), 1 REINTERPRETED (F1 as TYPE), 1 absorbed (I1 → Coherence)
- `sensemaking.md` — stabilized on iteration-3.2.1 CLARIFICATION with 4 explicit additions to iteration-3.2; no structural changes; Cluster 4 unchanged

## The Whole Being Decomposed

**Produce iteration-3.2.1 — a clarification document adding 4 explicit additions to the APT spec:**

1. `f` is additive in its 4 variables (no interaction terms)
2. Signal specificity is a magnitude factor per variable
3. Sender-side Self-Positioning is readable from message style in single-interaction contexts
4. Attachment has two output dimensions: MAGNITUDE (scalar) and TYPE (qualitative)

Plus: worked example (user's Reddit case), spec placement, administrative integration.

All additions preserve iteration-3.2's architecture unchanged. Cluster 4 status unchanged.

---

## Step 1 — Coupling Topology

### Elements in the whole

a. `f` is additive explicit statement
b. Interaction-terms-absent justification (why additive, what was tested)
c. Signal specificity definition (`effective_magnitude = nominal × specificity`)
d. Specificity operationalization (generic vs specific examples)
e. Sender-side SP-readable-from-message mechanism
f. Message-style-as-modulator-signal examples (template vs engaged)
g. Attachment MAGNITUDE output dimension
h. Attachment TYPE output dimension
i. Illustrative attachment TYPE taxonomy (bonded/transactional/status-driven/coerced/hybrid)
j. Worked example (user's Reddit Person A vs Person B) — integrates all 4 additions
k. Spec placement decisions (where in `new_apt_layer.md` each addition goes)
l. Cluster 4 status statement (unchanged)
m. Iteration labeling (3.2.1)
n. Relationship fields update (supersedes, inherits)
o. APT Inference / Profiling downstream flag (TYPE reporting extension)

### Coupling analysis

**Strong coupling (must stay together):**
- {a, b} — additive statement + justification. Same conceptual unit.
- {c, d} — specificity definition + examples. Same conceptual unit.
- {e, f} — sender-SP mechanism + examples. Same conceptual unit.
- {g, h, i} — MAGNITUDE + TYPE + illustrative taxonomy. Dimensional-clarification unit.

**Moderate coupling (content → example, content → placement):**
- {a,b} → {j}: worked example uses additive f reasoning
- {c,d} → {j}: worked example uses specificity analysis
- {e,f} → {j}: worked example uses sender-SP reading
- {g,h,i} → {j}: worked example demonstrates MAGNITUDE + TYPE dimensions
- All 4 content units → {k}: spec placement depends on content

**Weak coupling (mostly independent):**
- {l} Cluster 4 status — independent acknowledgment
- {m} iteration labeling — administrative
- {n} relationship updates — administrative
- {o} downstream flag — forward-looking

### Coupling map (topology)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ P1 ADDITIVE  │  │ P2 SPECIFI-  │  │ P3 SENDER-SP │  │ P4 MAG/TYPE  │
│ {a, b}       │  │ CITY {c, d}  │  │ {e, f}       │  │ {g, h, i}    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └─────────────────┴───┬─────────────┴─────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │ P5 WORKED EXAMPLE│
                   │ {j}              │
                   │ (integrates all 4)│
                   └─────────┬────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │ P6 ADMINISTRATIVE│
                   │ {k, l, m, n, o}  │
                   │ (spec placement, │
                   │  Cluster 4,      │
                   │  labeling,       │
                   │  downstream flag)│
                   └──────────────────┘
```

### Major clusters identified

1. **P1 — Additive f statement**: explicit commitment + justification
2. **P2 — Signal specificity**: magnitude factor definition + examples
3. **P3 — Sender-side SP from message style**: mechanism + template/engaged examples
4. **P4 — Attachment MAGNITUDE vs TYPE**: dimensional clarification + illustrative taxonomy
5. **P5 — Worked example**: user's Reddit case integrating all 4 content units
6. **P6 — Administrative integration**: spec placement + Cluster 4 + labeling + relationships + downstream flags

### Major boundaries (low-coupling valleys)

- Between P1, P2, P3, P4: each is a standalone content unit. Minimal cross-reference needed during content drafting; references only at the worked-example stage.
- Between content units and P5: worked example INTEGRATES them; clean one-way flow.
- Between P5 and P6: administrative vs content. Different work types.
- Between P6 items: Cluster 4 statement, iteration labeling, relationship updates, downstream flags are all largely independent administrative items.

---

## Step 2 — Boundaries Detected (Top-Down)

Based on coupling topology, natural cuts produce **6 pieces:**

| # | Piece | Internal cluster | External couplings |
|---|---|---|---|
| **P1** | **Additive f statement** | {a, b} | Feeds P5 |
| **P2** | **Signal specificity** | {c, d} | Feeds P5 |
| **P3** | **Sender-side SP from message** | {e, f} | Feeds P5 |
| **P4** | **Attachment MAGNITUDE vs TYPE** | {g, h, i} | Feeds P5 |
| **P5** | **Worked example** | {j} | Consumes P1-P4 |
| **P6** | **Administrative integration** | {k, l, m, n, o} | Consumes all content |

### Boundary quality check

- **P1 ↔ P2 ↔ P3 ↔ P4:** Clean. Each is a standalone content unit. Minimal cross-reference during drafting.
- **P1/P2/P3/P4 → P5:** Integration interface. Worked example needs each unit's content to illustrate.
- **P5 → P6:** Administrative placement needs settled content.
- **P6 internal:** {l, m, n, o} can be done in any order or in parallel; {k} depends on content settling.

---

## Step 3 — Boundaries Validated (Bottom-Up Check)

### Obvious irreducible atoms

Atomic work units for producing iteration-3.2.1:

1. Write "f is additive" explicit statement (`f = a·charm + b·hope + c·fear + d·resonance`)
2. Write justification for additive structure (evidence-based: B1 killed by $100K/celebrity; F1 reinterpreted; I1 absorbed)
3. Write signal specificity definition (`effective_magnitude = nominal_content × specificity`)
4. Write generic-vs-specific operationalization examples
5. Write sender-side SP-readable-from-message-style mechanism
6. Write template-vs-engaged-message examples
7. Write MAGNITUDE output dimension paragraph (scalar from f-sum × g-product)
8. Write TYPE output dimension paragraph (qualitative from variable mix)
9. Draft illustrative TYPE taxonomy (bonded, transactional, status-driven, coerced, hybrid) with provisional flag
10. Write worked example paragraph — Person A analysis
11. Write worked example paragraph — Person B analysis
12. Write observation re-attribution paragraph (user's "Hope without Resonance" reframed)
13. Write observation re-attribution paragraph (user's "combinations unlock bigger locks" reframed as TYPE)
14. Decide spec placement for additive f statement
15. Decide spec placement for specificity clarification
16. Decide spec placement for sender-SP single-message note
17. Decide spec placement for MAGNITUDE/TYPE dimensions
18. Write Cluster 4 status statement (unchanged)
19. Write iteration labeling statement (3.2.1)
20. Update relationship fields (supersedes, inherits)
21. Add APT Inference / Profiling downstream flag (TYPE reporting extension)
22. Update iteration development trail in new_apt_layer.md

### Bottom-up clustering vs top-down

- Atoms 1-2 → **P1 Additive f** ✓
- Atoms 3-4 → **P2 Signal specificity** ✓
- Atoms 5-6 → **P3 Sender-SP from message** ✓
- Atoms 7-9 → **P4 MAGNITUDE vs TYPE** ✓
- Atoms 10-13 → **P5 Worked example** ✓
- Atoms 14-22 → **P6 Administrative integration** ✓

**Confidence: HIGH on all boundaries.** Top-down and bottom-up agree on all 6 pieces.

### Edge cases checked

- **Atoms 14-17 (spec placement) — in P6 as administrative or in each content piece?** Belongs in P6 because spec placement needs all content settled to know where each piece lands. Content drafts (P1-P4) produce the content; P6 integrates into existing spec structure.
- **Atom 9 (illustrative TYPE taxonomy) — in P4 or separate piece?** Belongs in P4. Taxonomy is an illustration of the TYPE dimension; same conceptual unit. Marked provisional in P4.
- **Atom 21 (APT Inference/Profiling flag) — in P6 or separate piece?** Belongs in P6. Administrative flag; not substantive content for iteration-3.2.1.

No destabilizing edge cases.

---

## Step 4 — Question Tree

### P1 — Additive f Statement

**Question:** What is the explicit statement that `f` is additive in its 4 variables, with context-appropriate justification?

**Verification criteria:**
- [ ] Formula written: `f = a·charm + b·hope + c·fear + d·resonance`
- [ ] Context-dependent coefficient note (empirical question flagged)
- [ ] "No interaction terms within f" stated
- [ ] Justification references exploration's tests (B1 killed by $100K/celebrity; F1 reinterpreted as TYPE; I1 absorbed by Coherence at g₂)
- [ ] Principled framing — parsimony default + burden-of-proof on interaction-term advocates
- [ ] Relationship to multiplicative gating clarified (f's internal structure additive; outer f × g multiplicative; these are independent claims)
- [ ] Apparent interactions (manipulation wariness) explicitly attributed to Coherence-failure at g₂, not f

**Stopping check:** Tractable in focused pass.

### P2 — Signal Specificity

**Question:** What is signal specificity, how does it relate to each variable's effective magnitude, and how is it operationalized (generic vs specific)?

**Verification criteria:**
- [ ] Formula written: `effective_magnitude(variable) = nominal_content(variable) × specificity(signal)`
- [ ] Definition of "specificity" — degree to which a signal is tailored to this specific counterparty vs could be sent to anyone
- [ ] Generic signal example (template-like)
- [ ] Specific signal example (tailored)
- [ ] Why specificity isn't a 5th variable (fails orthogonality — can't have specificity without content to be specific about)
- [ ] Implication for each of the 4 variables (Charm, Hope, Fear, Resonance each have specificity dimension)
- [ ] Flag for downstream: PRAGMA operationalization of specificity detection

**Stopping check:** Tractable in focused pass.

### P3 — Sender-Side SP from Message Style

**Question:** How is sender-side Self-Positioning read from message style in single-interaction contexts, and what are the template-vs-engaged examples?

**Verification criteria:**
- [ ] Mechanism statement: in single-message contexts, the message STYLE carries the sender's modulator signal; the receiver's g-function (from receiver's perspective, applied to sender) uses message-style as input
- [ ] Clarification: this is iteration-3.2's existing multiplicative-gating mechanism, made explicit for single-message case
- [ ] Longitudinal contrast: in multi-interaction contexts, modulator signals (especially Coherence) are readable longitudinally; in single-message contexts, only message-style is available
- [ ] Generic template example → Supplication display → low sender-SP → sender-g collapses
- [ ] Specific engaged message example → high Self-Focus display → high sender-SP → sender-g high
- [ ] Note: this mechanism applies to ALL 3 Modulator Suite members in principle, but Self-Positioning is most readable from single message (Coherence needs longitudinal; EC partially readable via voice/body if multimodal)
- [ ] Flag for downstream: PRAGMA single-message modulator-inference rules

**Stopping check:** Tractable.

### P4 — Attachment MAGNITUDE vs TYPE

**Question:** What are the two output dimensions of attachment (MAGNITUDE and TYPE), how does each arise from f's structure, and what illustrative taxonomy of TYPEs should the spec document (as provisional)?

**Verification criteria:**
- [ ] MAGNITUDE dimension defined: scalar from `f-sum × g-product`; how strongly the observer engages
- [ ] TYPE dimension defined: qualitative from variable mix inside f; what KIND of attachment
- [ ] Why TYPE doesn't reduce to MAGNITUDE (same magnitude, different mix → different persistence dynamics)
- [ ] Illustrative TYPE taxonomy:
  - Charm-dominant → status/admiration
  - Hope-dominant → transactional
  - Fear-dominant → coerced
  - Resonance-dominant → bonded/deep
  - Mixed → hybrid (with example)
- [ ] Explicit note that taxonomy is PROVISIONAL (illustrative, not exhaustive; comprehensive classification may need downstream empirical work)
- [ ] Flag for APT Profiling: output structure extension to report TYPE alongside MAGNITUDE
- [ ] Note on persistence dynamics (Resonance-grounded attachments persist; Fear-grounded evaporate when fear removed; Hope-grounded depend on continued exchange)

**Stopping check:** Tractable. Slightly heavier piece due to illustrative taxonomy; stays within single focused pass.

### P5 — Worked Example (User's Reddit Case)

**Question:** How does the user's Reddit Person A vs Person B case illustrate all 4 clarifications in action, and how are the user's intuitions re-attributed correctly?

**Verification criteria:**
- [ ] Person A analysis:
  - Specificity: high (specific product mention, real enthusiasm, concrete offer)
  - Effective magnitudes: moderate-high on Charm (competence demonstrated) + high on Hope (concrete collaboration offer) + high on Resonance (real understanding)
  - f-sum: substantial
  - Sender-SP display: high (Self-Focus — engaged with own evaluation, concrete offer, own-agenda)
  - g: high
  - MAGNITUDE: substantial
  - TYPE: Resonance + Hope mix → bonded-leaning/collaborative
- [ ] Person B analysis:
  - Specificity: low (generic template, could be sent to anyone)
  - Effective magnitudes: low across all variables
  - f-sum: low
  - Sender-SP display: Supplication (fishing, low-effort, permission-asking premise)
  - g: collapsed
  - MAGNITUDE: near-zero
  - TYPE: not meaningfully registered
- [ ] Observation re-attribution: "Hope without Resonance fails" → actual: low-everything + sender-Supplication; Resonance-absence was correlate of genericness, not cause
- [ ] Observation re-attribution: "combinations unlock bigger locks" → captures TYPE not MAGNITUDE; variable mix determines qualitative character, not additive bonus
- [ ] Practical takeaway: specific engaged messages hit multiple variables simultaneously AND display high sender-SP; generic templates fail across all dimensions at once

**Stopping check:** Tractable with careful structuring. Sets up P1-P4 in concrete application.

### P6 — Administrative Integration

**Question:** Where do the 4 clarifications go in `new_apt_layer.md`, what is the iteration label, how are relationship fields updated, what's the Cluster 4 status, and what downstream flags are needed?

**Verification criteria:**
- [ ] Spec placement decisions for each of 4 clarifications:
  - P1 additive f → extend the multiplicative-gating formula section with explicit additive-inner-structure note
  - P2 specificity → new "Signal Specificity" subsection near the 4 attachment variables
  - P3 sender-SP single-message → extend Self-Positioning section with single-message-reading paragraph
  - P4 MAGNITUDE/TYPE → new "Attachment Output Dimensions" subsection after attachment-variables + modulators
- [ ] P5 worked example placement — as illustration in an introductory paragraph or a dedicated subsection
- [ ] Iteration label: 3.2.1 (clarification, not refinement)
- [ ] Cluster 4 status statement: UNCHANGED from iteration-3.2; clarifications don't add modulators or attention-interaction dynamics
- [ ] Relationship fields:
  - Supersedes: `apt_modulator_landscape` (iteration-3.2) at clarification level only
  - Inherits: `apt_missing_dimension` (iteration-1 architecture) unchanged
- [ ] APT Inference output extension flag: report attachment TYPE alongside MAGNITUDE
- [ ] APT Profiling output extension flag: report TYPE tendencies (which TYPE of attachment each person tends to generate in others)
- [ ] Iteration development trail in `new_apt_layer.md` updated with iteration-3.2.1 row
- [ ] Forward-looking sequence preserved from iteration-3.2 (3.3 empirical → 3.4 cross-cultural → 3.5 interaction dynamics → 3.6 dyadic modulators → 4 substrate reframe); iteration-3.2.1 is a clarification, doesn't alter sequence

**Stopping check:** Tractable. Many small administrative items; none individually complex.

---

## Step 5 — Interface Map

Flows between pieces:

| From | To | What flows | Direction |
|---|---|---|---|
| P1 | P5 | Additive f statement used in worked example's f-sum analysis | One-way |
| P2 | P5 | Specificity framework used in worked example's effective-magnitude analysis | One-way |
| P3 | P5 | Sender-SP-reading mechanism used in worked example's g-collapse analysis | One-way |
| P4 | P5 | MAGNITUDE/TYPE dimensions applied in worked example's output characterization | One-way |
| P1 | P6 | Content settled → placement decision | One-way |
| P2 | P6 | Content settled → placement decision | One-way |
| P3 | P6 | Content settled → placement decision | One-way |
| P4 | P6 | Content settled → placement decision | One-way |
| P5 | P6 | Worked example placement decision (introductory vs subsection) | One-way |

**No circular dependencies.** Clean DAG.

**Interface hidden-coupling check:**

- **P1 and P2 interact via specificity vs additive structure:** P2 says specificity modifies each variable's effective magnitude. P1 says variables contribute additively. Together: `f = Σ (nominal_i × specificity_i × coefficient_i)`. Still additive; specificity is a magnitude factor, not an interaction term. Mitigation: P1 statement should note that additive structure applies to effective magnitudes (not nominal content).
- **P3 and P4 interact via sender-side reading affecting TYPE:** the sender's displayed SP doesn't directly determine attachment TYPE (TYPE is from receiver's variable-mix), but it does affect receiver's g which affects MAGNITUDE. Separation clean; mention cross-reference in worked example (P5) only.
- **P5 integrates all 4:** risk that worked example over-extends and becomes its own piece. Mitigation: keep P5 focused on user's specific case; don't generalize into theory claims (theory claims live in P1-P4).

---

## Step 6 — Dependency Order

### Order diagram

```
Phase 1 (parallel — 4 content units):
  P1 [Additive f]
  P2 [Specificity]
  P3 [Sender-SP from message]
  P4 [MAGNITUDE/TYPE]

Phase 2:
  P5 [Worked example]       ← consumes P1-P4

Phase 3 (last):
  P6 [Administrative]       ← consumes all substantive + P5
```

### Explicit ordering

1. **Phase 1 (parallel):** P1 + P2 + P3 + P4 — four content units, independent. Parallelizable.
2. **Phase 2:** P5 (worked example) — after P1-P4.
3. **Phase 3:** P6 (administrative) — after all substantive pieces.

### Parallel opportunities

- Phase 1: four-way parallel. Each content piece can be drafted independently.
- Within P6: {l, m, n, o} are independent administrative items; {k} depends on content settling.

### Circular dependency check

No circular dependencies. P6 is the sink.

---

## Step 7 — Self-Evaluation

### Minimum dimensions

- **Independence:** PASS — each piece's question answerable without reading siblings, except P5 (which consumes P1-P4 via defined interfaces) and P6 (consumes everything).
- **Completeness:** PASS — P1-P6 cover: 4 clarifications + worked example + administrative integration. All atomic work units mapped.
- **Reassembly:** PASS — all pieces + interfaces reconstruct iteration-3.2.1 document.

### Full dimensions

- **Tractability:** PASS — each piece is a focused work unit. P4 slightly heavier (illustrative TYPE taxonomy) but still single-pass. P5 slightly heavier (integrates 4 clarifications) but contained.
- **Interface clarity:** PASS — flows explicit. One subtle coupling flagged (P1+P2 together define effective-magnitude additive structure).
- **Balance:** PASS — P4 and P5 slightly larger than others; others are short content/admin pieces. Not dramatically imbalanced.
- **Confidence:** PASS — top-down and bottom-up boundaries agree on all 6 pieces.

### Summary

| Dimension | Result |
|---|---|
| Independence | PASS |
| Completeness | PASS |
| Reassembly | PASS |
| Tractability | PASS |
| Interface clarity | PASS (one subtle coupling noted) |
| Balance | PASS (P4, P5 slightly heavier but contained) |
| Confidence | PASS |

**Overall:** Decomposition is sound. Ready for innovation.

---

## Final Deliverable

### Coupling Map

6 clusters with clean DAG:

1. **P1 Additive f** — content unit
2. **P2 Signal specificity** — content unit
3. **P3 Sender-SP from message style** — content unit
4. **P4 MAGNITUDE vs TYPE** — content unit (heaviest)
5. **P5 Worked example** — integration (consumes P1-P4)
6. **P6 Administrative** — placement + labeling + relationships + downstream flags

### Question Tree

**P1 — Additive f Statement**
*What is the explicit additive-f statement with justification?*
7 verification criteria including formula, context-dependent coefficients, no-interaction-terms note, exploration-evidence justification, parsimony framing, multiplicative-gating clarification, Coherence-at-g₂ attribution for apparent interactions.

**P2 — Signal Specificity**
*What is signal specificity and how is it operationalized?*
7 verification criteria including effective-magnitude formula, definition, generic/specific examples, why-not-5th-variable, per-variable implication, PRAGMA operationalization flag.

**P3 — Sender-Side SP from Message Style**
*How is sender-SP read from single-message contexts?*
7 verification criteria including mechanism, iteration-3.2-consistency, longitudinal-contrast, template/engaged examples, Modulator Suite applicability, PRAGMA flag.

**P4 — Attachment MAGNITUDE vs TYPE**
*What are the two output dimensions and illustrative TYPE taxonomy?*
8 verification criteria including MAGNITUDE definition, TYPE definition, irreducibility, illustrative 5-type taxonomy with provisional flag, APT Profiling extension flag, persistence-dynamics note.

**P5 — Worked Example (User's Reddit Case)**
*How do all 4 clarifications apply to the user's Person A vs Person B case?*
5 verification criteria including Person A analysis, Person B analysis, "Hope without Resonance" re-attribution, "combinations unlock" re-attribution, practical takeaway.

**P6 — Administrative Integration**
*How does iteration-3.2.1 integrate into new_apt_layer.md (placement, labeling, relationships, downstream flags)?*
9 verification criteria including 4 placement decisions, P5 placement, iteration label, Cluster 4 status, relationship fields, APT Inference + Profiling downstream flags, development trail update, forward-looking sequence preservation.

### Interface Map

```
P1 (Additive f) ────────┐
P2 (Specificity) ───────┤
                        ├─→ P5 (Worked example)
P3 (Sender-SP) ─────────┤                │
P4 (MAGNITUDE/TYPE) ────┘                ▼
                                   P6 (Administrative)
                                   (consumes all above)
```

Interface contents:
- P1 → P5: additive f statement for worked-example f-sum analysis
- P2 → P5: specificity framework for effective-magnitude analysis
- P3 → P5: sender-SP-reading mechanism for g-collapse analysis
- P4 → P5: MAGNITUDE/TYPE dimensions for worked-example output characterization
- All substantive → P6: content settled → placement decisions

### Dependency Order

- **Phase 1 (parallel):** P1 + P2 + P3 + P4 — four-way parallel
- **Phase 2:** P5 — after all content pieces
- **Phase 3:** P6 — last; consumes all

### Self-Evaluation Summary

- Independence: PASS
- Completeness: PASS
- Reassembly: PASS
- Tractability: PASS (P4, P5 slightly heavier)
- Interface clarity: PASS (P1+P2 subtle coupling on effective-magnitude additive structure noted)
- Balance: PASS
- Confidence: PASS

**Decomposition ready for innovation.**

---

## Handoff to Innovation

Each of the 6 pieces is an innovation target:

- **P1** → innovation generates exact wording for additive-f statement + justification prose; decides where to place the formula (inside the existing multiplicative-gating section vs new subsection)
- **P2** → innovation generates specificity definition wording + generic/specific examples + operationalization guidance
- **P3** → innovation generates sender-SP-from-message mechanism wording + template/engaged examples + Modulator Suite note
- **P4** → innovation generates MAGNITUDE/TYPE wording + illustrative taxonomy table + persistence-dynamics note + provisional flag language
- **P5** → innovation generates worked-example prose (Person A + Person B + re-attribution + takeaway); decides example format (inline vs dedicated subsection)
- **P6** → innovation generates placement decisions + Cluster 4 statement + iteration labeling + relationship field updates + downstream flag phrasings

Critique should adjudicate with iteration-3.2 dimensions tuned for iteration-3.2.1 scope:
- Structural Coherence with iteration-3.2 (critical — preserving all commitments; purely additive; no new modulators or variables)
- Definitional Distinctness (critical — specificity ≠ 5th variable; TYPE ≠ magnitude; sender-SP single-message ≠ new mechanism)
- Operational Testability (critical — signal specificity operationalization; attachment TYPE detection)
- Architectural Parsimony (medium — 4 clarifications + worked example is appropriate scope for 3.2.1)
- Pedagogical Clarity (medium — worked example lands for reader; user's intuitions re-attributed honestly)
- Honesty on Cluster 4 and TYPE taxonomy provisional status (medium — clarifications acknowledge what's confident vs provisional)
