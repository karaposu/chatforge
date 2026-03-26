"""Subagent-Aware Stream Bridge for chatforge.

Extends LangGraphStreamBridge to detect DeepAgents subagent
spawning via `task` tool calls. Integrates with ProgressTracker
to report subagent lifecycle (spawn → running → completed/failed).

Works with any DeepAgents graph that uses the `task` tool for
subagent delegation. No domain-specific assumptions.

Usage:
    from chatforge.services.stream_bridge import SubagentAwareStreamBridge
    from chatforge.services.progress import ProgressTracker

    tracker = ProgressTracker()
    bridge = SubagentAwareStreamBridge(progress=tracker)

    async for event in agent.astream(...):
        for chunk in bridge.translate(event):
            await queue.put(chunk)
"""

import logging
from typing import Any

from chatforge.services.progress import ProgressTracker
from chatforge.services.stream_bridge import LangGraphStreamBridge, _extract_text

logger = logging.getLogger(__name__)


class SubagentAwareStreamBridge(LangGraphStreamBridge):
    """Extends stream bridge with subagent progress tracking.

    Detects `task` tool calls (DeepAgents' subagent delegation
    mechanism) and reports them to a ProgressTracker.
    """

    def __init__(self, progress: ProgressTracker | None = None) -> None:
        super().__init__()
        self._progress = progress
        self._pending_tasks: dict[str, tuple[str, str]] = {}

    def translate(self, event: dict) -> list[dict[str, Any]]:
        """Translate event and detect subagent lifecycle.

        Extends the base translate() with subagent detection.
        Emits additional progress chunks when subagents spawn
        or complete.
        """
        chunks = super().translate(event)

        for _node_name, node_data in event.items():
            if node_data is None:
                continue
            raw_messages = node_data.get("messages", [])
            if hasattr(raw_messages, "value"):
                raw_messages = raw_messages.value
            if not isinstance(raw_messages, list):
                continue

            for msg in raw_messages:
                self._handle_subagent_lifecycle(msg)

        if self._progress and self._progress.active:
            chunks.append({
                "type": "progress",
                "progress": self._progress.to_dict(),
            })

        return chunks

    def _handle_subagent_lifecycle(self, msg: Any) -> None:
        """Detect task spawns and completions in messages."""
        msg_type = getattr(msg, "type", None)

        if msg_type == "ai":
            spawn = self._detect_task_spawn(msg)
            if spawn:
                call_id, agent_name, description = spawn
                self._pending_tasks[call_id] = (agent_name, description)
                if self._progress:
                    task_id = f"{agent_name}_{call_id[:8]}"
                    self._progress.on_task_started(task_id, f"{agent_name}: {description}")

        elif msg_type == "tool":
            completion = self._detect_task_completion(msg)
            if completion:
                call_id, agent_name, description = completion
                if self._progress:
                    task_id = f"{agent_name}_{call_id[:8]}"
                    result = str(getattr(msg, "content", ""))[:200]
                    self._progress.on_task_completed(task_id, result)

    @staticmethod
    def _detect_task_spawn(msg: Any) -> tuple[str, str, str] | None:
        """Check if an AI message spawns a subagent via `task` tool.

        DeepAgents' `task` tool call has args:
            subagent_type: str  (e.g., "generalPurpose", "explore")
            description: str    (e.g., "Match template for slide 0")
            prompt: str         (full task description)

        Returns:
            (call_id, agent_name, description) or None.
        """
        for tc in getattr(msg, "tool_calls", None) or []:
            if tc.get("name") == "task":
                args = tc.get("args", {})
                agent_name = args.get("subagent_type", "subagent")
                description = args.get("description", "")
                call_id = tc.get("id", "")
                if agent_name and call_id:
                    return (call_id, agent_name, description)
        return None

    def _detect_task_completion(self, msg: Any) -> tuple[str, str, str] | None:
        """Check if a tool result matches a pending task spawn.

        Returns:
            (call_id, agent_name, description) or None.
        """
        tool_call_id = getattr(msg, "tool_call_id", "")
        pending = self._pending_tasks.pop(tool_call_id, None)
        if pending:
            agent_name, description = pending
            return (tool_call_id, agent_name, description)
        return None