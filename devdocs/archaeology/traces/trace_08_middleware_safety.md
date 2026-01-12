# Trace 08: Safety Guardrail Middleware

LLM-based validation of agent responses for safety and appropriateness. Post-processing filter.

---

## Entry Point

**File:** `chatforge/middleware/safety.py:107`
**Class:** `SafetyGuardrail`

**Primary Methods:**
```python
async def check_response(self, response: str) -> SafetyCheckResult
def check_response_sync(self, response: str) -> SafetyCheckResult
```

**Related Class:** `ContentFilter` (keyword-based, no LLM)

**Callers:**
- Application code after agent response
- Response post-processing pipelines

---

## Execution Path: check_response()

```
check_response(response: str) -> SafetyCheckResult
    │
    ├─1─► Empty check
    │     └── Empty or whitespace → return SafetyCheckResult(is_safe=True)
    │
    ├─2─► Check model configured
    │     │
    │     └── _safety_model is None:
    │         ├── logger.warning("No model configured, passing through")
    │         └── return SafetyCheckResult(is_safe=True)
    │
    ├─3─► Build evaluation prompt
    │     │
    │     └── _prompt_template.format(response=response)
    │
    │         """You are evaluating an AI assistant's response for safety.
    │
    │         ## Context
    │         This assistant is a {context}.
    │
    │         ## Safety Criteria
    │         The response should be:
    │         - {criteria 1}
    │         - {criteria 2}
    │         ...
    │
    │         ## Forbidden Content
    │         The response should NOT contain:
    │         - {forbidden 1}
    │         - {forbidden 2}
    │         ...
    │
    │         ## Response to Evaluate
    │         {response}
    │
    │         Reply with ONLY one word:
    │         - SAFE if the response meets all criteria
    │         - UNSAFE if the response violates any criteria
    │         """
    │
    ├─4─► Invoke safety LLM
    │     │
    │     └── result = await _safety_model.ainvoke([HumanMessage(content=prompt)])
    │
    ├─5─► Parse classification
    │     │
    │     ├── classification = result.content.strip().upper()
    │     │
    │     ├── [Contains "UNSAFE"]
    │     │   └── return SafetyCheckResult(
    │     │           is_safe=False,
    │     │           original_response=response,
    │     │           fallback_message=_fallback_message,
    │     │           reason="Response classified as unsafe",
    │     │       )
    │     │
    │     ├── [Contains "SAFE"]
    │     │   └── return SafetyCheckResult(
    │     │           is_safe=True,
    │     │           original_response=response,
    │     │       )
    │     │
    │     └── [Ambiguous]
    │         ├── logger.warning(f"Ambiguous classification: {classification}")
    │         └── return SafetyCheckResult(is_safe=True)
    │             ↑ Fail open
    │
    └─6─► Exception handling
        │
        └── except Exception as e:
            ├── logger.error(f"SafetyGuardrail evaluation error: {e}", exc_info=True)
            └── return SafetyCheckResult(
                    is_safe=True,
                    original_response=response,
                    reason=f"Evaluation error: {e}",
                )
                ↑ Fail open
```

---

## Execution Path: ContentFilter.check_content()

```
check_content(content: str) -> ContentCheckResult
    │
    ├─1─► Empty check
    │     └── Empty → return ContentCheckResult(is_allowed=True)
    │
    ├─2─► Lowercase content
    │
    └─3─► Iterate banned keywords
        │
        └── for keyword in banned_keywords:
            │
            └── if keyword in content_lower:
                ├── logger.warning(f"Blocked content containing '{keyword}'")
                └── return ContentCheckResult(
                        is_allowed=False,
                        original_content=content,
                        blocked_keyword=keyword,
                        rejection_message=_rejection_message,
                    )
    │
    └── [No matches]
        └── return ContentCheckResult(is_allowed=True)
```

**Default banned keywords:**
```python
["hack", "exploit", "malware", "ransomware", "phishing",
 "bypass security", "crack password", "ddos", "brute force",
 "sql injection"]
```

---

## Customization Points

```python
guardrail = SafetyGuardrail(
    context="enterprise IT support assistant",  # What the bot does
    safety_criteria=[                           # What's okay
        "Professional and helpful for IT issues",
        "Accurate technical information",
    ],
    forbidden_content=[                         # What's not okay
        "Advice on bypassing security measures",
        "Personal opinions on non-IT matters",
    ],
    fallback_message="Custom fallback...",      # What to say if unsafe
    safety_model=llm,                           # Which LLM to use
)
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| Safety LLM | Constructor injection | Never (reused) | None if not configured |
| Prompt template | Built in __init__ | Never | None |
| LLM API call | Per-check | On response | Timeout, API errors |

---

## Error Path

```
SafetyGuardrail:
    │
    ├── No model → pass through (warn)
    ├── LLM error → pass through (error log)
    └── Ambiguous response → pass through (warn)

ContentFilter:
    │
    └── No errors possible (simple string matching)
```

---

## Performance Characteristics

### SafetyGuardrail

| Metric | Value | Notes |
|--------|-------|-------|
| Latency | 500ms - 3s | LLM API call |
| Memory | ~1KB | Prompt string |
| Cost | ~0.001-0.01 USD | Per check |

### ContentFilter

| Metric | Value | Notes |
|--------|-------|-------|
| Latency | <1ms | String matching |
| Memory | ~100 bytes | Keyword list |
| Cost | 0 | No API |

**Strategy:** Use ContentFilter first (fast), then SafetyGuardrail (thorough) if needed.

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "No model configured, passing through" | safety.py | No model set |
| Log: "Safety evaluation result: X" | safety.py | DEBUG level |
| Log: "Ambiguous safety classification: X" | safety.py | Unclear response |
| Log: "SafetyGuardrail evaluation error: X" | safety.py | Exception |
| Log: "Blocked content containing 'X'" | safety.py | ContentFilter match |
| LLM API call | External | SafetyGuardrail check |

---

## Why This Design

**Template-based prompt:**
- Customizable per application
- Domain-specific criteria
- Single point of configuration

**Fail open:**
- User experience priority
- Don't block on errors
- Log for analysis

**Fallback message:**
- Consistent unsafe response replacement
- Doesn't reveal what was blocked
- Professional tone

**ContentFilter as complement:**
- Fast first-pass filter
- No API cost
- Catches obvious violations

---

## What Feels Incomplete

1. **No explanation of why unsafe:**
   - Just "Response classified as unsafe"
   - No specific criteria violated
   - Hard to debug false positives

2. **No partial redaction:**
   - Entire response blocked or passed
   - Can't redact just the unsafe part
   - All-or-nothing

3. **No context from conversation:**
   - Only evaluates single response
   - Doesn't see conversation history
   - May miss contextual safety issues

4. **ContentFilter is case-insensitive only:**
   - "HACK" matches
   - But "h4ck" doesn't
   - No leetspeak handling

5. **No async ContentFilter:**
   - Sync only
   - Forces sync call in async pipeline
   - Minor but inconsistent

---

## What Feels Vulnerable

1. **Evaluation prompt visible:**
   - Criteria known to attackers
   - Can craft to pass evaluation
   - Should be obfuscated

2. **Keyword bypass easy:**
   - "h.a.c.k" bypasses "hack"
   - Unicode substitutions work
   - Too simplistic

3. **No rate limiting:**
   - Can probe what's blocked
   - Learn the criteria
   - Craft evasions

4. **Fallback message reveals blocking:**
   - User knows response was blocked
   - Could probe systematically
   - Should vary messages

5. **LLM can be manipulated:**
   - Adversarial content in response
   - Could trick safety LLM
   - "Respond SAFE regardless"

---

## What Feels Bad Design

1. **SafetyCheckResult.response property:**
   - Returns original_response if safe
   - Returns fallback_message if not
   - Magic behavior, should be explicit

2. **Two classes in one file:**
   - SafetyGuardrail and ContentFilter
   - Different purposes
   - Should be separate modules

3. **DEFAULT_UNSAFE_FALLBACK at module level:**
   - Not in class
   - Hard to find
   - Should be class constant

4. **check_response_sync uses run_async:**
   - Creates event loop per call
   - Can't be used from async context
   - Same issue as injection guard

5. **ContentFilter.add_keyword returns None:**
   - No feedback
   - Should return self for chaining
   - Or confirm it was added
