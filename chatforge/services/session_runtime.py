"""Session Runtime for chatforge.

Live runtime state for a web-served agent session. This is the
in-memory counterpart to the persisted Chat record — it holds
the running agent, its event queue, background task, and status.

Created when a user starts or resumes a chat. Discarded on
server shutdown (the Chat record in the DB survives).

Usage:
    from chatforge.services.session_runtime import SessionRuntime

    runtime = SessionRuntime(
        session_id="abc123",
        agent=compiled_graph,
        thread_config={"configurable": {"thread_id": "abc123"}},
    )

    # Start streaming
    runtime.status = "streaming"
    runtime.active_task = asyncio.create_task(
        run_agent_stream(runtime.agent, messages, runtime.thread_config, runtime.queue)
    )

    # SSE endpoint reads from runtime.queue
    # Cancel via runtime.active_task.cancel()
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SessionRuntime:
    """Live runtime state for one agent session.

    Attributes:
        session_id: Unique ID matching the persisted Chat record.
        agent: Compiled LangGraph graph instance.
        thread_config: LangGraph config with thread_id for
            checkpoint scoping.
        queue: asyncio.Queue for SSE event delivery. The agent
            stream pushes chunks here, the SSE endpoint reads them.
        active_task: The asyncio.Task running the agent (if any).
            Used for cancel support.
        status: Current lifecycle state.
            - "idle": no agent running, ready for new message
            - "streaming": agent is running, events flowing
            - "error": last run failed
        user_id: ID of the user who owns this session.
        settings: Session-level settings (model overrides, etc.).
        created_at: When this runtime was created.
        log_dir: Optional directory for per-session debug logs.
    """

    session_id: str
    agent: Any = None
    thread_config: dict = field(default_factory=dict)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    active_task: asyncio.Task | None = None
    status: str = "idle"
    user_id: str = ""
    settings: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    log_dir: str | None = None

    @property
    def is_busy(self) -> bool:
        """True if the agent is currently streaming."""
        return self.status == "streaming"

    @property
    def is_idle(self) -> bool:
        """True if ready for a new message."""
        return self.status == "idle"

    def to_status_dict(self) -> dict:
        """Snapshot of runtime state for API responses."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "has_agent": self.agent is not None,
            "has_active_task": self.active_task is not None and not self.active_task.done(),
        }
