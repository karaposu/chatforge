# MLflow Tracing Adapter

## Overview

An adapter that implements `TracingPort` using MLflow's tracing capabilities (introduced in MLflow 2.9+).

---

## Why MLflow?

| Consideration | MLflow |
|---------------|--------|
| Already in dependencies | Yes (`mlflow>=2.9.0`) |
| LLM tracing support | Yes (native since 2.9) |
| LangChain integration | Yes (auto-instrumentation) |
| Self-hosted | Yes (simple `mlflow server`) |
| Experiment tracking | Excellent (core strength) |
| Model registry | Yes (bonus feature) |
| Community/Maturity | Very mature, widely adopted |

MLflow is already a dependency. Using it avoids adding another observability tool.

---

## Conceptual Mapping

### TracingPort → MLflow Concepts

| TracingPort Method | MLflow Equivalent |
|--------------------|-------------------|
| `span(name, inputs)` | `mlflow.start_span(name)` |
| `invoke_with_span()` | Auto-traced via LangChain integration |
| `get_active_trace_id()` | `mlflow.get_current_active_span().request_id` |
| `set_trace_metadata()` | `span.set_attributes()` |
| `log_feedback()` | Custom: store in MLflow tags or separate table |
| `enabled` | Check if MLflow tracking URI is configured |

### MLflow Tracing Hierarchy

```
Experiment (e.g., "chatforge-prod")
└── Run (optional grouping)
    └── Trace (one per request/conversation turn)
        └── Span (individual operations)
            ├── LLM call span
            ├── Tool call span
            └── Custom spans
```

---

## Key Concepts

### 1. Automatic LangChain Tracing

MLflow 2.9+ can auto-trace LangChain calls:

```python
mlflow.langchain.autolog()  # Enable once at startup
```

This automatically captures:
- LLM inputs/outputs
- Token counts
- Latency
- Chain structure

### 2. Manual Span Creation

For non-LangChain operations (custom logic, external APIs):

```python
with mlflow.start_span(name="extract_dimensions") as span:
    span.set_inputs({"dimensions": ["core_identity", "events"]})
    result = do_extraction()
    span.set_outputs({"items_found": len(result.items)})
```

### 3. Trace Context Propagation

MLflow maintains trace context automatically within a request. Child spans are nested under parent spans.

### 4. Feedback Tracking

MLflow doesn't have native "feedback" like Langfuse. Options:
- Store feedback as span tags/attributes
- Use MLflow's `log_param()` / `log_metric()`
- Separate feedback table linked by trace ID

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Application Code                    │
│                                                  │
│   tracing.span("my_operation")                  │
│   tracing.invoke_with_span(llm, messages)       │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│           MLflowTracingAdapter                   │
│           implements TracingPort                 │
│                                                  │
│   - Wraps mlflow.start_span()                   │
│   - Manages trace context                        │
│   - Handles feedback storage                     │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│              MLflow Server                       │
│                                                  │
│   - Stores traces                                │
│   - Provides UI for viewing                      │
│   - Experiment organization                      │
└─────────────────────────────────────────────────┘
```

---

## Configuration

The adapter would need:

```python
MLflowTracingAdapter(
    tracking_uri="http://localhost:5000",  # MLflow server
    experiment_name="chatforge",           # Experiment to log to
    enable_langchain_autolog=True,         # Auto-trace LangChain
)
```

Environment-based:
```
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=chatforge
```

---

## Trade-offs

### Pros
- Already a dependency (no new tools)
- Mature, well-documented
- Great experiment tracking (compare prompt versions)
- Model registry for prompt/model versioning
- Self-hosted friendly

### Cons
- LLM tracing is newer (2.9+), less polished than Langfuse
- Feedback tracking requires custom solution
- UI less tailored to LLM debugging than Langfuse
- Heavier weight (MLflow is a full ML platform)

---

## Alternative: Langfuse

If LLM-specific observability is priority:

| Feature | MLflow | Langfuse |
|---------|--------|----------|
| LLM focus | Secondary | Primary |
| Feedback UI | None | Built-in |
| Prompt playground | No | Yes |
| Cost tracking | Manual | Automatic |
| Setup complexity | Medium | Low |

Could implement both adapters and choose at runtime.

---

## Open Questions

1. **Feedback storage**: Where to store user feedback? MLflow tags? Separate table?

2. **Trace linking**: How to link traces to conversation messages for feedback lookup?

3. **Experiment organization**: One experiment per environment? Per feature?

4. **Retention**: How long to keep traces? MLflow doesn't auto-cleanup.

5. **LangChain autolog scope**: Global enable, or per-request?
