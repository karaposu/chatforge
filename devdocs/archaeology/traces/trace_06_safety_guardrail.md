# Trace 06: Safety Guardrail

How agent responses are evaluated for safety before being returned to users.

---

## Entry Point

**Location:** `middleware/safety.py:107` - `SafetyGuardrail` class

**Trigger:** Application code checking agent response before returning to user:
```python
guardrail = SafetyGuardrail(context="customer support")
result = await guardrail.check_response(agent_response)
if not result.is_safe:
    return result.fallback_message
else:
    return result.original_response
```

**Key Methods:**
```python
check_response(response) → SafetyCheckResult     # Async check
check_response_sync(response) → SafetyCheckResult # Sync wrapper
```

**Related Classes:**
```python
ContentFilter  # Simpler keyword-based blocking
```

---

## Execution Path

### Path A: SafetyGuardrail Check

```
SafetyGuardrail.check_response(response)
├── Check empty response
│   └── if not response or not response.strip() → return safe result
├── Check if model configured
│   └── if self._safety_model is None:
│       ├── Log warning: "No model configured, passing through"
│       └── return safe result (fail open)
├── Build evaluation prompt
│   └── Insert response into pre-built template
├── Invoke safety model
│   └── result = await self._safety_model.ainvoke([HumanMessage(prompt)])
├── Parse classification
│   ├── if "UNSAFE" in classification.upper():
│   │   └── return SafetyCheckResult(is_safe=False, fallback_message=...)
│   ├── if "SAFE" in classification.upper():
│   │   └── return SafetyCheckResult(is_safe=True)
│   └── else (ambiguous):
│       ├── Log warning
│       └── return safe result (fail open)
├── On exception:
│   ├── Log error with exc_info
│   └── return safe result with reason
```

### Path B: Template Construction

```
__init__(context, safety_criteria, forbidden_content, fallback_message, safety_model)
├── context = "general assistant" if not provided
├── safety_criteria = ["Helpful and accurate", "Professional tone", "No harmful content"]
├── forbidden_content = ["Personal attacks", "Dangerous instructions", "Illegal activities"]
├── fallback_message = DEFAULT_UNSAFE_FALLBACK
├── Build prompt template:
    └── SAFETY_EVALUATION_TEMPLATE.format(
        context=context,
        safety_criteria=bullet_list(criteria),
        forbidden_content=bullet_list(forbidden),
        response="{response}"  # Placeholder for runtime
    )
```

**Template structure:**
```
You are evaluating an AI assistant's response for safety.

## Context
This assistant is a {context}.

## Safety Criteria
The response should be:
- Helpful and accurate
- Professional tone
- No harmful content

## Forbidden Content
The response should NOT contain:
- Personal attacks or harassment
- Dangerous instructions
- Illegal activities

## Response to Evaluate
{response}

## Your Evaluation
Reply with ONLY one word:
- SAFE if the response meets all criteria
- UNSAFE if the response violates any criteria
```

### Path C: ContentFilter (Keyword-Based)

```
ContentFilter.check_content(content)
├── Check empty content
│   └── if not content → return allowed result
├── Lowercase the content
├── For each keyword in self.banned_keywords:
│   ├── if keyword in content_lower:
│   │   ├── Log warning about blocked keyword
│   │   └── return ContentCheckResult(
│   │       is_allowed=False,
│   │       blocked_keyword=keyword,
│   │       rejection_message=self._rejection_message
│   │   )
├── return ContentCheckResult(is_allowed=True)
```

**Default banned keywords:**
```python
["hack", "exploit", "malware", "ransomware", "phishing",
 "bypass security", "crack password", "ddos", "brute force", "sql injection"]
```

---

## Resource Management

### SafetyGuardrail
- LLM call per response checked
- Template built once at init
- No caching of results

### ContentFilter
- Pure string matching
- No external dependencies
- O(n × k) where n=content length, k=keyword count

---

## Error Path

### No Model Configured (SafetyGuardrail)
```python
if self._safety_model is None:
    logger.warning("SafetyGuardrail: No model configured, passing through")
    return SafetyCheckResult(is_safe=True, original_response=response)
```
- Fails open - unsafe content passes

### LLM Evaluation Error
```python
except Exception as e:
    logger.error(f"SafetyGuardrail evaluation error: {e}", exc_info=True)
    return SafetyCheckResult(
        is_safe=True,
        original_response=response,
        reason=f"Evaluation error: {e}",
    )
```
- Fails open - content passes with error reason attached

### Ambiguous Classification
```python
if not ("UNSAFE" in classification or "SAFE" in classification):
    logger.warning(f"Ambiguous safety classification: {classification}")
    return SafetyCheckResult(is_safe=True, original_response=response)
```

---

## Performance Characteristics

### SafetyGuardrail
| Component | Time |
|-----------|------|
| Prompt formatting | ~0.1ms |
| LLM inference | 200ms - 2s |
| Response parsing | ~0.1ms |
| **Total** | **200ms - 2s** |

### ContentFilter
| Text Length | Keywords | Time |
|-------------|----------|------|
| 100 chars | 10 | ~0.01ms |
| 1000 chars | 10 | ~0.05ms |
| 10000 chars | 10 | ~0.5ms |

### Combined Strategy
```
ContentFilter first (fast, catches obvious)
    ↓ if allowed
SafetyGuardrail (slow, catches nuanced)
```

---

## Observable Effects

### SafetyGuardrail - Unsafe Response
```python
SafetyCheckResult(
    is_safe=False,
    original_response="I'll help you hack into...",
    fallback_message="I apologize, but I cannot provide that response...",
    reason="Response classified as unsafe"
)
```

### SafetyGuardrail - Safe Response
```python
SafetyCheckResult(
    is_safe=True,
    original_response="Here's how to reset your password..."
)
```

### ContentFilter - Blocked
```python
ContentCheckResult(
    is_allowed=False,
    original_content="How do I hack a password?",
    blocked_keyword="hack",
    rejection_message="I'm sorry, but I cannot process requests..."
)
```

### Logging
```python
logger.debug(f"SafetyGuardrail initialized for context: {self._context}")
logger.debug(f"Safety evaluation result: {classification}")
logger.warning(f"Ambiguous safety classification: {classification}")
logger.error(f"SafetyGuardrail evaluation error: {e}", exc_info=True)
logger.warning(f"ContentFilter: Blocked content containing '{keyword}'")
```

---

## Why This Design

### Two-Layer Safety
**Choice:** ContentFilter (fast) + SafetyGuardrail (thorough)

**Rationale:**
- ContentFilter catches obvious violations instantly
- SafetyGuardrail catches nuanced issues
- Cost optimization: skip LLM for obvious cases

**Trade-off:**
- Two systems to maintain
- Could conflict in edge cases

### LLM-Based Evaluation
**Choice:** Use an LLM to judge safety

**Rationale:**
- Context-aware decisions
- Understands nuance ("hack" in cybersecurity context is fine)
- Can evaluate complex scenarios

**Trade-off:**
- Latency per response
- Cost per evaluation
- LLM can be wrong

### Configurable Criteria
**Choice:** safety_criteria and forbidden_content as lists

**Rationale:**
- Different apps have different standards
- Medical app vs casual chatbot
- Explicit about what's checked

**Trade-off:**
- Must configure thoughtfully
- Default may not fit all apps

### Fail Open Design
**Choice:** Return safe on error

**Rationale:**
- Availability prioritized
- User experience not blocked by failures
- Logged for review

**Trade-off:**
- Unsafe content may pass during outages
- Security vs availability tradeoff

---

## What Feels Incomplete

1. **No feedback loop**
   - Unsafe classifications not stored
   - Cannot improve over time
   - No analytics on what's blocked

2. **No severity levels**
   - Binary SAFE/UNSAFE
   - Cannot warn vs block
   - No confidence score

3. **No partial blocking**
   - Entire response blocked or passed
   - Cannot redact just unsafe parts
   - All-or-nothing

4. **ContentFilter has no update mechanism**
   - Keywords hardcoded
   - No dynamic list from database
   - Requires code change to update

5. **Not integrated with routes**
   - Must manually check after agent response
   - Easy to forget
   - No default protection

---

## What Feels Vulnerable

1. **Adversarial content**
   ```
   Response: "Here's how to hαck a password..."
   #         Using Greek alpha looks like 'a'
   ```
   - ContentFilter only does exact match
   - Unicode tricks bypass keyword filter
   - Need normalization

2. **Context manipulation**
   ```
   Response: "In the movie, the character says 'I'll hack the mainframe'"
   ```
   - Quoted content might trigger false positive
   - LLM might pass it as fiction context
   - Inconsistent handling

3. **Model disagreement**
   - Different safety models have different standards
   - GPT-4 vs Claude may classify differently
   - No ground truth

4. **Fallback message is generic**
   ```python
   DEFAULT_UNSAFE_FALLBACK = "I apologize, but I cannot provide that response..."
   ```
   - User doesn't know why blocked
   - Frustrating experience
   - Could be more specific

5. **Substring matching in ContentFilter**
   ```python
   if keyword in content_lower:
   ```
   - "hack" matches "hackathon"
   - "exploit" matches "exploit your strengths"
   - High false positive rate

---

## What Feels Like Bad Design

1. **SafetyCheckResult.response property**
   ```python
   @property
   def response(self) -> str:
       return self.original_response if self.is_safe else (self.fallback_message or "")
   ```
   - Convenience property but confusing
   - Returns empty string if unsafe and no fallback
   - Should require fallback

2. **Mutable keyword list**
   ```python
   def add_keyword(self, keyword: str) -> None:
       ...
   def remove_keyword(self, keyword: str) -> bool:
       ...
   ```
   - ContentFilter can be mutated after creation
   - Not thread-safe
   - Prefer immutable config

3. **Inconsistent check methods**
   ```python
   SafetyGuardrail.check_response()  # Returns SafetyCheckResult
   ContentFilter.check_content()      # Returns ContentCheckResult
   ```
   - Different result types
   - Cannot use interchangeably
   - Should share interface

4. **No caching**
   - Same response checked multiple times = multiple LLM calls
   - Could cache recent evaluations
   - Hash-based lookup would be fast

5. **Parsing uses `in` not `startswith`**
   ```python
   if "UNSAFE" in classification.upper():
   ```
   - "This response is SAFE and UNSAFE" would match UNSAFE
   - Order matters but logic doesn't account for it
   - Should be more precise

6. **DEFAULT_SAFETY_MODEL constant unused**
   ```python
   from .constants import DEFAULT_SAFETY_MODEL
   # Never used in safety.py
   ```
   - Imported but not applied
   - Suggests incomplete implementation
   - Dead code
