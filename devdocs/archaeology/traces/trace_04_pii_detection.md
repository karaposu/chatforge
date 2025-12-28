# Trace 04: PII Detection Middleware

How personally identifiable information is detected and handled before/after processing.

---

## Entry Point

**Location:** `middleware/pii.py:100` - `PIIDetector` class

**Trigger:** Application code calls detection methods:
- Before sending user input to agent
- Before logging messages
- Before storing in external systems

**Key Methods:**
```python
scan(text) → PIIScanResult           # Full scan with details
redact(text) → str                   # Quick redaction
contains_pii(text) → bool            # Quick check
```

---

## Execution Path

### Path A: Full Scan

```
PIIDetector.scan(text)
├── Check empty text
│   └── if not text → return empty PIIScanResult
├── Initialize matches list and blocked flag
├── For each rule in self._rules:
│   ├── Get compiled regex pattern
│   ├── For each match in pattern.finditer(text):
│   │   ├── Extract matched value
│   │   ├── Determine replacement based on strategy:
│   │   │   ├── BLOCK: Set blocked=True, use replacement_text
│   │   │   ├── MASK: Show last N chars, rest as asterisks
│   │   │   ├── HASH: SHA256 hash, first 8 chars
│   │   │   └── REDACT: Use replacement_text
│   │   └── Create PIIMatch object with position info
├── Build redacted text (replace in reverse position order)
├── Return PIIScanResult with all matches and redacted text
```

**Data flow example:**
```python
# Input
text = "Contact john@example.com or call 555-123-4567"

# Processing
matches = [
    PIIMatch(pii_type="email", value="john@example.com", start=8, end=24, replacement="[EMAIL REDACTED]"),
    PIIMatch(pii_type="phone", value="555-123-4567", start=33, end=45, replacement="[PHONE REDACTED]")
]

# Output
PIIScanResult(
    original_text="Contact john@example.com or call 555-123-4567",
    matches=[...],
    redacted_text="Contact [EMAIL REDACTED] or call [PHONE REDACTED]",
    blocked=False
)
```

### Path B: Redaction Strategy

```
Strategy: REDACT
├── replacement = rule.replacement_text
└── Example: "john@example.com" → "[EMAIL REDACTED]"

Strategy: MASK
├── if len(value) > mask_chars:
│   └── replacement = "*" * (len - mask_chars) + value[-mask_chars:]
├── else:
│   └── replacement = "*" * len(value)
└── Example: "4111111111111111" → "************1111"

Strategy: HASH
├── hash = sha256(value.encode()).hexdigest()[:8]
├── replacement = f"[{hash}]"
└── Example: "secret-api-key" → "[a3f2b1c9]"

Strategy: BLOCK
├── blocked = True
├── block_reason = f"Blocked PII type: {rule.pii_type}"
└── replacement = rule.replacement_text
```

### Path C: Default Rules Initialization

```
PIIDetector.__init__(rules=None)
├── If custom rules provided:
│   └── Add each rule via add_rule()
├── Else add default rules:
│   ├── email: EMAIL_PATTERN, REDACT, "[EMAIL REDACTED]"
│   ├── credit_card: CREDIT_CARD_PATTERN, MASK (last 4 chars)
│   ├── phone: PHONE_PATTERN, REDACT, "[PHONE REDACTED]"
│   ├── ip: IP_PATTERN, REDACT, "[IP REDACTED]"
│   ├── ssn: SSN_PATTERN, REDACT, "[SSN REDACTED]"
│   └── api_key: COMBINED_API_KEY_PATTERN, BLOCK
```

### Path D: Reverse Order Replacement

```
# Why reverse order?
text = "Email: a@b.com and c@d.com"
#       pos:   7-14       19-26

# Forward order would shift positions:
text = "Email: [REDACTED] and c@d.com"
#       19-26 is now wrong!

# Reverse order preserves positions:
text = "Email: a@b.com and [REDACTED]"  # Replace 19-26 first
text = "Email: [REDACTED] and [REDACTED]"  # Then 7-14
```

---

## Resource Management

### Regex Compilation
- Patterns compiled once on rule addition
- Stored as `re.Pattern` objects
- Case-insensitive matching (re.IGNORECASE)

### Memory
- Original text kept in result
- Matches list grows with PII found
- No streaming support - entire text in memory

### No External Dependencies
- Pure Python implementation
- No NLP models or ML inference
- No API calls

---

## Error Path

### Invalid Pattern
```python
rule.pattern = re.compile(rule.pattern, re.IGNORECASE)
# If pattern is invalid regex → re.error
# Exception propagates to caller
```

### Hash Function
```python
hashlib.sha256(value.encode()).hexdigest()[:8]
# If value contains invalid UTF-8... shouldn't happen with matched text
# But if it did → UnicodeDecodeError
```

### Blocked Content
```python
def redact(self, text: str) -> str:
    result = self.scan(text)
    if result.blocked:
        raise ValueError(result.block_reason)
    return result.redacted_text or text
```

---

## Performance Characteristics

### Time Complexity
| Operation | Complexity |
|-----------|------------|
| scan() | O(n * p) where n=text length, p=pattern count |
| Single regex match | O(n) per pattern |
| Replacement building | O(m) where m=match count |

### Benchmarks (approximate)
| Text Length | Patterns | Time |
|-------------|----------|------|
| 100 chars | 6 default | ~0.1ms |
| 1000 chars | 6 default | ~0.5ms |
| 10000 chars | 6 default | ~2ms |

### Pattern Details
```python
# From constants.py
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
CREDIT_CARD_PATTERN = r'\b(?:\d[ -]*?){13,16}\b'
PHONE_PATTERN = r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
IP_PATTERN = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
COMBINED_API_KEY_PATTERN = r'(sk-[a-zA-Z0-9]{20,}|...|...)'  # Multiple providers
```

---

## Observable Effects

### On Detection
- Matches collected with exact positions
- Redacted text generated
- Original text preserved in result

### On Blocking
- `blocked=True` flag set
- `block_reason` populated
- `redact()` raises ValueError

### Logging
```python
logger.debug(f"PIIDetector initialized with {len(self._rules)} rules")
# No logging during scan - caller should log
```

---

## Why This Design

### Regex-Based Detection
**Choice:** Use regex patterns, not ML models

**Rationale:**
- Fast and deterministic
- No external dependencies
- Predictable behavior
- Easy to customize

**Trade-off:**
- Limited to known patterns
- Cannot detect novel PII types
- May miss context-dependent PII

### Strategy Pattern
**Choice:** Configurable handling per PII type

**Rationale:**
- Different PII needs different treatment
- Credit cards: show last 4 for verification
- API keys: block entirely
- Flexibility for compliance requirements

**Trade-off:**
- More complex configuration
- Must decide strategy per type

### Position-Based Matching
**Choice:** Track start/end positions for each match

**Rationale:**
- Enables precise replacement
- Supports overlapping patterns
- Useful for highlighting in UI

**Trade-off:**
- More memory per match
- Reverse-order replacement needed

### Separate Scan/Redact
**Choice:** `scan()` returns full details, `redact()` returns just text

**Rationale:**
- Scan provides visibility for logging/auditing
- Redact is convenient for simple use cases
- Caller chooses based on needs

**Trade-off:**
- Two methods for similar operation
- Redact calls scan internally (no optimization)

---

## What Feels Incomplete

1. **No allowlist support**
   - Cannot exclude known-safe patterns
   - Example: company domain emails
   - Must build custom detector

2. **No context awareness**
   - "John" in "Dear John" vs "John Smith"
   - Cannot distinguish PII from common words
   - Would need NLP for this

3. **No confidence scores**
   - All matches treated equally
   - No "maybe PII" vs "definitely PII"
   - Regex is binary match

4. **No streaming support**
   - Must have full text in memory
   - Cannot process large documents incrementally
   - Would need different architecture

5. **No integration with routes**
   - Middleware exists but not wired in
   - Must manually call before/after agent
   - Easy to forget

---

## What Feels Vulnerable

1. **Pattern bypass**
   ```
   Email: j o h n @ e x a m p l e . c o m
   # Spaces between characters bypass pattern
   ```
   - Simple obfuscation defeats regex
   - Intentional bypass easy
   - Need character normalization

2. **Unicode lookalikes**
   ```
   Email: john＠example.com  # Full-width @
   # Different Unicode character, same appearance
   ```
   - Homoglyph attacks work
   - Should normalize Unicode first

3. **Partial matching**
   ```python
   IP_PATTERN = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
   # Matches: 999.999.999.999 (invalid IP)
   # Pattern doesn't validate IP ranges
   ```
   - False positives possible
   - May redact non-PII

4. **Overlapping patterns**
   - If two patterns match overlapping regions
   - Both matches recorded
   - Replacement order matters
   - Could corrupt text

---

## What Feels Like Bad Design

1. **Mutable rules list**
   ```python
   detector = PIIDetector()
   detector.add_rule(...)  # Modifies instance
   detector.remove_rule(...)
   ```
   - Instance state can change after creation
   - Not thread-safe for add/remove
   - Prefer immutable configuration

2. **Hash truncation**
   ```python
   hashlib.sha256(value.encode()).hexdigest()[:8]
   ```
   - Only 8 hex chars = 32 bits
   - High collision probability
   - Not suitable for reversibility protection

3. **Inconsistent return types**
   ```python
   scan() → PIIScanResult
   redact() → str
   contains_pii() → bool
   ```
   - Three methods with different return types
   - Could unify with scan() that has helper properties

4. **Default 4-char mask**
   ```python
   mask_chars: int = 4  # For MASK strategy
   ```
   - Shows last 4 chars of credit card
   - But also shows last 4 of phone, SSN, etc.
   - Not PII-type aware

5. **Block raises ValueError**
   ```python
   if result.blocked:
       raise ValueError(result.block_reason)
   ```
   - ValueError is too generic
   - Should have PIIBlockedError
   - Harder to catch specifically
