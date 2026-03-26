# Dynamics Profile — Specification

**Layer:** 2 of 3 within PRAGMA
**Epistemological status:** DESCRIPTION
**Method:** LLM-composed, one call per topic segment
**Input:** Aggregated Signal Layer outputs (Level 2-3 per dimension)
**Output:** Natural language description of what's happening in this segment, per participant and dyadic


## What the Dynamics Profile Is

The Dynamics Profile is the composition layer. It takes the Signal Layer's scores, trajectories, asymmetries, and signal gaps for a topic segment and composes them into a natural language description of the conversational dynamics.

It answers: **"What is happening in this segment?"**

It does NOT answer: "What does it mean?" (that's the Interpretation Layer).

```
Signal Layer produces (per segment):
  Numbers, vectors, labels, trajectories, asymmetries, gaps

Dynamics Profile composes:
  "A is driving this segment with high involvement and topic control.
   B is responding with high density but low novelty, restating
   prior points with added detail. Investment is asymmetric: A's
   is high and increasing, B's is high but involvement is moderate.
   The involvement-investment gap for B is 0.38."

Interpretation Layer reads the description and interprets:
  "B appears to be performing engagement while emotionally checked out.
   A's high involvement + topic control + discover intent suggests A
   is testing whether B is genuinely committed. Confidence: 0.65."
```


## Why LLM Composition

The combinatorial space of 7 dimensions x 2 participants x sub-components x trajectories x signal gaps is too large for templates. An LLM can:

1. **Prioritize** what matters. Not every dimension is interesting in every segment. If control is balanced and unremarkable, don't mention it. If there's a dramatic involvement-investment gap, lead with that.
2. **Compose across dimensions.** "High involvement but low investment" is a single insight that spans two dimensions. Templates handle individual dimensions; LLMs handle interactions.
3. **Compress.** A segment might have 50+ data points across all dimensions. The Dynamics Profile produces a paragraph that captures the essential dynamics, discarding noise.
4. **Prepare for interpretation.** The Interpretation Layer reads natural language, not JSON. The Dynamics Profile is a reasoning step that makes interpretation more focused and accurate.


## What It Receives

The Dynamics Profile LLM call receives the aggregated Signal Layer outputs for one topic segment. Specifically:

```
SEGMENT CONTEXT:
  Segment ID, topic label, message range, participants

PER PARTICIPANT (Level 2 aggregation):
  Expressed Involvement:
    avg micro-signals, trajectory, dominant signals
  Intent:
    dominant category, intent arc (if multi-message), confidence
  Information Density:
    avg specificity, avg novelty, avg relevance, trajectory
  Investment:
    avg score, trajectory
  Dialogic Function:
    dominant functions, function distribution
  Control Distribution:
    verbosity share, topic direction attempts, emotional register,
    effect (success rate)

DYADIC (Level 3 aggregation):
  Involvement asymmetry (who is more activated)
  Density asymmetry (who provides more substance)
  Investment asymmetry (who puts in more effort)
  Control balance (who controls what)

SIGNAL GAPS (computed from above):
  gap(investment, involvement) per participant
  gap(density, relevance) per participant
  gap(specificity, novelty) per participant
  gap(verbosity, control_effect) per participant
  gap(classified_intent, behavioral_signals) per participant
  Any gap with magnitude > 0.3 is flagged
```


## LLM Prompt Structure

```
You are composing a Dynamics Profile for a conversation segment.
Your job is to DESCRIBE what is happening, not INTERPRET why.

SEGMENT:
Topic: {topic_label}
Messages: {message_range} ({message_count} messages)
Participants: {participant_list}

AGGREGATED SIGNALS:

{per_participant_signals}

DYADIC COMPARISONS:

{dyadic_signals}

SIGNAL GAPS (magnitude > 0.3 only):

{flagged_signal_gaps}

Compose a natural language description of the conversational dynamics
in this segment. Follow these rules:

1. DESCRIBE, don't interpret. You compose what IS HAPPENING.
   The Interpretation Layer decides what it MEANS.

   ALLOWED (compositional observations):
   - "A's involvement is high while investment is low. Gap: 0.42."
   - "B's density is high but novelty is low, restating prior points
     with added precision."
   - "A controls topic direction (3 of 4 redirects followed) while
     B dominates verbosity."
   - "B's involvement trajectory is decreasing across this segment."

   NOT ALLOWED (causal claims, motive attribution):
   - "A seems disengaged." (motive)
   - "B is performing engagement." (motive)
   - "A is testing B's commitment." (strategic inference)
   - "The gap suggests obligation rather than genuine interest." (causal)
   - "B appears to be avoiding the topic." (interpretation)

   The test: if it uses words like "seems," "suggests," "appears to be,"
   "trying to," "in order to," or attributes a WHY — it's interpretation.
   Rewrite it as a WHAT.

2. Only describe what the data shows. Do not narrativize beyond
   what the aggregated signals support. If control is balanced
   and unremarkable, say "control is balanced" not "the conversation
   flows harmoniously." Stay grounded in the numbers.

3. Lead with what's interesting. If all dimensions are unremarkable,
   say so briefly. If there's a dramatic asymmetry or gap, lead
   with that.

4. Cover each participant. What is each person doing in this segment?
   Their involvement, effort, substance, intent, and function.

5. Note asymmetries. Where participants differ significantly,
   describe the difference with numbers.

6. Flag signal gaps. These are the most diagnostic features.
   Name them explicitly with magnitudes: "gap between A's investment
   and involvement is 0.45."

7. Include trajectories. Is involvement increasing or decreasing?
   Is density stable? Trajectories tell more than snapshots.

8. Handle short segments. If the segment has fewer than 4 messages,
   trajectories are unreliable. Focus on per-message signals
   rather than aggregated patterns. Note that trajectory data
   is insufficient.

9. Be concise. One paragraph per participant, one paragraph for
   dyadic dynamics and gaps. No more than 3-4 paragraphs total.

Respond with:
{
  "segment_id": "{segment_id}",
  "dynamics_profile": "<natural language description>",
  "headline": "<one sentence summary of the most notable dynamic>",
  "notable_gaps": [
    {
      "gap": "<gap name>",
      "participant": "<who>",
      "magnitude": <float>,
      "description": "<one sentence>"
    }
  ]
}
```


## Output Structure

```json
{
  "segment_id": "t_003",
  "topic": "system performance discussion",
  "dynamics_profile": "A drives this segment with high expressed involvement (strong self-reference and temporal involvement, trajectory increasing) and discover intent. A asks probing questions and steers topic direction, despite B producing more words. B responds with high information density (specificity 0.7, novelty 0.4, relevance 0.8) but low novelty, rehashing prior technical details with added precision rather than introducing new information. B's investment is high (long responses, fast reply times) but involvement is moderate and stable. The involvement-investment gap for B is 0.38, the largest gap in this segment. Control is split: B dominates verbosity, A controls topic direction with high effect (3 of 4 redirects followed). Density asymmetry favors B (0.72 vs A's 0.35), but A's lower density reflects querying function rather than low substance.",
  "headline": "A probes with high involvement while B responds with detailed but repetitive substance.",
  "notable_gaps": [
    {
      "gap": "investment_vs_involvement",
      "participant": "B",
      "magnitude": 0.38,
      "description": "B's investment is high (long responses, fast reply times) but expressed involvement is moderate and stable. Gap magnitude: 0.38."
    },
    {
      "gap": "specificity_vs_novelty",
      "participant": "B",
      "magnitude": 0.30,
      "description": "B's specificity is 0.7 but novelty is 0.4. Prior points are being restated with added precision rather than new information introduced."
    }
  ]
}
```


## When It Runs

The Dynamics Profile runs **once per completed topic segment**. Not per message.

A topic segment completes when Topic Flow detects a dominant topic change (new segment begins). At that point, the system has all per-message signals for the completed segment, computes Level 2-3 aggregations mechanically, and then runs the Dynamics Profile LLM call to compose the description.

For the currently active (incomplete) segment, the Dynamics Profile can be computed on-demand with available data, but it updates when the segment closes.


## What the Dynamics Profile Does NOT Do

- **Interpret.** "B seems disengaged" is interpretation. "B's involvement is low while investment is high" is description. The Dynamics Profile stays on the description side.
- **Extract new signals.** No new measurements. Everything comes from Signal Layer aggregations.
- **Score or classify.** No new scores. It reads existing scores and describes them.
- **Attribute motive.** "A is trying to charm B" is Interpretation Layer. "A's involvement increases specifically when B shares expertise" is description.


## Downstream Consumers

| Consumer | What it reads | How |
|---|---|---|
| **Interpretation Layer** | The `dynamics_profile` text | As input to tension/subtext/strategy queries |
| **APT Inference** | The `dynamics_profile` + `notable_gaps` | As input to charm/hope/fear mapping |
| **Human analyst** | The `headline` + `dynamics_profile` | As readable summary of segment dynamics |
| **Behavioral Profiling** | Cross-segment dynamics profiles | Aggregated patterns across conversations |


## Temporal Structure

Temporal Structure (PRAGMA dimension 7) is per-conversation, not per-segment. It describes the shape of the whole conversation (linear, circular, branching, fragmented).

The Dynamics Profile does NOT include Temporal Structure. It describes dynamics within a single segment. Temporal Structure is computed after all segments are known, and feeds into per-conversation summary, not per-segment Dynamics Profile.

If a per-conversation Dynamics Profile is needed (aggregating across all segments), Temporal Structure would be part of that. But the per-segment DP handles the 6 segment-level dimensions only.


## Cost

One LLM call per topic segment. A typical conversation has 3-8 topic segments. So the Dynamics Profile adds 3-8 LLM calls per conversation, not per message.

This is significantly cheaper than per-message calls because segments are the natural unit for composed description. Per-message dynamics profiles would be redundant (most messages don't change the overall picture) and expensive.