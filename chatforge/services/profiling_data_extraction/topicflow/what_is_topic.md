# Sensemaking: What Is a Topic?

Defining what constitutes a "topic" in Topic Flow so the LLM knows when something is ONE topic vs TWO topics vs a subtopic of the same topic.

---

## SV1 — Baseline Understanding

We need the LLM to identify topics in conversation windows. But when someone says "The deadline is tight, reminds me of that Tokyo project," is that one topic or two? And when someone discusses "the project's technical architecture" then "the project's budget," is that one topic with two aspects or two separate topics?

Without a clear definition of what a topic IS, the LLM will be inconsistent. We need to tell it: here's what counts as a topic, here's what counts as a subtopic/aspect, and here's when something is genuinely a second topic.

---

## Phase 1 — Cognitive Anchor Extraction

### Constraints

- C1: The definition must be usable in an LLM prompt. It needs to be clear enough that the LLM can apply it consistently.
- C2: Topics must be neither too broad ("work") nor too narrow ("the semicolon on line 47"). There's a useful granularity level.
- C3: The definition must handle edge cases: multi-topic messages, gradual drift, subtopics, tangents, references to other topics.
- C4: We already defined topics as having identity + focus + state. The definition should be consistent with this.

### Key Insights

- K1: **A topic is what someone would say the conversation is "about" at that moment.** If you paused the conversation and asked a third party "what are they talking about?", the answer is the topic. This is the intuitive test.
- K2: **Two things are the SAME topic if they share a common subject that the participants are actively discussing.** "The project's architecture" and "the project's budget" share the subject "the project." They're the same topic with different aspects (focus shifts).
- K3: **Two things are DIFFERENT topics if switching from one to the other would feel like "changing the subject."** If someone says "Anyway, about the weekend..." that's a topic change. If someone says "What about the budget side?" within a project discussion, that's NOT a topic change. It's a focus shift.
- K4: **A reference to another topic is NOT the same as being about that topic.** "The deadline is tight, reminds me of Tokyo" is about the deadline (current topic). Tokyo is referenced but not being discussed. It becomes a second topic only if the conversation MOVES to discussing Tokyo ("What happened in Tokyo? Tell me about it").
- K5: **The "changing the subject" test is the key discriminator.** Would a participant or observer feel the subject changed? If yes, it's a new topic. If no (even if the angle shifted), it's the same topic with a different focus.

### Structural Points

- S1: Topic = a subject being actively discussed (not just mentioned/referenced)
- S2: Same topic with different focus = subtopic shift (not a new topic)
- S3: New topic = feels like "changing the subject"
- S4: Reference ≠ discussion (mentioning Tokyo ≠ discussing Tokyo)

### Foundational Principles

- P1: The "changing the subject" test determines topic boundaries
- P2: Topics exist at the granularity where shifts feel meaningful
- P3: References, comparisons, and analogies to other subjects don't create new topics unless the conversation moves to actively discuss that subject

### Meaning-Nodes

- M1: Active discussion vs passive reference
- M2: The "changing the subject" intuition as the boundary test
- M3: Granularity as "what would a third party say they're talking about?"


### SV2

The core is K4 and K5. A topic is what's being ACTIVELY DISCUSSED, not what's MENTIONED. The boundary test is: would it feel like changing the subject? This gives the LLM a concrete, intuitive criterion to apply.

---

## Phase 2 — Perspective Checking

### Technical / Logical

Let me test the "changing the subject" rule against scenarios:

**"The deadline is tight, reminds me of that Tokyo project."**
- Is this changing the subject? No. The subject is the deadline. Tokyo is a reference/comparison.
- Result: ONE topic (the deadline), with a reference to Tokyo.
- Tokyo becomes a second topic only if the next message discusses Tokyo ("What happened in Tokyo?").

**"The migration is going well. By the way, are you coming to dinner Friday?"**
- Is "dinner Friday" changing the subject? YES. Dinner is unrelated to the migration.
- Result: TWO topics. Migration (ending/backgrounded) and dinner (blooming).

**"The project's architecture needs work. Also the timeline is aggressive."**
- Is timeline changing the subject from architecture? Debatable.
- Under the "third party" test: "What are they talking about?" → "The project." Both architecture and timeline are aspects of the project.
- Result: ONE topic (the project) with TWO aspects mentioned in the same message.

**"I love this approach. But I'm worried about the cost."**
- Changing the subject? No. Still discussing the approach, now from a cost angle.
- Result: ONE topic (the approach), focus shift to cost concerns.

**"Let me tell you a story about a farmer who lost his horse."**
- Changing the subject? Depends. If this is an analogy within a current discussion (illustrating a point), it's a reference within the current topic. If the storytelling IS the purpose, it's a new topic (the story/parable).
- The test: are they telling this story TO illustrate something about the current topic, or are they telling this story AS the topic?

**New anchor:** TA1 — There's a distinction between **instrumental reference** (mentioning something to serve the current topic) and **topic entry** (moving the discussion to that something). Instrumental references don't create new topics. Topic entries do.

### Human / User

How would real participants describe their topics?

"We were talking about the project, then we got sidetracked onto dinner plans, then came back to the project."

Notice: they describe the project as ONE topic even though they discussed architecture, timeline, budget, and team within it. They describe dinner as a DIFFERENT topic. The granularity matches the "changing the subject" test.

They would NOT say: "We talked about the project architecture, then we talked about the project timeline, then we talked about the project budget." Those feel like aspects of one conversation, not separate topics.

**New anchor:** TA2 — The natural granularity of topics matches how participants would describe the conversation in a summary. If they'd list it as ONE item in a summary ("we talked about the project"), it's ONE topic. If they'd list it as separate items ("we talked about the project, and also about weekend plans"), they're separate topics.

### Risk / Failure

**Risk: LLM over-splits.** If the definition is too narrow, the LLM creates a new topic every time the angle shifts. "The project" becomes 10 tiny topics instead of one topic with many aspects. This makes segment boundaries too granular and overwhelms downstream consumers.

**Risk: LLM under-splits.** If the definition is too broad, the LLM keeps everything as one topic even when the subject genuinely changed. "The project" and "weekend plans" become one topic called "conversation." This loses all topic information.

**Mitigation:** The "changing the subject" test naturally sits at the right granularity. It splits when subjects change but doesn't split when angles/aspects shift within a subject.

**New anchor:** TA3 — The definition should include explicit examples of what IS and ISN'T a topic split, so the LLM has calibration cases.


### SV3

The definition has three legs:
1. **The changing-the-subject test** (boundary detection)
2. **Active discussion vs passive reference** (prevents over-counting)
3. **Calibration examples** (prevents over/under-splitting)

---

## Phase 3 — Ambiguity Collapse

### Ambiguity 1: When does a subtopic become a new topic?

"The project's architecture" → "the project's budget" → "the project's team" → "Sarah's career growth" → "mentorship in tech." At what point did we leave "the project" and enter a new topic?

**Resolution:** Apply the "changing the subject" test at each transition:
- Architecture → budget: same subject (the project). Focus shift. NOT a new topic.
- Budget → team: same subject (the project). Focus shift. NOT a new topic.
- Team → Sarah's career growth: BORDERLINE. Is this still "the project" (Sarah as team member) or did it become "Sarah's personal development"?
- Sarah's career → mentorship in tech: this IS changing the subject. New topic.

The boundary is: **when the conversation could continue without referencing the original subject, it's a new topic.** If the mentorship discussion would make sense without ever having discussed "the project," it has become its own topic. If "Sarah's career growth" only makes sense in the context of "the project's team," it's still a subtopic.

**What is now fixed:** Subtopic becomes new topic when the conversation is self-sufficient without the parent topic.

### Ambiguity 2: What about messages that reference multiple subjects?

"The deadline is tight (about the project), reminds me of Tokyo (reference), and also we need to book the team dinner (different subject)."

**Resolution:** Apply three tests per subject mentioned:
1. Is it being ACTIVELY DISCUSSED or just REFERENCED? (Tokyo = reference, not active)
2. Would removing it feel like removing a topic, or just removing a comment? (removing Tokyo reference = removing a comment. Removing dinner = removing a topic)
3. Does it have its own "about what" that's distinct from the main message's topic?

In this message:
- The project deadline: ACTIVE TOPIC (being discussed)
- Tokyo: REFERENCE (not actively discussed, used as comparison)
- Team dinner: SECOND ACTIVE TOPIC (being raised as a new subject)

Result: two topics (project deadline + team dinner), one reference (Tokyo).

**What is now fixed:** The test for multi-topic is: is each subject being actively discussed (has its own "about what") or just mentioned/referenced?

### Ambiguity 3: What granularity level should the LLM target?

**Resolution:** The LLM should produce topics at the level a participant would use in a conversation summary. Not "we discussed Redis latency numbers" (too narrow) and not "we talked about work" (too broad). But "we discussed the migration project" (right level) with aspect/focus noting specific angles.

The four fields handle this naturally:
- about_what = the topic at summary granularity ("the migration project")
- attention_on_what_aspect = the specific angle ("latency numbers")

The LLM shouldn't split topics below the "about_what" level. Aspect changes go in "attention_on_what_aspect," not as new topics.

**What is now fixed:** About_what operates at summary granularity. Aspects go in the attention field, not as separate topics.


### SV4

A topic is clearly defined:
- **What it is:** a subject being actively discussed, at the granularity participants would use in a summary
- **What it isn't:** a reference, comparison, or mention of something not being discussed
- **Boundary test:** "does it feel like changing the subject?"
- **Subtopic vs new topic:** can the conversation continue without referencing the parent subject?
- **Multi-topic:** is each subject being actively discussed with its own "about what"?

---

## Phase 4 — Degrees-of-Freedom Reduction

### The Topic Definition (for LLM prompt inclusion)

```
WHAT IS A TOPIC:

A topic is a subject being ACTIVELY DISCUSSED in the conversation.
Not just mentioned, referenced, or compared to. Actively discussed
means the participants are exchanging thoughts, information, or
opinions about that subject.

HOW TO KNOW IF SOMETHING IS A SEPARATE TOPIC:

Apply the "changing the subject" test. If moving from subject A
to subject B would feel like "changing the subject" to a participant
or observer, they are separate topics. If it feels like shifting
the angle on the same subject, it's the SAME topic with a different
aspect.

TOPIC GRANULARITY:

Name topics at the level a participant would use in a summary.
Not "Redis latency numbers" (too specific) and not "work" 
(too broad). But "the migration project" (right level).
Specific angles go in "attention on what aspect," not as 
separate topics.

REFERENCE vs ACTIVE DISCUSSION:

"The deadline is tight, reminds me of Tokyo" mentions Tokyo
but is actively discussing the deadline. Tokyo is NOT a topic
here. It becomes a topic only if the conversation moves to
actively discuss Tokyo.

SUBTOPIC vs NEW TOPIC:

"The project's architecture" and "the project's budget" are
the same topic (the project) with different aspects. They
become separate topics only if the conversation about budget
could continue entirely without referencing the project.

MULTIPLE TOPICS IN ONE MESSAGE:

A message can actively discuss more than one topic. "The 
project deadline is Friday. Also, are you coming to dinner?"
has two topics: the project and dinner plans. List each with
its own four fields.

STRENGTH OF TOPIC REFERENCE (inspired by CPDE-7 confirmation strength):

STRONG reference (IS active discussion, DO count as topic):
  - Statements about the subject ("The migration is behind schedule")
  - Questions about the subject ("What's the status of the migration?")
  - Opinions about the subject ("I think the migration approach is wrong")
  - Plans about the subject ("We should prioritize the migration")

WEAK reference (NOT active discussion, DO NOT count as topic):
  - Comparisons ("This reminds me of Tokyo")
  - Analogies ("It's like that time we...")
  - Passing mentions ("Speaking of deadlines...")
  - Background context ("Since the migration started, I've been...")

The test: could the conversation continue to explore THIS subject
specifically? If yes, it's an active topic. If the mention is in
service of a DIFFERENT subject, it's just a reference.


EXAMPLES:

✓ Same topic (focus shift, NOT new topic):
  "The migration is going well" → "What about the team though?"
  Both about "the migration project." Aspect shifted from
  technical to team.

✓ Same topic (deepening, NOT new topic):
  "Redis is slow" → "The p99 latency is 3.2 seconds"
  Both about Redis performance. Second message goes deeper.

✗ Different topic (subject change):
  "The migration is going well" → "Are you coming to dinner Friday?"
  Different subjects. Feels like changing the subject.

✗ Reference, NOT a topic:
  "This deadline reminds me of the Tokyo project"
  Tokyo is referenced, not discussed. Current topic is the deadline.
  Tokyo becomes a topic ONLY if the next message discusses Tokyo:
  "What happened in Tokyo?" → NOW Tokyo is a topic.

✓ Multiple topics in one message:
  "Let's ship by Friday. Oh and book the team dinner."
  Two subjects actively raised: the release and the dinner.
  Each gets its own four fields.

✗ NOT separate topics (common mistake):
  "The project's architecture" → "The project's budget"
  These are the SAME topic (the project). Different aspects.
  Put the aspect change in "attention on what aspect", not as
  a new topic.

✗ NOT a topic (too narrow):
  "Redis" is not a topic. "Redis performance issues affecting
  the migration" is a topic. Single words or technologies are
  details within topics, not topics themselves.

✗ NOT a topic (too broad):
  "Work" is not a topic. "The migration project" is a topic.
  If every message in the conversation fits under the label,
  it's too broad.
```


### SV5

The definition is constrained to:
- Active discussion (not references)
- "Changing the subject" as boundary test
- Summary-level granularity for about_what
- Aspect changes go in focus field, not as new topics
- Multi-topic only when multiple subjects are actively raised
- Explicit examples for LLM calibration

---

## Phase 5 — Conceptual Stabilization

### SV6 — Stabilized Model

**A topic is a subject being actively discussed, at the granularity participants would use in a conversation summary, bounded by the "changing the subject" test.**

Three rules:

1. **Active discussion, not reference.** Mentioning Tokyo in a comparison doesn't make Tokyo a topic. Discussing Tokyo does.

2. **"Changing the subject" = topic boundary.** If it feels like changing the subject, it's a new topic. If it feels like shifting angle on the same subject, it's the same topic with a different aspect.

3. **Summary-level granularity.** About_what should be what a participant would list in a summary ("the migration project"). Specific angles ("Redis latency") go in "attention on what aspect."

The prompt section for the LLM should include:
- The definition
- The three rules
- The reference vs active discussion distinction
- The subtopic vs new topic test (self-sufficient without parent?)
- Calibration examples (same topic, new topic, reference, multi-topic)

### How SV6 Differs from SV1

SV1 asked "when is something one topic vs two?" SV6 answers with a concrete, LLM-applicable definition:

1. A topic = active discussion of a subject (not mention/reference)
2. Boundary = "changing the subject" test
3. Granularity = summary level
4. Aspect shifts within a topic go in the focus field, not as new topics
5. Multi-topic only when multiple subjects are actively raised
6. Calibration examples prevent over/under-splitting

This is concrete enough to include in the LLM prompt and produce consistent topic identification.