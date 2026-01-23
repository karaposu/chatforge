# Batch CPDE-7 Improvement: Target-Only Extraction

## Current Behavior

The batch prompts (`batch_prompts.py`) extract profiling data from **ALL messages** in the batch:

```
=== MESSAGES TO ANALYZE ===
{messages}
```

The LLM extracts from any message containing relevant information, tagging each item with `source_message_id`.

## The Problem

When profiling conversational data between a user and an AI assistant (or any two parties), extracting from ALL messages can be problematic:

### Example: AI Assistant Makes Assumptions

```
Assistant: "You seem like someone who values efficiency over relationships..."
User: "Yeah, I guess that's true"
```

Current batch behavior extracts:
- From Assistant message: `{aspect: "personality", value: "values efficiency over relationships"}`
- From User message: `{aspect: "personality", value: "values efficiency over relationships"}` (confirmation)

**Problem:** The assistant's assumption becomes a profile fact, even though:
1. The user only weakly confirmed ("I guess")
2. The insight originated from the AI, not the user
3. The AI might be wrong or manipulating

### Example: AI Reflects Back Information

```
Assistant: "So you're telling me you're a 34-year-old engineer who hates criticism and struggles with your daughter..."
User: "Yes, exactly"
```

Current behavior extracts rich data from the assistant's summary. But this data was already extracted when the user originally said it - now it's duplicated and attributed to the assistant's reflection.

### Example: AI Probes With Leading Questions

```
Assistant: "Are you afraid of being abandoned? That would explain your behavior..."
User: "Maybe, I don't know"
```

Current behavior might extract: `{type: "fear", target: "abandonment"}`

**Problem:** This was an AI hypothesis, not a user statement. The user expressed uncertainty.

---

## Proposed Improvement

### New Batch Format: Target + Context

```
=== CONTEXT MESSAGES (use for understanding, do NOT extract from) ===
{context_messages}

=== TARGET MESSAGES (extract ONLY from these) ===
{target_messages}
```

### How It Works

1. **All messages** are sent to the LLM for full conversational context
2. **Only target messages** (e.g., user messages) are sources for extraction
3. Context messages help the LLM understand references and meaning
4. Extracted items can ONLY have `source_message_id` from target messages

### Implementation Options

#### Option A: Separate Placeholders

```python
CPDE_ALL_7_BATCH_TARGETED = """
Your job is to extract profiling data from the TARGET MESSAGES below.
Use CONTEXT MESSAGES to understand references and conversation flow,
but ONLY extract information explicitly stated in TARGET MESSAGES.

CRITICAL RULE:
- source_message_id MUST reference a TARGET MESSAGE
- Do NOT extract facts stated only in CONTEXT MESSAGES
- If a TARGET MESSAGE confirms something from CONTEXT, extract it

=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGES (extract from these) ===
{target_messages}

... rest of dimension definitions ...
"""
```

#### Option B: Inline Markers

```python
# Format messages with role markers
messages = """
Message ID: msg_1
Role: assistant (CONTEXT ONLY)
Content: What do you do for work?

Message ID: msg_2
Role: user (EXTRACT FROM THIS)
Content: I'm an engineer at Google

Message ID: msg_3
Role: assistant (CONTEXT ONLY)
Content: That's interesting! You must value technical challenges.

Message ID: msg_4
Role: user (EXTRACT FROM THIS)
Content: Yes, I love solving hard problems
"""
```

With prompt instruction:
```
CRITICAL: Only extract from messages marked "(EXTRACT FROM THIS)"
Messages marked "(CONTEXT ONLY)" are for understanding references only.
```

#### Option C: Post-Extraction Filtering

Keep current batch prompt, but filter results:

```python
async def extract_from_targets_only(
    self,
    all_messages: str,
    target_message_ids: Set[str]
) -> BatchAll7Output:
    # Get all extractions
    result = await self.extract_all_7(all_messages)

    # Filter to only target sources
    for dimension_name, dimension_result in result:
        if dimension_result and dimension_result.items:
            dimension_result.items = [
                item for item in dimension_result.items
                if item.source_message_id in target_message_ids
            ]
            dimension_result.has_content = len(dimension_result.items) > 0

    return result
```

**Pros:** No prompt changes needed
**Cons:** Wastes tokens extracting data that gets filtered out

---

## Why This Matters

### 1. Profile Accuracy

Profiles should reflect what the **user actually stated**, not:
- AI assumptions
- AI hypotheses
- AI reflections/summaries
- Leading questions the user didn't clearly confirm

### 2. Manipulation Resistance

In adversarial or persuasion contexts (games, therapy bots, sales), the AI might:
- Plant ideas and get weak confirmations
- Reflect back exaggerated versions of what user said
- Make assumptions to test reactions

Extracting from AI messages captures these as "facts."

### 3. Deduplication

When AI summarizes ("So you're Ali, an engineer..."), extracting from both:
- Original user statement
- AI summary

Creates duplicate profile entries from the same underlying fact.

### 4. Attribution Clarity

With target-only extraction:
- Every profile fact traces to something the **user explicitly said**
- Easier to audit and verify
- Clearer provenance for sensitive applications (healthcare, legal)

### 5. Confirmation Handling

Target-only extraction with context awareness handles confirmations correctly:

```
Assistant: "So you're saying you hate your job?"
User: "Yes, exactly"
```

The LLM sees the context and extracts from the user's "Yes, exactly":
- `{about: "job", view: "hates it", source_message_id: "msg_user_2"}`

The context helps interpret the confirmation, but the extraction comes from the user message.

---

## Recommended Approach

**Option A (Separate Placeholders)** is recommended because:

1. **Explicit separation** - Clear boundary between context and targets
2. **No prompt hacking** - Can't trick LLM by putting "EXTRACT FROM THIS" in message content
3. **Flexible** - Caller decides what's context vs target
4. **Clean API** - Two parameters instead of mixed format

### API Design

```python
async def extract_all_7_targeted(
    self,
    target_messages: str,
    context_messages: str = ""
) -> BatchAll7Output:
    """
    Extract from target messages only, using context for understanding.

    Args:
        target_messages: Messages to extract from (formatted with IDs)
        context_messages: Messages for context only (not extracted from)

    Returns:
        BatchAll7Output with items only from target_messages
    """
    prompt = CPDE_ALL_7_BATCH_TARGETED.format(
        target_messages=target_messages,
        context_messages=context_messages
    )
    ...
```

### Usage Example

```python
# Separate user vs assistant messages
user_messages = format_messages([m for m in messages if m.role == "user"])
assistant_messages = format_messages([m for m in messages if m.role == "assistant"])

# Extract only from user messages, using assistant messages for context
result = await service.extract_all_7_targeted(
    target_messages=user_messages,
    context_messages=assistant_messages
)
```

---

## Applications

| Application | Target Messages | Context Messages |
|-------------|-----------------|------------------|
| User profiling from chat | User messages | Assistant messages |
| Customer support analysis | Customer messages | Agent messages |
| Interview analysis | Interviewee messages | Interviewer messages |
| Therapy session profiling | Patient messages | Therapist messages |
| Game character profiling | Player messages | NPC messages |
| Sales call analysis | Prospect messages | Sales rep messages |

---

## Migration Path

1. **Add new method** `extract_all_7_targeted()` alongside existing `extract_all_7()`
2. **Add new prompt** `CPDE_ALL_7_BATCH_TARGETED` alongside existing
3. **Existing code** continues working unchanged
4. **New applications** can opt into targeted extraction

---

## Summary

Current batch extraction extracts from all messages, which can capture AI assumptions and hypotheses as profile facts. Adding a targeted extraction mode that uses all messages for context but only extracts from specified target messages provides:

- More accurate profiles
- Resistance to manipulation
- Better deduplication
- Clearer attribution
- Proper confirmation handling

This is especially important for applications where the AI might make assumptions, lead the conversation, or summarize/reflect user statements.
