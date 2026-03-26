# Node 1 Output: CPDE-7 Architecture Patterns for PRAGMA

Study of the CPDE-7 implementation to extract patterns PRAGMA must follow.


## File Structure

```
cpde7/
├── __init__.py                    # Public API — exports service, models, config, prompts
├── config.py                      # ExtractionConfig dataclass (which dimensions to run)
├── models.py                      # Pydantic models for structured LLM output (~787 lines)
├── prompts.py                     # Proteas-based prompt builder (dimension registry)
├── batch_prompts.py               # Full batch prompts (all messages = extraction targets)
├── batch_prompts_targeted.py      # Targeted prompts (TARGET/CONTEXT markers) (~1443 lines)
├── cpde7llmservice.py             # Main service class (~979 lines)
├── docs/                          # Documentation
└── extraction_tests/              # Test data
```


## Key Architectural Patterns

### 1. Pydantic Models for Structured Output

Every LLM call uses LangChain's `with_structured_output()` which forces the LLM to return data matching a Pydantic model. No JSON parsing. No regex. The LLM is constrained to the schema.

```python
structured_llm = self._get_llm().with_structured_output(BatchCoreIdentityOutput)
result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
```

**PRAGMA implication:** Every PRAGMA prompt output (EI micro-signals, intent classification, density axes, etc.) needs a Pydantic model. The LLM returns structured data directly.


### 2. Per-Dimension Extraction Methods

Each dimension has its own `extract_X()` method:

```python
async def extract_core_identity(self, messages: str) -> BatchCoreIdentityOutput:
    prompt = CPDE_CORE_IDENTITY_BATCH.format(messages=messages)
    structured_llm = self._get_llm().with_structured_output(BatchCoreIdentityOutput)
    return await structured_llm.ainvoke([HumanMessage(content=prompt)])
```

Pattern: prompt template + model + LLM call. Same for all 7 dimensions.

**PRAGMA implication:** PRAGMA needs `extract_expressed_involvement()`, `extract_intent()`, `extract_density()`, `extract_investment()`, `extract_dialogic_function()` — each with its own prompt + model.


### 3. Configurable Dimension Selection

`ExtractionConfig` controls which dimensions to run:

```python
@dataclass
class ExtractionConfig:
    dimensions: list[str] = field(default_factory=lambda: list(CPF7_DIMENSIONS))
    batch_size: int = 50
    min_messages_for_extraction: int = 5
    confidence_threshold: float = 0.5
```

The service's `extract_all()` method checks which dimensions are in the config and only runs those.

**PRAGMA implication:** PRAGMA needs a `PragmaConfig` with:
- `dimensions: list[str]` (which of the 5 LLM-based dimensions to run)
- `run_topic_flow: bool` (whether to run Topic Flow upstream)
- `run_dynamics_profile: bool` (whether to compose per segment)
- `run_interpretation: bool` (whether to run tension checks)
- `run_apt_inference: bool` (whether to run APT)


### 4. Parallel vs Sequential Execution

The service supports both:

```python
async def extract_all(self, messages, dimensions=None, parallel=False):
    if parallel:
        tasks = [self.extract_X(messages) for X in dimensions]
        outputs = await asyncio.gather(*tasks)
    else:
        for dim in dimensions:
            output = await self.extract_dimension(messages, dim)
```

**PRAGMA implication:** PRAGMA's 5 per-message LLM calls can run in parallel (they're independent once Topic Flow completes). Topic Flow must complete first (dependency). Upper layers are sequential (each depends on the prior).


### 5. Prompt Structure (Targeted)

Prompts use TARGET/CONTEXT markers to control what the LLM extracts from:

```
Messages are marked with either "(TARGET)" or "(CONTEXT)":
TARGET messages — Extract from these
CONTEXT messages — Use for understanding, do NOT extract from
```

**PRAGMA implication:** PRAGMA doesn't need TARGET/CONTEXT markers (it analyzes ALL messages in a conversation). But it DOES need to handle multi-participant conversations. The message format should include sender identity.


### 6. Model Hierarchy

```
Item model (single extracted fact)
  → Result model (collection of items + has_content flag)
    → Output model (wrapper for structured output)
      → Combined result (all dimensions together)
```

Example:
```python
CoreIdentityItem → CoreIdentityResult → BatchCoreIdentityOutput
                                              ↓
                              BatchProfilingDataExtractionResult (all 7)
```

**PRAGMA implication:** PRAGMA needs:
```
EIMicroSignal → EIResult → EIOutput
IntentCategory → IntentResult → IntentOutput
DensityAxis → DensityResult → DensityOutput
...
→ PragmaSignalLayerResult (all dimensions combined)
→ PragmaSegmentResult (+ aggregation + dynamics profile)
→ PragmaConversationResult (+ interpretation + APT)
```


### 7. LLM Factory

Uses chatforge's `get_llm()` factory:

```python
from chatforge.services.llm.factory import get_llm
self._llm = get_llm(provider=self._provider, model_name=self._model_name, temperature=0)
```

**PRAGMA implication:** Same pattern. PRAGMA uses the same LLM factory. No custom LLM setup needed.


### 8. All Methods Are Async

Every extraction method is `async def`. Uses `await` for LLM calls. Supports `asyncio.gather()` for parallelism.

**PRAGMA implication:** PRAGMA service must be fully async.


### 9. Batch Processing

CPDE-7 processes messages in batches (configurable `batch_size`). A batch of N messages → one LLM call per dimension.

**PRAGMA implication:** PRAGMA is different. It processes PER MESSAGE (not per batch). Each message gets up to 5 LLM calls. But it could batch multiple messages into one prompt for efficiency (similar to how Topic Flow's medium/long windows work). This is an optimization decision, not a structural one.


### 10. Export Pattern

`__init__.py` exports everything needed:
- Service class
- Config class
- All models
- All prompts
- Targeted extraction helpers

**PRAGMA implication:** `pragma/__init__.py` must export: `PragmaService`, `PragmaConfig`, all output models, all prompts.


## Key Differences Between CPDE-7 and PRAGMA

| Aspect | CPDE-7 | PRAGMA |
|---|---|---|
| **Unit of analysis** | Batch of messages | Per message + per segment |
| **What it extracts** | Facts about a person (content) | Behavioral dynamics (acts) |
| **Dimensions** | 7 content categories | 7 behavioral dimensions |
| **State** | Stateless (each batch is independent) | Stateful (accumulates across messages, tracks segments) |
| **Dependencies** | Each dimension is independent | Topic Flow → Signal Layer → Dynamics Profile → Interpretation |
| **Output timing** | After processing a batch | Per message (signals) + per segment (composition) + per conversation (profiles) |
| **LLM calls per unit** | 1-7 per batch (configurable) | 5 per message + 1 per segment + on-demand |

The biggest architectural difference: **CPDE-7 is stateless, PRAGMA is stateful.** PRAGMA needs to accumulate per-message signals, detect segment boundaries, and aggregate across segments. This requires a state management layer that CPDE-7 doesn't have.


## What This Means for Node 2 (Models + Config)

The models need to handle three levels:
1. **Per-message output** (what each LLM call returns)
2. **Per-segment aggregation** (accumulated from per-message outputs)
3. **Per-conversation result** (composition of all segments)

The config needs:
- Which dimensions to run (like CPDE-7)
- Whether to run upper layers (Dynamics Profile, Interpretation, APT)
- Topic Flow window sizes (configurable)
- Aggregation parameters

The service needs state management that CPDE-7 doesn't need:
- Active segment tracking
- Per-message signal accumulation
- Segment completion detection
- Cross-segment profile building