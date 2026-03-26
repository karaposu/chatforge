"""File-Based Debug Logger for chatforge.

Per-session debug logging to JSONL files. Zero setup, zero
dependencies beyond the standard library. Works out of the box.

Each session gets its own directory with structured log files.
Open in any text editor, grep for errors, diff between runs.

Usage:
    from chatforge.services.debug_logger import SessionDebugLogger

    logger = SessionDebugLogger("session_abc123")

    logger.log_model_response(
        agent_name="orchestrator",
        response={"content": "I'll process slide 0..."},
        input_tokens=5000,
        output_tokens=200,
        duration_s=3.5,
    )

    logger.log_tool_call(
        tool_name="fetch_data",
        args={"id": "123"},
        result={"success": True},
        duration_ms=450,
    )
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SessionDebugLogger:
    """Per-session file-based debug logging.

    Creates a directory structure:
        {base_dir}/{session_id}/
            model_responses.jsonl
            tool_calls.jsonl

    Each line is a self-contained JSON object with timestamp
    and all relevant data. Append-only, crash-safe (each write
    is flushed).
    """

    def __init__(
        self,
        session_id: str,
        base_dir: str = "debug_output",
    ) -> None:
        self.session_id = session_id
        self.log_dir = Path(base_dir) / session_id
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._model_file = self.log_dir / "model_responses.jsonl"
        self._tool_file = self.log_dir / "tool_calls.jsonl"

        logger.debug("SessionDebugLogger: %s", self.log_dir)

    def log_model_response(
        self,
        agent_name: str,
        response: Any,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        reasoning_tokens: int | None = None,
        duration_s: float | None = None,
        model: str | None = None,
    ) -> None:
        """Log one LLM model response.

        Args:
            agent_name: Which agent made the call (e.g., "orchestrator",
                "content-filler", "template-matcher").
            response: The model's response (dict, str, or any
                JSON-serializable object).
            input_tokens: Prompt tokens used.
            output_tokens: Completion tokens used.
            reasoning_tokens: Reasoning/thinking tokens (if applicable).
            duration_s: Wall-clock seconds for the call.
            model: Model name (e.g., "gpt-5").
        """
        entry = {
            "timestamp": _now_iso(),
            "agent": agent_name,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "duration_s": duration_s,
            "response": _safe_serialize(response),
        }
        self._append(self._model_file, entry)

    def log_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: Any = None,
        error: str | None = None,
        duration_ms: int | None = None,
        agent_name: str | None = None,
    ) -> None:
        """Log one tool invocation.

        Args:
            tool_name: Name of the tool called.
            args: Arguments passed to the tool.
            result: Tool result (truncated for large outputs).
            error: Error message if the tool failed.
            duration_ms: Execution time in milliseconds.
            agent_name: Which agent called this tool.
        """
        entry = {
            "timestamp": _now_iso(),
            "agent": agent_name,
            "tool_name": tool_name,
            "args": _truncate_values(args, max_len=200),
            "result": _safe_serialize(result, max_len=500),
            "error": error,
            "duration_ms": duration_ms,
        }
        self._append(self._tool_file, entry)

    def log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Log a generic event (for extensibility).

        Args:
            event_type: Type of event (e.g., "session_created",
                "progress_update", "error").
            data: Event data.
        """
        entry = {
            "timestamp": _now_iso(),
            "event_type": event_type,
            **data,
        }
        events_file = self.log_dir / "events.jsonl"
        self._append(events_file, entry)

    @staticmethod
    def _append(filepath: Path, entry: dict) -> None:
        """Append one JSON line to a file. Flush immediately."""
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            logger.warning("Failed to write debug log %s: %s", filepath, e)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_serialize(obj: Any, max_len: int = 1000) -> Any:
    """Convert to JSON-safe value, truncating large strings."""
    if obj is None:
        return None
    if isinstance(obj, (int, float, bool)):
        return obj
    if isinstance(obj, str):
        return obj[:max_len] if len(obj) > max_len else obj
    if isinstance(obj, dict):
        return _truncate_values(obj, max_len=max_len)
    try:
        s = json.dumps(obj, default=str)
        return s[:max_len] if len(s) > max_len else json.loads(s)
    except (TypeError, ValueError):
        s = str(obj)
        return s[:max_len]


def _truncate_values(d: dict, max_len: int = 200) -> dict:
    """Truncate string values in a dict for readable logging."""
    result = {}
    for k, v in d.items():
        if isinstance(v, str) and len(v) > max_len:
            result[k] = v[:max_len] + "..."
        else:
            result[k] = v
    return result