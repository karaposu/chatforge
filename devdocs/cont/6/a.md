"""Agent Lifecycle Manager for chatforge.

Manages the full lifecycle of a background agent run: queue drain,
status transitions, background task dispatch, cancellation, and
guaranteed termination events.

Designed for HTTP-served agents where the request handler must
return immediately while the agent runs in the background,
streaming events to an SSE endpoint via asyncio.Queue.

Usage:
    from chatforge.services.agent_lifecycle import AgentLifecycle
    from chatforge.services.stream_bridge import run_agent_stream

    lifecycle = AgentLifecycle()

    # Start a new agent run
    task = await lifecycle.start(
        session=runtime,
        coro=run_agent_stream(agent, messages, config, runtime.queue),
    )

    # Cancel mid-run
    await lifecycle.cancel(session=runtime)
"""

import asyncio
import logging
from typing import Any, Coroutine

logger = logging.getLogger(__name__)


class AgentLifecycle:
    """Manages background agent execution with cancel + status tracking."""

    @staticmethod
    def drain_queue(queue: asyncio.Queue) -> int:
        """Remove all pending events from the queue.

        Call before starting a new turn to prevent stale events
        from a previous run leaking into the SSE stream.

        Returns:
            Number of events drained.
        """
        count = 0
        while not queue.empty():
            try:
                queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        if count:
            logger.debug("Drained %d stale events from queue", count)
        return count

    @staticmethod
    async def start(
        session: Any,
        coro: Coroutine,
    ) -> asyncio.Task:
        """Start a background agent run.

        Drains the queue, sets status to "streaming", and creates
        an asyncio.Task for the provided coroutine.

        Args:
            session: A SessionRuntime (or any object with `queue`,
                `status`, and `active_task` attributes).
            coro: The coroutine to run (e.g., run_agent_stream()).

        Returns:
            The created asyncio.Task.
        """
        AgentLifecycle.drain_queue(session.queue)
        session.status = "streaming"
        session.active_task = asyncio.create_task(coro)
        logger.debug("Agent task started for session %s", getattr(session, "session_id", "?"))
        return session.active_task

    @staticmethod
    async def cancel(session: Any) -> bool:
        """Cancel a running agent task.

        Cancels the task and pushes a `done` event to the queue
        so the SSE endpoint doesn't hang. Sets status to "idle".

        Safe to call on an already-completed task (no-op).

        Args:
            session: A SessionRuntime with `active_task`, `queue`,
                `status`, and `session_id` attributes.

        Returns:
            True if a task was actually cancelled, False if idle.
        """
        task = getattr(session, "active_task", None)
        if task is None or task.done():
            return False

        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

        AgentLifecycle.drain_queue(session.queue)
        await session.queue.put({
            "type": "done",
            "session_id": getattr(session, "session_id", ""),
            "cancelled": True,
        })
        session.status = "idle"
        session.active_task = None

        logger.info("Agent task cancelled for session %s", getattr(session, "session_id", "?"))
        return True
# Contribution 2: Agent Lifecycle Manager

## What It Solves

Chatforge's `ReActAgent.process_message()` blocks the caller.
`process_message_with_timeout()` adds a ThreadPoolExecutor but
has no cancel support, no queue management, no status tracking.

When you serve an agent over HTTP, you need:
- Background execution (don't block the request handler)
- Cancel mid-run (user clicks "Stop")
- Queue drain (clear stale events before a new turn)
- Status transitions (`idle → streaming → idle/error`)
- Error guarantee (always emit `done` or `error`, never hang)

This component manages all of that in one place.

## How It Works

```
User sends message
       │
       ▼
  drain_queue()       ← clear stale events from previous turn
       │
       ▼
  status = "streaming"
       │
       ▼
  start()             ← creates asyncio.Task running the agent
       │
       ├──► agent streams events to queue
       │
       ├──► user clicks cancel
       │         │
       │         ▼
       │    cancel()  ← cancels task, pushes done event
       │
       └──► agent finishes
                │
                ▼
           status = "idle"
           queue ← {"type": "done"}
## Key Guarantees

**Always ends with done or error** — the SSE endpoint never hangs waiting for an event that won't come
**Cancel is safe** — cancelling a completed task is a no-op
**Queue drain prevents ghost events** — events from a previous turn don't leak into the next one
**Status is always correct** — no "streaming" status after the agent finished or was cancelled
## Target Location in Chatforge

chatforge/services/agent_lifecycle.py