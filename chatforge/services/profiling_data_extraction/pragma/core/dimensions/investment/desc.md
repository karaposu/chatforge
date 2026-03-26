# Investment: Full Definition

**PRAGMA Dimension: Investment**
**Measurement: LLM-based semantic assessment per message**

**One-sentence definition:** Investment measures how much effort a participant is putting into a message, assessed semantically by understanding whether the response exceeds, meets, or falls short of what the conversational moment called for.


## What Investment Is

Investment measures EFFORT, not ACTIVATION. A person can invest heavily (carefully crafted response, thoughtful elaboration, unsolicited depth) while being completely uninvolved emotionally (going through motions). Or they can be highly activated (internally processing, preoccupied) while investing minimally (short response, delayed).

Investment is the observable effort. Involvement is the internal state. The GAP between them is one of the most diagnostic signals in PRAGMA.

**Why LLM, not mechanical:** A copy-paste of 500 words is mechanically "high investment" but semantically zero. A carefully crafted 10-word answer that perfectly addresses a complex question is mechanically "low investment" but semantically high. Word count and response time are proxies that miss the meaning. Only semantic understanding can assess whether someone actually invested effort in their response.

| Investment | Involvement | What it means |
|---|---|---|
| High | High | Genuine engagement |
| High | Low | Obligation, going through motions |
| Low | High | Activated but disengaging (frustrated? strategic?) |
| Low | Low | Checked out |


## The Two Sources

### Structural Investment

Observable from Message Properties. How much structural effort is being put in, regardless of content quality.

| Signal | What it measures | Source |
|---|---|---|
| **Response speed** | How quickly they responded to the previous message | Message Properties: response_latency_ms |
| **Message length** | How much they wrote (word count, character count) | Message Properties: word_count |
| **Initiation** | Did they start this exchange or respond to one? | Message Properties: is the first message in a new exchange after silence |
| **Silence breaking** | Did they break a silence? (higher investment than responding to an active thread) | Message Properties: is_silence_breaker |
| **Multi-message bursts** | Did they send multiple messages without waiting for response? (high investment, possibly urgency) | Message Properties: consecutive_own_messages |

### Content Investment

Observable from Raw Linguistic Features + Dialogic Function. How much substance and engagement is in the content, beyond just writing a lot.

| Signal | What it measures | Source |
|---|---|---|
| **Elaboration** | Detail beyond what was asked or required | Raw Linguistic Features: word_count relative to question specificity |
| **Unsolicited detail** | Information provided that wasn't requested | Detectable from Dialogic Function (transmitting/sharing without prior querying) |
| **Question-asking** | Asking follow-up questions (investing in the conversation's continuation) | Raw Linguistic Features: question_marks + Dialogic Function: querying |
| **Topic expansion** | Broadening the discussion beyond current scope | Topic Flow: did this message introduce subtopic or branch? |
| **Depth of reasoning** | Multi-step arguments, nuanced positions | Raw Linguistic Features: sentence_count, hedging_markers, certainty_markers, conjunction patterns |


## Why Investment Replaces Engagement + Interest

The original framework (CAF) had two separate dimensions:
- **Engagement Level**: desire to participate (highly engaged → attempting to disengage)
- **Interest Level**: attention to content (deeply interested → actively bored)

The problem: the observable signals for both are the same. Fast response, long messages, questions, elaboration. You can't distinguish "engaged but not interested" from "interested but not engaged" purely from message behavior. The internal distinction (do they WANT to be here vs do they CARE about the topic) is invisible to measurement.

Investment unifies them: one construct measuring observable effort. The internal distinction (why are they investing: desire, obligation, interest, fear?) is interpreted from context, not measured separately.

The signal gap `gap(investment, involvement)` captures what the two separate dimensions were trying to capture: someone who invests without being involved is going through motions. Someone involved without investing is strategically disengaging.


## Measurement: LLM Prompt

Investment is assessed per message via LLM call. Not mechanical heuristics.

### Prompt

```
=============================================================================
INVESTMENT ASSESSMENT
=============================================================================

You are assessing how much EFFORT the speaker put into this message.
Not how activated or emotional they are (that's involvement).
Not what they're trying to accomplish (that's intent).
How much EFFORT went into crafting this response.

IMPORTANT:
- Long does NOT automatically mean high effort. A copy-paste or
  rambling message can be long but low-effort.
- Short does NOT automatically mean low effort. A precise 10-word
  answer to a complex question can be very high-effort.
- Fast response does NOT automatically mean high effort. Quick
  reflexive replies can be zero-effort.

CONTEXT MESSAGES (for reference):
{context_messages}

TARGET MESSAGE:
Speaker: {sender}
Message: {content}

=============================================================================
INSTRUCTIONS
=============================================================================

Assess these three aspects of investment:

1. STRUCTURAL EFFORT
   Is this a quick/minimal response or a substantial one?
   Consider: length relative to what was asked, whether they
   initiated or responded, whether they broke a silence.
   Level: zero | low | moderate | high

2. CONTENT EFFORT
   Did they elaborate beyond what was needed?
   Did they provide unsolicited detail or depth?
   Did they ask follow-up questions (investing in continuation)?
   Did they expand the topic or bring new angles?

   The test: could they have responded with less and still
   been adequate? If yes, the extra is investment.
   Level: zero | low | moderate | high

3. OVERALL INVESTMENT
   Considering both structural and content effort:
   Level: zero | low | moderate | high | very_high

=============================================================================
OUTPUT
=============================================================================

Return JSON:
{
  "structural_effort": {
    "level": "zero|low|moderate|high",
    "evidence": "string"
  },
  "content_effort": {
    "level": "zero|low|moderate|high",
    "evidence": "string"
  },
  "overall_investment": "zero|low|moderate|high|very_high",
  "explanation": "1-2 sentences on why this investment level"
}
```

### Output

```json
{
  "message_id": 7,
  "sender": "participant_a",
  "investment": {
    "structural_effort": {
      "level": "moderate",
      "evidence": "Responded within minutes with a multi-sentence message"
    },
    "content_effort": {
      "level": "high",
      "evidence": "Elaborated beyond the question with comparison data and a follow-up question"
    },
    "overall_investment": "high",
    "explanation": "Provided more detail than asked for, including unsolicited comparison and a question to continue the discussion"
  }
}
```


## Aggregation

### Per Segment, Per Participant

```python
def aggregate_segment_investment(segment_messages, participant):
    msgs = [m for m in segment_messages if m.sender == participant]
    if not msgs:
        return None

    investments = [m.investment for m in msgs]

    return {
        "avg_structural": mean([i["structural"] for i in investments]),
        "avg_content": mean([i["content"] for i in investments]),
        "avg_combined": mean([i["combined"] for i in investments]),
        "trajectory": compute_trajectory(
            [i["combined"] for i in investments]
        ),
        "message_count": len(msgs),
    }
```

### Per Segment, Dyadic

```python
def compute_investment_asymmetry(a_agg, b_agg):
    if not a_agg or not b_agg:
        return None

    diff = a_agg["avg_combined"] - b_agg["avg_combined"]

    return {
        "more_invested": "a" if diff > 0.1 else "b" if diff < -0.1 else "balanced",
        "asymmetry_magnitude": abs(diff),
        "structural_asymmetry": a_agg["avg_structural"] - b_agg["avg_structural"],
        "content_asymmetry": a_agg["avg_content"] - b_agg["avg_content"],
    }
```


## Dependencies

| Dependency | What it provides | Required? |
|---|---|---|
| **Message Properties** | Response latency, word count, initiation, silence breaking | Yes (structural) |
| **Raw Linguistic Features** | Question marks, sentence count, hedging/certainty markers | Yes (content) |
| **Dialogic Function** | Whether sharing/explaining was solicited or unsolicited | Helpful |
| **Topic Flow** | Whether participant expanded the topic | Helpful |


## Downstream Consumers

| Consumer | What it uses |
|---|---|
| **Control Distribution** | Investment asymmetry feeds verbosity control effect assessment |
| **Signal Gaps** | gap(investment, involvement) = obligation/disengagement signal |
| **Signal Gaps** | gap(investment, density) = effort vs substance (waffling signal) |
| **Behavioral Profiling** | Cross-conversation investment patterns (consistently high/low investor) |
| **APT Inference** | Investment per topic per participant reveals where attention goes |


## What Investment Does NOT Cover

- **WHY** they're investing (motivation: interest, obligation, fear, hope). That's Intent + Interpretation Layer
- **HOW activated** they are internally (that's Expressed Involvement)
- **WHAT substance** they're producing (that's Information Density)
- **Strategic meaning** of investment patterns (that's Interpretation Layer)

Investment measures one thing: **how much observable effort is this person putting into this message.** Everything else is built on top.