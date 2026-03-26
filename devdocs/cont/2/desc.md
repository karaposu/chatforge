# Contribution 6: File-Based Debug Logger

## What It Solves

Chatforge has `TracingPort` for external services (MLflow,
LangSmith). But setting up an external tracing service just to
debug an agent during development is overkill. You need to:
1. Sign up for a service
2. Get API keys
3. Configure the integration
4. Learn their UI

This logger gives you per-session debug logging that works out
of the box with zero setup. Every session gets a directory with
JSONL files. Open them in any text editor.

## What It Produces

```
debug_output/
  abc123/                          ← one dir per session
    agent_debug.log                ← human-readable log
    model_responses/
      subagent.jsonl               ← one JSON object per LLM call
    tool_calls/
      tools.jsonl                  ← one JSON object per tool call
Each JSONL line is a self-contained JSON object with timestamp,
agent name, input/output, and duration. Grep-friendly, diff-
friendly, no special viewer needed.

## When To Use

**Development:** always on. Zero cost, instant feedback.
**Production:** off by default, enable per-session for debugging specific issues.
**Post-mortem:** read the JSONL files after a failed run to understand what happened.
## Relationship to TracingPort

This doesn't replace TracingPort — it complements it:

| | Debug Logger | TracingPort |
|---|---|---|
| Setup | Zero | External service needed |
| Cost | Free (disk) | Service billing |
| Format | JSONL files | Service-specific |
| Best for | Development, local debugging | Production monitoring, dashboards |
| Survives restart | Yes (files on disk) | Yes (external service) |

## Target Location in Chatforge

chatforge/services/debug_logger.py
```