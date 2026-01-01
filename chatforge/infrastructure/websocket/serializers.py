"""Message serializers for WebSocket client."""

import json
from typing import Any, Protocol, Union


class MessageSerializer(Protocol):
    """Protocol for message serialization."""

    def serialize(self, data: Any) -> Union[str, bytes]:
        """Serialize data for sending."""
        ...

    def deserialize(self, data: Union[str, bytes]) -> Any:
        """Deserialize received data."""
        ...


class JsonSerializer:
    """JSON serialization for text-based protocols."""

    def serialize(self, data: Any) -> str:
        """Serialize to JSON string."""
        return json.dumps(data)

    def deserialize(self, data: Union[str, bytes]) -> Any:
        """Deserialize from JSON string."""
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)


class RawSerializer:
    """Pass-through serialization (no transformation)."""

    def serialize(self, data: Any) -> Any:
        """Return data as-is."""
        return data

    def deserialize(self, data: Any) -> Any:
        """Return data as-is."""
        return data


# Optional: MessagePack for binary protocols
try:
    import msgpack

    class MsgPackSerializer:
        """MessagePack binary serialization."""

        def serialize(self, data: Any) -> bytes:
            return msgpack.packb(data)

        def deserialize(self, data: Union[str, bytes]) -> Any:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return msgpack.unpackb(data)

except ImportError:
    MsgPackSerializer = None  # type: ignore
