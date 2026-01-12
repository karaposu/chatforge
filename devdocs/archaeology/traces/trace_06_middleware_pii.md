# Trace 06: PII Detection Middleware

Scans text for personally identifiable information (PII) and optionally redacts it. Part of the security middleware layer.

---

## Entry Point

**File:** `chatforge/middleware/pii.py:100`
**Class:** `PIIDetector`

**Primary Methods:**
```python
def scan(self, text: str) -> PIIScanResult
def redact(self, text: str) -> str
def contains_pii(self, text: str) -> bool
```

**Callers:**
- Application code before storage
- Application code before sending to LLM
- Pre-processing pipelines

---

## Execution Path: scan()

```
scan(text: str) -> PIIScanResult
    │
    ├─1─► Empty check
    │     └── Empty or None → return PIIScanResult(original=text, redacted=text)
    │
    ├─2─► Initialize tracking
    │     ├── matches: list[PIIMatch] = []
    │     ├── blocked = False
    │     └── block_reason = None
    │
    ├─3─► Iterate through rules
    │     │
    │     └── for rule in self._rules:
    │         │
    │         ├── Compile pattern if string
    │         │
    │         ├── Find all matches: pattern.finditer(text)
    │         │
    │         └── for match in matches:
    │             │
    │             ├── Extract value: match.group()
    │             │
    │             ├── Determine replacement based on strategy:
    │             │   │
    │             │   ├── [BLOCK]
    │             │   │   ├── blocked = True
    │             │   │   ├── block_reason = "Blocked PII type: X"
    │             │   │   └── replacement = rule.replacement_text
    │             │   │
    │             │   ├── [MASK]
    │             │   │   └── replacement = "*" * (len - mask_chars) + last_chars
    │             │   │       Example: "4111111111111111" → "************1111"
    │             │   │
    │             │   ├── [HASH]
    │             │   │   └── replacement = "[{sha256[:8]}]"
    │             │   │       Example: "john@example.com" → "[a1b2c3d4]"
    │             │   │
    │             │   └── [REDACT]
    │             │       └── replacement = rule.replacement_text
    │             │           Example: "john@example.com" → "[EMAIL REDACTED]"
    │             │
    │             └── Append PIIMatch(type, value, start, end, replacement)
    │
    ├─4─► Build redacted text
    │     │
    │     ├── Sort matches by start position (descending)
    │     │   └── Descending to preserve positions during replacement
    │     │
    │     └── for match in sorted_matches:
    │         redacted = redacted[:start] + replacement + redacted[end:]
    │
    └─5─► Return PIIScanResult(
            original_text=text,
            matches=matches,
            redacted_text=redacted,
            blocked=blocked,
            block_reason=block_reason,
        )
```

---

## Execution Path: redact()

```
redact(text: str) -> str
    │
    ├── result = scan(text)
    │
    ├── if result.blocked:
    │   └── raise ValueError(result.block_reason)
    │
    └── return result.redacted_text or text
```

---

## Default Rules

```python
_add_default_rules():
    │
    ├── email
    │   ├── Pattern: EMAIL_PATTERN (complex regex)
    │   ├── Strategy: REDACT
    │   └── Replacement: "[EMAIL REDACTED]"
    │
    ├── credit_card
    │   ├── Pattern: CREDIT_CARD_PATTERN
    │   ├── Strategy: MASK
    │   └── Mask chars: 4 (show last 4 digits)
    │
    ├── phone
    │   ├── Pattern: PHONE_PATTERN
    │   ├── Strategy: REDACT
    │   └── Replacement: "[PHONE REDACTED]"
    │
    ├── ip
    │   ├── Pattern: IP_PATTERN
    │   ├── Strategy: REDACT
    │   └── Replacement: "[IP REDACTED]"
    │
    ├── ssn
    │   ├── Pattern: SSN_PATTERN
    │   ├── Strategy: REDACT
    │   └── Replacement: "[SSN REDACTED]"
    │
    └── api_key
        ├── Pattern: COMBINED_API_KEY_PATTERN
        └── Strategy: BLOCK  ← Note: blocks, not redacts
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| Compiled regex | __init__ or first scan | Never (cached) | Memory for patterns |
| Input text | Parameter | Immediate | None |
| Match objects | Per scan | End of scan | None |

**Memory:**
- Patterns compiled once
- Text copied for redaction
- Matches list grows with findings

---

## Error Path

```
scan():
    └── No exceptions - always returns PIIScanResult
        └── Empty input → empty result

redact():
    │
    └── Blocked PII found
        └── raise ValueError(block_reason)
            Example: "Blocked PII type: api_key"
```

**Pattern errors:**
- Invalid regex in custom rule → re.compile raises at add_rule time
- Not caught in scan

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Scan latency | <1ms for short text | Regex matching |
| Scan latency | 10-100ms for long text | Multiple patterns |
| Memory | O(n) | Copies of text |
| Complexity | O(n × p) | n = text length, p = pattern count |

**Performance factors:**
1. Number of rules (default: 6)
2. Text length
3. Pattern complexity (some patterns are expensive)
4. Number of matches (replacement iterations)

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "PIIDetector initialized with N rules" | pii.py | __init__ |
| No runtime logging | - | scan() is silent |

**Side effects:** None. Pure function behavior.

---

## Why This Design

**Strategy pattern:**
- Different handling per PII type
- BLOCK for dangerous items (API keys)
- MASK for partial visibility (credit cards)
- REDACT for full removal (emails)

**Regex-based:**
- Fast for pattern matching
- No external dependencies
- Easy to customize

**Descending order replacement:**
- Preserves character positions
- Avoids recalculating offsets
- Simple implementation

**Default rules built-in:**
- Ready to use out of box
- Common PII types covered
- Can override or extend

---

## What Feels Incomplete

1. **No context-aware detection:**
   - "My ID is 123456" - is 123456 a SSN?
   - No NER (Named Entity Recognition)
   - False positives for numbers in context

2. **No confidence scores:**
   - Match is binary (yes/no)
   - No probability
   - Can't threshold borderline cases

3. **No internationalization:**
   - US-centric patterns
   - SSN is US format
   - Phone patterns may not match international

4. **No async support:**
   - Blocking regex operations
   - Could block event loop on large text
   - Should offer async variant

5. **No statistics/reporting:**
   - No aggregate PII counts
   - No audit log
   - No dashboard metrics

---

## What Feels Vulnerable

1. **API key pattern may miss formats:**
   - COMBINED_API_KEY_PATTERN is complex
   - New providers may not match
   - False negatives for novel keys

2. **Regex ReDoS potential:**
   - Complex patterns with backtracking
   - Malicious input could cause slow scan
   - No timeout on regex

3. **HASH is reversible for short inputs:**
   - SHA256 is fast
   - Rainbow tables could reveal
   - Should use salt

4. **No input sanitization:**
   - Assumes text is valid string
   - Unicode edge cases?
   - Null bytes?

5. **Block strategy raises in redact():**
   - Caller must catch ValueError
   - Easy to forget
   - Could expose raw text on error

---

## What Feels Bad Design

1. **PIIScanResult.blocked vs has_pii:**
   - Two separate concepts
   - blocked = True means exception in redact()
   - Confusing which to check

2. **Strategy as enum but stored as string:**
   - `PIIStrategy.REDACT` is enum
   - But `rule.strategy` compared with enum
   - Works, but mixing paradigms

3. **Replacement happens in scan():**
   - scan() should just find matches
   - Redaction should be separate step
   - Coupling detection and action

4. **add_rule modifies pattern:**
   - `rule.pattern = re.compile(...)` mutates input
   - Side effect on passed object
   - Should copy or not mutate

5. **remove_rule returns bool:**
   - Returns True if removed
   - But caller rarely checks
   - Should raise if not found, or always return None
