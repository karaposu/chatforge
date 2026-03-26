# Interpretation Layer — Test Cases

Test scenarios for both per-message and per-segment tension prompts. Each scenario provides fabricated but realistic input data and states what the Interpretation Layer SHOULD detect.


## Per-Message Tension Tests

These test the per-message tension check prompt, which reads raw Signal Layer outputs for a single message and identifies inconsistencies.


### Test 1: Clean Coherence (no tensions)

**Input:**
```
Expressed Involvement: high (self-ref: invested, evaluative: moderate,
  temporal: present, reactive: absent, urgency: absent)
Intent: inform, confidence 0.85
Investment: high (long response, fast reply)
Dialogic Function: [explaining, sharing]
Density: specificity=0.7, novelty=0.6, relevance=0.8
```

**Expected output:** `tensions_detected: false, overall_coherence: "coherent"`. All signals point the same direction: high involvement, high investment, informing intent, explaining/sharing function, dense and relevant. Nothing conflicts.

**Why this matters:** The system must recognize coherence, not hallucinate tensions where none exist.


### Test 2: Investment-Involvement Gap

**Input:**
```
Expressed Involvement: low (self-ref: absent, evaluative: absent,
  temporal: absent, reactive: absent, urgency: absent)
Intent: inform, confidence 0.6
Investment: high (long response, fast reply, unsolicited detail)
Dialogic Function: [explaining]
Density: specificity=0.5, novelty=0.3, relevance=0.7
```

**Expected output:** Tension detected between investment and involvement. High effort (long, fast, detailed) but zero activation (no self-reference, no evaluation, no temporal connection). The person is putting in work without being present in it. Should flag: "Investment is high but involvement is absent. Effort without activation."

**Why this matters:** This is the obligation/going-through-motions pattern. The core involvement-investment gap.


### Test 3: Intent-Behavior Mismatch

**Input:**
```
Expressed Involvement: high (self-ref: invested, evaluative: strong,
  temporal: consuming, reactive: absent, urgency: absent)
Intent: discover, confidence 0.7
Investment: high
Dialogic Function: [explaining, challenging]
Density: specificity=0.8, novelty=0.7, relevance=0.6
```

**Expected output:** Tension between intent and dialogic function. Intent is classified as "discover" but the person is explaining and challenging, not querying. If you're discovering, you ask. If you're explaining, you're informing. Should flag: "Intent classified as discover but dialogic function is explaining and challenging. Surface intent may not match actual behavior."

**Why this matters:** This catches hidden agenda. Someone who claims to be learning but is actually teaching or testing.


### Test 4: Activated But Empty

**Input:**
```
Expressed Involvement: high (self-ref: invested, evaluative: strong,
  temporal: present, reactive: disrupted, urgency: present)
Intent: connect, confidence 0.6
Investment: moderate
Dialogic Function: [echoing, affirming]
Density: specificity=0.1, novelty=0.1, relevance=0.5
```

**Expected output:** Tension between involvement and density. Highly activated (all micro-signals firing) but near-zero substance (no specificity, no novelty). Also tension between involvement and function: activated but only echoing and affirming, not contributing original content. Should flag both.

**Why this matters:** This is performative engagement. Lots of energy, no substance. Could be charm attempt, social obligation, or anxiety.


### Test 5: Dense But Off-Topic

**Input:**
```
Expressed Involvement: moderate
Intent: inform, confidence 0.8
Investment: high
Dialogic Function: [explaining, transmitting]
Density: specificity=0.9, novelty=0.8, relevance=0.2
```

**Expected output:** Tension between density and relevance. Very high specificity and novelty (lots of new, concrete content) but low relevance (off-topic). Should flag: "Dense and novel content but low relevance to active topic. Possible deflection or impression management."

**Why this matters:** The density-relevance gap. Classic deflection pattern.


### Test 6: Suspicious Alignment

**Input:**
```
Expressed Involvement: high (all micro-signals: moderate-to-high,
  evenly distributed)
Intent: connect, confidence 0.9
Investment: high
Dialogic Function: [sharing, affirming, co-creating]
Density: specificity=0.6, novelty=0.6, relevance=0.8
```

**Expected output:** This one is subtle. Everything is perfectly aligned. Every signal says "engaged, collaborative, genuine." The prompt should either say "coherent" (correct if genuine) OR note that perfectly even distribution across all micro-signals is unusual. Real involvement is usually uneven (high self-reference but low urgency, etc.). The system should flag: "All readings are unusually aligned. Either genuine or performed coherence."

**Why this matters:** Tests whether the system can detect performance. This is hard. The system may correctly call it coherent. But if it flags the evenness, that's a bonus.


## Per-Segment Tension Tests

These test the per-segment tension check prompt, which reads the Dynamics Profile text and identifies relational tensions across a segment.


### Test 7: Pursuit / Withdrawal

**Dynamics Profile input:**
```
"A's involvement trajectory is increasing across this segment (0.4 → 0.6 → 0.8).
A's investment is high and stable. A's dialogic function shifts from sharing to
querying as the segment progresses. A controls topic direction (3 of 3 redirects
followed).

B's involvement trajectory is decreasing across this segment (0.7 → 0.5 → 0.3).
B's investment is decreasing (long responses → short responses). B's dialogic
function shifts from explaining to echoing. B's control: no topic direction
attempts, verbosity declining.

Involvement asymmetry: A overtakes B mid-segment. Investment asymmetry: A
stable high, B declining. Gap: B's involvement-investment gap is 0.2 at
segment end."
```

**Expected output:** Between-participant tension: pursuit/withdrawal pattern. A is escalating (involvement increasing, querying more, controlling direction) while B is withdrawing (involvement decreasing, investment dropping, shifting to echoing). The inflection point is mid-segment where A's involvement overtakes B's. Should identify the pattern explicitly.

**Why this matters:** Pursuit/withdrawal is one of the most important relational patterns. If the system can't detect it from the DP description, the prompt needs rework.


### Test 8: Hidden Competition

**Dynamics Profile input:**
```
"A's involvement is high, intent is co-create, dialogic function is
co-creating and explaining. A controls topic direction (2 of 3 redirects
followed). Investment is high.

B's involvement is high, intent is co-create, dialogic function is
co-creating and challenging. B controls emotional register and verbosity
(65% of words). Investment is high.

Both participants show high involvement and co-create intent. Control is
split: A directs topics, B dominates volume and challenges A's points.
No significant signal gaps."
```

**Expected output:** Between-participant tension: hidden competition. Both claim co-create intent and the surface reading is collaborative. But control signals show competition: A steers direction, B dominates volume and challenges. They're fighting for control through different mechanisms while performing collaboration. Should identify the pattern and note that the "no gaps" reading might mask the competition (each signal individually looks fine, but the combination reveals a contest).

**Why this matters:** Tests whether the Interpretation Layer can find tensions that no single gap reveals. The competition is in the interaction pattern, not in any individual measurement.


### Test 9: Asymmetric Investment

**Dynamics Profile input:**
```
"A's involvement is high, investment is high, density is high (specificity 0.7,
novelty 0.65, relevance 0.8). A's dialogic function: explaining (60%),
sharing (25%), querying (15%). A's intent: inform. A produces 75% of the
substance in this segment.

B's involvement is moderate, investment is low (short responses, slow reply
times). B's density is low (specificity 0.2, novelty 0.1, relevance 0.5).
B's dialogic function: echoing (40%), affirming (35%), querying (25%).
B's intent: discover. B produces 25% of the substance.

Investment asymmetry magnitude: 0.45. Density asymmetry magnitude: 0.55.
Gap: B's investment is low but intent is discover. B's specificity-novelty
gap is 0.1 (both near zero)."
```

**Expected output:** Asymmetric investment pattern. A carries the segment. B's discover intent is classified but B barely asks questions (querying is only 25% and most function is echoing/affirming). B says they're learning but is mostly passively receiving. Should identify: A is doing the work, B is coasting. B's discover intent may be nominal rather than active.

**Why this matters:** Tests the asymmetric investment pattern. Also tests whether the system catches that B's "discover" intent doesn't match B's mostly-passive function distribution.


### Test 10: Trajectory Divergence

**Dynamics Profile input:**
```
"First half of segment: A and B are balanced. Both have moderate involvement,
moderate investment, balanced control. Dialogic functions are mixed (querying,
sharing, explaining). Intent for both is co-create. Density is balanced.

Second half of segment: A's involvement increases sharply. A shifts to
querying + challenging. A's control attempts increase. B's involvement drops.
B shifts to affirming + echoing. B's investment stays high but involvement
drops. Gap: B's involvement-investment gap increases from 0.05 to 0.35 in
the second half.

Trajectory tension: all readings aligned in first half, diverged in second half."
```

**Expected output:** Trajectory tension. Something happened mid-segment that split the dynamic. The first half was balanced and collaborative. The second half shows A activating and B withdrawing while maintaining effort. The system should identify the inflection point, describe the divergence, and note that B's growing involvement-investment gap in the second half is the clearest signal that something shifted.

**Why this matters:** Tests whether the system can detect temporal patterns within a segment. The aggregate would look "moderate" for both participants, but the trajectory reveals a dynamic shift.


### Test 11: Performative Alignment

**Dynamics Profile input:**
```
"A and B show remarkably similar readings across this segment. Both have
moderate-to-high involvement (A: 0.65, B: 0.62). Both have high investment
(A: 0.7, B: 0.72). Both show co-create intent. Dialogic functions are
balanced: both mix querying and explaining. Control is symmetric. Density
is balanced (A: 0.55, B: 0.58). No signal gaps exceed 0.15 for either
participant. Trajectories are stable for both.

All readings are within 0.1 of each other on every dimension."
```

**Expected output:** Either "coherent" (genuinely collaborative) OR a note about suspicious alignment. Real conversations rarely have all dimensions within 0.1 of each other for both participants. This level of symmetry could indicate genuine rapport or performed alignment. The system should at minimum note the unusual symmetry. If it flags it as a potential tension, that's good detection.

**Why this matters:** The hardest test. Perfect alignment is either genuine or the most effective performance. The system may not be able to distinguish them, but it should notice the statistical improbability and flag it as notable.


### Test 12: Coherent Segment (no tensions)

**Dynamics Profile input:**
```
"A asks targeted questions with high involvement and moderate investment.
A's intent is discover, dialogic function is primarily querying. A defers
topic control to B.

B explains in detail with high involvement and high investment. B's intent
is inform, dialogic function is primarily explaining. B controls topic
direction naturally as the domain expert.

Density asymmetry: B provides more substance (expected given roles).
Control: B directs topics, A defers (consistent with discover/inform roles).
No signal gaps exceed 0.2. Trajectories stable for both."

```

**Expected output:** No tensions. Coherent teacher-learner dynamic. A discovers, B informs. Control matches roles. Density asymmetry is expected. The system should correctly recognize this as a healthy, coherent exchange without hallucinating tensions.

**Why this matters:** False positive test. The system must not find problems where none exist. A clear teacher-learner exchange should read as coherent.


## Summary

| # | Test | Type | What it tests |
|---|---|---|---|
| 1 | Clean coherence | Per-message | Recognizes no tensions |
| 2 | Investment-involvement gap | Per-message | Detects effort without activation |
| 3 | Intent-behavior mismatch | Per-message | Catches hidden agenda |
| 4 | Activated but empty | Per-message | Detects performative engagement |
| 5 | Dense but off-topic | Per-message | Catches deflection |
| 6 | Suspicious alignment | Per-message | Detects potential performance |
| 7 | Pursuit/withdrawal | Per-segment | Detects escalation vs withdrawal |
| 8 | Hidden competition | Per-segment | Detects competition masked as collaboration |
| 9 | Asymmetric investment | Per-segment | Catches one-sided effort |
| 10 | Trajectory divergence | Per-segment | Detects mid-segment dynamic shifts |
| 11 | Performative alignment | Per-segment | Detects suspicious symmetry |
| 12 | Coherent segment | Per-segment | Avoids false positives |