# Project Description (From Code Analysis)

What Chatforge actually does, based on code behavior rather than documentation claims.

---

## What The System Actually Does

### Core Function

Chatforge is a **Python toolkit for building AI-powered chat assistants** that can:

1. **Process conversational messages** through a ReACT (Reason-Act-Observe) agent loop
2. **Persist conversation history** across sessions via pluggable storage backends
3. **Execute tools** to extend agent capabilities beyond pure conversation
4. **Apply security checks** (PII detection, prompt injection, response safety)
5. **Integrate with vision-capable LLMs** for image analysis

### What It Is NOT

Based on code analysis, Chatforge is:

- **Not a complete application** — It's a toolkit/library, not a deployable product
- **Not a hosted service** — No cloud deployment, no user accounts, no billing
- **Not a chatbot framework** — No conversation flow design, no intent recognition, no dialog management
- **Not an LLM wrapper** — It delegates to LangChain/LangGraph for LLM orchestration

---

## Current Capabilities (From Working Code)

### Fully Implemented

| Capability | Evidence in Code |
|------------|------------------|
| Multi-provider LLM support | `services/llm/factory.py` - OpenAI, Anthropic, Bedrock |
| Conversation storage | Three working adapters: InMemory, SQLite, SQLAlchemy |
| ReACT agent execution | `services/agent/engine.py` wraps LangGraph's `create_react_agent` |
| Tool execution framework | `AsyncAwareTool` base class with sync/async bridging |
| PII detection | Regex-based detector with REDACT/MASK/HASH/BLOCK strategies |
| Prompt injection guard | LLM-based detection in `middleware/injection.py` |
| Response safety check | LLM-based guardrail in `middleware/safety.py` |
| Content filtering | Keyword blocklist in `middleware/safety.py` |
| Image analysis | Vision LLM integration in `services/vision/analyzer.py` |
| FastAPI integration | Router factory with /chat and /chat/stream endpoints |
| Background cleanup | Async and sync cleanup runners for TTL enforcement |

### Interface-Only (No Real Implementations)

| Capability | Evidence |
|------------|----------|
| Messaging platforms (Slack, Teams) | Only `NullMessagingAdapter` exists |
| Knowledge bases (Notion, Confluence) | Only `NullKnowledgeAdapter` exists |
| Ticketing systems (Jira, ServiceNow) | Only `NullTicketingAdapter` exists |
| Distributed tracing (MLflow, Langsmith) | Only `NullTracingAdapter` exists |

---

## Current User Base (Inferred)

Based on code patterns, the intended users are:

### Primary User: Python Developers Building Chat Agents

Evidence:
- Library structure (not application)
- Heavy use of dependency injection
- Configurable everything via constructor parameters
- No CLI, no GUI, no admin interface

### Secondary User: Enterprise/Compliance Teams

Evidence:
- PII detection with multiple handling strategies
- Prompt injection protection
- Response safety guardrails
- Conversation TTL for data retention compliance

### NOT The User: End Users of Chat Applications

- No user authentication
- No user-facing API documentation
- No rate limiting
- No multi-tenant support

---

## Use Cases (From Code Paths)

### 1. Internal Support Bot

**Evidence:**
- Knowledge base port for RAG integration
- Ticketing port for escalation workflows
- Conversation history for context continuity
- Tool execution for looking up information

**Code Path:**
```
User question → Agent → Knowledge search tool → RAG context → LLM response
                     → Ticket creation tool → External system
```

### 2. Compliance-Sensitive Chat Interface

**Evidence:**
- PII detection and redaction
- Configurable rejection messages
- Conversation TTL cleanup
- Audit-ready message storage

**Code Path:**
```
User input → PII scan → Prompt injection check → Agent → Safety check → Response
                ↓ (if blocked)
            Rejection message returned
```

### 3. Multi-Modal Support (Screenshots)

**Evidence:**
- ImageAnalyzer with batch processing
- Vision-capable LLM factory method
- FileAttachment handling in messaging port
- Cache support for repeated image queries

**Code Path:**
```
User uploads screenshot → Image analysis → Structured result → Agent context
```

### 4. Development/Prototyping Environment

**Evidence:**
- InMemory storage (no database required)
- Optional dependencies throughout
- Graceful degradation (works without tracing, messaging, etc.)
- Null adapters for all optional ports

**Code Path:**
```
Minimal setup: LLM API key → get_llm() → ReActAgent → process_message()
```

---

## Actual Problems Being Solved

### Problem 1: LLM Provider Lock-In

**Solution in Code:**
- Factory pattern abstracts provider selection
- Unified `BaseChatModel` interface from LangChain
- Provider-specific code isolated in factory functions

**Evidence:** `services/llm/factory.py` handles OpenAI, Anthropic, Bedrock with same interface

### Problem 2: Conversation State Management

**Solution in Code:**
- Session ID based history retrieval
- Pluggable storage backends
- Automatic cleanup of expired conversations

**Evidence:** Storage port with three implementations, `cleanup_expired()` method

### Problem 3: Agent Capability Extension

**Solution in Code:**
- Tool injection via constructor
- `AsyncAwareTool` base class simplifies tool creation
- Error handling that lets agent reason about failures

**Evidence:** `services/agent/tools/base.py`, tool registration in `ReActAgent`

### Problem 4: Security in LLM Applications

**Solution in Code:**
- Pre-processing: PII detection, prompt injection guard
- Post-processing: Safety guardrail, content filter
- Configurable handling strategies

**Evidence:** Full middleware stack in `middleware/` directory

### Problem 5: Platform Integration Abstraction

**Solution in Code (Partial):**
- Messaging platform port for multi-channel deployment
- Knowledge port for RAG from various sources
- Ticketing port for workflow integration

**Evidence:** Ports defined; no real adapters yet (design complete, implementation pending)

---

## What's Missing (Problems Not Yet Solved)

| Problem | Status |
|---------|--------|
| User authentication | Not addressed (assumed external) |
| Rate limiting | Not addressed (assumed infrastructure) |
| Multi-tenancy | Not addressed (single-tenant only) |
| Production monitoring | Interface only (TracingPort) |
| Horizontal scaling | Architecturally possible, not tested |
| Real platform integrations | Interfaces only |

---

## Summary

Chatforge is a **developer toolkit** that solves the problem of building AI chat assistants that are:
- Provider-agnostic (switch LLMs easily)
- Security-conscious (PII, injection, safety)
- Extensible (tools, adapters, middleware)
- Testable (dependency injection, null adapters)

It does NOT solve:
- Deployment and operations
- User management and authentication
- Platform-specific integrations (yet)
- Production monitoring (interface only)

The codebase reflects a **"toolkit not framework"** philosophy where developers compose the pieces they need rather than inheriting from an opinionated structure.
