"""
ProfilingDataExtractor - Pure extraction logic without DB awareness.

This class handles:
- Message formatting with TARGET/CONTEXT markers
- Batch chunking
- Calling CPDE7LLMService for extraction
- Parsing LLM results into storage-ready format

Usage:
    from chatforge.services.profiling_data_extraction import (
        ProfilingDataExtractor,
        CPDE7LLMService,
    )

    llm_service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")
    extractor = ProfilingDataExtractor(llm_service)

    # Extract from a batch of messages
    items = await extractor.extract_batch(messages, target_roles=["user"])

    # Format messages with markers
    formatted = extractor.format_messages(messages, target_roles=["user"])
"""

from typing import Any, Callable, Iterator, Protocol, runtime_checkable

from chatforge.services.profiling_data_extraction.cpde7 import (
    CPDE7LLMService,
    BatchProfilingDataExtractionResult,
    format_messages_with_markers,
)


@runtime_checkable
class MessageProtocol(Protocol):
    """Protocol for message objects. Supports both dict and object access."""

    @property
    def id(self) -> int | str: ...

    @property
    def role(self) -> str: ...

    @property
    def content(self) -> str: ...


class ExtractedItem:
    """A single extracted item ready for storage.

    Attributes:
        source_message_id: The original message ID (e.g., "msg_42" -> 42)
        source_quote: The exact quote from the message
        dimension: Which CPDE-7 dimension this belongs to
        data: The extracted data (dimension-specific fields)
    """

    def __init__(
        self,
        source_message_id: int | str,
        source_quote: str,
        dimension: str,
        data: dict[str, Any],
    ):
        self.source_message_id = source_message_id
        self.source_quote = source_quote
        self.dimension = dimension
        self.data = data

    def to_storage_dict(self) -> dict:
        """Convert to dict format for repository storage."""
        return {
            "source_message_ids": [self.source_message_id],
            "source_quotes": [self.source_quote],
            "data": {
                "dimension": self.dimension,
                **self.data,
            },
        }

    def __repr__(self) -> str:
        return f"ExtractedItem(dimension={self.dimension!r}, source_id={self.source_message_id})"


class ProfilingDataExtractor:
    """
    Pure extraction logic - handles batching, LLM calls, and result parsing.

    This class is DB-agnostic. It takes messages, calls the LLM, and returns
    ExtractedItem objects ready for storage.

    Args:
        llm_service: CPDE7LLMService instance for LLM calls
        batch_size: Number of messages per LLM call (default: 50)
        target_roles: Default roles to extract from (default: ["user"])

    Example:
        llm_service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")
        extractor = ProfilingDataExtractor(llm_service, batch_size=50)

        # Extract from messages
        items = await extractor.extract_batch(messages)

        # Save items using your repository
        for item in items:
            repo.save_item(**item.to_storage_dict())
    """

    # CPDE-7 dimension names
    DIMENSIONS = [
        "core_identity",
        "opinions_views",
        "preferences_patterns",
        "desires_needs",
        "life_narrative",
        "events",
        "entities_relationships",
    ]

    def __init__(
        self,
        llm_service: CPDE7LLMService,
        batch_size: int = 50,
        target_roles: list[str] | None = None,
        dimensions: list[str] | None = None,
    ):
        self.llm_service = llm_service
        self.batch_size = batch_size
        self.target_roles = target_roles or ["user"]
        self.dimensions = dimensions  # None = extract all 7

    @property
    def model_info(self) -> str:
        """Return model identifier for logging/tracking."""
        return self.llm_service.model_info

    def chunk_messages(
        self,
        messages: list,
        batch_size: int | None = None,
    ) -> Iterator[list]:
        """
        Split messages into batches.

        Args:
            messages: List of message objects or dicts
            batch_size: Override default batch size

        Yields:
            Batches of messages
        """
        size = batch_size or self.batch_size
        for i in range(0, len(messages), size):
            yield messages[i : i + size]

    def format_messages(
        self,
        messages: list,
        target_roles: list[str] | None = None,
    ) -> str:
        """
        Format messages with TARGET/CONTEXT markers.

        Args:
            messages: List of message objects or dicts
            target_roles: Roles to mark as TARGET (default: self.target_roles)

        Returns:
            Formatted string with markers
        """
        roles = target_roles or self.target_roles

        # Convert to dict format expected by format_messages_with_markers
        message_dicts = []
        for m in messages:
            if isinstance(m, dict):
                message_dicts.append({
                    "id": f"msg_{m.get('id', m.get('message_id'))}",
                    "role": m.get("role"),
                    "content": m.get("content"),
                })
            else:
                # Object with attributes
                message_dicts.append({
                    "id": f"msg_{m.id}",
                    "role": m.role,
                    "content": m.content,
                })

        return format_messages_with_markers(message_dicts, target_roles=roles)

    async def extract_batch(
        self,
        messages: list,
        target_roles: list[str] | None = None,
        dimensions: list[str] | None = None,
    ) -> list[ExtractedItem]:
        """
        Extract profiling data from a batch of messages.

        This is the main extraction method. It formats messages, calls the LLM,
        and parses results into ExtractedItem objects.

        Args:
            messages: List of message objects or dicts
            target_roles: Roles to extract from (default: self.target_roles)
            dimensions: Dimensions to extract (default: self.dimensions, None = all 7)

        Returns:
            List of ExtractedItem objects ready for storage
        """
        # Format messages
        formatted = self.format_messages(messages, target_roles)
        roles = target_roles or self.target_roles
        dims = dimensions if dimensions is not None else self.dimensions

        # Extract dimensions (None = all 7)
        llm_result = await self.llm_service.extract_targeted(
            messages=formatted,
            target_roles=roles,
            dimensions=dims,
        )

        # Parse results into ExtractedItems
        return self._parse_llm_result(llm_result)

    async def extract_all_batches(
        self,
        messages: list,
        target_roles: list[str] | None = None,
        on_batch_complete: Callable | None = None,
    ) -> list[ExtractedItem]:
        """
        Extract from all messages, processing in batches.

        Args:
            messages: All messages to process
            target_roles: Roles to extract from
            on_batch_complete: Optional callback(batch_num, items) after each batch

        Returns:
            Combined list of all extracted items
        """
        all_items = []
        batches = list(self.chunk_messages(messages))

        for batch_num, batch in enumerate(batches):
            items = await self.extract_batch(batch, target_roles)
            all_items.extend(items)

            if on_batch_complete:
                on_batch_complete(batch_num, items)

        return all_items

    def _parse_llm_result(
        self, result: BatchProfilingDataExtractionResult
    ) -> list[ExtractedItem]:
        """
        Parse LLM result into list of ExtractedItem.

        Args:
            result: LLM extraction result (all 7 or targeted dimensions)

        Returns:
            List of ExtractedItem objects
        """
        items = []

        # Iterate over all dimensions
        dimension_results = [
            ("core_identity", result.core_identity),
            ("opinions_views", result.opinions_views),
            ("preferences_patterns", result.preferences_patterns),
            ("desires_needs", result.desires_needs),
            ("life_narrative", result.life_narrative),
            ("events", result.events),
            ("entities_relationships", result.entities_relationships),
        ]

        for dimension_name, dimension_result in dimension_results:
            if not dimension_result or not dimension_result.has_content:
                continue

            for item in dimension_result.items:
                # Parse message ID: "msg_42" -> 42
                source_id = self._parse_message_id(item.source_message_id)

                # Get all fields except source attribution
                item_dict = item.model_dump(
                    exclude={"source_message_id", "source_quote"}
                )

                extracted = ExtractedItem(
                    source_message_id=source_id,
                    source_quote=item.source_quote,
                    dimension=dimension_name,
                    data=item_dict,
                )
                items.append(extracted)

        return items

    def _parse_message_id(self, msg_id: str) -> int | str:
        """
        Parse message ID from format "msg_42" to 42.

        Args:
            msg_id: Message ID string (e.g., "msg_42")

        Returns:
            Parsed ID (int if numeric, str otherwise)
        """
        if msg_id.startswith("msg_"):
            id_part = msg_id[4:]  # Remove "msg_" prefix
            try:
                return int(id_part)
            except ValueError:
                return id_part
        return msg_id

    def get_dimensions_with_data(self, result: BatchProfilingDataExtractionResult) -> list[str]:
        """
        Get list of dimensions that have extracted data.

        Args:
            result: LLM extraction result

        Returns:
            List of dimension names with has_content=True
        """
        dimensions = []

        for dim_name in self.DIMENSIONS:
            dim_result = getattr(result, dim_name, None)
            if dim_result and dim_result.has_content:
                dimensions.append(dim_name)

        return dimensions
