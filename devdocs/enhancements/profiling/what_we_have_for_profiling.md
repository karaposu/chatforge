# What We Have for Profiling

## The Distinction: Extraction vs Profiling

There are two separate concerns:

1. **Profiling Data Extraction** - Pulling raw facts from conversations
2. **Profiling** - Aggregating and synthesizing those facts into a coherent user profile

We have built the first. The second is the next challenge.

---

## What CPDE-7 Extraction Produces

The `CPDE7LLMService` extracts raw profiling data across 7 dimensions:

| Dimension | What It Captures | Example Extracted Item |
|-----------|------------------|------------------------|
| **Core Identity** | Who they are (roles, attributes, states) | `{aspect: "profession", state_value: "software engineer"}` |
| **Opinions & Views** | Lasting beliefs and worldviews | `{about: "remote work", view: "is the future"}` |
| **Preferences & Patterns** | Behavioral tendencies | `{activity: "coding", preference: "better at night"}` |
| **Desires & Needs** | Wants, hopes, goals | `{type: "want", target: "transition to AI/ML"}` |
| **Life Narrative** | Biographical facts | `{what_happened: "lived in Tokyo", period: "3 years"}` |
| **Events** | Current/recent occurrences | `{event: "interviewing at Google", involvement: "candidate"}` |
| **Entities & Relationships** | People, orgs, places they mention | `{name: "Sarah", entity_type: "person", relationship: "mentor"}` |

### Characteristics of Extracted Data

- **Atomic**: Each item is a single fact
- **Attributed**: Source message ID and quote included
- **Timestamped**: Extraction time known (message timestamp available)
- **Dimensional**: Categorized into one of 7 dimensions
- **Accumulative**: Multiple extractions over time produce many items

---

## The Gap: Raw Data → User Profile

Extracted data is **raw material**, not a profile.

Consider a user with 50 conversations over 6 months. Extraction might produce:
- 200+ identity facts
- 150+ opinions
- 100+ preferences
- Many potentially conflicting or evolving statements

**Questions that arise:**
- How do we turn raw data to profiling data
- What is Profiling data anyway? for who for what? 
- How do we reconcile contradictions? ("I love mornings" vs "I'm a night person")
- How do we handle temporal evolution? (Opinions change, jobs change)
- How do we weight recent vs old information?
- How do we represent uncertainty and confidence?
- How much detail does the profile need?

---

## Profiling: The Next Step

Profiling takes the extracted data and produces something usable - a synthesized representation of the user.

### What Profiling Must Do

1. **Aggregate** - Combine items across multiple extractions/conversations
2. **Reconcile** - Handle conflicts and contradictions
3. **Prioritize** - Weight by recency, frequency, or importance
4. **Synthesize** - Produce a coherent representation
5. **Update** - Evolve as new data arrives

### The Configurability Requirement

Different use cases need different profile depths:

| Use Case | Profile Depth Needed |
|----------|---------------------|
| Quick personalization | Shallow - key facts only |
| Recommendation system | Medium - preferences and patterns |
| Long-term assistant | Deep - full context including history |
| Analytics/Research | Varies - might need everything |

The profiling system should be **configurable** - allowing control over:
- Which dimensions to include
- Level of detail/compression
- Temporal weighting
- Confidence thresholds
- Output format

---

## The Need for a Conceptual Framework

Just as CPDE-7 provides a framework for extraction (7 dimensions, clear schemas), profiling needs its own conceptual framework.

This framework would define:
- How profiles are structured
- How aggregation works
- How conflicts are resolved
- How profiles evolve over time
- How depth/detail is controlled

**This framework does not exist yet.**

The extraction system is complete. The profiling system needs design.

---

## Current State Summary

| Component | Status |
|-----------|--------|
| CPDE-7 Extraction | ✅ Implemented |
| Extraction Service | ✅ `CPDE7LLMService` |
| Raw Data Schema | ✅ Pydantic models |
| Storage | ⚠️ Port defined, adapters exist |
| Profiling Framework | ❌ Not defined |
| Profiling Service | ❌ Not implemented |
| Profile Schema | ❌ Not defined |

---

## What Comes Next

Before implementation, we need:

1. A conceptual framework for profiling
2. Decisions on configurability dimensions
3. Profile schema design
4. Aggregation strategy
5. Conflict resolution approach

These are open design questions that require exploration.
