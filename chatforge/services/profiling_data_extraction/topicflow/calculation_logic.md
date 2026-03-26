# Topic Flow: Calculation Logic

Topic Flow is calculated via LLM calls at three different window sizes, using a sliding window approach. No embeddings. No heuristics. Pure LLM semantic understanding.


## The Three Window Sizes

A conversation has topics at different scales. What's being discussed "right now" (last few messages) may be different from the broader topic "lately" (last 20 messages) which may be different from the overarching topic "overall" (the whole conversation).

| Window | Size | What it captures | Analogy |
|---|---|---|---|
| **Immediate** | Last 3 messages | What's being discussed RIGHT NOW. The current beat. | The current bar in a piece of music |
| **Medium** | Last 20 messages | What's been the subject LATELY. The current section. | The current movement |
| **Long** | Last 50+ messages | What's the overarching subject. The whole piece. | The whole composition |

These three readings can differ. The immediate topic might be "Redis performance" while the medium topic is "the migration project" and the long topic is "work." This IS the topic hierarchy in action, detected naturally through different window sizes rather than explicitly constructed.


## The Sliding Window Approach

For every new message, the system runs the immediate window (last 3 messages). The medium and long windows run less frequently (every 5-10 messages, or on demand) since they change more slowly.

```
Message arrives
     │
     ├── Always: Immediate window (last 3 messages)
     │           → what is being discussed RIGHT NOW?
     │
     ├── Every ~5 messages: Medium window (last 20 messages)
     │           → what has been the subject LATELY?
     │
     └── Every ~10 messages or on demand: Long window (last 50+ messages)
                 → what is the overarching topic?
```


## The LLM Prompt

Each window size uses the same prompt structure. The LLM receives two inputs:
1. The **focus window** (the messages to analyze, e.g. last 3)
2. The **context window** (wider context for reference, e.g. last 10)

The context window is always larger than the focus window. It provides background so the LLM understands what the focus messages are responding to.

### Immediate Window Prompt

```
=============================================================================
WHAT IS A TOPIC
=============================================================================

A topic is a subject being ACTIVELY DISCUSSED. Not just mentioned,
referenced, or compared to. Actively discussed means the participants
are exchanging thoughts, information, or opinions about that subject.

BOUNDARY TEST: If moving from subject A to subject B would feel like
"changing the subject," they are separate topics. If it feels like
shifting the angle on the same subject, it's the SAME topic with a
different aspect.

GRANULARITY: Name topics at the level a participant would use in a
summary. Not "Redis latency numbers" (too specific) and not "work"
(too broad). But "the migration project" (right level). Specific
angles go in "attention on what aspect," not as separate topics.

STRONG reference (IS a topic): statements, questions, opinions, or
plans about the subject.

WEAK reference (NOT a topic): comparisons ("reminds me of Tokyo"),
analogies, passing mentions, background context. These are references
in service of the actual topic, not topics themselves.

=============================================================================
MESSAGES
=============================================================================

Here are the last 10 messages of a conversation (CONTEXT):

{last_10_messages_formatted}

Now focus on the LAST 3 MESSAGES specifically:

{last_3_messages_formatted}

=============================================================================
INSTRUCTIONS
=============================================================================

Based on the last 3 messages, tell me what is being discussed right now.

For EACH topic being actively discussed, answer these four questions:

1. ABOUT WHAT
   What is the topic being talked about right now?
   Be specific. Not "work" but "the Redis migration's impact on latency."

2. IN WHAT CONTEXT
   In what broader context is this topic being discussed?
   What led to this topic? What conversation is this part of?

3. ATTENTION ON WHAT ASPECT
   What specific aspect or angle of this topic is getting attention
   right now? For example: the technical details? the timeline? the
   team impact? the emotional weight? the decision that needs to be made?

4. WHY IS IT DISCUSSED (if obvious)
   Is it obvious why this topic came up? If yes, why?
   Was it a natural continuation? A deliberate introduction?
   A reaction to something? A redirect?
   If not obvious, say "not obvious."

If there is MORE THAN ONE topic being actively discussed in these
last 3 messages, give me the same four fields for EACH topic.
Do NOT count references, comparisons, or passing mentions as
separate topics. Only subjects being actively discussed.

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "topics": [
    {
      "about_what": "string",
      "in_what_context": "string",
      "attention_on_what_aspect": "string",
      "why_discussed": "string or 'not obvious'"
    }
  ]
}

If only one topic, the array has one item.
If multiple topics are actively discussed, the array has multiple items.
```

### Medium Window Prompt

```
=============================================================================
WHAT IS A TOPIC
=============================================================================

A topic is a subject being ACTIVELY DISCUSSED. Not just mentioned,
referenced, or compared to.

BOUNDARY TEST: If moving from subject A to subject B would feel like
"changing the subject," they are separate topics. If it feels like
shifting the angle on the same subject, it's the SAME topic with a
different aspect.

GRANULARITY: Name topics at summary level. Not too specific ("Redis
latency"), not too broad ("work"). Right level: "the migration project."

=============================================================================
MESSAGES
=============================================================================

Here are the last 30 messages of a conversation (CONTEXT):

{last_30_messages_formatted}

Now focus on the LAST 20 MESSAGES as a group:

{last_20_messages_formatted}

=============================================================================
INSTRUCTIONS
=============================================================================

Based on these 20 messages, tell me what has been discussed lately.

For EACH topic that was actively discussed across these messages,
answer these four questions:

1. ABOUT WHAT
   What is this topic? Name it at summary level.

2. IN WHAT CONTEXT
   In what broader context is this topic being discussed?
   What is the purpose of this section of conversation?

3. ATTENTION ON WHAT ASPECT
   What aspect of this topic has gotten the most attention?
   Has the aspect shifted during these messages? If so, how?
   Describe the aspect trajectory if it evolved.

4. WHY IS IT DISCUSSED (if obvious)
   Why is this topic being discussed? What triggered it?
   Is there an underlying purpose or goal?

If MULTIPLE topics were discussed across these 20 messages,
list each with its own four fields. Order by prominence
(most discussed first).

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "topics": [
    {
      "about_what": "string",
      "in_what_context": "string",
      "attention_on_what_aspect": "string",
      "aspect_shifted": true/false,
      "aspect_trajectory": "string or null",
      "why_discussed": "string or 'not obvious'",
      "prominence": 0.0-1.0
    }
  ]
}

Order topics by prominence (highest first).
Prominence scores should sum to approximately 1.0.
```

### Long Window Prompt

```
=============================================================================
WHAT IS A TOPIC
=============================================================================

A topic is a subject being ACTIVELY DISCUSSED. Not just mentioned,
referenced, or compared to.

BOUNDARY TEST: If moving from subject A to subject B would feel like
"changing the subject," they are separate topics.

GRANULARITY: Name topics at summary level.

=============================================================================
MESSAGES
=============================================================================

Here is the full conversation so far (or last 50+ messages):

{full_conversation_or_last_50_messages}

=============================================================================
INSTRUCTIONS
=============================================================================

Looking at this conversation as a whole, identify ALL topics that
were actively discussed. For EACH topic, answer these four questions:

1. ABOUT WHAT
   What is this topic?

2. IN WHAT CONTEXT
   In what broader context was this topic discussed?
   What is the relationship between participants?

3. ATTENTION ON WHAT ASPECT
   What aspects of this topic got the most attention?
   How did the focus evolve over time within this topic?

4. WHY IS IT DISCUSSED (if obvious)
   What is the underlying reason this topic came up?

Also provide an overall conversation summary:
   What is the overall purpose of this conversation?
   What is the attention trajectory across the full conversation
   (how did focus move between topics over time)?

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "topics": [
    {
      "about_what": "string",
      "in_what_context": "string",
      "attention_on_what_aspect": "string",
      "aspect_trajectory": "string or null",
      "why_discussed": "string or 'not obvious'",
      "prominence": 0.0-1.0
    }
  ],
  "overall_context": "string",
  "overall_attention_trajectory": "string",
  "overall_purpose": "string or 'not obvious'"
}

Order topics by prominence (highest first).
Prominence scores should sum to approximately 1.0.
```


## The Four Fields

Each window produces four fields. These fields are the atomic output of Topic Flow:

### 1. About What

The identity of the topic. What is being discussed. This answers Topic Flow's core question at each scale.

At immediate scale: "Redis performance after the migration"
At medium scale: "the migration project"
At long scale: "work planning and team coordination"

The hierarchy emerges naturally: immediate topics are subtopics of medium topics, which are subtopics of long topics.

### 2. In What Context

What broader conversation this topic sits within. This provides the reference frame that makes the topic meaningful.

"Redis performance" in the context of "evaluating the migration's success" is different from "Redis performance" in the context of "debugging a production incident." The topic identity is the same but the context changes what it means.

### 3. Attention on What Aspect

Which angle or facet of the topic is currently getting attention. This IS the topic focus that we defined in `desc.md`. It's what shifts during subtopic transitions.

"The migration project" with attention on "technical performance" is different from attention on "team burnout" or attention on "budget constraints." The about-what stays the same. The attention-on-what-aspect moves.

At medium and long windows, this field also captures how the aspect has shifted over time (the focus trajectory).

### 4. Why Is It Discussed

Whether the reason for discussing this topic is visible from the conversation. This is NOT Intent (why the PERSON is here). It's why THIS TOPIC came up.

"Because A asked about the project status" (prompted)
"Because the previous topic naturally led here" (drift)
"Because B deliberately changed the subject" (redirect)
"Not obvious" (unclear from context)

This field helps Topic Flow generate accurate topic events (explicit introduction, drift, prompted emergence, etc.) without needing a separate event classification step.


## How the Three Windows Relate

The three windows produce a natural topic hierarchy:

```
Long window (50+ msgs):
  about_what: "work planning"
  context: "quarterly planning session"
  
  └── Medium window (20 msgs):
       about_what: "the migration project"
       context: "evaluating whether migration is on track"
       
       └── Immediate window (3 msgs):
            about_what: "Redis latency numbers"
            context: "checking if performance targets are met"
```

The immediate topic is a subtopic of the medium topic, which is a subtopic of the long topic. The hierarchy is computed from the window outputs, not explicitly extracted.

### When Windows Disagree

Sometimes the immediate and medium windows will describe different topics. This means a topic shift occurred recently:

```
Medium window: about_what: "the migration project"
Immediate window: about_what: "weekend plans"
```

This disagreement IS the topic shift signal. The system detects: "the last 3 messages are about 'weekend plans' but the last 20 messages are about 'the migration project.' A topic shift occurred."

The shift point is somewhere in the last 3 messages. The why_discussed field tells you how it happened ("B explicitly changed the subject" vs "drifted naturally").


## Topic State Derivation

From the three windows, Topic Flow derives the topic state map:

```python
def derive_topic_state(immediate, medium, long):
    """Derive topic state from three window outputs."""
    
    # Active topic = immediate window's about_what
    active_topic = {
        "identity": immediate["about_what"],
        "focus": immediate["attention_on_what_aspect"],
        "context": immediate["in_what_context"],
        "state": "active",
    }
    
    # Check if immediate differs from medium
    if topics_differ(immediate["about_what"], medium["about_what"]):
        # The medium topic is now backgrounded
        backgrounded_topic = {
            "identity": medium["about_what"],
            "focus": medium["attention_on_what_aspect"],
            "state": "backgrounded",
        }
    
    # Check if medium differs from long
    if topics_differ(medium["about_what"], long.get("main_topics", [{}])[0].get("topic")):
        # There are dormant overarching topics
        pass
    
    return topic_state_map
```

### Topic Events Derivation

```python
def derive_topic_events(current_immediate, previous_immediate):
    """Detect topic events from consecutive immediate window outputs."""
    
    if previous_immediate is None:
        return [{"event": "blooming", "topic": current_immediate["about_what"]}]
    
    if topics_same(current_immediate["about_what"], previous_immediate["about_what"]):
        # Same topic
        if aspects_differ(
            current_immediate["attention_on_what_aspect"],
            previous_immediate["attention_on_what_aspect"]
        ):
            return [{"event": "subtopic_shift",
                     "from_focus": previous_immediate["attention_on_what_aspect"],
                     "to_focus": current_immediate["attention_on_what_aspect"]}]
        else:
            return [{"event": "continuation"}]
    
    else:
        # Different topic
        events = []
        
        # New topic bloomed
        why = current_immediate.get("why_discussed", "not obvious")
        if "redirect" in why.lower() or "changed" in why.lower():
            blooming_type = "explicit_introduction"
        elif "naturally" in why.lower() or "drift" in why.lower():
            blooming_type = "drift"
        elif "asked" in why.lower() or "prompted" in why.lower():
            blooming_type = "prompted_emergence"
        else:
            blooming_type = "explicit_introduction"
        
        events.append({
            "event": "blooming",
            "blooming_type": blooming_type,
            "topic": current_immediate["about_what"],
        })
        
        # Previous topic faded/backgrounded
        events.append({
            "event": "fading",
            "fading_type": "displacement",
            "topic": previous_immediate["about_what"],
        })
        
        return events
```


## Segment Boundary Detection

Segment boundaries are detected when the immediate window's about_what changes:

```python
def detect_segment_boundary(current_immediate, previous_immediate, message_id):
    """Detect segment boundary from consecutive immediate outputs."""
    
    if previous_immediate is None:
        return None
    
    if topics_differ(current_immediate["about_what"], previous_immediate["about_what"]):
        return {
            "boundary": True,
            "at_message": message_id,
            "from_topic": previous_immediate["about_what"],
            "to_topic": current_immediate["about_what"],
            "why": current_immediate.get("why_discussed"),
        }
    
    return None
```


## Per-Participant Attribution

The immediate window prompt can be extended to include attribution:

```
5. WHO DROVE THIS
   Looking at the last 3 messages, who is driving the topic?
   Who introduced it, who is sustaining it, who is following?
```

This produces per-message attribution without needing a separate analysis step:

```json
{
  "about_what": "Redis performance",
  "in_what_context": "evaluating migration success",
  "attention_on_what_aspect": "latency numbers",
  "why_discussed": "A asked about performance metrics",
  "who_drove": "A introduced, B is providing data"
}
```


## Output Format

### Per-Message Output (from immediate window)

```json
{
  "message_id": 15,
  "topic_flow": {
    "immediate": {
      "about_what": "Redis latency after migration",
      "in_what_context": "evaluating migration success",
      "attention_on_what_aspect": "specific latency numbers and targets",
      "why_discussed": "A asked for performance update"
    },
    "segment_id": "seg_003",
    "topic_event": "continuation",
    "is_subtopic_shift": false
  }
}
```

### Periodic Output (from medium window, every ~5 messages)

```json
{
  "as_of_message": 15,
  "topic_flow_medium": {
    "about_what": "the migration project",
    "subtopics": ["Redis performance", "team workload", "timeline"],
    "in_what_context": "quarterly review of project progress",
    "attention_on_what_aspect": "technical performance metrics",
    "aspect_shifted": true,
    "aspect_trajectory": "started with team issues, shifted to technical metrics",
    "why_discussed": "scheduled project review"
  }
}
```

### Conversation-Level Output (from long window)

```json
{
  "as_of_message": 50,
  "topic_flow_long": {
    "main_topics": [
      {"topic": "migration project", "prominence": 0.6},
      {"topic": "team dynamics", "prominence": 0.25},
      {"topic": "personal catch-up", "prominence": 0.15}
    ],
    "in_what_context": "ongoing work relationship between engineering leads",
    "attention_trajectory": "started personal, shifted to project, deepened into technical details",
    "overall_purpose": "project coordination with relational maintenance"
  }
}
```


## What PRAGMA Consumes

PRAGMA dimensions consume the immediate window output:

| Consumer | What it takes from Topic Flow |
|---|---|
| **Information Density** | `about_what` for relevance computation (is this message on-topic?). Segment boundaries for novelty (is this new within this topic?) |
| **Control Distribution** | `who_drove` for topic direction attribution. Segment boundaries for per-segment control measurement |
| **Expressed Involvement** | `about_what` for per-topic involvement aggregation |
| **Intent** | Segment boundaries for intent arc computation. `why_discussed` for context |
| **Investment** | Segment boundaries for per-topic investment patterns |


## Configuration

| Parameter | Default | Description |
|---|---|---|
| `immediate_window_focus` | 3 | Messages in the focus window for immediate analysis |
| `immediate_window_context` | 10 | Messages in the context window for immediate analysis |
| `medium_window_focus` | 20 | Messages in the focus window for medium analysis |
| `medium_window_context` | 30 | Messages in the context window for medium analysis |
| `long_window_size` | 50+ | Messages for long/full conversation analysis |
| `medium_frequency` | 5 | Run medium window every N messages |
| `long_frequency` | 10 | Run long window every N messages |
| `topics_differ_threshold` | LLM-based | Comparison is semantic, not string matching |


## Why This Approach Works

1. **No embeddings needed.** The LLM understands topics semantically. No vector math, no similarity thresholds, no clustering.

2. **Hierarchy emerges from window sizes.** Immediate topics are naturally subtopics of medium topics. No explicit hierarchy construction needed.

3. **Topic shifts detected from disagreement between windows.** When immediate differs from medium, a shift occurred. No separate shift detection mechanism.

4. **The four fields capture everything.** About-what = identity. Attention-on-what-aspect = focus. In-what-context = broader frame. Why-discussed = event type. All from one prompt.

5. **Testable independently.** Each window can be tested separately. Does the immediate window correctly identify the current topic? Does the medium window correctly summarize the recent discussion? Each is a self-contained LLM call with verifiable output.

6. **Sliding window handles evolution.** As the conversation progresses, the windows slide. Gradual topic drift is captured because the immediate window changes gradually. No need for explicit drift detection.