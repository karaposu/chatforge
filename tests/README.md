# Chatforge Test Suite

This directory contains the comprehensive test suite for Chatforge, following a micro-to-macro testing strategy based on hexagonal architecture principles.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── pytest.ini               # Pytest settings and markers
├── utils/                   # Test utilities and helpers
├── unit/                    # Fast, isolated unit tests
│   └── llm/                 # LLM factory and provider tests
│       ├── test_factory_routing.py        # Layer 1: Factory routing logic
│       ├── test_openai_adapter.py         # Layer 2: OpenAI instantiation
│       ├── test_anthropic_adapter.py      # Layer 2: Anthropic instantiation
│       ├── test_bedrock_adapter.py        # Layer 2: Bedrock instantiation
│       └── test_llm_interface.py          # Layer 3: Interface conformance
└── integration/             # Integration tests (real API calls)
    └── llm/
        └── test_simple_llm_call.py        # Layer 4: Real LLM calls
```

## Test Layers

Following hexagonal architecture, tests are organized into 4 layers:

### Layer 1: Direct Implementation (Pure Logic)
- **What**: Test factory routing logic without actual LLM instantiation
- **Speed**: Very fast (~10ms per test)
- **Dependencies**: None (everything mocked)
- **File**: `tests/unit/llm/test_factory_routing.py`
- **Tests**: 18 tests covering provider selection, vision support, parameter handling

### Layer 2: Adapter Only (Provider Instantiation)
- **What**: Test each provider's LLM instantiation in isolation
- **Speed**: Fast (~50ms per test)
- **Dependencies**: Provider packages (langchain-openai, langchain-anthropic, boto3)
- **Files**:
  - `tests/unit/llm/test_openai_adapter.py` (13 tests)
  - `tests/unit/llm/test_anthropic_adapter.py` (11 tests, skipped if package missing)
  - `tests/unit/llm/test_bedrock_adapter.py` (7 tests, skipped if package missing)
- **Tests**: Parameter validation, credential handling, error cases

### Layer 3: Port + Adapter (Interface Conformance)
- **What**: Verify LLMs conform to LangChain's BaseChatModel protocol
- **Speed**: Fast (~20ms per test)
- **Dependencies**: langchain-core
- **File**: `tests/unit/llm/test_llm_interface.py`
- **Tests**: 16 tests verifying methods (invoke, stream, bind), attributes, Runnable interface

### Layer 4: Full Integration (Real API Calls)
- **What**: End-to-end tests with actual LLM API calls
- **Speed**: Slow (~1-5 seconds per test)
- **Cost**: $$$ (uses real API keys, incurs charges)
- **File**: `tests/integration/llm/test_simple_llm_call.py`
- **Tests**: 14 tests covering sync/async calls, streaming, conversation history
- **Note**: Skipped by default unless `--run-integration` flag is used

## Running Tests

### Quick Start (Fast Unit Tests Only)

```bash
# Run all unit tests (Layers 1-3, no API calls)
pytest tests/unit/llm/ -v

# Expected: 44 passed, 5 skipped (in ~2 seconds)
# Skipped tests require optional dependencies (langchain-anthropic, boto3)
```

### Test Tier Execution

```bash
# Tier 1: Unit tests only (default, fast, free)
pytest tests/unit/ -v

# Tier 2: Integration tests (requires API keys, costs money)
pytest tests/integration/ -v --run-integration

# Tier 3: All tests including integration
pytest tests/ -v --run-integration
```

### Running Specific Test Layers

```bash
# Layer 1: Factory routing only
pytest tests/unit/llm/test_factory_routing.py -v

# Layer 2: Provider instantiation only
pytest tests/unit/llm/test_openai_adapter.py -v

# Layer 3: Interface conformance only
pytest tests/unit/llm/test_llm_interface.py -v

# Layer 4: Integration tests (requires --run-integration)
pytest tests/integration/llm/test_simple_llm_call.py -v --run-integration
```

### Using Test Markers

```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests (still need --run-integration flag)
pytest -m integration -v --run-integration

# Run only expensive tests (requires --run-integration)
pytest -m expensive -v --run-integration

# Run everything EXCEPT expensive tests
pytest -m "not expensive" -v
```

## Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.unit` - Fast unit tests with no external dependencies
- `@pytest.mark.integration` - Integration tests requiring real services
- `@pytest.mark.expensive` - Tests that cost money (real API calls)
- `@pytest.mark.e2e` - End-to-end user scenario tests
- `@pytest.mark.stress` - Stress/load tests (very slow)

## Integration Test Requirements

Integration tests (Layer 4) require real API keys:

### OpenAI Tests
```bash
export OPENAI_API_KEY="sk-..."
pytest tests/integration/llm/ -v --run-integration -k openai
```

### Anthropic Tests
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pytest tests/integration/llm/ -v --run-integration -k anthropic
```

### Bedrock Tests
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
pytest tests/integration/llm/ -v --run-integration -k bedrock
```

### Cost Optimization

Integration tests use the cheapest models to minimize costs:
- **OpenAI**: `gpt-4o-mini` (~$0.15 per 1M input tokens)
- **Anthropic**: `claude-3-haiku-20240307` (~$0.25 per 1M input tokens)
- **Bedrock**: `anthropic.claude-instant-v1` (variable pricing)

Full integration test run costs approximately **$0.01-$0.05**.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=chatforge
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v --run-integration
```

## Test Results Summary

### Current Status (as of last run)

**Unit Tests (Layers 1-3):**
- ✅ 44 tests passed
- ⏭️ 5 tests skipped (optional dependencies not installed)
- ⏱️ Execution time: ~2 seconds
- 💰 Cost: $0

**Integration Tests (Layer 4):**
- 🔒 14 tests created (skipped by default)
- ⏱️ Execution time: ~30-60 seconds (when run)
- 💰 Cost: ~$0.01-$0.05 per full run

### Coverage by Component

| Component | Layer 1 | Layer 2 | Layer 3 | Layer 4 | Total |
|-----------|---------|---------|---------|---------|-------|
| Factory Routing | 18 ✅ | - | - | - | 18 |
| OpenAI Adapter | - | 13 ✅ | 1 ✅ | 6 ✅ | 20 |
| Anthropic Adapter | - | 11 ⏭️ | 1 ⏭️ | 2 ⏭️ | 14 |
| Bedrock Adapter | - | 7 ⏭️ | 1 ⏭️ | 1 ⏭️ | 9 |
| Interface | - | - | 13 ✅ | - | 13 |
| Async/Streaming | - | - | 2 ✅ | 4 🔒 | 6 |
| **TOTAL** | **18** | **31** | **16** | **14** | **79** |

Legend: ✅ Passing | ⏭️ Skipped (optional deps) | 🔒 Gated by --run-integration

## Development Workflow

### Before committing
```bash
# Run fast unit tests
pytest tests/unit/ -v
```

### Before merging PR
```bash
# Run all tests with integration
pytest tests/ -v --run-integration
```

### Adding new tests

1. **Unit tests** (preferred for most cases):
   - Add to `tests/unit/` directory
   - Mock all external dependencies
   - Mark with `@pytest.mark.unit`
   - Should run in <100ms

2. **Integration tests** (use sparingly):
   - Add to `tests/integration/` directory
   - Mark with `@pytest.mark.integration` AND `@pytest.mark.expensive`
   - Document required environment variables
   - Use cheapest models possible

## Troubleshooting

### Tests fail with "No module named 'langchain_anthropic'"
**Solution**: Tests are correctly skipping - this is expected if optional packages aren't installed.

To install optional packages:
```bash
# For Anthropic support
pip install chatforge[anthropic]

# For Bedrock support
pip install chatforge[bedrock]

# For all providers
pip install chatforge[all]
```

### Integration tests don't run
**Solution**: Make sure you're using the `--run-integration` flag:
```bash
pytest tests/integration/ -v --run-integration
```

### Integration tests fail with authentication errors
**Solution**: Verify API keys are set:
```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### Tests are slow
**Solution**: Run only unit tests by default:
```bash
pytest tests/unit/ -v
```

## Next Steps

According to the testing roadmap, the next components to test are:

1. **Storage Operations** (Layer 1-4)
   - InMemoryStorageAdapter
   - SQLiteStorageAdapter
   - StoragePort contract tests

2. **Agent Operations** (Layer 1-4)
   - ReActAgent state management
   - Tool execution
   - Full conversation flows

3. **Middleware Operations** (Layer 1-4)
   - PIIDetector (pure regex, easiest)
   - SafetyGuardrail
   - PromptInjectionGuard

4. **FastAPI Integration** (Layer 1-4)
   - Route handlers
   - Request/response schemas
   - Complete HTTP request flows

## Additional Resources

- [Testing Roadmap](../.claude/plans/effervescent-mixing-kitten.md)
- [pytest documentation](https://docs.pytest.org/)
- [pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [LangChain testing guide](https://python.langchain.com/docs/contributing/testing/)
