# Control Distribution — Full Definition

**PRAGMA Dimension: Control Distribution (output name)**
**Measurement: Three mechanisms + effect (no atomic semantic unit needed)**

**One-sentence definition:** Control measures who determines what happens next in the conversation, through three independent mechanisms (verbosity, topic direction, emotional register), each with a measurable success rate.


## What Control Is

Control = who determines what happens next. Not who talks more, not who looks dominant. The person asking one redirecting question can have more control than the person who spoke for five minutes — if the other person follows the redirect.

**Critical distinction: dominance ≠ control.**

| Concept | What it looks like | What it actually is |
|---------|-------------------|---------------------|
| **Dominance** | Lots of words, explaining, holding the floor | Observable behavior — may or may not correspond to control |
| **Control** | Who determines direction, topic, emotional register | Measured by mechanism attempts + success rate |
| **Frame control** | Who is evaluating whom, whose reality governs | Emergent from pattern of all mechanisms — Interpretation Layer |


## The Three Control Mechanisms

Control operates through three independent mechanisms, each measuring a different dimension of conversation:

### 1. Verbosity Control — HOW MUCH is said

Who takes conversational space and do others engage with that content.

**Mechanism signals** (from Message Properties):
- Word count ratio between participants
- Message count ratio
- Consecutive messages without response (monologue)
- Space taken per topic segment

**Effect** (did it work?):
- Did the other person engage with the verbose content (respond to specific points, follow up)?
- Or did they redirect, ignore, or respond briefly?
- Success rate: `engaged_responses / total_verbose_turns`

### 2. Topic Direction Control — WHAT is discussed

Who determines the subject matter and do others follow.

**Mechanism signals** (from Topic Flow + Dialogic Function):
- Redirect attempts (explicit topic shifts, divergent questions)
- Topic introductions
- Topic blocking (continuing own topic when other tries to shift)
- Topic abandonment (dropping a topic the other participant is sustaining)

**Effect** (did it work?):
- Did the other person follow the redirect (yield)?
- Or did they hold their current topic, counter-redirect, or ignore?
- Success rate: `redirects_followed / redirect_attempts`

**Active blocking vs passive non-following:** When someone talks over a redirect attempt (actively preventing the shift), that's a stronger control signal than simply not acknowledging a redirect. Detectable through Topic Flow: B's shift attempt occurs → A continues own topic immediately → B's shift produces zero effect.

### 3. Emotional Register Control — HOW IT FEELS

Who sets the emotional tone and do others' emotional states follow.

**Mechanism signals** (from Expressed Involvement):
- Emotional state shifts (evaluative force direction changes, intensity shifts)
- Tone-setting moves (introducing humor into serious discussion, getting serious in light conversation)

**Effect** (did it work?):
- Did the other person's emotional state shift to match within 1-2 messages?
- Or did they hold their own emotional register?
- Success rate: `shifts_followed / shifts_initiated`

**Detection:**
```
A's evaluative force:  pos → pos → NEG → neg → POS
B's evaluative force:  pos → pos → pos → NEG → POS
                                          ↑      ↑
                                   B followed  B followed
                                   A's neg     A's pos
                                   (1 msg lag) (immediate)

→ A leads emotional register (B follows A's shifts)
```

**Emotional register is the strongest charm indicator.** You can consciously resist someone's topics and their verbosity, but if their mood shifts pull your mood with them, they have you. Emotional following is less conscious and harder to resist than topic following.

### Special Case: Silence as Control

Zero on all three mechanisms can be more controlling than high on all three. When one participant goes silent and the other's behavior becomes reactive:
- Increasing message frequency
- Topic shifts toward engagement-seeking ("is everything okay?")
- Emotional register shifts to concern/anxiety

→ The silent participant controls through absence.

Detection: Message Properties shows one participant's response rate drops to zero/near-zero AND the active participant exhibits the reactive behavior pattern above.

### Independence of Mechanisms

The three mechanisms are genuinely independent — any combination is possible:

| Verbosity | Direction | Register | What it looks like |
|---|---|---|---|
| A | A | A | Full control — lecturing with authority, sets the mood |
| A | A | B | A talks and steers, but B sets the emotional tone |
| A | B | A | A talks a lot and sets the tone, but B picks what A talks about |
| Low | B | A | Quiet authority — A says little, B picks topics, but A's mood governs |
| B | B | A | B runs the content, but A's emotional shifts pull B along (charm) |
| Low | Low | A | Pure emotional influence — doesn't talk much, doesn't steer topics, but their mood infects the other person |


## Aggregation Hierarchy

```
LEVEL 1: Per exchange (redirect-response pair / verbosity turn / emotional shift)
──────────────────────────────────────────────
  What happened: B redirected, A followed. A sent long message, B engaged.
  A shifted mood, B matched.

LEVEL 2: Per topic segment, per participant
──────────────────────────────────────────────
  Per-mechanism scores within this segment:
    Verbosity: A 72%, effect 60%
    Direction: A 2 attempts (1 success), B 1 attempt (1 success)
    Register: A 1 shift (0 followed), B 2 shifts (2 followed)

LEVEL 3: Per conversation, per participant
──────────────────────────────────────────────
  Full control profile across all segments:
    A: high verbosity, moderate direction, low register control
    B: low verbosity, high direction success, high register control
    → B controls despite A's volume

LEVEL 4: Frame control (Interpretation Layer)
──────────────────────────────────────────────
  Emergent from all three mechanisms + effects:
    "B runs the conversation. A performs for B."
  Query-driven, confidence-scored.

LEVEL 5: Cross-conversation, per participant (Behavioral Profiling)
──────────────────────────────────────────────
  Stable control patterns:
    "A tends to use verbosity as primary mechanism. Moderate
     effectiveness. Yields direction and register when challenged."
    "B controls primarily through emotional register and selective
     direction. Low verbosity, high influence."
```

### Multi-Party Aggregation

In conversations with more than two participants, effect computation uses proportion of group:

`control_effect = participants_who_followed / (total_participants - 1)`

Coalition dynamics: when the group splits on who to follow, the alliances that form are a relational signal visible only in multi-party conversations.


## Dependencies

| Dependency | What it provides | Required? |
|---|---|---|
| **Message Properties** | Word counts, response latency, message frequency, silence detection | Yes — verbosity mechanism |
| **Topic Flow** | Redirect events, topic attribution, segment boundaries | Yes — direction mechanism |
| **Dialogic Function** | Question/challenge/affirm classification for redirect typing | Yes — direction mechanism |
| **Expressed Involvement** | Evaluative force trajectory for emotional register comparison | Yes — register mechanism |


## Downstream Consumers

| Consumer | What it takes | Level |
|---|---|---|
| **Dynamics Profile** | Control Distribution dimension (per segment) | Level 2 |
| **Interpretation Layer** | Frame control query — "who is running the show?" | Level 4 |
| **APT Inference** | Control mechanism patterns → charm/hope/fear | Level 2-3 |
| **Behavioral Profiling** | Stable control style across conversations | Level 5 |
| **Signal Gaps** | gap(verbosity, direction_effect), gap(involvement, control_effect) | Level 2-3 |


## Connection to APT

Control patterns are primary APT signals. How someone yields or holds control reveals attachment type:

| Control pattern | APT signal |
|---|---|
| B yields topic direction voluntarily, high involvement when following A | **Charm** — B follows because impressed |
| B follows A's emotional register shifts (mood contagion) | **Charm** — strongest indicator |
| A yields topic direction on benefit-related topics only | **Hope** — A follows when there's something to gain |
| B yields despite low involvement, avoids counter-redirecting | **Fear** — B follows because can't afford not to |
| A's verbosity increases when B redirects (tries harder) | **Charm (reversed)** — A is performing for B |
| B follows A's register but resists topic direction | **Charm without hope** — emotionally drawn but not seeking benefit |
| B's success rate is near-100% on all three mechanisms | **Frame control** — B runs the show |

**Getting control wrong inverts APT inferences.** If the system reads A's verbosity as control when actually A is performing for B's approval AND following B's emotional register, the charm inference reverses completely.


## Does Control Need Its Own Atomic Semantic Unit?

**No.** Unlike energy (which needed Expressed Involvement because speaker activation is irreducibly semantic), control's three mechanisms are measurable from existing signals:

- **Verbosity**: word count ratios, message count ratios (mechanical, from Message Properties)
- **Topic direction**: redirect events (from Topic Flow) + response classification (from Dialogic Function)
- **Emotional register**: emotional state shifts (from Expressed Involvement) + trajectory comparison between participants
- **Effect (all three)**: response analysis — did the other person follow or resist? (from respective signals)

What control needs:
1. **Effect computation** — for each mechanism, did it succeed?
2. **Emotional shift comparison** — comparing Expressed Involvement trajectories between participants
3. **Silence pattern detection** — recognizing control through absence
4. **Semantic quality assessment** — voluntary vs reluctant yielding (selective LLM, enrichment only)
5. **Frame control as Interpretation Layer query** — emergent from pattern of all three mechanisms


## What Control Does NOT Cover

- **Why** someone yields or holds control — Interpretation Layer
- **Whether** yielding is genuine or strategic — Interpretation Layer (expressed-vs-felt principle)
- **What** they're controlling about (content) — CPDE-7
- **Frame control** — emergent from mechanisms pattern, not directly measured
- **Strategic manipulation** (gaslighting, crowd pressure, performed submission) — detectable as signal gaps and patterns, interpreted by Interpretation Layer