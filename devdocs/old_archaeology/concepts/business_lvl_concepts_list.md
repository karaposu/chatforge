# Business-Level Concepts

Concepts related to domain modeling, user-facing features, and business logic.

---

## Core Domain Entities

### 1. Conversation
A sequence of messages between a user and the agent, identified by a session/conversation ID. The fundamental unit of interaction that persists across multiple exchanges.

| Status | Location |
|--------|----------|
| Implemented | `ConversationRecord`/`ChatRecord` in `ports/storage_types.py`; tracked via `conversation_id` throughout |

---

### 2. Message
A single communication unit within a conversation, with role (user/assistant), content, timestamp, and optional metadata. The atomic element of conversation history.

| Status | Location |
|--------|----------|
| Implemented | `MessageRecord` in `ports/storage_types.py`; `Message` in `ports/messaging_platform_integration.py` |

---

### 3. Agent
The AI reasoning entity that processes user messages and produces responses. Uses ReACT pattern for autonomous task completion with optional tool usage.

| Status | Location |
|--------|----------|
| Implemented | `ReActAgent` in `services/agent/engine.py` |

---

### 4. Tool
A capability the agent can use to perform actions or retrieve information. Extends agent beyond pure conversation into task execution.

| Status | Location |
|--------|----------|
| Implemented | `AsyncAwareTool` base class; tools registered via `ReActAgent(tools=[...])` |

---

## User Identity

### 5. User
An entity interacting with the agent, identified by user_id (platform-specific) and optionally by email. Minimal identity model without authentication.

| Status | Location |
|--------|----------|
| Partially Implemented | `user_id` and `user_email` passed through system; no User entity or validation |

**Hidden Assumption:** User identity is externally managed. Chatforge trusts caller to provide valid user context.

---

### 6. Anonymous User
Default identity when no user_id provided. Allows usage without authentication while maintaining session tracking.

| Status | Location |
|--------|----------|
| Implemented | `user_id = request.user_id or "anonymous"` in routes |

---

## Session Management

### 7. Session
A logical grouping of interactions, typically mapping to a conversation. Client-controlled identifier enabling stateless server architecture.

| Status | Location |
|--------|----------|
| Implemented | `session_id` in API requests; maps to `conversation_id` in storage |

---

### 8. Session Continuity
Ability to resume previous conversation by providing same session_id. History loaded from storage and included in context.

| Status | Location |
|--------|----------|
| Implemented | Routes fetch history via `storage.get_conversation(session_id)` before processing |

---

## Platform Integration

### 9. Messaging Platform
External chat systems (Slack, Teams, Discord) where conversations originate. Chatforge can embed into these platforms via adapters.

| Status | Location |
|--------|----------|
| Interface Only | `MessagingPlatformIntegrationPort` defined; no concrete implementations |

---

### 10. Platform-Agnostic Messaging
Abstraction layer that normalizes platform-specific features into common model. Enables "build once, deploy anywhere" for chat agents.

| Status | Location |
|--------|----------|
| Interface Implemented | `ConversationContext`, `Message`, `FileAttachment` in `ports/messaging_platform_integration.py` |

**Trade-off:** Loses platform-specific richness (reactions, threads, rich formatting) for portability.

---

### 11. File Attachment
User-uploaded files (images, documents) that may need processing. Platform-specific download URLs normalized into common structure.

| Status | Location |
|--------|----------|
| Interface Implemented | `FileAttachment` dataclass with `is_image`, `is_text` properties |

---

## Knowledge & Information Retrieval

### 12. Knowledge Base
External information source (Notion, Confluence, SharePoint) that agent can query for answers. Enables RAG (Retrieval Augmented Generation) patterns.

| Status | Location |
|--------|----------|
| Interface Only | `KnowledgePort` in `ports/knowledge.py`; only `NullKnowledgeAdapter` exists |

---

### 13. RAG Context Injection
Relevant knowledge base content injected into agent prompt. Grounds responses in organizational knowledge.

| Status | Location |
|--------|----------|
| Interface Defined | `get_context_for_rag()` method in `KnowledgePort`; not wired into agent |

---

### 14. Knowledge Search Result
Structured search result with title, content, URL, relevance score, and source. Formatted differently for display vs. RAG injection.

| Status | Location |
|--------|----------|
| Implemented | `KnowledgeResult` dataclass with `format_for_display()` and `format_for_rag()` methods |

---

## Workflow & Actions

### 15. Ticketing/Workflow System
External systems (Jira, ServiceNow, Zendesk) where agent can create tasks, tickets, or trigger workflows. Extends agent from informational to operational.

| Status | Location |
|--------|----------|
| Interface Only | `TicketingPort` in `ports/ticketing.py`; only `NullTicketingAdapter` exists |

---

### 16. Action
A request to create something in external system (ticket, task, incident). Normalized structure regardless of target system.

| Status | Location |
|--------|----------|
| Interface Implemented | `ActionData`, `ActionResult`, `ActionPriority` in `ports/ticketing.py` |

---

### 17. Action Priority
Standardized priority levels (LOW, MEDIUM, HIGH, CRITICAL) for workflow items. Maps to system-specific priorities.

| Status | Location |
|--------|----------|
| Implemented | `ActionPriority` enum with `from_string()` conversion |

---

## Safety & Compliance

### 18. PII (Personally Identifiable Information)
Sensitive user data (email, phone, SSN, credit card) that requires protection. Detection and handling is compliance requirement.

| Status | Location |
|--------|----------|
| Implemented | `PIIDetector` in `middleware/pii.py` with multiple PII types |

---

### 19. PII Handling Strategy
Policy for what to do with detected PII: redact (replace with placeholder), mask (show partial), hash (one-way transform), or block (reject message).

| Status | Location |
|--------|----------|
| Implemented | `PIIStrategy` enum; configurable per PII type via `PIIRule` |

---

### 20. Prompt Injection
Attack where user attempts to manipulate agent by overriding instructions, extracting system prompt, or bypassing safety measures.

| Status | Location |
|--------|----------|
| Detection Implemented | `PromptInjectionGuard` in `middleware/injection.py` |

---

### 21. Response Safety
Evaluation of agent output for harmful, dangerous, or inappropriate content before returning to user.

| Status | Location |
|--------|----------|
| Implemented | `SafetyGuardrail` in `middleware/safety.py` |

---

### 22. Content Filtering
Keyword-based blocking of specific topics (hacking, exploits, malware). Fast, deterministic alternative to LLM-based safety.

| Status | Location |
|--------|----------|
| Implemented | `ContentFilter` in `middleware/safety.py` |

---

## Observability

### 23. Trace
Record of a single request's execution path, including LLM calls, tool invocations, and timing. Enables debugging and performance analysis.

| Status | Location |
|--------|----------|
| Interface Only | `TracingPort` in `ports/tracing.py`; no real implementation |

---

### 24. Trace-Based Feedback
User feedback (thumbs up/down) linked to specific traces. Enables evaluation of agent quality and training data collection.

| Status | Location |
|--------|----------|
| Interface Defined | `log_feedback()` in `TracingPort`; not wired to UI |

---

### 25. Health Check
Liveness/readiness probe for deployment orchestration. Verifies system and dependency availability.

| Status | Location |
|--------|----------|
| Implemented | `/health` endpoint in routes; checks storage health |

---

## Vision/Multimodal

### 26. Image Analysis
Ability to process user-uploaded images using vision-capable LLMs. Extract text, describe content, analyze errors in screenshots.

| Status | Location |
|--------|----------|
| Implemented | `ImageAnalyzer` in `services/vision/analyzer.py` |

---

### 27. Batch Image Processing
Analyze multiple images in sequence or parallel. Useful for processing multiple screenshots in support context.

| Status | Location |
|--------|----------|
| Implemented | `analyze_batch()` with `parallel` and `max_concurrent` options |

---

## Data Lifecycle

### 28. Conversation TTL (Time To Live)
Automatic deletion of old conversations for compliance and storage management. Configurable retention period.

| Status | Location |
|--------|----------|
| Implemented | `cleanup_expired(ttl_minutes)` in storage adapters; `CleanupRunner` for automation |

---

### 29. Conversation Deletion
User-triggered removal of conversation and all associated messages. Compliance with "right to be forgotten."

| Status | Location |
|--------|----------|
| Implemented | `DELETE /conversations/{id}` endpoint; `delete_conversation()` in storage |

---

## Implicit Business Concepts (Hidden in Code)

### 30. Conversation Ownership
Implied relationship between user_id and conversation. Not enforced—any user can access any conversation by ID.

| Status | Location |
|--------|----------|
| Not Enforced | `user_id` stored but not validated for access control |

**Security Gap:** Conversation access is by-ID only. No verification that requester owns the conversation.

---

### 31. System Prompt as Agent Personality
The system prompt defines agent's behavior, capabilities, and constraints. Different prompts create different "agents" from same code.

| Status | Location |
|--------|----------|
| Implemented | `system_prompt` parameter throughout; `DEFAULT_SYSTEM_PROMPT` as fallback |

**Business Pattern:** Reuse same Chatforge deployment for multiple "agents" by varying system prompt per request.

---

### 32. Tool as Business Capability
Tools represent what the agent can "do" beyond conversation. Adding tools = extending business capabilities without code changes.

| Status | Location |
|--------|----------|
| Architecturally Supported | Tools are injected list; new tools added by configuration |

---

### 33. Graceful Degradation as Feature
When components are unavailable, system continues with reduced capability rather than failing. Missing storage = ephemeral conversations. Missing tracing = no trace IDs.

| Status | Location |
|--------|----------|
| Implemented | Optional dependencies throughout; null adapters for disabled features |

**Business Value:** Development and testing don't require full infrastructure. Production progressively enhanced.

---

### 34. Context Window as Memory Limit
Agent only sees last N messages (default 50). Older context is effectively "forgotten." Business logic depends on what fits in context.

| Status | Location |
|--------|----------|
| Implemented | `limit=50` in history retrieval |

**Implication:** Very long support cases may lose important early context. Summarization or retrieval might be needed.

---

### 35. Rejection Message as Brand Voice
When content is blocked (injection, safety), the rejection message is configurable. Allows brand-appropriate responses to violations.

| Status | Location |
|--------|----------|
| Implemented | `rejection_message` parameter in guards; `fallback_message` in safety |

---

### 36. Cache as Cost Optimization
Image analysis results can be cached to avoid repeated LLM calls for same image. Trading storage for API cost reduction.

| Status | Location |
|--------|----------|
| Implemented | Optional `cache` parameter in `ImageAnalyzer` |

**Business Value:** Repeated queries about same screenshot don't incur additional vision LLM costs.

---

### 37. Streaming as UX Feature
Streaming responses (`/chat/stream`) provide faster perceived response time. Users see partial output while generation continues.

| Status | Location |
|--------|----------|
| Partially Implemented | Endpoint exists; currently simulates streaming by chunking complete response |

**Gap:** True token-by-token streaming not implemented. UX benefit not fully realized.

---

### 38. Trace ID for Customer Support
Returning `trace_id` in API responses enables customer support. Users can provide trace ID when reporting issues.

| Status | Location |
|--------|----------|
| Implemented | `trace_id` included in `ChatResponse` |

**Value:** Support can look up exact execution path for reported issues (if tracing enabled).
