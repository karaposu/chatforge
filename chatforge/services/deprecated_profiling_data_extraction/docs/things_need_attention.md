# Things That Need Attention

A comprehensive list of decisions, issues, and unknowns for the Profiling Data Extraction service.

---

## 1. Framework Choice: CPDE-7 vs ASNE

### Current Status
Two extraction frameworks are documented:
- **CPDE-7** (`cpde-7.md`): Schema-bound extraction into 7 dimensions with structured fields
- **ASNE** (`ASNE.md`): Schema-free extraction into atomic natural language statements with tags

Both are well-documented with pros/cons.

### What Needs to Be Determined
- Which framework to implement first?
- Are they mutually exclusive or can both exist?
- Is ASNE a future enhancement or an alternative?

### Why This Matters
- **Implementation scope**: CPDE-7 requires Pydantic models per dimension; ASNE needs different infrastructure
- **Downstream compatibility**: CPDE-7 is query-friendly (field-based); ASNE is LLM-friendly (natural language)
- **Resource allocation**: Can't build both simultaneously
- **Architecture decisions**: Service interface differs significantly between approaches

### Recommendation
Start with CPDE-7 (already have prompts, models, clear schema). ASNE can be a future alternative.

---

## 2. Processing Model: Per-Message vs Batch

### Current Status
Conflicting approaches in documentation:
- `prompts.py`: Designed for **per-message** extraction with TARGET + CONTEXT pattern
- `elaboration.md`: Shows **per-message** with `context_window` config
- `step_by_step_...md`: Describes **batch** processing (multiple messages per LLM call)

### What Needs to Be Determined
- Which processing model is canonical?
- If per-message: what is the context window size?
- If batch: how do we maintain message-level attribution?
- How does this affect `batch_size` config meaning?

### Why This Matters
- **Prompt design**: Current prompts assume per-message; batch requires redesign
- **Traceability**: Per-message gives exact source attribution; batch is ambiguous
- **Cost**: Per-message = more LLM calls; batch = fewer calls but less precision
- **Implementation complexity**: Per-message needs windowing logic; batch needs different aggregation

### Recommendation
Use **per-message with context window** - matches existing prompts and provides better traceability.

---

## 3. Prompts Need Pydantic Alignment

### Current Status
- `prompts.py`: Contains detailed JSON schema instructions in each prompt
- `models.py`: Created with Pydantic models matching those schemas
- `with_structured_output()`: Should replace manual JSON generation

### What Needs to Be Determined
- Should prompts be stripped of JSON schema sections?
- Do Field descriptions in Pydantic models provide enough guidance?
- Are there extraction rules in prompts that must be preserved?

### Why This Matters
- **Redundancy**: JSON schema in prompts + Pydantic models = duplication
- **Token efficiency**: Removing JSON instructions saves tokens per call
- **Reliability**: Pydantic structured output is more reliable than JSON parsing
- **Maintenance**: Two places to update when schema changes

### Recommendation
Keep extraction logic (what counts, examples, rules) in prompts. Remove JSON schema sections. Let Pydantic handle output structure.

---

## 4. Config Completeness

### Current Status
`config.py` has:
```python
dimensions: list[str]
batch_size: int = 50
min_messages_for_extraction: int = 5
confidence_threshold: float = 0.5
```

`elaboration.md` shows additional fields:
```python
context_window: int
deduplication: bool
output_format: str
```

### What Needs to Be Determined
- Add `context_window`? (needed for per-message extraction)

- Is `batch_size` still relevant if using per-message model?
- Should we rename/repurpose `batch_size` to mean something else?

### Why This Matters
- **Per-message model**: Needs `context_window` to know how many previous messages to include
- **API clarity**: Config fields should match processing model
- **Flexibility**: Users need control over extraction behavior

### Recommendation
- Add `context_window: int = 5`
- Keep `batch_size` as "messages per extraction run" (not per LLM call)
- Defer `deduplication` until needed

---

## 5. Aggregation Scope Confirmation

### Current Status
- `elaboration.md`: Shows `aggregated_profile` in output
- `details.md`: States "Profiling (aggregation) is a separate future step"
- Current dataclasses: Only `ExtractedProfilingData` (raw facts)

### What Needs to Be Determined
- Confirm aggregation is out of scope for this service
- Should `elaboration.md` be updated to remove aggregation?
- What is the boundary between extraction and aggregation?

### Why This Matters
- **Scope creep**: Building aggregation now delays core extraction
- **Documentation accuracy**: Conflicting docs cause confusion
- **Architecture**: Aggregation may need different service with different concerns (deduplication, temporal reasoning, contradiction handling)

### Recommendation
Confirm: Extraction only. No aggregation. Update `elaboration.md` to mark aggregation as future.

---

## 6. CPDE7LLMService Implementation

### Current Status
- Concept documented in `cpde_7_llmservice.md`
- `models.py` created with Pydantic schemas
- `prompts.py` exists with dimension prompts
- No actual `cpde7llmservice.py` file yet

### What Needs to Be Determined
- Implementation approach (one method per dimension vs dynamic)
- How to handle LLM caching
- Sync vs async interface
- Error handling strategy per dimension

### Why This Matters
- **Core functionality**: This is where extraction actually happens
- **Reusability**: Other services depend on this
- **Testability**: Need clean interface for mocking
- **Performance**: LLM caching affects cost and latency

### Action Required
Implement `cpde7llmservice.py` following the documented pattern.

---

## 7. Sender Attribution (Multi-Party)

### Current Status
- `handicaps.md` identifies this as a problem
- Current assumption: Single-speaker extraction (filter by sender_id first)
- No implementation for multi-party attribution

### What Needs to Be Determined
- Is single-speaker sufficient for MVP?
- How to handle conversations with multiple users?
- Should extracted facts be attributed to specific speakers?

### Why This Matters
- **Data accuracy**: "I'm 28 years old" - WHO is 28?
- **Profile mixing**: Without attribution, profiles get contaminated
- **Use case support**: Group chats, support tickets, multi-party conversations

### Recommendation
MVP: Single-speaker (filter messages by user_id before extraction). Multi-party is future enhancement.

---

## 8. Storage & Database

### Current Status
- `StoragePort` has 6 extraction methods defined
- `SQLAlchemy` adapter has methods implemented
- SQLAlchemy models exist (`ProfilingDataExtractionRun`, `ExtractedProfilingData`)
- No migrations or table creation tested

### What Needs to Be Determined
- How are tables created? (Alembic migrations? Auto-create?)
- Are the foreign keys correct? (chat_id references chats.id)
- Does `get_messages_for_extraction` query work correctly?
- Memory adapter for testing?

### Why This Matters
- **Production readiness**: Tables must exist before service runs
- **Data integrity**: FK constraints must be correct
- **Testing**: Need in-memory adapter for unit tests
- **Query performance**: Join logic in `get_messages_for_extraction` needs validation

### Action Required
- Test table creation
- Validate FK relationships
- Create memory adapter for testing
- Add indexes for common queries

---

## 9. Confidence Scoring

### Current Status
- `ExtractionConfig.confidence_threshold = 0.5`
- Prompts mention confidence but don't explain how LLM should determine it
- Pydantic models don't include confidence field (except in item-level extraction)

### What Needs to Be Determined
- How does LLM determine confidence?
- Should confidence be per-item or per-extraction?
- What does confidence threshold filter on?
- Is confidence even reliable from LLMs?

### Why This Matters
- **Quality filtering**: Low-confidence extractions may be noise
- **User trust**: Confidence scores affect downstream decisions
- **LLM reliability**: LLMs may not self-assess accurately

### Recommendation
Add confidence to item models. Provide guidance in prompts for when to use high vs low confidence. Accept that LLM confidence is approximate.

---

## 10. Dimension Naming Inconsistency

### Current Status
- `config.py`: `"entities_relationships"`
- Some prompts/docs: `"entities"`
- `DIMENSION_MODELS` in models.py: `"entities_relationships"`

### What Needs to Be Determined
- What is the canonical name for dimension 7?
- Are all references consistent across codebase?

### Why This Matters
- **Runtime errors**: Mismatched names cause KeyError
- **Config validation**: `ExtractionConfig.__post_init__` checks against `CPF7_DIMENSIONS`
- **Documentation**: Users need consistent terminology

### Action Required
Audit all files and standardize to `"entities_relationships"` everywhere.

---

## 11. Testing Strategy

### Current Status
- No tests exist for profiling data extraction
- `step_by_step_...md` shows test examples but not implemented
- Need unit tests (mock LLM) and integration tests (real LLM)

### What Needs to Be Determined
- How to mock `with_structured_output()`?
- What fixtures are needed?
- Integration test with real LLM - how to manage costs?
- How to test storage adapter methods?

### Why This Matters
- **Reliability**: Untested code breaks in production
- **Refactoring safety**: Tests enable confident changes
- **Documentation**: Tests serve as usage examples
- **CI/CD**: Need automated validation

### Action Required
Create test suite:
- `tests/unit/profiling_data_extraction/test_cpde7llmservice.py`
- `tests/unit/profiling_data_extraction/test_service.py`
- `tests/integration/profiling_data_extraction/test_extraction.py`

---

## 12. Error Handling Strategy

### Current Status
- `step_by_step_...md` mentions graceful degradation
- No formal error handling defined
- Run status: pending → running → completed/failed

### What Needs to Be Determined
- What happens if LLM call fails mid-extraction?
- Retry strategy?
- Partial success handling (some dimensions fail, others succeed)?
- How to surface errors to callers?

### Why This Matters
- **Resilience**: LLM APIs fail; service must handle gracefully
- **Debugging**: Need visibility into what failed and why
- **Recovery**: Should failed extractions be retryable?
- **User experience**: Callers need meaningful error information

### Recommendation
- Log and continue on per-dimension failures
- Mark run as "partial" if some dimensions fail
- Store error details in `ProfilingDataExtractionRun.error`
- Don't retry automatically (let caller decide)

---

## 13. Incremental Extraction

### Current Status
- `since_message_id` parameter exists in storage methods
- `message_id_range` tracked in extraction runs
- No formal incremental extraction workflow documented

### What Needs to Be Determined
- How does caller know last extracted message ID?
- Should we auto-track last extraction per user?
- What about re-extraction of updated messages?
- How to handle deleted messages?

### Why This Matters
- **Efficiency**: Don't re-extract already-processed messages
- **Cost**: Avoid duplicate LLM calls
- **Freshness**: New messages should be extracted incrementally
- **Complexity**: Tracking state adds implementation burden

### Recommendation
MVP: Caller provides `since_message_id`. Future: Auto-track last extraction in extraction runs.

---

## 14. LLM Provider Compatibility

### Current Status
- Using `get_llm()` from chatforge
- `with_structured_output()` is LangChain feature
- Different providers may behave differently

### What Needs to Be Determined
- Does `with_structured_output()` work with Anthropic?
- What about AWS Bedrock, Azure, local models?
- Are there provider-specific quirks?

### Why This Matters
- **Portability**: Users may want different providers
- **Cost optimization**: Some providers cheaper than others
- **Feature parity**: Not all providers support structured output equally

### Action Required
Test with at least OpenAI and Anthropic. Document any provider-specific notes.

---

## 15. Documentation Cleanup

### Current Status
Multiple docs with overlapping/conflicting content:
- `cpde-7.md` - Framework spec
- `ASNE.md` - Alternative approach
- `elaboration.md` - Architecture (may be outdated)
- `notes.md` - Implementation notes
- `cpde_7_llmservice.md` - Service pattern
- `step_by_step_...md` - Build guide
- `details.md` - Prerequisites (in parent folder)
- `handicaps.md` - Known issues

### What Needs to Be Determined
- Which docs are authoritative?
- Which are outdated and need updating?
- Should some be consolidated?

### Why This Matters
- **Onboarding**: New developers get confused
- **Maintenance**: Outdated docs cause bugs
- **Decision making**: Hard to know what's decided vs proposed

### Recommendation
- Mark `elaboration.md` as "design exploration" (not current implementation)
- Keep `notes.md` as living document for decisions
- `cpde-7.md` is the framework spec (canonical)
- `step_by_step_...md` should reflect actual implementation plan

---

## Summary: Priority Actions

| Priority | Item | Action |
|----------|------|--------|
| **P0** | Processing Model | Decide: per-message with context (recommended) |
| **P0** | CPDE7LLMService | Implement the service |
| **P0** | Prompt cleanup | Remove JSON schema, keep extraction logic |
| **P1** | Config update | Add `context_window` field |
| **P1** | Dimension naming | Standardize to `entities_relationships` |
| **P1** | Aggregation scope | Confirm out of scope, update docs |
| **P1** | Storage testing | Validate tables, queries, FKs |
| **P2** | Testing | Create test suite |
| **P2** | Error handling | Define strategy, implement |
| **P2** | Confidence scoring | Add to models, document in prompts |
| **P3** | Provider compatibility | Test OpenAI + Anthropic |
| **P3** | Documentation cleanup | Mark outdated, consolidate |
| **Future** | Multi-party attribution | After MVP |
| **Future** | ASNE framework | Alternative to CPDE-7 |
| **Future** | Aggregation service | Separate from extraction |
