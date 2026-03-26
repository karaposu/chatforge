# Sense-Making: APT Inference Prompt Design

## SV1
APT Inference needs a prompt that maps Dynamics Profile + tensions to charm/hope/fear readings.

## Key Decisions Made

1. **Categorical, not floats.** 5 levels: absent, low, moderate, high, very_high. Attachment can't be measured to decimal precision.

2. **Directional.** A→B and B→A are separate readings. The asymmetry IS the dynamic.

3. **Per-field reasoning.** Every charm/hope/fear score has a reason field grounded in specific observed dynamics, not vague impressions.

4. **Domain 2 is descriptive.** Content, Style, Expressed Frame are free-text, not categorical. The Dynamics Profile already provides the substance; APT re-frames it through the presentation lens.

5. **Cumulative across segments.** Prior APT readings are passed as context. Confidence increases: low (1 segment) → moderate (2-3) → high (4+).

6. **Overall dynamic field.** Freestyle summary of the attachment relationship. "Who is more attached? What drives it? What is the asymmetry?"

7. **Evolution field.** What changed from prior readings and why. Tracks how attachment develops across the conversation.

## What Grounds the Reasons

Reasons must reference specific dynamics from the input:
- GOOD: "Charm is high because A's involvement increases when B demonstrates expertise"
- BAD: "A seems impressed by B"

The test: could you point to a specific line in the Dynamics Profile that supports this reason?