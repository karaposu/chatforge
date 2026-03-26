# Contribution 5: Subagent-Aware Stream Bridge

## What It Solves

DeepAgents (`create_deep_agent`) spawns subagents via a `task`
tool call. The orchestrator says "delegate this to a specialist"
and the framework creates a subagent that runs independently.

The base `LangGraphStreamBridge` (#1) sees these as regular tool
calls — it emits `{"type": "tool_call", "tool_name": "task"}`
and moves on. The user sees "tool_call: task" in the UI which
is meaningless.

This extension detects `task` tool calls, extracts the subagent
name and description, and integrates with the `ProgressTracker`
(#4) to show meaningful progress:

```
Without (base bridge):
  tool_call: task  ← what does this mean?
  tool_result: task
  tool_call: task
  tool_result: task

With (subagent-aware bridge):
  progress: "template-matcher: Match slide 0"    ← meaningful
  progress: "template-matcher: completed"
  progress: "content-filler: Fill slide 0"
  progress: "content-filler: completed"
## How Detection Works

DeepAgents' task tool has a consistent signature:

task(
    subagent_type="generalPurpose",  # or specific subagent name
    description="Match a template for source slide 0...",
    prompt="...",
)
The bridge detects:
1. **Spawn:** AIMessage with tool_calls where name == "task".
   Extracts subagent_type and description from args.
2. **Completion:** ToolMessage whose tool_call_id matches a
   pending spawn. Extracts result summary.

The tool_call_id links spawn to completion.

## Relationship to Other Contributions

#1 LangGraphStreamBridge     ← base: translates events
       │
       ▼
#5 SubagentAwareStreamBridge ← extends: detects subagent lifecycle
       │
       ▼
#4 ProgressTracker           ← consumes: tracks task progress
## Target Location in Chatforge

chatforge/services/stream_bridge.py  (same file as #1, extends it)
```