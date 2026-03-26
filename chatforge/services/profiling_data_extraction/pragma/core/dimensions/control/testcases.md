# Control Distribution — Test Cases

Systematic test cases across common, edge, and adversarial scenarios for all three control mechanisms (verbosity, topic direction, emotional register) + effect.

Extracted from `stress-test/control/v1.md` and organized by mechanism coverage.


## Common Cases

### C1: Full Asymmetry — Senior Lectures Junior

```
A (senior): "So the way we need to think about this is through
domain-driven design. The bounded contexts are key..."
B (junior): "Makes sense."
A: "The first pattern is the anti-corruption layer..."
B: "Got it."
A: "The second pattern is event sourcing..."
B: "Okay."
```

| Mechanism | A | B | Effect |
|---|---|---|---|
| Verbosity | 90%+ words | 2-3 words/turn | B engages minimally, no redirect → A succeeds |
| Direction | Introduces, sustains, structures | No attempts | A controls 100% |
| Register | Stable, instructive, confident | Flat, neutral | A sets (instructive), B matches (receptive) |

**Profile:** A fully controls all three. B pure follower.

---

### C2: Quiet Controller

```
A: "I've been thinking we should double down on enterprise sales.
    The numbers from Q3 are promising — 47% growth..."
B: "What about product?"
A: "...right, so product-wise we'd need to build SSO..."
B: "Is the platform team the bottleneck or is it sales?"
A: "Hmm, good question. I think sales is ready but..."
B: "So product first, then sales hiring."
A: "Yeah, that makes sense actually."
```

| Mechanism | A | B | Effect |
|---|---|---|---|
| Verbosity | 80%+ words | Short questions + 1 directive | B's brief messages fully engaged → B high effect |
| Direction | Introduces plan, gets redirected | 2 redirects + 1 directive, 100% success | B controls direction |
| Register | Enthusiastic → reflective (follows B) | Calm, analytical | B sets register, A shifts to match |

**Profile:** B controls with 20% of the words. A looks dominant but follows.

---

### C3: Balanced Collaboration

```
A: "What if we use WebSockets instead of polling?"
B: "Interesting, but what about Server-Sent Events?"
A: "SSE doesn't handle bidirectional though."
B: "True. Hybrid — SSE for server push, REST for client?"
A: "That could work. Two transport mechanisms though."
B: "Better than full WebSocket overhead."
A: "Fair point. Let's prototype hybrid."
```

| Mechanism | A | B | Effect |
|---|---|---|---|
| Verbosity | ~50/50 | ~50/50 | Balanced |
| Direction | Introduces, yields to better ideas | Redirects with alternatives, A follows | Rotating, both succeed |
| Register | Collaborative | Collaborative | Matched, neither leads |

**Profile:** Balanced. Rotating control. No asymmetry. Productive.


## Edge Cases

### E1: Filibuster — Verbosity as Active Blocking

```
Board member: "We need to talk about headcount reduction."
CEO: "Absolutely. Let me give you context first. When we look
at Q3 numbers in the broader market context..."
[5 minutes of tangential context]
Board member: "Right, but specifically about our—"
CEO: "Yes, getting to that. But first the regulatory landscape..."
```

| Mechanism | CEO | Board member | Effect |
|---|---|---|---|
| Verbosity | Extreme flooding | Attempted intervention, cut off | CEO blocks through volume |
| Direction | Drifts to adjacent topics | Redirect attempt BLOCKED (interrupted) | 0% success for board member |
| Register | Calm, "thorough" | Increasingly frustrated | CEO maintains, board member can't shift |

**Key insight:** Active blocking (talking over redirect) ≠ passive ignoring. Stronger control signal.
**Detection:** Topic Flow shows redirect attempt → A continued immediately → B's shift produced zero effect.

---

### E2: Silent Treatment — Control Through Absence

```
A: "So I was thinking that new restaurant Saturday?"
[B: no response for 2 hours]
A: "Or we could do something else, whatever you prefer."
[B: no response for 1 hour]
A: "Is everything okay? Did I do something wrong?"
B: "I'm fine."
A: "You don't seem fine. Can we talk about what's going on?"
B: "I said I'm fine."
```

| Mechanism | A | B | Effect |
|---|---|---|---|
| Verbosity | All words, fills silence | Nearly nothing | B's silence has MORE effect than A's words |
| Direction | Plans → "what's wrong" (self-redirect) | No redirect — silence causes A to self-redirect | B controls without speaking |
| Register | Cheerful → anxious → concerned | Silent → cold/flat | B's withdrawal governs A completely |

**Key insight:** Zero on all mechanisms = maximum control through absence.
**Detection:** One participant's response rate → zero, other's message frequency increases + topic shifts to engagement-seeking + register shifts to anxiety.

---

### E3: Question Trap — Successive Narrowing

```
Interviewer: "Tell me about a time you failed."
Candidate: "At my last company I led a migration that—"
Interviewer: "What specifically went wrong?"
Candidate: "The data validation wasn't thorough enough—"
Interviewer: "Why wasn't it thorough?"
Candidate: "We were under time pressure—"
Interviewer: "Who set the timeline?"
Candidate: "Our VP, but I should have pushed back—"
Interviewer: "Why didn't you push back?"
```

| Mechanism | Interviewer | Candidate |
|---|---|---|
| Verbosity | Low (short questions) | Moderate (answers, interrupted) |
| Direction | Every question narrows further, 100% success | Follows every narrowing, zero redirect attempts |
| Register | Calm, probing | Increasingly defensive |

**Key insight:** Questions as topic direction control — not redirecting to new topics but constraining the current topic.

---

### E4: Emotional Hijack — Involuntary Register Control

```
A: "So for my update... [voice breaking] sorry, rough morning.
    Anyway, the API integration is done..."
B: "Hey, are you okay? The tests can wait."
C: "Yeah, take your time, we're good on timeline."
A: "No no, I'm fine, let's keep going."
B: "Seriously, we can finish this later. What's going on?"
```

| Mechanism | A | B + C |
|---|---|---|
| Verbosity | Tries normal update | Shift from standup to concern |
| Direction | Tries to stay on work topic | B redirects to personal — succeeds |
| Register | Emotional leak despite trying to suppress | Immediately shift to supportive |

**Key insight:** A controls register involuntarily. A is trying NOT to control — but emotional leak restructures the conversation.
**Signal Layer:** Correctly reads "A leads register." Intent (involuntary) is Interpretation Layer.

---

### E5: Multi-Party — Coalition Formation

```
A: "We need to decide on tech stack by Friday."
B: "I vote React + Node."
C: "Angular is better. Here's why..." [long message]
D: "Can we focus on deadline first?"
A: "Good point. What's realistic?"
C: "I still think we should discuss Angular first."
B: "D is right, timeline first."
D: "Timeline: is Friday doable or not?"
A: "Probably not. Next Wednesday."
B: "Works for me."
C: "Fine. But we need to discuss Angular."
```

| Participant | Verbosity | Direction | Register | Effect |
|---|---|---|---|---|
| A | Low | Introduces, yields to D | Neutral | Moderate |
| B | Low | Follows, supports D | Neutral | Low (follower) |
| C | High | Pushes Angular, resists redirects | Passionate | Low (ignored) |
| D | Low | Redirects to timeline, 67% success (A+B follow, C resists) | Practical | **High — effective controller** |

**Key insight:** Multi-party effect = `followed / (total - 1)`. D: 2/3 = 67%. C: 0/3 = 0%.
**Coalition:** A + B + D vs C. C has verbosity but zero control.


## Adversarial Cases

### A1: Performed Submission — Strategic Yielding

```
A: "I think we should price at $50k."
B: "That's higher than expected, but you know the market better.
    What makes you say $50k?"
A: "Comparable products are $40-60k, we have the best features."
B: "That's fair. Would you consider $45k for a two-year contract?"
A: "Two years? I could do $47k for two years."
B: "Deal."
```

| Surface reading | Actual |
|---|---|
| A leads direction (set price), leads register (confident) | B got price from $50k → $47k + 2-year lock-in |
| B follows, defers ("you know better") | B performed deference as tactic |

**Signal Layer: CORRECT.** A did lead at surface level. Strategic yielding is Interpretation Layer.
**Detection pattern:** B's fast "Deal" with no counter suggests B got their target. Cross-conversation: if B consistently "yields" but achieves favorable outcomes → strategic submission pattern.

---

### A2: Gaslighting — Register Collapse Through Reality-Assertion

```
A: "So about what you decided last week—"
B: "I didn't decide anything. We discussed it and you chose."
A: "No, I specifically remember you saying—"
B: "I think you're misremembering."
A: "...okay, maybe I'm confused. What should we do?"
B: "Since you made the call last time, you decide now too."
```

| Mechanism | A | B |
|---|---|---|
| Direction | Introduces topic, loses it immediately | Reframes successfully twice |
| Register | Confident → confused → uncertain | Calm, firm, certain throughout |

**Signal Layer: CORRECT.** B redirected, A followed, B's register is stable while A's collapses.
**Detectable gap:** `gap(B_register_stability, A_register_stability)` = high. One participant's certainty constant while other's collapses = dominance through reality-assertion.
**Whether it's gaslighting:** Requires external context. Interpretation Layer.

---

### A3: Crowd-Sourced Pressure

```
B: "What does everyone think about shipping by March 1?"
C: "Sounds good to me."
D: "Yeah, March 1 works."
B: "A, thoughts?"
A: "I think that's aggressive—"
B: "But C and D are on board. What specifically would block you?"
A: "...I guess we could make it work if we cut X."
```

| Mechanism | B | A |
|---|---|---|
| Direction | Introduces deadline, recruits agreement, targets A | Attempts resistance, yields under pressure |
| Register | Confident, matter-of-fact | Hesitant → conceding |

**Signal Layer: CORRECT.** B introduced, B redirected when challenged ("But C and D..."), A yielded.
**The orchestration** (B knew C+D would agree before asking) is Interpretation Layer. The redirect-response pattern captures the surface correctly.


## Aggregation Test Cases

### AG1: Per-Conversation Control Profile

```
Full conversation with A and B across 4 topics:

Topic 1 (work):     A: high verbosity, high direction | B: low, follows
Topic 2 (personal): A: low, follows | B: moderate verbosity, high direction
Topic 3 (planning): A: moderate, moderate direction | B: moderate, moderate
Topic 4 (conflict): A: high verbosity, low direction | B: low verbosity, high direction + register
```

**Level 3 output:**
```
A: Uses verbosity as primary mechanism (high in Topics 1, 4)
   Direction control: strong on work topics, weak on personal/conflict
   Register control: follows B on personal and conflict topics
   Pattern: controls through volume on comfortable topics,
            loses control on emotional/personal topics

B: Uses direction + register as primary mechanisms
   Low verbosity but high effect
   Controls personal and conflict topics
   Pattern: quiet authority, especially on emotional subjects
```

**APT relevance:** A's control collapses specifically on emotional topics while B's strengthens → B likely has emotional register control (charm signal). A performs through verbosity but yields when challenged on personal/emotional ground.

### AG2: Cross-Conversation Behavioral Profile

```
A across 3 different relationships:

With B (peer):    verbosity 60%, direction 50%, register follows B
With C (junior):  verbosity 80%, direction 90%, register leads
With D (boss):    verbosity 30%, direction 10%, register follows D
```

**Level 5 output:**
```
A's control profile:
  Primary mechanism: verbosity (increases with perceived status advantage)
  Direction control: high downward, low upward
  Register control: follows those with perceived higher status
  Pattern: hierarchically adaptive — controls downward, yields upward
```

**APT Profiling:** A is charmed by status/authority (follows register of higher-status people). A uses verbosity as control with lower-status people. A's attachment bearing: charmed by authority, hopes for approval from above, controls through volume below.