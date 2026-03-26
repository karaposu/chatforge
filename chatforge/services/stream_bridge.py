"""LangGraph Stream Bridge for chatforge.

Translates LangGraph agent.astream() events into typed SSE chunks
and pushes them into an asyncio.Queue for the SSE endpoint to
consume.

Works with any LangGraph compiled graph — no domain-specific
assumptions. Handles AIMessage (text + tool calls) and
ToolMessage (tool results).

Usage:
    from chatforge.services.stream_bridge import run_agent_stream

    queue = asyncio.Queue()
    await run_agent_stream(agent, messages, config, queue)
    # queue now has typed chunks for SSE consumption
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _extract_text(content: Any) -> str:
    """Normalize AI message content to plain text.

    LangGraph messages can have content as str, list of dicts
    (with type=text entries), or other structures.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content)


class LangGraphStreamBridge:
    """Translates LangGraph stream events into typed SSE chunks.

    Stateless per event — call translate() for each event from
    agent.astream(). Accumulates text parts for retrieval after
    streaming via get_full_text().
    """

    def __init__(self) -> None:
        self._text_parts: list[str] = []

    def translate(self, event: dict) -> list[dict[str, Any]]:
        """Convert one LangGraph stream event to SSE chunks.

        Args:
            event: One event from agent.astream(stream_mode="updates").
                Keys are node names, values are node outputs with
                a "messages" list.

        Returns:
            List of typed chunk dicts ready for SSE.
        """
        chunks: list[dict[str, Any]] = []

        for _node_name, node_data in event.items():
            if node_data is None:
                continue
            raw_messages = node_data.get("messages", [])
            if hasattr(raw_messages, "value"):
                raw_messages = raw_messages.value
            if not isinstance(raw_messages, list):
                continue

            for msg in raw_messages:
                msg_type = getattr(msg, "type", None)

                if msg_type == "ai":
                    tool_calls = getattr(msg, "tool_calls", None)
                    if tool_calls:
                        for tc in tool_calls:
                            chunks.append({
                                "type": "tool_call",
                                "tool_name": tc["name"],
                                "tool_args": {
                                    k: str(v)[:100]
                                    for k, v in tc.get("args", {}).items()
                                },
                            })
                    elif msg.content:
                        text = _extract_text(msg.content)
                        self._text_parts.append(text)
                        chunks.append({
                            "type": "text",
                            "content": text,
                        })

                elif msg_type == "tool":
                    chunks.append({
                        "type": "tool_result",
                        "tool_name": getattr(msg, "name", ""),
                        "content": str(getattr(msg, "content", ""))[:200],
                    })

        return chunks

    def get_full_text(self) -> str:
        """Return accumulated assistant text from all translated events."""
        return "\n\n".join(self._text_parts)


async def run_agent_stream(
    agent: Any,
    messages: list[dict],
    config: dict,
    queue: asyncio.Queue,
    session_id: str = "",
) -> None:
    """Run agent.astream() and push translated chunks to queue.

    This is the main entry point. Call it from a route handler
    to stream agent events to the SSE endpoint.

    Args:
        agent: A compiled LangGraph graph (from create_react_agent,
            create_deep_agent, or any CompiledGraph).
        messages: List of message dicts (e.g., [{"role": "user",
            "content": "Hello"}]).
        config: LangGraph config with thread_id (e.g.,
            {"configurable": {"thread_id": "abc123"}}).
        queue: asyncio.Queue to push SSE chunks into.
        session_id: Optional session ID for the done event.
    """
    bridge = LangGraphStreamBridge()

    try:
        async for event in agent.astream(
            {"messages": messages},
            config=config,
            stream_mode="updates",
        ):
            for chunk in bridge.translate(event):
                await queue.put(chunk)

        await queue.put(
            {"type": "done", "session_id": session_id},
        )

    except Exception as e:
        logger.error("Agent stream error: %s", e, exc_info=True)
        await queue.put(
            {"type": "error", "error": str(e), "recoverable": False},
        )
