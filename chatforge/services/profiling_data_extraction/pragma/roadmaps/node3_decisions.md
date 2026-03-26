# Node 3 Decisions: Topic Flow Service

Decisions made during roadmap execution that resolved the foggy areas.


## Decision 1: Topic Flow lives inside pragma/

**Question:** Separate service or module within PRAGMA?

**Decision:** Module within `src/pragma/topic_flow.py`. PRAGMA depends on Topic Flow, so they stay in the same package for now. Can be extracted into a separate service later if needed.

**Rationale:** CPDE-7 is self-contained. Topic Flow is PRAGMA's upstream dependency, not a separate product. Keeping it co-located simplifies imports and state sharing.


## Decision 2: State is in-memory, exportable to JSON

**Question:** Where does segment state live between messages?

**Decision:** In-memory Python object during processing. Exportable to JSON for persistence and debugging. No database models yet. DB models and tables will be created later once fields stabilize.

**Rationale:** The state shape (active topics, segment boundaries, topic history) is still evolving. Committing to DB schema now would create migration overhead. JSON export gives persistence without schema commitment.

**State includes:**
- Active topics (identity, focus, state per topic)
- Segment boundaries (where dominant topics change)
- Topic history (full timeline of topic events)
- Per-message topic assignments


## Decision 3: Processing frequency is configurable

**Question:** How often do Topic Flow LLM calls run?

**Decision:** Configurable via `PragmaConfig`. Default: immediate window runs every message (or every 3 messages batched), medium window every 5 messages, long window every 10 messages. The exact frequency is a tuning parameter, not an architectural decision.

**Key insight:** Topic Flow can batch. Send 3 messages in one call, get topic readings for the window. This is what the existing Topic Flow prompt already does: it takes a window and produces readings for the window, not per-message.

**Per-message PRAGMA dimensions** (EI, Intent, Density, Investment, Dialogic Function) still run per-message since each message needs its own reading.


## Impact on Roadmap

These decisions make Node 3 **clear** (was foggy). The implementation path is:
1. Create `src/pragma/topic_flow.py` with a `TopicFlowState` class (in-memory state)
2. Implement the three-window LLM prompts from `devdocs/topicflow/calculation_logic.md`
3. Add `to_json()` / `from_json()` for state export/import
4. Integrate with `PragmaConfig` for window sizes and frequency