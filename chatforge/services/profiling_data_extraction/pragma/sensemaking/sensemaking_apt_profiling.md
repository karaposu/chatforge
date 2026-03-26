# Sense-Making: APT Profiling Schema

## SV1
APT Profiling aggregates APT Inference outputs across conversations into an individual profile.

## Key Decisions

1. **Pattern extraction, not level averaging.** "Charm=high 3 times" is meaningless at profile level. "Charmed by expertise 3 times" is the signal. The reason fields from APT Inference are the primary data.

2. **Triggers + blockers + non-triggers.** Each attachment variable has three pattern types: what triggers it, what blocks it even when triggers are present, and what doesn't trigger it. Non-triggers are informative ("wealth does NOT charm this person").

3. **Condition→behavior mappings for presentation.** "When confident → terse. When insecure → over-explains." Extracted from presentation descriptions across conversations.

4. **LLM semantic update, not statistical.** The LLM reads existing profile + new APT Inference and decides what to strengthen, weaken, or add. Not append-only.

5. **One profile per person, universal with context tags.** Don't split into work/personal sub-profiles. Tag context when available but keep one profile. Split when data warrants it.

6. **Counter-examples are first-class.** Don't delete a pattern when contradicted. Note the counter-evidence. "Usually charmed by expertise BUT NOT when condescending."

7. **Confidence scales with observation count.** 1 conv = very_low, 4-7 = moderate, 16+ = very_high.

## How It Should NOT Be
- Not arithmetic averaging of categorical levels
- Not a static snapshot (it's a living document)
- Not a single conversation projected onto a person
- Not a replacement for APT Inference

## SV6
APT Profiling is a per-person, LLM-updated, living profile that extracts trigger patterns and condition→behavior mappings from accumulated APT Inference reason fields. The key insight: aggregate reasons and patterns, not levels and numbers.