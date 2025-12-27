# ChatForge Testing Plan - Getting It Working Step by Step

**Status**: This codebase is under heavy development and not currently working. This document outlines a plan to bring it up piece by piece.

---

## Philosophy

Instead of trying to get everything working at once, we'll test components incrementally:
1. Start with the simplest possible component
2. Verify it works in isolation
3. Uncover hidden problems as we go
4. Build up to more complex integrations

---

## Phase 1: Simple LLM Call ✓ (Current)

**Goal**: Make a single LLM call without any storage, tracing, middleware, or complex features.

**What We're Testing**:
- LLM factory (`src/llm/factory.py`)
- Configuration loading (`src/config/llm.py`)
- Environment variable reading
- Basic LangChain integration

**Test Script**: `src/test_simple_llm_call.py`

### Setup Instructions

1. **Install core dependencies**:
```bash
pip install langchain-core langchain-openai pydantic pydantic-settings python-dotenv
```

2. **Create .env file**:
```bash
cp .env.example .env
```

Then edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4o-mini
LLM_TEMPERATURE=0.0
```

3. **Run the test**:
```bash
cd src
python test_simple_llm_call.py
```

### Expected Output

```
============================================================
ChatForge - Simple LLM Call Test
============================================================
✓ Successfully imported chatforge modules

------------------------------------------------------------
Configuration:
------------------------------------------------------------
Provider: openai
Model: gpt-4o-mini
Temperature: 0.0
API Key configured: Yes
------------------------------------------------------------

[1/3] Creating LLM instance...
✓ LLM instance created successfully

[2/3] Sending test message to LLM...
Message: "Hello! Please respond with a simple greeting."
✓ Received response from LLM

[3/3] Response:
------------------------------------------------------------
Hello! How can I assist you today?
------------------------------------------------------------

[Bonus] Testing conversation format...
✓ Conversation format works
Response: 2 + 2 equals 4.

============================================================
Test completed successfully! ✓
============================================================
```

### Known Issues to Discover

As we run this test, we might find:
- Import path issues
- Missing dependencies
- Configuration loading problems
- API key validation issues
- LangChain version compatibility issues

**Action**: Document each issue as we find it!

---

## Phase 2: Agent Without Tools (Next)

**Goal**: Create a ReActAgent that can have a conversation, but with no tools (just pure chat).

**What We're Testing**:
- Agent creation (`src/adapters/agent/engine.py`)
- LangGraph integration
- Message conversion
- Conversation history handling
- Basic agent loop

**Test Script**: `test_agent_no_tools.py` (to be created)

### Setup Steps

1. Install additional dependencies:
```bash
pip install langgraph
```

2. Create test script that:
   - Creates a ReActAgent with empty tools list
   - Sends a simple message
   - Processes response
   - Sends follow-up message with history
   - Verifies conversation memory works

### Expected Problems

- LangGraph version compatibility
- Message format issues
- Agent state management
- Error handling in agent loop

---

## Phase 3: Agent With Simple Tool (Future)

**Goal**: Add a single, simple tool to the agent (e.g., a calculator or echo tool).

**What We're Testing**:
- Tool creation (`src/tools/base.py`)
- AsyncAwareTool base class
- Agent tool selection
- Tool execution
- Result formatting

**Test Script**: `test_agent_with_tool.py` (to be created)

### Setup Steps

1. Create a simple calculator tool:
```python
class CalculatorTool(AsyncAwareTool):
    name = "calculator"
    description = "Performs basic math: add, subtract, multiply, divide"

    async def _execute_async(self, operation: str, a: float, b: float) -> str:
        if operation == "add":
            return f"{a} + {b} = {a + b}"
        # ... etc
```

2. Test that agent:
   - Recognizes when to use the tool
   - Passes correct arguments
   - Handles tool result
   - Responds to user with formatted result

### Expected Problems

- Tool schema definition issues
- Async/sync bridging problems
- Pydantic model validation
- Agent tool selection logic

---

## Phase 4: Storage Integration (Future)

**Goal**: Add conversation persistence using in-memory storage.

**What We're Testing**:
- InMemoryStorageAdapter (`src/adapters/storage/memory.py`)
- StoragePort interface (`src/ports/storage.py`)
- Message saving/retrieval
- Conversation management

**Test Script**: `test_storage.py` (to be created)

### Setup Steps

1. Test storage adapter independently:
   - Save messages
   - Retrieve conversation
   - Delete conversation
   - Cleanup expired

2. Integrate with agent:
   - Agent saves messages after processing
   - Agent loads history before processing
   - Verify multi-turn conversations persist

### Expected Problems

- Async storage operations
- DateTime timezone handling
- Conversation record creation
- Message metadata handling

---

## Phase 5: Middleware Integration (Future)

**Goal**: Add safety guardrails and PII detection.

**What We're Testing**:
- PIIDetector (`src/middleware/pii.py`)
- SafetyGuardrail (`src/middleware/safety.py`)
- PromptInjectionGuard (`src/middleware/injection.py`)

**Test Script**: `test_middleware.py` (to be created)

### Test Cases

1. **PII Detection**:
   - Detect email addresses
   - Detect credit cards
   - Redact sensitive data
   - Block API keys

2. **Prompt Injection**:
   - Detect "ignore previous instructions"
   - Detect system prompt extraction attempts
   - Allow legitimate messages through

3. **Safety Guardrails**:
   - Detect unsafe responses
   - Replace with fallback message
   - Log safety violations

### Expected Problems

- LLM model configuration for guardrails
- Regex pattern matching issues
- False positive/negative rates
- Performance impact

---

## Phase 6: FastAPI Integration (Future)

**Goal**: Get the REST API working.

**What We're Testing**:
- FastAPI routes (`src/adapters/fastapi/routes.py`)
- Request/response schemas (`src/adapters/fastapi/schemas.py`)
- Dependency injection
- Error handling

**Test Script**: `test_fastapi_server.py` (to be created)

### Setup Steps

1. Install FastAPI dependencies:
```bash
pip install fastapi uvicorn
```

2. Create test server:
```python
from fastapi import FastAPI
from chatforge.adapters.fastapi import create_chat_router

app = FastAPI()
router = create_chat_router(agent=agent, storage=storage)
app.include_router(router, prefix="/api/v1")
```

3. Test endpoints:
   - POST /api/v1/chat
   - POST /api/v1/chat/stream
   - GET /api/v1/conversations/{id}
   - GET /api/v1/health

### Expected Problems

- Async endpoint handling
- Session ID generation
- Error response formatting
- Streaming response issues

---

## Phase 7: Vision Capabilities (Future)

**Goal**: Test image analysis features.

**What We're Testing**:
- Vision LLM (`src/llm/factory.py::get_vision_llm()`)
- ImageAnalyzer (`src/services/vision/analyzer.py`)
- Base64 image encoding
- Multi-modal messages

**Test Script**: `test_vision.py` (to be created)

### Setup Steps

1. Load a test image
2. Convert to base64 data URI
3. Send to vision LLM
4. Verify accurate description

### Expected Problems

- Image format compatibility
- Base64 encoding issues
- Vision model configuration
- Token limits with images

---

## Phase 8: Cleanup Services (Future)

**Goal**: Test memory management and cleanup.

**What We're Testing**:
- AsyncCleanupRunner (`src/services/cleanup.py`)
- Background task scheduling
- Cleanup metrics
- Memory monitoring

**Test Script**: `test_cleanup.py` (to be created)

---

## Issue Tracking

As we discover issues, we'll document them here:

### Issue Log

| Phase | Issue | Status | Solution |
|-------|-------|--------|----------|
| - | - | - | - |

---

## Success Criteria

For each phase, we consider it successful when:

1. ✅ Test script runs without errors
2. ✅ Expected output matches actual output
3. ✅ All edge cases are handled
4. ✅ Logging is clear and helpful
5. ✅ Documentation is updated

---

## Notes for Developers

### Debugging Tips

1. **Import Errors**: Make sure `src/` is in Python path
2. **Config Issues**: Print `llm_config.__dict__` to see all settings
3. **API Errors**: Check API key, rate limits, model names
4. **Async Issues**: Remember to `await` async functions

### Common Fixes

1. **Module not found**: Add to `sys.path` or use `-m` flag
2. **Environment variables not loading**: Check `.env` file location
3. **Pydantic validation errors**: Check field types match config
4. **LangChain errors**: Verify version compatibility

---

## Progress Tracker

- [x] Phase 1: Simple LLM Call - Setup complete, ready to test
- [ ] Phase 2: Agent Without Tools
- [ ] Phase 3: Agent With Simple Tool
- [ ] Phase 4: Storage Integration
- [ ] Phase 5: Middleware Integration
- [ ] Phase 6: FastAPI Integration
- [ ] Phase 7: Vision Capabilities
- [ ] Phase 8: Cleanup Services

---

## Next Steps

1. **Run Phase 1 test** and document any issues
2. **Fix issues** as they arise
3. **Move to Phase 2** once Phase 1 is solid
4. **Repeat** for each phase

Let's get started! 🚀
