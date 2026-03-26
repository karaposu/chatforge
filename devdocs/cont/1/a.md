# Contribution 7: React SSE Hook

## What It Solves

Chatforge has a FastAPI backend with SSE endpoints, but no
frontend client. Anyone building a web UI for a chatforge agent
has to figure out:

- How to connect to the SSE stream
- How to parse typed chunks (`text`, `tool_call`, `progress`, etc.)
- How to manage reconnection across multi-turn conversations
- How to detect session changes and reconnect
- How to handle optimistic message insertion
- How to track streaming state for UI controls

This hook handles all of that in one composable React hook.

## What It Returns

```typescript
const {
  messages,       // Chat messages (user + assistant)
  debugEntries,   // Tool calls + results (for debug panel)
  progress,       // Progress tracker snapshot (for progress bar)
  isStreaming,     // True while agent is responding
  error,          // Last error (if any)
  addUserMessage, // Optimistic insert before server confirms
  reconnect,      // Force reconnect to SSE stream
} = useAgentStream(sessionId);
## How It Works

User sends message
       │
  addUserMessage("Hello")     ← optimistic insert into messages[]
       │
  POST /api/chat/{id}/message ← send to backend
       │
  useAgentStream reconnects   ← SSE stream starts
       │
  EventSource receives:
    data: {"type":"text","content":"I'll help..."}
       → append to messages[]
    data: {"type":"tool_call","tool_name":"search",...}
       → append to debugEntries[]
    data: {"type":"progress","progress":{...}}
       → update progress state
    data: {"type":"done"}
       → set isStreaming = false
## Key Behaviors

**Auto-reconnect on session change** — when sessionId changes, closes old EventSource, opens new one
**Multi-turn support** — reconnect() called after each message send. Uses streamTrigger counter to force EventSource re-creation
**Optimistic messages** — addUserMessage() inserts the user's message immediately (before server round-trip)
**Clean separation** — messages for the chat UI, debugEntries for a collapsible debug panel, progress for a progress bar. Three concerns, three state arrays.
## Target Location

@chatforge/react   (npm package or reference implementation)
  src/
    useAgentStream.ts
    types.ts
Or as a reference file in chatforge's docs/examples.