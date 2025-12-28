# Known Requirements (From Code Analysis)

Requirements inferred from implementations, constraints visible in code, and compliance/security measures present.

---

## Functional Requirements (Inferred From Implementations)

### FR-1: Multi-Provider LLM Support

**Implementation Evidence:**
```python
# services/llm/factory.py
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
```

**Inferred Requirement:**
> The system MUST support multiple LLM providers with a unified interface, allowing provider switching without application code changes.

**Constraints Visible:**
- Each provider has separate API key configuration
- Provider-specific packages imported lazily (optional dependencies)
- Different default models per provider

---

### FR-2: Conversation Persistence

**Implementation Evidence:**
```python
# ports/storage.py
class StoragePort(ABC):
    async def save_message(self, conversation_id, message, role, ...)
    async def get_conversation(self, conversation_id, limit=50)
    async def delete_conversation(self, conversation_id)
```

**Inferred Requirement:**
> The system MUST persist conversation history with retrieval by session ID, supporting continuation of conversations across requests.

**Constraints Visible:**
- Messages stored with role, content, timestamp, metadata
- History limited to last 50 messages (bounded retrieval)
- Conversation-level operations (create, delete, cleanup)

---

### FR-3: Tool Execution Capability

**Implementation Evidence:**
```python
# services/agent/tools/base.py
class AsyncAwareTool(BaseTool):
    async def _execute_async(self, *args, **kwargs):
        raise NotImplementedError
```

**Inferred Requirement:**
> The system MUST allow extending agent capabilities through executable tools that can perform actions or retrieve information.

**Constraints Visible:**
- Tools must be sync/async compatible
- Tool errors become text responses (agent can reason about failures)
- Tools registered at agent construction time

---

### FR-4: Security Middleware Pipeline

**Implementation Evidence:**
- `middleware/pii.py` — PII detection and handling
- `middleware/injection.py` — Prompt injection detection
- `middleware/safety.py` — Response safety evaluation

**Inferred Requirement:**
> The system MUST provide security components for input sanitization, attack detection, and output safety verification.

**Constraints Visible:**
- Middleware not auto-wired (opt-in)
- Each component independently configurable
- Multiple handling strategies (block, redact, mask, allow)

---

### FR-5: Image/Vision Analysis

**Implementation Evidence:**
```python
# services/vision/analyzer.py
class ImageAnalyzer:
    async def analyze(self, image_url_or_path, prompt=None)
    async def analyze_batch(self, images, prompts=None, parallel=True)
```

**Inferred Requirement:**
> The system MUST support analyzing images using vision-capable LLMs, including batch processing and caching.

**Constraints Visible:**
- Supports URL and local file paths
- Custom analysis prompts optional
- Parallel batch processing with concurrency limits

---

### FR-6: Platform Abstraction Layer

**Implementation Evidence:**
```python
# ports/messaging_platform_integration.py
class MessagingPlatformIntegrationPort(ABC):
    async def send_message(self, channel_id, message)
    async def send_typing_indicator(self, channel_id)
    async def fetch_file_content(self, file_info)
```

**Inferred Requirement:**
> The system MUST abstract messaging platform details to enable deployment across multiple platforms (Slack, Teams, Discord, etc.) without code changes.

**Status:** Interface defined, no implementations yet.

---

### FR-7: Knowledge Base Integration

**Implementation Evidence:**
```python
# ports/knowledge.py
class KnowledgePort(ABC):
    def search(self, query, max_results=5) -> list[KnowledgeResult]
    def get_context_for_rag(self, query) -> str
```

**Inferred Requirement:**
> The system MUST support querying external knowledge bases to ground agent responses in organizational knowledge (RAG pattern).

**Status:** Interface defined, no implementations yet.

---

### FR-8: Workflow/Ticketing Integration

**Implementation Evidence:**
```python
# ports/ticketing.py
class TicketingPort(ABC):
    def create_action(self, action_data: ActionData) -> ActionResult
    def update_action(self, action_id, updates)
```

**Inferred Requirement:**
> The system MUST support creating and managing items in external workflow systems (Jira, ServiceNow, Zendesk) through agent actions.

**Status:** Interface defined, no implementations yet.

---

### FR-9: Automatic Data Cleanup

**Implementation Evidence:**
```python
# services/cleanup.py
class AsyncCleanupRunner:
    def schedule_component(self, name, cleanup_fn, interval_seconds)
    async def run_all_cleanups(self)
```

**Inferred Requirement:**
> The system MUST support automatic cleanup of expired data based on configurable TTL values.

**Constraints Visible:**
- Per-component cleanup intervals
- Cleanup history tracking (max 100 cycles)
- Both async and sync runner implementations

---

### FR-10: RESTful API Exposure

**Implementation Evidence:**
```python
# adapters/fastapi/routes.py
@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse

@router.get("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse
```

**Inferred Requirement:**
> The system MUST expose functionality through a RESTful API with support for both synchronous and streaming responses.

**Constraints Visible:**
- FastAPI as web framework
- Server-Sent Events for streaming
- Standard HTTP error codes

---

## Non-Functional Requirements (Inferred)

### NFR-1: Horizontal Scalability

**Evidence:**
- Stateless request processing (history passed in, not stored in memory)
- No server-side session state
- Storage externalized

**Inferred Requirement:**
> The system architecture MUST support horizontal scaling by ensuring any instance can handle any request.

---

### NFR-2: Testability

**Evidence:**
- Dependency injection throughout
- Null adapters for all optional ports
- Abstract base classes for all ports

**Inferred Requirement:**
> The system MUST be testable in isolation through mockable dependencies and null implementations.

---

### NFR-3: Minimal Required Configuration

**Evidence:**
```python
# Minimal working setup
llm = get_llm()  # Uses defaults
agent = ReActAgent(llm=llm)  # All other params optional
response = agent.process_message("Hello")
```

**Inferred Requirement:**
> The system MUST work with minimal configuration (just LLM API key) while allowing progressive enhancement.

---

### NFR-4: Provider Independence

**Evidence:**
- Ports define interfaces
- Adapters implement specifics
- Services depend only on ports

**Inferred Requirement:**
> The system MUST not be locked to any specific external provider for storage, LLM, or integrations.

---

## Constraints Visible In Code

### C-1: Python 3.10+ Required

**Evidence:**
```python
# Type hints use modern syntax
user_id: str | None = None  # Union syntax requires 3.10+
```

---

### C-2: LangChain Compatibility

**Evidence:**
- `BaseChatModel` from LangChain as LLM interface
- `HumanMessage`, `AIMessage` for message types
- `create_react_agent` from LangGraph

**Constraint:**
> The system MUST maintain compatibility with LangChain's interfaces and patterns.

---

### C-3: Async Context Required For Core Operations

**Evidence:**
```python
# Storage is async-only
async def save_message(...)
async def get_conversation(...)
```

**Constraint:**
> Core operations MUST be called from async context. Sync-to-async bridging provided for edge cases.

---

### C-4: Message History Limit

**Evidence:**
```python
messages = await storage.get_conversation(session_id, limit=50)
```

**Constraint:**
> Context window is limited to 50 most recent messages. Older context is not available to the agent.

---

### C-5: Single LLM Call Timeout

**Evidence:**
```python
# services/llm/factory.py
request_timeout=60  # Hardcoded
```

**Constraint:**
> LLM calls timeout after 60 seconds. Not configurable without code change.

---

### C-6: Per-Operation Database Connections

**Evidence:**
```python
# adapters/storage/sqlite.py
async with aiosqlite.connect(self.db_path) as db:
    # Each operation opens/closes connection
```

**Constraint:**
> SQLite adapter does not pool connections. Each operation has connection overhead.

---

## Compliance/Security Measures Present

### SEC-1: PII Detection and Handling

**Implementation:**
```python
class PIIDetector:
    # Detects: email, phone, SSN, credit card, IP address
    # Strategies: REDACT, MASK, HASH, BLOCK
```

**Compliance Alignment:**
- GDPR: Can redact PII before storage
- HIPAA: Can block messages containing sensitive data
- PCI-DSS: Credit card detection and handling

**Limitations:**
- Regex-based (no ML detection)
- No context-aware detection
- English-centric patterns

---

### SEC-2: Prompt Injection Protection

**Implementation:**
```python
class PromptInjectionGuard:
    # LLM-based detection of:
    # - Instruction override attempts
    # - System prompt extraction
    # - Jailbreak patterns
```

**Security Measure:**
- Evaluates user input before processing
- Configurable legitimate use cases
- Returns structured detection result

**Limitations:**
- Requires LLM call (latency, cost)
- Fails open on errors
- Can be bypassed with novel attacks

---

### SEC-3: Response Safety Evaluation

**Implementation:**
```python
class SafetyGuardrail:
    # LLM-based evaluation of:
    # - Harmful content
    # - Dangerous advice
    # - Inappropriate responses
```

**Security Measure:**
- Post-processing check before returning to user
- Configurable safety criteria
- Fallback message on unsafe detection

**Limitations:**
- Requires additional LLM call
- Fails open on errors
- Subject to LLM judgment inconsistency

---

### SEC-4: Content Filtering

**Implementation:**
```python
class ContentFilter:
    # Keyword blocklist
    # Fast, deterministic alternative to LLM-based safety
```

**Security Measure:**
- Zero latency keyword matching
- Customizable blocklist
- No external dependencies

**Limitations:**
- Easily bypassed (l33tspeak, Unicode tricks)
- No semantic understanding
- Requires manual maintenance

---

### SEC-5: Conversation Data Cleanup

**Implementation:**
```python
async def cleanup_expired(self, ttl_minutes: int) -> int:
    # Deletes conversations older than TTL
```

**Compliance Alignment:**
- Data retention policies
- Right to be forgotten (partial)
- Storage cost management

**Limitations:**
- TTL-based only (no selective retention)
- No audit trail of deletions
- Hard delete (no soft delete option)

---

### SEC-6: Configurable Rejection Messages

**Implementation:**
```python
PromptInjectionGuard(rejection_message="I can't help with that.")
SafetyGuardrail(fallback_message="I'm not able to respond to that.")
```

**Security Measure:**
- Prevents information leakage about detection
- Brand-appropriate responses
- No stack traces or internal details

---

## Missing Security Measures

| Measure | Status | Risk |
|---------|--------|------|
| Authentication | Not implemented | Identity not verified |
| Authorization | Not implemented | No access control |
| Rate limiting | Not implemented | DoS possible |
| Input size limits | Not implemented | Large message attacks |
| Audit logging | Not implemented | No forensic trail |
| Encryption at rest | Not implemented | Data exposure risk |
| Secret management | Environment variables only | Secrets in memory |

---

## Requirements Summary Table

| Category | Requirement | Status |
|----------|-------------|--------|
| **Functional** | Multi-provider LLM | ✅ Implemented |
| | Conversation persistence | ✅ Implemented |
| | Tool execution | ✅ Implemented |
| | Security middleware | ✅ Implemented (opt-in) |
| | Image analysis | ✅ Implemented |
| | Platform abstraction | ⚠️ Interface only |
| | Knowledge base | ⚠️ Interface only |
| | Ticketing integration | ⚠️ Interface only |
| | Data cleanup | ✅ Implemented |
| | REST API | ✅ Implemented |
| **Non-Functional** | Horizontal scalability | ✅ Architecturally supported |
| | Testability | ✅ Designed for testing |
| | Minimal config | ✅ Works with defaults |
| | Provider independence | ✅ Port/adapter pattern |
| **Security** | PII detection | ✅ Implemented |
| | Injection protection | ✅ Implemented |
| | Response safety | ✅ Implemented |
| | Content filtering | ✅ Implemented |
| | Authentication | ❌ Not implemented |
| | Authorization | ❌ Not implemented |
| | Rate limiting | ❌ Not implemented |

---

## Inferred Priority

Based on implementation completeness:

1. **Highest Priority (Fully Implemented):**
   - LLM integration
   - Conversation management
   - Security middleware
   - API exposure

2. **Medium Priority (Interface Only):**
   - Platform integrations
   - Knowledge base
   - Ticketing systems
   - Distributed tracing

3. **Deferred (Not Addressed):**
   - Authentication/Authorization
   - Rate limiting
   - Multi-tenancy
   - Production monitoring

This prioritization suggests a **"core functionality first, integrations second, production hardening third"** development approach.
