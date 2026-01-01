"""Connection metrics for WebSocket client."""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectionMetrics:
    """Track connection statistics for debugging and monitoring."""

    # Counters
    connect_count: int = 0
    disconnect_count: int = 0
    reconnect_count: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    messages_dropped: int = 0  # Receive queue overflow
    bytes_sent: int = 0
    bytes_received: int = 0
    send_queue_full_count: int = 0  # Backpressure events

    # Timestamps (using monotonic for durations)
    connect_time: Optional[float] = None
    last_send_time: Optional[float] = None
    last_receive_time: Optional[float] = None

    # Connection ID (set externally)
    connection_id: Optional[str] = None

    def on_connect(self) -> None:
        """Record a connection event."""
        self.connect_count += 1
        self.connect_time = time.monotonic()

    def on_disconnect(self) -> None:
        """Record a disconnection event."""
        self.disconnect_count += 1

    def on_reconnect(self) -> None:
        """Record a reconnection event."""
        self.reconnect_count += 1

    def on_message_sent(self, size: int) -> None:
        """Record an outgoing message."""
        self.messages_sent += 1
        self.bytes_sent += size
        self.last_send_time = time.monotonic()

    def on_message_received(self, size: int) -> None:
        """Record an incoming message."""
        self.messages_received += 1
        self.bytes_received += size
        self.last_receive_time = time.monotonic()

    def on_message_dropped(self) -> None:
        """Record a dropped message (receive queue full)."""
        self.messages_dropped += 1

    def on_backpressure(self) -> None:
        """Record a backpressure event (send queue full)."""
        self.send_queue_full_count += 1

    def get_stats(self) -> dict:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection metrics and calculated values
        """
        now = time.monotonic()
        stats = {
            "connection_id": self.connection_id,
            "connects": self.connect_count,
            "disconnects": self.disconnect_count,
            "reconnects": self.reconnect_count,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "messages_dropped": self.messages_dropped,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "backpressure_events": self.send_queue_full_count,
        }

        # Add calculated metrics
        if self.connect_time:
            stats["uptime_seconds"] = round(now - self.connect_time, 2)

        if self.last_send_time:
            stats["seconds_since_send"] = round(now - self.last_send_time, 2)

        if self.last_receive_time:
            stats["seconds_since_receive"] = round(now - self.last_receive_time, 2)

        # Calculate rates if we have uptime
        if self.connect_time and (now - self.connect_time) > 0:
            uptime = now - self.connect_time
            stats["messages_per_second"] = round(
                (self.messages_sent + self.messages_received) / uptime, 2
            )
            stats["bytes_per_second"] = round(
                (self.bytes_sent + self.bytes_received) / uptime, 2
            )

        return stats

    def reset(self) -> None:
        """Reset all counters and timestamps."""
        self.connect_count = 0
        self.disconnect_count = 0
        self.reconnect_count = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_dropped = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.send_queue_full_count = 0
        self.connect_time = None
        self.last_send_time = None
        self.last_receive_time = None
