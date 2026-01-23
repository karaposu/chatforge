# Langfuse Tracing Adapter

## Overview

An adapter that implements `TracingPort` using Langfuse - an open-source LLM observability platform built specifically for LLM applications.

---

## Why Langfuse?

| Consideration | Langfuse |
|---------------|----------|
| LLM-first design | Yes (core focus) |
| Feedback tracking | Native, built-in |
| Cost tracking | Automatic |
| Prompt management | Yes |
| LangChain integration | Yes (callback-based) |
| Self-hosted | Yes (Docker) |
| Cloud option | Yes (langfuse.com) |

Langfuse is purpose-built for LLM observability, unlike MLflow which is a general ML platform with LLM support added later.

---

## Conceptual Mapping

### TracingPort → Langfuse Concepts

| TracingPort Method | Langfuse Equivalent |
|--------------------|---------------------|
| `span(name, inputs)` | `langfuse.span(name=name, input=inputs)` |
| `invoke_with_span()` | LangChain callback handler |
| `get_active_trace_id()` | `trace.id` from context |
| `set_trace_metadata()` | `trace.update(metadata={...})` |
| `log_feedback()` | `langfuse.score(trace_id, name, value)` |
| `set_platform_context_on_trace()` | `trace.update(metadata={...})` |
| `enabled` | Check if Langfuse client is configured |

### Langfuse Hierarchy

```
Project (e.g., "chatforge")
└── Trace (one per request/conversation turn)
    ├── Span (grouping of operations)
    │   └── Generation (LLM call)
    ├── Generation (LLM call)
    └── Score (feedback/evaluation)
```

---

## Key Concepts

### 1. Traces and Generations

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Create a trace for the request
trace = langfuse.trace(name="chat_response", user_id="user_123")

# Log an LLM generation
generation = trace.generation(
    name="extract_dimensions",
    model="gpt-4o-mini",
    input=messages,
    output=response,
    usage={"input": 100, "output": 50},  # tokens
)
```

### 2. LangChain Integration

Langfuse provides a callback handler for automatic tracing:

```python
from langfuse.callback import CallbackHandler

handler = CallbackHandler()
llm.invoke(messages, config={"callbacks": [handler]})
```

This automatically captures:
- All LLM calls in the chain
- Token usage and costs
- Latency
- Input/output content

### 3. Native Feedback/Scores

Unlike MLflow, Langfuse has first-class feedback support:

```python
# Log user feedback
langfuse.score(
    trace_id="trace_123",
    name="user_feedback",
    value=1,  # 1 = positive, 0 = negative
    comment="Helpful response",
)

# Log automated evaluation
langfuse.score(
    trace_id="trace_123",
    name="relevance",
    value=0.85,
)
```

### 4. Cost Tracking

Langfuse automatically calculates costs based on model and token usage. No manual configuration needed for common models.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Application Code                    │
│                                                  │
│   tracing.span("my_operation")                  │
│   tracing.log_feedback(trace_id, positive=True) │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│          LangfuseTracingAdapter                  │
│          implements TracingPort                  │
│                                                  │
│   - Wraps Langfuse client                       │
│   - Manages trace context                        │
│   - Provides LangChain callback handler          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         Langfuse Server (Cloud/Self-hosted)     │
│                                                  │
│   - Stores traces, generations, scores          │
│   - Analytics dashboard                          │
│   - Prompt management                            │
│   - Cost tracking                                │
└─────────────────────────────────────────────────┘
```

---

## Configuration

The adapter would need:

```python
LangfuseTracingAdapter(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com",  # or self-hosted URL
)
```

Environment-based:
```
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Feedback Flow

Langfuse excels at feedback tracking - a key feature for LLM applications:

```
User sends message
       │
       ▼
┌─────────────────┐
│  LLM Response   │ ──────► Trace created (trace_id stored)
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Platform Message│ ──────► Link message_id to trace_id
│   (Slack, etc)  │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ User Feedback   │ ──────► langfuse.score(trace_id, ...)
│   (👍 / 👎)     │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Langfuse UI     │ ──────► View traces with feedback scores
└─────────────────┘
```

---

## Trade-offs

### Pros
- Purpose-built for LLM observability
- Native feedback/scoring system
- Automatic cost tracking
- Better UI for LLM debugging
- Prompt management built-in
- Lightweight (focused tool)

### Cons
- Additional dependency (not currently in project)
- Less mature than MLflow
- No experiment tracking (A/B testing)
- No model registry
- Smaller community

---

## Comparison with MLflow

| Feature | Langfuse | MLflow |
|---------|----------|--------|
| **Primary focus** | LLM observability | General ML |
| **Feedback tracking** | Native | Custom solution |
| **Cost tracking** | Automatic | Manual |
| **LLM UI** | Excellent | Basic |
| **Experiment tracking** | Basic | Excellent |
| **Model registry** | No | Yes |
| **Maturity** | Newer | Very mature |
| **In dependencies** | No | Yes |

### When to use Langfuse
- LLM observability is primary concern
- Need feedback tracking
- Want cost visibility
- Focused LLM debugging

### When to use MLflow
- Already using MLflow for ML experiments
- Need model registry
- Want experiment comparisons
- Prefer mature tooling

---

## Open Questions

1. **Dependency addition**: Add `langfuse` to dependencies? Optional extra?

2. **Cloud vs self-hosted**: Default to cloud for simplicity? Require self-hosted?

3. **Dual adapter**: Support both MLflow and Langfuse simultaneously?

4. **Context propagation**: How to pass trace context through async operations?

5. **Batch flushing**: Langfuse batches events - how to ensure flush on request end?
