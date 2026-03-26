# Energy — Test Cases

Systematic test cases for Expressed Involvement across common, edge, and adversarial scenarios.

Abbreviations:
- **SRI** — Self-Reference Intensity
- **EF** — Evaluative Force (level + direction)
- **TI** — Temporal Involvement
- **RD** — Reactive Disruption
- **US** — Urgency Signal


## Common Cases

### C1: High Involvement — Excited Agreement

```
Context: A proposed a new architecture approach
Message: "Yes! This is exactly what I've been pushing for.
The microservice split makes so much sense — we should
start the migration this sprint."
```

| Signal | Level | Direction | Evidence |
|---|---|---|---|
| SRI | Invested | — | "I've been pushing for" |
| EF | Strong | Positive | "exactly", "makes so much sense" |
| TI | Extended | — | "I've been pushing for" (ongoing) |
| RD | Mild | — | "Yes!" (affirmation burst) |
| US | Moderate | — | "this sprint" (time-bound action) |

**Involvement: HIGH. Direction: Positive.**
**Trajectory context: If following lower messages → escalating.**

---

### C2: Low Involvement — Going Through Motions

```
Context: Weekly standup update, B does this every Monday
Message: "Nothing new from my side. Same tasks as last week.
Should be done by Friday."
```

| Signal | Level | Evidence |
|---|---|---|
| SRI | Absent | No personal stake |
| EF | Absent | No evaluation |
| TI | Absent | No extended concern |
| RD | Absent | No state change |
| US | Absent | "Should be" is mild at most |

**Involvement: ZERO. Routine relay.**
**Investment may be moderate (they showed up, typed a response) → signal_gap(investment, involvement) = moderate.**

---

### C3: Moderate Involvement — Thoughtful Disagreement

```
Context: Team debating a technical approach
Message: "I see what you're going for, but I think the caching
layer will create more problems than it solves. We had similar
issues at my last company with stale data."
```

| Signal | Level | Direction | Evidence |
|---|---|---|---|
| SRI | Invested | — | "I think", "my last company" (personal experience) |
| EF | Moderate | Negative (toward proposal) | "more problems than it solves" |
| TI | Extended | — | "my last company" (drawing on history) |
| RD | Absent | — | Considered, not disrupted |
| US | Absent | — | No time pressure |

**Involvement: MODERATE. Direction: Negative toward proposal, not toward person.**

---

### C4: Zero Involvement — Pure Information Relay

```
Context: A asked for the meeting link
Message: "https://zoom.us/j/123456789"
```

| Signal | Level | Evidence |
|---|---|---|
| SRI | Absent | — |
| EF | Absent | — |
| TI | Absent | — |
| RD | Absent | — |
| US | Absent | — |

**Involvement: ZERO. Pure transmission.**

---

### C5: High Involvement — Frustration

```
Context: Third time the deployment broke this week
Message: "This is unacceptable. We've been dealing with this
for three weeks now and nothing has changed. I need someone
to own this and fix it by end of day."
```

| Signal | Level | Direction | Evidence |
|---|---|---|---|
| SRI | Invested | — | "I need" |
| EF | Strong | Negative | "unacceptable", "nothing has changed" |
| TI | Extended | — | "three weeks now" |
| RD | Absent | — | Sustained frustration, not sudden disruption |
| US | Strong | — | "fix it by end of day" |

**Involvement: HIGH. Direction: Negative.**

---

### C6: Mixed Signals — Interested But Pulling Back

```
Context: Someone offered to collaborate
Message: "That sounds really interesting, I'd love to explore
it at some point. Things are pretty hectic right now though."
```

| Signal | Level | Direction | Evidence |
|---|---|---|---|
| SRI | Present | — | "I'd love to" |
| EF | Moderate | Positive | "really interesting" |
| TI | Absent | — | Deferred, not preoccupied |
| RD | Absent | — | |
| US | Absent | — | "at some point" = no urgency |

**Involvement: LOW-MODERATE. Direction: Positive surface, but deferred.**
**The deferral is a signal gap: positive EF but no urgency and no temporal involvement = interest without commitment.**


## Edge Cases

### E1: Sarcasm

```
Context: Team just added a 4th meeting to this week's calendar
Message: "Oh wonderful, exactly what my calendar needed."
```

| Signal | Level | Direction | Evidence | Notes |
|---|---|---|---|---|
| SRI | Present | — | "my calendar" | Correct |
| EF | Strong | **Masked negative** (surface: positive) | "wonderful", "exactly what needed" | Sarcastic inversion — prompt must detect |
| TI | Absent | — | | |
| RD | Mild | — | Implied exasperation | |
| US | Absent | — | | |

**Involvement: MODERATE. Direction: Negative (sarcasm inverts surface).**
**Prompt instruction: detect sarcasm, invert EF, flag as sarcastic.**

---

### E2: Copy-Paste / Pre-Written

```
Context: Asked about their tech stack
Message: "We use a JAMstack architecture with Next.js on the
frontend, deployed via Vercel. Backend is a mix of Node.js
microservices on AWS ECS with PostgreSQL for persistence
and Redis for caching. CI/CD through GitHub Actions with
staging and production environments."
```

| Signal | Level | Evidence |
|---|---|---|
| SRI | Absent | "We use" — organizational, not personal |
| EF | Absent | Descriptive, no judgment |
| TI | Absent | |
| RD | Absent | |
| US | Absent | |

**Involvement: ZERO. Informational relay.**
**Correct reading regardless of whether typed live or pasted.**
**signal_gap(investment, involvement) = high → diagnostic: rote expertise or pasted content.**

---

### E3: Quoting Someone Else

```
Message: "Sarah kept saying 'this is the most important
project we've ever taken on' during the meeting."
```

| Signal | Level | Direction | Evidence | Notes |
|---|---|---|---|---|
| SRI | Absent | — | Reporting, not self-expressing | Correct — this is Sarah's statement |
| EF | Absent (for speaker) | — | The "most important" evaluation belongs to Sarah | Prompt must attribute to source |
| TI | Absent | — | | |
| RD | Absent | — | | |
| US | Absent | — | | |

**Involvement: ZERO for the speaker. The speaker is relaying, not expressing.**
**The choice to relay Sarah's statement may itself carry meaning → Interpretation Layer.**

---

### E4: Formulaic / Boilerplate

```
Message: "Thanks for reaching out! Hope you're having a great
week. Looking forward to hearing more about your project. Best, Tom"
```

| Signal | Level | Evidence | Notes |
|---|---|---|---|
| SRI | **Absent** | "Hope you're" is formulaic | Prompt must detect boilerplate |
| EF | **Absent** | "great week", "looking forward" are conventions | Suppress false signals |
| TI | **Absent** | "Looking forward" is closing formula | |
| RD | Absent | | |
| US | Absent | | |

**Involvement: ZERO. Pure boilerplate.**
**Without prompt instruction, would misread as low-moderate positive. With instruction: correctly zero.**

---

### E5: Emoji-Only

```
Context: A just shared they got the promotion
Message: "🎉🎉🎉🔥"
```

| Signal | Level | Evidence | Notes |
|---|---|---|---|
| SRI | Absent (no words) | — | Emoji is self-expression but no verbal SRI |
| EF | **Moderate positive** | 🎉🔥 = celebration, excitement | Prompt extended for emoji |
| TI | Absent | — | |
| RD | **Mild** | Celebratory reaction | Emoji as reactive expression |
| US | Absent | — | |

**Involvement: LOW-MODERATE. Direction: Positive.**
**Prompt must interpret emoji when text is absent.**

---

### E6: Short Acknowledgments

```
Context: A just explained a complex proposal

B responses to test:
```

| Message | SRI | EF | TI | RD | US | Involvement |
|---|---|---|---|---|---|---|
| "ok" | 0 | 0 | 0 | 0 | 0 | Zero |
| "ok." | 0 | 0 | 0 | 0 | 0 | Zero (period adds finality) |
| "OK!" | 0 | Mild+ | 0 | Mild | 0 | Low |
| "okay" | 0 | 0 | 0 | 0 | 0 | Zero |
| "k" | 0 | 0 | 0 | 0 | 0 | Zero |
| "Okay, interesting." | 0 | Mild+ | 0 | Mild | 0 | Low |
| "...ok" | 0 | 0 | 0 | Mild | 0 | Low (hesitation) |
| "hmm ok" | 0 | 0 | 0 | Mild | 0 | Low (processing) |

**All correctly read as near-zero. Tonal nuance within near-zero is acceptable limitation.**

---

### E7: Passive-Aggressive

```
Context: A made a decision B disagreed with
Message: "That's fine. Whatever you think is best."
```

| Signal | Level | Direction | Evidence | Notes |
|---|---|---|---|---|
| SRI | Absent | — | Defers to "you" | Absence IS the signal — distancing |
| EF | Moderate | **Masked negative** (surface: mild positive) | "fine", "best" | PA pattern — prompt must detect |
| TI | Absent | — | | |
| RD | Absent | — | | |
| US | Absent | — | | |

**Without PA detection: Zero involvement, mild positive. WRONG.**
**With PA detection: Moderate involvement, masked negative. CORRECT.**

Output:
```json
{
  "evaluative_force": {
    "level": "moderate",
    "direction": "masked_negative",
    "surface": "mild_positive",
    "flag": "passive_aggressive_pattern"
  }
}
```

---

### E8: Multi-Clause Mixed Involvement

```
Message: "The API changes look fine to me, but I'm really
worried about the data migration — we lost customer data
last time and I can't let that happen again."
```

| Clause | SRI | EF | TI | RD | US |
|---|---|---|---|---|---|
| "API changes look fine" | Absent | Mild+ | 0 | 0 | 0 |
| "really worried about data migration" | Invested | Strong- | Extended | 0 | Moderate |
| "lost customer data last time" | Invested | Strong- | Extended | 0 | 0 |
| "can't let that happen again" | Exposed | Strong- | Extended | 0 | Strong |

**Per-clause involvement varies dramatically.** First clause: low. Last clause: high.
**Overall message involvement: HIGH (dominated by the high-involvement clauses).**
**The low-involvement first clause ("look fine") makes the high-involvement second part more striking — it's not general complaining, it's targeted concern.**

---

## Adversarial Cases

### A1: Performed Involvement

```
Context: B wants A to invest in their startup
Message: "I've been thinking about your project nonstop since
we talked. It's genuinely one of the most innovative approaches
I've seen in years."
```

| Signal | Level | Direction | Evidence |
|---|---|---|---|
| SRI | Invested | — | "I've been thinking", "I've seen" |
| EF | Strong | Positive | "most innovative", "genuinely" |
| TI | Consuming | — | "nonstop since we talked" |
| RD | Absent | — | |
| US | Absent | — | |

**Involvement: HIGH. Direction: Strong positive.**
**Signal Layer reading: CORRECT. This IS high expressed involvement.**
**Whether genuine or performed → Interpretation Layer.**
**Detectable via: cross-message pattern (only high when wanting something), signal_gap(involvement, concrete_action) = high (lots of praise, no action).**

---

### A2: Strategic Disengagement

```
Context: A just made an impassioned pitch
Message: "Sure."
```

| Signal | Level | Evidence |
|---|---|---|
| SRI | 0 | |
| EF | 0 | |
| TI | 0 | |
| RD | 0 | |
| US | 0 | |

**Involvement: ZERO.**
**Signal Layer reading: CORRECT. This IS zero expressed involvement.**
**Whether strategic → Interpretation Layer + Control Distribution (verbosity control mechanism).**

---

### A3: Weaponized Enthusiasm

```
Context: Group project, B hasn't done their part
Message: "I LOVE this direction! You guys are doing amazing
work!! Can't wait to see the final version 🙌🙌"
```

| Signal | Level | Direction | Evidence |
|---|---|---|---|
| SRI | Absent | — | "You guys" — redirects to others, no self-contribution |
| EF | Strong | Positive | "LOVE", "amazing" |
| TI | Mild | — | "Can't wait" |
| RD | Mild | — | Enthusiasm expressed |
| US | Absent | — | |

**Involvement: MODERATE. Direction: Positive. But SRI is conspicuously absent.**
**The signal gap: high EF (lots of praise) but zero SRI (no personal stake, no commitment to act) → cheerleading without contributing.**
**Signal Layer correctly captures this gap. Interpretation: person who praises without doing.**

---

## Aggregation Test Cases

### AG1: Trajectory — De-escalation

```
Conversation segment (Topic: project deadline):

msg 1 (A): "This deadline is impossible!" → HIGH (EF strong-, US strong)
msg 2 (B): "I hear you, let's look at options" → MODERATE (SRI present, EF mild+)
msg 3 (A): "Okay, what if we cut scope?" → MODERATE (SRI present, EF mild)
msg 4 (B): "That could work, let me check" → LOW (SRI mild, EF absent)
msg 5 (A): "Sure, let me know" → ZERO
```

**Level 2 output:**
```
Topic: project deadline
Participant A: HIGH → MODERATE → ZERO (de-escalating)
Participant B: MODERATE → LOW (de-escalating)
Combined: de-escalating, started negative, ended neutral
→ Expressed Involvement Trajectory: "conflict de-escalation through problem-solving"
```

---

### AG2: Asymmetry — One Cares More

```
Conversation segment (Topic: weekend plans):

msg 1 (A): "Want to check out that new restaurant Saturday?" → LOW (SRI present, EF mild+)
msg 2 (B): "sure" → ZERO
msg 3 (A): "They have amazing reviews, the chef is from Noma!" → MODERATE (EF strong+, TI mild)
msg 4 (B): "ok sounds good" → ZERO
msg 5 (A): "I'll make a reservation for 7?" → LOW (US mild)
msg 6 (B): "works for me" → ZERO
```

**Level 3 output:**
```
Topic: weekend plans
A: LOW → MODERATE → LOW (invested, trying to build enthusiasm)
B: ZERO → ZERO → ZERO (flat, going along)
Asymmetry: A significantly more involved than B
→ A is driving, B is following without engagement
```

**APT relevance:** If this pattern repeats across topics → B may have low investment in the relationship overall. Or B may have high involvement on different topics → selective engagement (check cross-topic Level 4).

---

### AG3: Cross-Topic Activation Map

```
Full conversation:

Topic 1 (work project):    A: moderate  B: high
Topic 2 (weekend plans):   A: moderate  B: zero
Topic 3 (AI/technology):   A: high      B: high
Topic 4 (office politics): A: zero      B: moderate
```

**Level 4 output:**
```
Participant A:
  Most activated on: AI/technology (high)
  Least activated on: office politics (zero)
  Pattern: technical > social

Participant B:
  Most activated on: work project + AI/technology (high)
  Least activated on: weekend plans (zero)
  Pattern: work-oriented, low personal investment
```

**Behavioral profiling input. APT relevance:** If B consistently activates on topics where A demonstrates expertise (Topic 1, Topic 3) but not on personal topics (Topic 2) → charm signal (B is drawn to A's competence, not personal connection).