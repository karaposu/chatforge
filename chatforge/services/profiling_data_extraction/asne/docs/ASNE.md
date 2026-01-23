## ASNE: Atomic Statement Normalization & Extraction

### A Schema-Free Approach to Conversational Data Extraction

---

## Introduction

ASNE (Atomic Statement Normalization & Extraction) is an alternative methodology for extracting profiling data from conversation. Rather than decomposing utterances into predefined schema objects, ASNE normalizes them into atomic natural language statements, then tags those statements with dimensional categories.

The core insight: **natural language is already a flexible data format.** Instead of forcing conversational content into rigid schemas, we simplify and atomize while staying in natural language, then apply loose categorical tags for retrieval and organization.

---

## The Problem with Schema-Bound Extraction

Consider this utterance:

> "I've been struggling with Seattle weather but the Amazon job is worth it for now"

A schema-bound approach (like CPF-7) must map this to predefined fields:

```json
{"dimension": "opinion", "about": "Seattle weather", "view": "negative"}
{"dimension": "core_identity", "aspect": "employer", "value": "Amazon"}
```

But what happened to the relationship between these facts? The speaker *endures* the weather *because of* the job. That's valuable information—arguably the most interesting part—but it has no home in a schema designed around discrete dimensions.

Schema-bound extraction faces a fundamental tension:
- **Tight schemas** enable precise queries but lose information that doesn't fit
- **Loose schemas** capture more but become inconsistent and hard to query

ASNE sidesteps this by not using schemas for the extraction output at all.

---

## The ASNE Approach

### Two-Stage Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    STAGE 1: NORMALIZE                    │
│                                                          │
│  Complex utterance                                       │
│         ↓                                                │
│  Atomic natural language statements                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    STAGE 2: TAG                          │
│                                                          │
│  Atomic statements                                       │
│         ↓                                                │
│  Statements + dimensional tags                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Stage 1: Normalization

### Goal

Transform complex, contextual, conversational utterances into simple, self-contained, atomic statements.

### Principles

**1. Atomicity**
Each output statement expresses one fact, opinion, relationship, or inference. If a statement contains "and" or "but" connecting distinct ideas, it should probably be split.

**2. Self-containment**
Statements should be interpretable without the original context. Pronouns resolved. References clarified. Implicit subjects made explicit.

**3. Inference preservation**
Don't just extract what was literally said. Extract what was clearly implied or can be reasonably inferred. If someone says "the commute is killing me," extract both the literal (long/difficult commute) and the inference (dislikes commute, commute causes stress).

**4. Simplification**
Strip hedging, filler, and conversational noise. "I mean, honestly, I've kind of been struggling" → "struggles with X"

**5. Tense normalization**
Convert to present tense or timeless form where appropriate, with temporal markers as separate notation when needed.

### Examples

**Input:**
> "Just moved to Seattle for my new role at Amazon. Missing my family back in Boston, but excited about leading the AI team."

**Normalized output:**
```
recently moved to Seattle
works at Amazon
new role at Amazon
family lives in Boston
misses family
leads AI team at Amazon
excited about leading AI team
moved to Seattle for Amazon job
```

---

**Input:**
> "I've been struggling with Seattle weather but the Amazon job is worth it for now"

**Normalized output:**
```
dislikes Seattle weather
Seattle weather is difficult
works at Amazon in Seattle
considers Amazon job worth it
job worth it "for now" (uncertain long-term)
endures Seattle weather because of job
```

---

**Input:**
> "After my startup failed, I joined Google to learn from the best"

**Normalized output:**
```
previously founded a startup
startup failed
now works at Google
joined Google after startup failed
joined Google to learn
considers Google employees "the best" to learn from
career transition: founder → Google employee
```

---

### Normalization is Generative, Not Extractive

Notice that normalization doesn't just pull out keywords or fill slots. It *generates* simplified statements that capture meaning. The LLM doing normalization is interpreting, inferring, and restating.

This is a feature, not a bug. We want the richness of LLM understanding applied at extraction time, producing human-readable statements that preserve that understanding.

---

## Stage 2: Tagging

### Goal

Apply dimensional and topical tags to each atomic statement for organization and retrieval.

### Tag Types

**Dimensional tags** (what kind of information is this?)
- `identity` — who they are, roles, attributes
- `opinion` — views, judgments, evaluations
- `preference` — patterns, tendencies, likes/dislikes
- `desire` — wants, needs, hopes, goals
- `narrative` — life story, biographical elements
- `event` — things happening, occurrences
- `relationship` — connections to people, organizations, places
- `reasoning` — causal connections, explanations, trade-offs
- `emotion` — feelings, emotional states
- `intention` — plans, commitments, decisions

**Topical tags** (what is it about?)
Emergent from content. Examples: `career`, `family`, `location`, `health`, `finances`, `work`, `weather`, `housing`, etc.

**Temporal tags** (when?)
- `current` — present state
- `past` — historical
- `future` — planned or anticipated
- `uncertain` — hedged, conditional

**Confidence tags** (how clear?)
- `explicit` — directly stated
- `inferred` — reasonably derived
- `speculative` — possible interpretation

### Tagged Output Format

```
┌─────────────────────────────────────────────────────────┐
│ statement: "endures Seattle weather because of job"     │
│ dimensions: [reasoning, preference]                     │
│ topics: [weather, career, location]                     │
│ temporal: current                                       │
│ confidence: inferred                                    │
│ source_id: msg_4821                                     │
└─────────────────────────────────────────────────────────┘
```

### Full Example

**Input:**
> "I've been struggling with Seattle weather but the Amazon job is worth it for now"

**Normalized + Tagged:**

```
┌──────────────────────────────────────────────────────────────┐
│ statement: "dislikes Seattle weather"                        │
│ dimensions: [opinion, preference]                            │
│ topics: [weather, location]                                  │
│ temporal: current                                            │
│ confidence: explicit                                         │
├──────────────────────────────────────────────────────────────┤
│ statement: "works at Amazon in Seattle"                      │
│ dimensions: [identity]                                       │
│ topics: [career, location]                                   │
│ temporal: current                                            │
│ confidence: explicit                                         │
├──────────────────────────────────────────────────────────────┤
│ statement: "considers Amazon job worth it"                   │
│ dimensions: [opinion]                                        │
│ topics: [career]                                             │
│ temporal: current                                            │
│ confidence: explicit                                         │
├──────────────────────────────────────────────────────────────┤
│ statement: "uncertain if job worth it long-term"             │
│ dimensions: [opinion, desire]                                │
│ topics: [career]                                             │
│ temporal: future                                             │
│ confidence: inferred                                         │
├──────────────────────────────────────────────────────────────┤
│ statement: "endures Seattle weather because of job"          │
│ dimensions: [reasoning, preference]                          │
│ topics: [weather, career, location]                          │
│ temporal: current                                            │
│ confidence: inferred                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Why This Works

### 1. No Information Loss to Schema Mismatch

CPF-7 asks: "Which schema field does this belong to?"
ASNE asks: "What atomic statements capture this meaning?"

If something doesn't fit a schema, CPF-7 either drops it or distorts it. ASNE just writes it down.

### 2. Inferences Have a Home

"Endures Seattle weather because of job" is an inference connecting two facts. In CPF-7, it either gets lost or awkwardly split between dimensions. In ASNE, it's simply a tagged statement.

### 3. LLM-Friendly Downstream

The extracted data is natural language. Downstream LLMs can read it directly without parsing structured schemas. This makes RAG-style memory and context injection trivial:

```
"Here's what we know about this user:
- dislikes Seattle weather
- works at Amazon in Seattle
- endures Seattle weather because of job
- uncertain if job worth it long-term
..."
```

### 4. Tagging is Soft, Not Hard

A statement can have multiple dimension tags. "Endures weather because of job" is both `reasoning` and `preference`. No need to pick one canonical dimension.

### 5. Human Readable and Auditable

Anyone can read the extracted statements and understand what was captured. No schema documentation required. Easy to audit, correct, or annotate further.

### 6. Handles Contradiction Naturally

If someone says "I love my job" in January and "I hate my job" in March, you get:

```
statement: "loves job"
temporal: past (January)

statement: "hates job"  
temporal: current (March)
```

Both exist. Downstream systems decide how to handle contradiction. The extraction layer doesn't force premature resolution.

---

## Comparison: CPF-7 vs ASNE

| Aspect | CPF-7 | ASNE |
|--------|-------|------|
| Output format | Schema objects | Natural language statements |
| Structure | Rigid, predefined fields | Flexible, emergent |
| Inference capture | Limited by schema | Unlimited |
| Multi-dimensional content | Must pick primary dimension | Multiple tags allowed |
| Downstream integration | Requires schema parsing | Direct LLM consumption |
| Human readability | Requires schema knowledge | Immediately readable |
| Query method | Field-based queries | Tag + semantic search |
| Contradiction handling | Must resolve or overwrite | Both versions preserved |
| Implementation complexity | High (schema design, validation) | Lower (normalize, tag) |

---

## Implementation

### LLM Prompt Structure

**Stage 1: Normalization**

```
Given the following conversational message, extract all information 
into atomic, self-contained natural language statements.

Rules:
- One fact/opinion/inference per statement
- Resolve pronouns and references
- Include reasonable inferences, not just literal content
- Strip filler and hedging
- Keep statements simple and direct

Message: "{input}"

Atomic statements:
```

**Stage 2: Tagging**

```
For each statement, apply relevant tags.

Dimensions (select all that apply):
- identity, opinion, preference, desire, narrative, event, 
- relationship, reasoning, emotion, intention

Topics: extract relevant subject matter

Temporal: current / past / future / uncertain

Confidence: explicit / inferred / speculative

Statement: "{statement}"

Tags:
```

### Storage

Statements stored with:
- Statement text
- Dimension tags (array)
- Topic tags (array)
- Temporal marker
- Confidence marker
- Source message ID
- Timestamp
- Conversation ID

### Retrieval

**By dimension:**
```
SELECT * WHERE dimensions CONTAINS 'opinion'
```

**By topic:**
```
SELECT * WHERE topics CONTAINS 'career'
```

**By semantic similarity:**
```
SELECT * WHERE embedding SIMILAR TO query_embedding
```

**Combined:**
```
SELECT * WHERE dimensions CONTAINS 'opinion' 
         AND topics CONTAINS 'career'
         ORDER BY semantic_similarity(embedding, query)
```

---

## When to Use ASNE vs CPF-7

### Use ASNE when:
- Downstream systems are LLM-based
- You can't predict all relevant schema fields upfront
- Capturing inferences and relationships matters
- You want human-auditable extraction
- Building conversational memory / RAG systems
- Domain is broad or undefined

### Use CPF-7 when:
- You need precise, field-level queries
- Downstream systems expect structured records
- Cross-user analytics on specific attributes matter
- Domain is narrow and well-understood
- Schema stability is valuable

---

## Conclusion

ASNE offers a different philosophy for conversational data extraction. Rather than forcing rich, messy human conversation into predefined schemas, it normalizes into atomic natural language statements and applies loose categorical tags.

The result: extracted data that preserves inferential richness, handles contradiction gracefully, integrates naturally with LLM-based downstream systems, and remains human-readable throughout.

It's not the right choice for every application. But for systems that want to capture *what was really communicated* rather than just *what fits the schema*, ASNE provides a compelling alternative.