# Conversational Intent — Test Cases

Systematic test cases for intent classification, hidden intent detection, intent arcs, and intent mismatch. Drawn from the 19 scenarios in `intent_scenarios.md`.


## Classification Test Cases

### CT1: Clear Single Intent — Inform

```
Context: Status update requested
Message: "We shipped the auth module last Tuesday. Latency dropped
from 3.2s to 400ms. Still blocked on Stripe's sandbox API key."
```

| Field | Expected |
|---|---|
| Primary | **inform** |
| Secondary | null |
| Confidence | 0.9 |
| Explanation | "Neutral status update with specific data. No advocacy, no request, no personal stake." |

**EI signals:** Low SRI, absent EF, absent TI, absent RD, absent US
**Hidden intent:** None (EI aligns with classification)

---

### CT2: Shifting Intent — Inform then Convince

```
Context: A says "That seems slow" after B's status update

Message 1 (B): "We're at 60% completion. Auth is done, payments in progress."
Message 2 (B): "It's actually ahead of comparable projects. LinkedIn's migration
took 18 months. We're at month 4 with 3x their test coverage."
```

| Message | Primary | Confidence | Explanation |
|---|---|---|---|
| 1 | **inform** | 0.9 | Neutral data sharing |
| 2 | **convince** | 0.8 | Comparative data used to defend/advocate. "Actually ahead" = repositioning |

**Intent shift:** inform → convince, significance 0.5 (moderate)
**Shift trigger:** A's challenge ("seems slow") caused B to shift from neutral to defensive

---

### CT3: Ambiguous — Low Confidence

```
Context: Casual conversation
Message: "I noticed you've been spending a lot of time with the marketing team."
```

| Field | Expected |
|---|---|
| Primary | **test** |
| Secondary | **discover** |
| Confidence | **0.3** |
| Explanation | "Could be genuine curiosity, observation, probing, or implicit accusation. Insufficient context to determine. Most likely testing how the other person reacts." |

**Key point:** Low confidence is the CORRECT output. Not every message has a clear intent.

---

### CT4: Dual Intent — Support + Inform

```
Context: A just said they bombed a presentation
Message: "That sounds rough. Presentations are hard. You know what helped me?
Recording myself practicing. Want me to share some tips?"
```

| Field | Expected |
|---|---|
| Primary | **support** |
| Secondary | **inform** |
| Confidence | 0.8 |
| Explanation | "Opens with emotional validation (support), then transitions to practical advice (inform). Support-first, inform-second layering." |

---

### CT5: Hidden Intent — Connect surface, Request hidden

```
Context: A messages B after years of no contact
Message: "Hey! How have you been? It's been ages since we caught up!"
```

| Field | Expected |
|---|---|
| Primary | **connect** |
| Secondary | null |
| Confidence | 0.7 |
| Explanation | "Appears to be genuine reconnection." |

**Hidden intent check at this message:** None detectable yet. Surface and EI signals align.

**Hidden intent emerges later when A says:** "Hey, quick question — do you still have contacts at that VC firm?"
- Now the pattern reveals: A's real intent was **request**
- The Connect classification for early messages was correct AT THE TIME — hidden intent only became visible retrospectively

---

### CT6: Perform

```
Context: Team meeting
Message: "I just want to make sure everyone's voice is heard on this.
B, what do you think?"
```

| Field | Expected |
|---|---|
| Primary | **perform** |
| Secondary | **discover** |
| Confidence | 0.5 |
| Explanation | "Soliciting input could be genuine collaboration (discover) or performative inclusivity (perform). Mid-confidence — need to see if the input is actually incorporated." |

**Hidden intent (if next message dismisses the input):** Surface = discover/perform. Hidden = **control** (pre-decided, performing consultation).

---

### CT7: Process

```
Context: Personal conversation
Message: "I really want to take the job in Tokyo, but I also don't want
to leave my mom alone. She says go, but I can tell she doesn't mean it."
```

| Field | Expected |
|---|---|
| Primary | **process** |
| Secondary | null |
| Confidence | 0.85 |
| Explanation | "Thinking out loud about internal conflict. Not seeking advice (deflects solutions offered). Using conversation as processing space." |

---

### CT8: Control via Escalation

```
Context: Third exchange about a report error
Message: "I need you to own this. Fix the numbers or I'll have
to escalate to your manager."
```

| Field | Expected |
|---|---|
| Primary | **control** |
| Secondary | **request** |
| Confidence | 0.9 |
| Explanation | "Explicit directive with consequence. Escalation threat = control through pressure." |

---

### CT9: Co-create

```
Context: Brainstorming, energy building
Message: "Wait, it would also solve the migration problem we talked
about last week! We should build this."
```

| Field | Expected |
|---|---|
| Primary | **co_create** |
| Secondary | null |
| Confidence | 0.85 |
| Explanation | "Spontaneous connection to prior problem. Mutual excitement. Intent emerged from conversation, not pre-existing." |

---

### CT10: Avoid

```
Context: A asked what the board decided
Message: "We're still evaluating options."
```

| Field | Expected |
|---|---|
| Primary | **avoid** |
| Secondary | null |
| Confidence | 0.7 |
| Explanation | "Technically responsive but conveys zero information. Third consecutive non-answer. Strategic withholding." |


## Hidden Intent Test Cases

### HI1: Inform classified, Convince hidden

```
Classified intent: inform (confidence 0.7)
EI signals: SRI = invested, EF = strong positive, TI = extended
```

**Contradiction:** Inform should have low SRI + neutral EF. Invested SRI + strong positive EF = advocacy.

**Expected output:**
```json
{
  "hidden_intent_likely": "convince",
  "contradiction": "Classified as inform but high self-reference and strong evaluative force suggest advocacy",
  "gap_magnitude": 0.6
}
```

---

### HI2: Discover classified, Control hidden (manipulation)

```
Classified intent: discover (confidence 0.6)
EI signals: RD = absent (never surprised), SRI = present, EF = mild
Pattern: every question moves conversation toward same predetermined outcome
```

**Contradiction:** Genuine discover should show RD (surprise at answers). Absent RD + consistent direction = guiding, not discovering.

**Expected output:**
```json
{
  "hidden_intent_likely": "control",
  "contradiction": "Classified as discover but zero reactive disruption and consistent conversational direction suggest predetermined outcome",
  "gap_magnitude": 0.7
}
```

---

### HI3: Connect classified, Request hidden

```
Classified intent: connect (confidence 0.7)
EI signals: Low SRI, no TI, urgency appearing in later messages
Pattern: personal questions → bridge phrase → business ask
```

**Contradiction:** Genuine connect should have TI (ongoing relational investment). No TI + emerging urgency = instrumentalizing connection.

**Expected output:**
```json
{
  "hidden_intent_likely": "request",
  "contradiction": "Classified as connect but no temporal involvement and emerging urgency suggest relationship as vehicle for a request",
  "gap_magnitude": 0.5
}
```

---

### HI4: No Contradiction — Genuine Inform

```
Classified intent: inform (confidence 0.9)
EI signals: SRI = absent, EF = absent, TI = absent, RD = absent, US = absent
```

**No contradiction.** EI signals align with Inform classification. Low involvement + neutral evaluation = genuine neutral information sharing.

**Expected output:**
```json
{
  "hidden_intent_likely": null
}
```


## Intent Arc Test Cases

### ARC1: Funnel

```
Sequence: [discover, discover, discover, convince, request]
```

**Expected:** `{arc: "funnel", stages: ["discover", "convince", "request"]}`
**Interpretation:** Buyer's journey — learning → evaluating → asking.

---

### ARC2: Escalation

```
Sequence: [inform, inform, convince, convince, control]
```

**Expected:** `{arc: "escalation", from: "inform", to: "control"}`
**Interpretation:** Started neutral, challenged, escalated to directive.

---

### ARC3: De-escalation

```
Sequence: [control, convince, inform, support]
```

**Expected:** `{arc: "de_escalation", from: "control", to: "support"}`
**Interpretation:** Started directive, softened, ended with care.

---

### ARC4: Collapse

```
Sequence: [convince, convince, convince, avoid, avoid]
```

**Expected:** `{arc: "collapse", from: "convince", at: message_index_4}`
**Interpretation:** Tried to convince, gave up. Disengagement after failed advocacy.

---

### ARC5: Emergence

```
Sequence: [discover, inform, discover, co_create, co_create]
```

**Expected:** `{arc: "emergence", from: "discover"}`
**Interpretation:** Started exploring → something new emerged → both building together.

---

### ARC6: Recoil

```
Sequence: [connect, request, connect, connect]
```

**Expected:** `{arc: "recoil", base: "connect", attempted: "request"}`
**Interpretation:** Tried to make a request mid-connection, pulled back when it didn't land.

---

### ARC7: Stable

```
Sequence: [inform, inform, inform, inform]
```

**Expected:** `{arc: "stable", intent: "inform"}`
**Interpretation:** Straightforward information exchange. No shift.

---

### ARC8: Oscillation

```
Sequence: [process, support, process, support, process]
```

**Expected:** `{arc: "oscillation", between: ["process", "support"]}`
**Interpretation:** Alternating between expressing and being supported. Emotional conversation rhythm.


## Intent Mismatch Test Cases

### MM1: Complementary (no friction)

```
A's dominant intent: discover
B's dominant intent: inform
```

**Expected:** `{mismatch_type: "complementary", friction_level: 0.1}`
**Interpretation:** A asks, B answers. Different intents but aligned interaction.

---

### MM2: Friction

```
A's dominant intent: connect
B's dominant intent: request
```

**Expected:** `{mismatch_type: "friction", friction_level: 0.7}`
**Interpretation:** A wants relationship. B wants transaction. A feels used.

---

### MM3: Competing

```
A's dominant intent: discover
B's dominant intent: convince
```

**Expected:** `{mismatch_type: "competing", friction_level: 0.5}`
**Interpretation:** A is exploring. B is pushing. B's advocacy undermines A's exploration.

---

### MM4: Power Contest

```
A's dominant intent: control
B's dominant intent: control
```

**Expected:** `{mismatch_type: "power_contest", friction_level: 0.8}`
**Interpretation:** Both directing. Neither yielding.

---

### MM5: Level Mismatch

```
A's dominant intent: process
B's dominant intent: inform
```

**Expected:** `{mismatch_type: "level_mismatch", friction_level: 0.6}`
**Interpretation:** A needs emotional space. B gives data. Density-relevance gap at the intent level.


## Aggregation Test Cases

### AGG1: Cross-Topic Intent Profile

```
Conversation with 4 topics:

Topic 1 (technical):  A: inform → convince      B: discover
Topic 2 (personal):   A: connect                B: connect
Topic 3 (planning):   A: discover → request     B: avoid
Topic 4 (conflict):   A: control                B: support → avoid
```

**Level 4 output:**
```
Participant A:
  Primary intents: convince (technical), connect (personal), request (planning), control (conflict)
  Arc patterns: escalation on technical (inform → convince), funnel on planning (discover → request)
  Shift triggers: shifts to convince when challenged, shifts to control on conflict

Participant B:
  Primary intents: discover (technical), connect (personal), avoid (planning + conflict)
  Arc patterns: collapse on planning and conflict (→ avoid)
  Pattern: engages on knowledge and relationship, withdraws on decisions and confrontation
```

**APT relevance:** B avoids planning and conflict → fear-related withdrawal on high-stakes topics. A escalates when challenged → control-seeking under pressure.

### AGG2: Dyadic Arc Comparison

```
Topic 1:
  A's arc: discover → convince (escalation)
  B's arc: inform → inform (stable)

Dyadic: DIVERGING — A is pushing harder while B stays neutral.
```

```
Topic 3:
  A's arc: discover → request (funnel)
  B's arc: inform → avoid (collapse)

Dyadic: ASYMMETRIC — A is pursuing an ask, B is withdrawing.
```

**Combined dyadic reading:** A pursues, B withdraws under pressure. This pattern across multiple topics is a strong APT signal: A's intent escalation triggers B's avoidance. The relationship dynamic is pursuit/withdrawal.