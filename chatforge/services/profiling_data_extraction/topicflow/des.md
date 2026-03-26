# Topic Flow

Shared conversation infrastructure that tracks what is being discussed at every point. How topics bloom, persist, interleave, evolve, fade, and return across a conversation.

Topic Flow sits upstream of both PRAGMA and CPDE-7 as foundational infrastructure. It is not a PRAGMA dimension. It is the reference frame that makes PRAGMA dimensions contextually meaningful.


## The Analogy

Topic Flow is like **polyphonic music**: multiple melodic lines playing simultaneously, each with its own arc. Some voices enter early, some late. Some carry the melody (dominant topic), some provide harmony (backgrounded topics). A theme is introduced, developed, varied, and sometimes reprised. The same theme can sound completely different each time it returns, played in a different key or tempo (topic focus evolution). The whole piece is the conversation; each voice is a topic thread.

But there is also a **river delta** quality to it. A single conversation branches into multiple channels. Some channels are wide and deep (major topics), some narrow (minor threads). Channels merge, split, dry up, reappear underground then surface again. A topic that was discussed and seemingly finished doesn't disappear. It flows underground, shaping the terrain, influencing what comes next. When it resurfaces later, it carries everything it accumulated while hidden. A "finished" topic still contributes to the conversation's meaning long after the last message about it was sent.


## What Topic Flow Does

Track multiple concurrent topics across a conversation:

- **Blooming**: how new topics emerge (introduced explicitly, drifted into, prompted by the other participant)
- **Persistence**: how long topics stay active and how they're sustained
- **Interleaving**: how multiple topics coexist, alternate, and compete for attention
- **Evolution**: how a topic's focus shifts while its identity remains (subtopic transitions)
- **Fading**: how topics lose activity and dissolve (explicitly closed, gradually abandoned, displaced)
- **Returning**: how previously faded topics come back (callback, unfinished business, triggered by association)

The output is not a single "current topic" label. It's a **multi-track topic state** where multiple topics can be active simultaneously at different intensities, and the system tracks how each one evolves.


## What a Topic Is

A topic is not a label or a keyword cluster. It is a **living semantic field** with three components:

**Identity**: the broad subject being discussed. "The migration project", "weekend plans", "AI research". Identity can stay constant across many messages even as the conversation evolves within it.

**Focus**: which aspect of the subject is active right now. "The migration project's timeline" vs "the migration project's team morale" vs "the migration project's budget". Focus shifts within the same identity are subtopic transitions, not new topics.

**State**: where the topic is in its lifecycle (blooming, active, backgrounded, fading, dormant, returned, closed).

```
A topic is NOT:
  "work"              (too broad, no identity)
  "Redis"             (too narrow, a detail within a topic)

A topic IS:
  Identity: "the migration project"
  Focus:    "budget constraints"
  State:    active
  
  Focus trajectory over this conversation:
    technical status → team health → staffing → budget → prioritization
```

The focus trajectory shows how the semantic center of a topic MOVES over time. This is what polyphonic development sounds like: the same theme, played with different emphasis each time it appears.


## Topic Hierarchy

Topics are hierarchical. Parent and child relationships:

```
work (level 0)
  └── the migration project (level 1)
       ├── technical status (level 2)
       │    └── Redis performance (level 3)
       ├── team health (level 2)
       │    └── Sarah's workload (level 3)
       └── budget constraints (level 2)
            └── contractor hiring (level 3)
```

The active granularity level is configurable. By default, the system operates at the level where meaningful topic shifts occur (usually level 1 or 2). Segment boundaries are produced at the configured level.

If configured at level 1, the entire example above is one segment ("the migration project"). If configured at level 2, there are three segments (technical, team, budget).


## Topic State and Lifecycle

At any point in the conversation, each tracked topic has a state:

| State | Description |
|-------|-------------|
| **Blooming** | Just introduced. First messages establishing a new thread |
| **Active** | Currently being discussed. Messages are contributing to this topic |
| **Backgrounded** | Not currently discussed but not resolved. Could return |
| **Fading** | Losing activity. Fewer messages, less investment, being displaced |
| **Dormant** | Hasn't been touched for a while. Still in history but no longer active |
| **Returned** | Was dormant or backgrounded, now active again |
| **Closed** | Explicitly or implicitly concluded |

A "closed" or "dormant" topic is not gone. Like a river channel that dried up, it shaped the terrain. Its content, its emotional residue, the positions taken within it, all of these persist underground and influence what comes next. When a topic returns, it carries the accumulated context from before.


## Multi-Topic Tracking

Conversations rarely have one topic at a time. Topic Flow tracks multiple concurrent topics as parallel voices:

```
Time     msg1   msg2   msg3   msg4   msg5   msg6   msg7   msg8   msg9

Topic A: ████   ████   ████   ░░░░   ░░░░   ░░░░   ░░░░   ████   ████
         active active active fading dormnt dormnt dormnt returnd active

Topic B:                      ████   ████   ████   ████
                              bloom  active active active

Topic C:                                           ████   ████   ████
                                                   bloom  active active
```

Topics don't switch cleanly. They overlap, compete, interleave. Messages can contribute to multiple topics simultaneously. A single message like "The deadline is tight, reminds me of that Tokyo project" touches both the current project (Topic B) and past experiences (Topic A). The system handles this multiplicity rather than forcing single-topic assignment.


## Topic Events

Topic Flow produces a stream of structural events:

### Blooming Events (how topics enter)

| Event | Description |
|-------|-------------|
| **explicit_introduction** | Participant directly raises a new subject |
| **drift** | Topic gradually shifts from current topic without explicit change |
| **prompted_emergence** | One participant's message causes the other to introduce a new topic |
| **branch** | Subtopic splits off from parent topic |

### Persistence Events (how topics stay alive)

| Event | Description |
|-------|-------------|
| **continuation** | Next message stays on the same topic |
| **deepening** | Topic is explored in more depth |
| **mutual_sustain** | Both participants are actively contributing |
| **one_sided_sustain** | Only one participant is keeping this topic going |

### Transition Events (how the conversation moves between topics)

| Event | Description |
|-------|-------------|
| **clean_shift** | One topic ends, another begins with clear boundary |
| **gradual_drift** | No clear boundary. Topic slides into something different |
| **interruption** | New topic breaks into an active topic abruptly |
| **backgrounding** | Current topic is paused to address something else |
| **return** | Previously backgrounded or dormant topic becomes active again |
| **callback** | Explicit reference to an earlier topic |
| **association_trigger** | Something in the current topic triggers a return to an earlier one |

### Fading Events (how topics dissolve)

| Event | Description |
|-------|-------------|
| **displacement** | Another topic takes over. This one fades because attention moved |
| **exhaustion** | Topic has been fully discussed. Nothing more to add |
| **abandonment** | Participants stop engaging with the topic without resolution |
| **explicit_close** | Participant deliberately ends the topic |
| **mutual_dropout** | Both participants' investment declines simultaneously |
| **one_sided_dropout** | One participant stops engaging while the other tries to continue |


## Attribution

Every topic event is attributed to a participant. Surface-level only: who observably caused the event. Not who strategically guided it (that's PRAGMA's Interpretation Layer).

```
{
  "event": "explicit_introduction",
  "topic_id": "t_003",
  "caused_by": "participant_a",
  "at_message": 12,
  "relation_to_previous": "unrelated"
}
```


## Detection: LLM Calls

Topic Flow uses LLM calls at three window sizes to detect topics. No embeddings, no heuristics. Pure semantic understanding.

### Three Windows

| Window | Focus | Context | What it captures |
|---|---|---|---|
| **Immediate** | Last 3 messages | Last 10 messages | What's being discussed RIGHT NOW |
| **Medium** | Last 20 messages | Last 30 messages | What's been the subject LATELY |
| **Long** | Last 50+ messages | Full conversation | What's the overarching theme |

Each window asks the LLM four questions about every active topic:
1. **About what**: the topic identity
2. **In what context**: the broader frame
3. **Attention on what aspect**: the current focus/angle
4. **Why is it discussed**: how this topic came up

Multiple topics can be active simultaneously. Each gets its own four fields.

### Why LLM, Not Embeddings

Embeddings detect topic BREAKS (sharp similarity drops) but miss topic EVOLUTION (gradual drift where similarity stays high). The conversation "technical status → team health → budget constraints" looks continuous to embeddings (all project-related) but has evolved through three distinct subtopics. Only LLM semantic understanding catches this.

See `calculation_logic.md` for the full prompts and implementation detail.


## Processing Order

Topic Flow runs BEFORE PRAGMA. They are separate systems with separate LLM calls. The dependency is one-directional:

```
Step 1: Message Properties (preprocess)
Step 2: Topic Flow (its own LLM call, produces topic context)
Step 3: PRAGMA (its own LLM call, consumes topic context from Step 2)
```

PRAGMA dimensions depend on Topic Flow:
- Information Density needs topic for novelty and relevance
- Control Distribution needs topic attribution for direction control
- Energy needs topic segments for per-topic aggregation
- Intent arcs need segment boundaries


## Output

Topic Flow produces four outputs:

### 1. Topic State Map

Current state of all tracked topics at any point:

```
{
  "as_of_message": 15,
  "topics": [
    {
      "topic_id": "t_001",
      "identity": "the migration project",
      "current_focus": null,
      "state": "dormant",
      "first_message": 1,
      "last_active_message": 6,
      "message_count": 5,
      "focus_trajectory": ["technical status", "team health"]
    },
    {
      "topic_id": "t_002",
      "identity": "weekend plans",
      "current_focus": "restaurant choice",
      "state": "active",
      "first_message": 7,
      "last_active_message": 15,
      "message_count": 8,
      "focus_trajectory": ["general plans", "restaurant choice"]
    }
  ]
}
```

### 2. Event Stream

Ordered list of topic events:

```
msg 1:   blooming(t_001, explicit_introduction, by=a)
msg 1-3: continuation(t_001, focus="technical status")
msg 4:   subtopic_shift(t_001, focus="team health")
msg 4-6: continuation(t_001, focus="team health")
msg 7:   blooming(t_002, explicit_introduction, by=b)
msg 7:   fading(t_001, displacement)
msg 7-15: continuation(t_002)
```

### 3. Segment Boundaries

Message indices where dominant topic changes (at configured granularity):

```
segments: [
  { start: 1, end: 6, dominant_topic: "t_001", focus: "technical → team" },
  { start: 7, end: 15, dominant_topic: "t_002", focus: "restaurant" }
]
```

### 4. Per-Participant Topic Behavior

How each participant interacts with topics:

```
participant_a:
  topics_introduced: 2
  topics_abandoned: 0
  topics_returned_to: 1
  avg_topic_sustain_messages: 7
  subtopic_shifts_initiated: 3

participant_b:
  topics_introduced: 1
  topics_abandoned: 1
  topics_returned_to: 0
  avg_topic_sustain_messages: 4
  subtopic_shifts_initiated: 1
```


## What Consumes Topic Flow

| Consumer | What it uses |
|----------|-------------|
| **PRAGMA Signal Layer** | Segment boundaries for per-segment computations. Topic context for meaningful signals ("involvement toward what topic?") |
| **PRAGMA Interpretation Layer** | Topic attribution and event stream to infer strategic dynamics |
| **CPDE-7** | Topic segments for batching extraction. Topic context helps extract relevant content |
| **Behavioral Profiling** | Per-participant topic behavior as a profiling signal |
| **Summarization** | Topic state map and event stream produce conversation summaries |


## What Topic Flow Does NOT Do

- **Does not interpret WHY** topics change (that's PRAGMA Intent + Interpretation Layer)
- **Does not measure energy or involvement** per topic (that's PRAGMA Expressed Involvement, aggregated per topic segment)
- **Does not extract content or facts** about people (that's CPDE-7)
- **Does not determine who "really" controls topics** (it records who observably introduced, sustained, or abandoned them. Strategic attribution is PRAGMA Interpretation Layer)
- **Does not assign purpose** to topic discussions. The same topic discussed to inform, to convince, or to process anxiety is the same topic. Purpose is Intent's job, not Topic Flow's.


## The Underground River Principle

A topic that was discussed and concluded does not vanish. Like a river that goes underground, it continues to flow beneath the surface:

- The positions taken during that topic still influence later behavior
- The emotional residue from that discussion colors subsequent topics
- When the topic resurfaces (and they often do), it carries everything accumulated while dormant
- A "closed" topic can be reopened by either participant, by association, or by external events

Topic Flow tracks this by keeping dormant/closed topics in history. When the LLM detects a return to an earlier topic (through the immediate window analysis), the topic state transitions from dormant to returned.

The underground flow is what makes conversations coherent across topics. It's why a conversation about "the project" followed by "weekend plans" followed by "career goals" is not three disconnected exchanges. The underground rivers connect them.