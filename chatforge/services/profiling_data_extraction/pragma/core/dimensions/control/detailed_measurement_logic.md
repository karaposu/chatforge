# Control Distribution — Detailed Measurement Logic

Implementation specification for measuring Control Distribution across three mechanisms. A developer should be able to build this from this document alone.


## System Overview

```
Inputs:
  • Message Properties (word count, timestamps, sender)
  • Topic Flow (redirect events, topic attribution, segments)
  • Dialogic Function (per-message classification)
  • Expressed Involvement (evaluative force trajectory)

Step 1: Per-exchange mechanism detection
Step 2: Effect computation (did it work?)
Step 3: Per-segment aggregation
Step 4: Silence pattern detection
Step 5: Dyadic comparison
Step 6: Output to consumers
```


## Step 1: Per-Exchange Mechanism Detection

For each message, detect control moves across all three mechanisms.

### 1a: Verbosity Signals

**Source:** Message Properties
**Runs on:** Every message (mechanical, zero cost)

```python
def compute_verbosity_signals(msg, conversation_history):
    participant_msgs = [m for m in conversation_history if m.sender == msg.sender]
    other_msgs = [m for m in conversation_history if m.sender != msg.sender]

    return {
        "word_count": msg.word_count,
        "word_count_ratio": (
            sum(m.word_count for m in participant_msgs) /
            max(sum(m.word_count for m in conversation_history), 1)
        ),
        "consecutive_own_messages": count_consecutive_from_sender(
            msg.sender, conversation_history, msg.position
        ),
        "is_monologue": consecutive_own_messages >= 3,
        "length_relative_to_other": (
            msg.word_count /
            max(mean_word_count(other_msgs), 1)
        ),
    }
```

### 1b: Topic Direction Signals

**Source:** Topic Flow + Dialogic Function
**Runs on:** Every message (mechanical — computed from existing signals)

```python
def detect_direction_move(msg, topic_flow, dialogic_function):
    move = {
        "is_redirect_attempt": False,
        "redirect_type": None,
        "is_topic_introduction": False,
        "is_topic_block": False,
    }

    # Check Topic Flow for shift events
    topic_event = topic_flow.get_event_at(msg.message_id)

    if topic_event:
        if topic_event.type == "explicit_introduction":
            move["is_topic_introduction"] = True
            move["is_redirect_attempt"] = True
            move["redirect_type"] = "introduction"

        elif topic_event.type in ("drift", "prompted_emergence"):
            move["is_redirect_attempt"] = True
            move["redirect_type"] = "shift"

        elif topic_event.type == "branch":
            move["is_redirect_attempt"] = True
            move["redirect_type"] = "branch"

    # Divergent questions as redirect attempts
    df = dialogic_function.get(msg.message_id)
    if df and df.primary == "querying":
        # Check if the question diverges from current topic
        if topic_flow.is_divergent_from_current(msg):
            move["is_redirect_attempt"] = True
            move["redirect_type"] = "divergent_question"

    # Topic blocking: continuing own topic when other tried to shift
    prev_msg = get_previous_message(conversation_history, msg.position)
    if prev_msg and prev_msg.sender != msg.sender:
        prev_event = topic_flow.get_event_at(prev_msg.message_id)
        if prev_event and prev_event.type in ("explicit_introduction", "drift"):
            # Other person tried to shift, did this message follow or hold?
            if topic_flow.continues_pre_shift_topic(msg):
                move["is_topic_block"] = True

    return move
```

### 1c: Emotional Register Signals

**Source:** Expressed Involvement (evaluative force trajectory)
**Runs on:** Messages where Expressed Involvement data is available (semantic tier)

```python
def detect_register_move(msg, involvement_history):
    current = involvement_history.get(msg.message_id)
    previous_own = involvement_history.get_previous_for(msg.sender)

    if not current or not previous_own:
        return {"is_register_shift": False}

    # Detect shift in evaluative force direction
    direction_changed = (
        current.evaluative_force.direction != previous_own.evaluative_force.direction
    )

    # Detect shift in intensity
    intensity_diff = abs(current.involvement_score - previous_own.involvement_score)
    intensity_changed = intensity_diff > 0.25

    if direction_changed or intensity_changed:
        return {
            "is_register_shift": True,
            "shift_type": "direction" if direction_changed else "intensity",
            "from": {
                "direction": previous_own.evaluative_force.direction,
                "intensity": previous_own.involvement_score,
            },
            "to": {
                "direction": current.evaluative_force.direction,
                "intensity": current.involvement_score,
            },
        }

    return {"is_register_shift": False}
```


## Step 2: Effect Computation

For each detected mechanism move, check the next message(s) from the other participant to determine effect.

### 2a: Verbosity Effect

```python
def compute_verbosity_effect(verbose_msg, next_response):
    """Did the other person engage with the verbose content?"""
    if not next_response:
        return {"effect": "no_response", "success": False}

    # Short response to long message = low engagement
    length_ratio = next_response.word_count / max(verbose_msg.word_count, 1)

    # Check if response addresses content of verbose message
    # (requires Topic Flow — does response continue same topic?)
    continues_topic = topic_flow.same_topic(verbose_msg, next_response)

    # Check if response redirects away
    is_redirect = detect_direction_move(next_response, ...).is_redirect_attempt

    if is_redirect:
        return {"effect": "redirected", "success": False}
    elif continues_topic and length_ratio > 0.2:
        return {"effect": "engaged", "success": True}
    elif continues_topic and length_ratio <= 0.2:
        return {"effect": "minimal_ack", "success": False}
    else:
        return {"effect": "ignored", "success": False}
```

### 2b: Topic Direction Effect

```python
def compute_direction_effect(redirect_msg, next_response):
    """Did the other person follow the redirect?"""
    if not next_response:
        return {"effect": "no_response", "success": False}

    redirect_topic = topic_flow.get_topic_at(redirect_msg.message_id)
    response_topic = topic_flow.get_topic_at(next_response.message_id)

    if response_topic == redirect_topic:
        # They followed the new topic
        return {"effect": "followed", "success": True}

    pre_redirect_topic = topic_flow.get_previous_topic(redirect_msg.message_id)
    if response_topic == pre_redirect_topic:
        # They returned to the previous topic — held/counter-redirected
        # Check if they actively blocked (continued immediately)
        if next_response.response_latency_ms < 5000:
            return {"effect": "blocked", "success": False, "active_block": True}
        else:
            return {"effect": "held", "success": False, "active_block": False}

    # Went to a third topic — counter-redirect
    return {"effect": "counter_redirected", "success": False}
```

### 2c: Emotional Register Effect

```python
def compute_register_effect(shift_msg, next_responses, window=2):
    """Did the other person's emotional state follow the shift?"""
    shifter = shift_msg.sender
    shift_direction = detect_register_move(shift_msg, ...).to.direction
    shift_intensity = detect_register_move(shift_msg, ...).to.intensity

    # Check next 1-2 messages from other participant
    other_responses = [
        r for r in next_responses
        if r.sender != shifter
    ][:window]

    if not other_responses:
        return {"effect": "no_response", "success": False}

    for response in other_responses:
        resp_involvement = involvement_history.get(response.message_id)
        if not resp_involvement:
            continue

        # Did their direction match the shift?
        direction_followed = (
            resp_involvement.evaluative_force.direction == shift_direction
        )

        # Did their intensity move toward the shift?
        resp_intensity = resp_involvement.involvement_score
        prev_resp_intensity = involvement_history.get_previous_for(response.sender)
        if prev_resp_intensity:
            intensity_moved_toward = (
                abs(resp_intensity - shift_intensity) <
                abs(prev_resp_intensity.involvement_score - shift_intensity)
            )
        else:
            intensity_moved_toward = False

        if direction_followed or intensity_moved_toward:
            return {
                "effect": "followed",
                "success": True,
                "lag_messages": response.position - shift_msg.position,
            }

    return {"effect": "held_own", "success": False}
```


## Step 3: Per-Segment Aggregation

Aggregate mechanism moves + effects per topic segment per participant.

```python
def aggregate_segment_control(segment, participants):
    result = {}

    for participant in participants:
        msgs = segment.messages_by(participant)

        # Verbosity
        total_words = sum(m.word_count for m in msgs)
        segment_words = sum(m.word_count for m in segment.all_messages)
        verbosity_ratio = total_words / max(segment_words, 1)

        verbose_moves = [m for m in msgs if m.word_count > segment_avg_length * 1.5]
        verbosity_effects = [compute_verbosity_effect(m, get_next_response(m)) for m in verbose_moves]
        verbosity_success = (
            sum(1 for e in verbosity_effects if e["success"]) /
            max(len(verbosity_effects), 1)
        )

        # Topic Direction
        direction_moves = [m for m in msgs if detect_direction_move(m, ...).is_redirect_attempt]
        direction_effects = [compute_direction_effect(m, get_next_response(m)) for m in direction_moves]
        direction_success = (
            sum(1 for e in direction_effects if e["success"]) /
            max(len(direction_effects), 1)
        )
        active_blocks = sum(1 for e in direction_effects if e.get("active_block"))

        # Emotional Register
        register_moves = [m for m in msgs if detect_register_move(m, ...).get("is_register_shift")]
        register_effects = [compute_register_effect(m, get_next_responses(m)) for m in register_moves]
        register_success = (
            sum(1 for e in register_effects if e["success"]) /
            max(len(register_effects), 1)
        )

        result[participant] = {
            "verbosity": {
                "ratio": verbosity_ratio,
                "effect_success_rate": verbosity_success,
                "moves": len(verbose_moves),
            },
            "topic_direction": {
                "redirect_attempts": len(direction_moves),
                "effect_success_rate": direction_success,
                "blocks_received": active_blocks,
            },
            "emotional_register": {
                "shifts_initiated": len(register_moves),
                "effect_success_rate": register_success,
            },
        }

    return result
```

### Output — Per Segment

```json
{
  "segment_id": "t_002",
  "control": {
    "participant_a": {
      "verbosity": {
        "ratio": 0.72,
        "effect_success_rate": 0.60,
        "moves": 4
      },
      "topic_direction": {
        "redirect_attempts": 2,
        "effect_success_rate": 0.50,
        "blocks_received": 0
      },
      "emotional_register": {
        "shifts_initiated": 1,
        "effect_success_rate": 0.0
      }
    },
    "participant_b": {
      "verbosity": {
        "ratio": 0.28,
        "effect_success_rate": 0.90,
        "moves": 0
      },
      "topic_direction": {
        "redirect_attempts": 1,
        "effect_success_rate": 1.0,
        "blocks_received": 0
      },
      "emotional_register": {
        "shifts_initiated": 2,
        "effect_success_rate": 1.0
      }
    }
  }
}
```


## Step 4: Silence Pattern Detection

**Source:** Message Properties
**Runs on:** Conversation-level analysis

```python
def detect_silence_control(conversation, silence_threshold_ms=3600000):
    """Detect control through withdrawal/silence."""
    patterns = []

    for i, msg in enumerate(conversation.messages):
        # Find gaps where one participant is silent
        if msg.response_latency_ms > silence_threshold_ms:
            silent_participant = get_expected_responder(conversation, i)
            active_participant = msg.sender

            # Check if active participant shows reactive behavior
            recent_msgs = get_messages_after_silence_start(conversation, i, window=5)
            active_msgs = [m for m in recent_msgs if m.sender == active_participant]

            if len(active_msgs) >= 2:
                # Increasing frequency?
                frequency_increasing = is_frequency_increasing(active_msgs)

                # Topic shift to engagement-seeking?
                topics_shifted_to_concern = any(
                    is_engagement_seeking(m) for m in active_msgs
                )

                # Register shift to anxiety/concern?
                register_shifted = any(
                    involvement_history.get(m.message_id) and
                    involvement_history.get(m.message_id).evaluative_force.direction in ("negative", "mixed")
                    for m in active_msgs
                )

                if frequency_increasing or topics_shifted_to_concern or register_shifted:
                    patterns.append({
                        "type": "silence_control",
                        "silent_participant": silent_participant,
                        "active_participant": active_participant,
                        "duration_ms": msg.response_latency_ms,
                        "reactive_signals": {
                            "frequency_increasing": frequency_increasing,
                            "topic_shifted_to_concern": topics_shifted_to_concern,
                            "register_shifted": register_shifted,
                        },
                    })

    return patterns
```


## Step 5: Dyadic Comparison

Compare control profiles between participants.

```python
def compute_control_asymmetry(segment_control):
    """Compare control profiles between two participants."""
    a = segment_control["participant_a"]
    b = segment_control["participant_b"]

    return {
        "verbosity_asymmetry": {
            "dominant": "a" if a["verbosity"]["ratio"] > 0.6 else "b" if b["verbosity"]["ratio"] > 0.6 else "balanced",
            "effective": "a" if a["verbosity"]["effect_success_rate"] > b["verbosity"]["effect_success_rate"] else "b",
        },
        "direction_asymmetry": {
            "more_attempts": "a" if a["topic_direction"]["redirect_attempts"] > b["topic_direction"]["redirect_attempts"] else "b",
            "more_successful": "a" if a["topic_direction"]["effect_success_rate"] > b["topic_direction"]["effect_success_rate"] else "b",
        },
        "register_asymmetry": {
            "leader": "a" if a["emotional_register"]["effect_success_rate"] > b["emotional_register"]["effect_success_rate"] else "b",
        },
        "overall_control": determine_overall_control(a, b),
    }

def determine_overall_control(a, b):
    """Who has overall control? Weighted by mechanism importance."""
    a_score = (
        a["verbosity"]["effect_success_rate"] * 0.2 +
        a["topic_direction"]["effect_success_rate"] * 0.4 +
        a["emotional_register"]["effect_success_rate"] * 0.4
    )
    b_score = (
        b["verbosity"]["effect_success_rate"] * 0.2 +
        b["topic_direction"]["effect_success_rate"] * 0.4 +
        b["emotional_register"]["effect_success_rate"] * 0.4
    )

    if abs(a_score - b_score) < 0.1:
        return "balanced"
    return "a" if a_score > b_score else "b"
```

**Weighting rationale:** Topic direction and emotional register are weighted equally (0.4 each) because both indicate genuine control. Verbosity is weighted lower (0.2) because high verbosity often corresponds to low actual control (performing, not controlling).

### Multi-Party Extension

```python
def compute_multiparty_effect(redirect_msg, all_participants, responses):
    """Effect as proportion of group."""
    other_participants = [p for p in all_participants if p != redirect_msg.sender]
    followed = 0

    for participant in other_participants:
        response = next((r for r in responses if r.sender == participant), None)
        if response:
            effect = compute_direction_effect(redirect_msg, response)
            if effect["success"]:
                followed += 1

    return {
        "followed": followed,
        "total_others": len(other_participants),
        "success_rate": followed / max(len(other_participants), 1),
    }
```


## Step 6: Output to Consumers

### To Dynamics Profile

```json
{
  "dimension": "control_distribution",
  "segment": "t_002",
  "value": {
    "dominant_controller": "b",
    "verbosity_holder": "a",
    "direction_holder": "b",
    "register_holder": "b",
    "label": "B controls through direction and register despite A's verbosity"
  }
}
```

### To APT Inference

```json
{
  "control_patterns": {
    "a_yields_direction_to_b": true,
    "a_follows_b_register": true,
    "a_verbosity_increases_when_b_redirects": true,
    "interpretation_hint": "A may be performing for B (charm reversed)"
  }
}
```

### To Signal Gaps

```json
{
  "signal_gaps": [
    {
      "gap": "verbosity_vs_direction_effect",
      "participant": "a",
      "verbosity_ratio": 0.72,
      "direction_success": 0.50,
      "magnitude": 0.22,
      "hint": "High volume, moderate direction control — performing?"
    },
    {
      "gap": "involvement_vs_control_effect",
      "participant": "b",
      "involvement": 0.65,
      "register_control_success": 1.0,
      "direction_control_success": 1.0,
      "hint": "High involvement with high control — genuine authority"
    }
  ]
}
```

### To Behavioral Profiling

```json
{
  "participant": "a",
  "control_profile": {
    "primary_mechanism": "verbosity",
    "verbosity_avg_ratio": 0.68,
    "direction_avg_success": 0.55,
    "register_avg_success": 0.30,
    "pattern": "Controls through volume. Yields direction and register when challenged.",
    "consistency": "stable across 5 conversations"
  }
}
```


## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `verbosity_high_threshold` | 1.5 | Word count multiplier over segment average to count as verbose move |
| `silence_threshold_ms` | 3600000 | Gap duration (ms) to trigger silence control detection |
| `register_shift_threshold` | 0.25 | Involvement score change to count as register shift |
| `register_follow_window` | 2 | Messages to check for register following |
| `active_block_latency_ms` | 5000 | Response time threshold for active blocking vs passive holding |
| `multiparty_min_follow` | 0.5 | Proportion of group needed to count as successful redirect in multi-party |
| `direction_weight` | 0.4 | Weight of topic direction in overall control score |
| `register_weight` | 0.4 | Weight of emotional register in overall control score |
| `verbosity_weight` | 0.2 | Weight of verbosity in overall control score |


## Data Flow Summary

```
Message arrives
     │
     ├── Step 1a: Verbosity signals (mechanical, every message)
     ├── Step 1b: Direction signals (from Topic Flow + Dialogic Function)
     └── Step 1c: Register signals (from Expressed Involvement, when available)
              │
              ▼
     Step 2: Effect computation for each detected move
              │
              ▼
     Step 3: Aggregate per segment per participant
              │
              ├── Step 4: Silence pattern detection (conversation-level)
              │
              ▼
     Step 5: Dyadic/multi-party comparison
              │
              ▼
     Step 6: Output to consumers
              ├── Dynamics Profile → Control Distribution dimension
              ├── APT Inference → control patterns for charm/hope/fear
              ├── Signal Gaps → verbosity vs direction, involvement vs control
              └── Behavioral Profiling → stable control style
```