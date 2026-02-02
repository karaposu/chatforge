# chatforge/services/profiling_data_extraction/trigger.py
"""
Generic Trigger Service for Profiling Data Extraction.

This module provides a reusable trigger layer that orchestrates when and how
extraction runs. Apps can use BaseTriggerService by providing concrete
implementations of the repository protocols.

Usage:
    from chatforge.services.profiling_data_extraction import (
        BaseTriggerService,
        TriggerConfig,
        MessageRepository,
        ExtractionRepository,
    )

    # Create with your app's concrete repositories
    trigger = BaseTriggerService(
        message_repo=my_message_repo,
        extraction_repo=my_extraction_repo,
        extractor=my_extractor,
        config=TriggerConfig(auto_trigger_threshold=10),
    )

    # Use the generic logic
    if await trigger.should_auto_trigger(chat_id):
        result = await trigger.trigger_extraction(user_id, chat_id)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, List, Protocol, runtime_checkable

from chatforge.services.profiling_data_extraction.extractor import (
    ProfilingDataExtractor,
    ExtractedItem,
)

logger = logging.getLogger(__name__)


# ─── Configuration ────────────────────────────────────────────────────────


@dataclass
class TriggerConfig:
    """Configuration for trigger behavior.

    Attributes:
        auto_trigger_threshold: Number of new messages before auto-triggering extraction
        min_messages: Minimum messages required to run extraction at all
        max_messages_per_run: Maximum messages to process in a single extraction run
    """
    auto_trigger_threshold: int = 10
    min_messages: int = 5
    max_messages_per_run: int = 500


# ─── Repository Protocols ─────────────────────────────────────────────────


@runtime_checkable
class MessageRepository(Protocol):
    """Protocol for message repository operations needed by trigger service."""

    def fetch_messages(self, *, chat_id: int, limit: int) -> List[Any]:
        """Fetch messages for a chat (oldest to newest)."""
        ...

    def fetch_messages_after(
        self, *, chat_id: int, after_message_id: int, limit: int
    ) -> List[Any]:
        """Fetch messages after a specific message ID."""
        ...

    def count_messages(self, *, chat_id: int) -> int:
        """Count total messages in a chat."""
        ...


@runtime_checkable
class ExtractionRepository(Protocol):
    """Protocol for extraction run repository operations."""

    def get_active_run(self, *, chat_id: int) -> Any | None:
        """Get pending/running extraction for a chat, or None."""
        ...

    def get_latest_completed_run(self, *, chat_id: int) -> Any | None:
        """Get most recent completed run for a chat, or None."""
        ...

    def get_run(self, *, run_id: int) -> Any | None:
        """Get extraction run by ID."""
        ...

    def get_runs_for_chat(self, *, chat_id: int, limit: int) -> List[Any]:
        """Get extraction runs for a chat."""
        ...

    def update_run_status(self, *, run_id: int, status: str) -> Any | None:
        """Update run status (e.g., for cancellation)."""
        ...

    def create_run(
        self, *, user_id: str, chat_id: int, config: dict, model_used: str | None
    ) -> Any:
        """Create a new extraction run."""
        ...

    def start_run(
        self, *, run_id: int, message_count: int, message_id_range: dict
    ) -> Any:
        """Mark run as started."""
        ...

    def complete_run(self, *, run_id: int, duration_ms: int) -> Any:
        """Mark run as completed."""
        ...

    def fail_run(self, *, run_id: int, error: str) -> Any:
        """Mark run as failed."""
        ...

    def save_extracted_items_batch(
        self, *, run_id: int, user_id: str, chat_id: int, items: List[dict]
    ) -> None:
        """Save extracted items in batch."""
        ...


# ─── Result Types ─────────────────────────────────────────────────────────


@dataclass
class TriggerResult:
    """Result of a trigger operation.

    Attributes:
        run_id: Extraction run ID (None if skipped)
        status: Run status (completed, skipped, failed, cancelled, partial)
        items_extracted: Number of items extracted
        message_count: Number of messages processed
        duration_ms: Duration in milliseconds
        error: Error message if failed
    """
    run_id: int | None = None
    status: str = "pending"
    items_extracted: int = 0
    message_count: int | None = None
    duration_ms: int | None = None
    error: str | None = None


# ─── Base Trigger Service ─────────────────────────────────────────────────


class BaseTriggerService:
    """
    Generic trigger service for profiling data extraction.

    This class provides reusable orchestration logic for triggering extraction.
    Apps provide concrete repository implementations via dependency injection.

    Responsibilities:
    - Check if auto-trigger conditions are met
    - Fetch messages for extraction
    - Orchestrate extraction runs
    - Manage run lifecycle (cancel, status)

    Args:
        message_repo: Repository for message operations
        extraction_repo: Repository for extraction run operations
        extractor: ProfilingDataExtractor instance for LLM extraction
        config: Trigger configuration

    Example:
        trigger = BaseTriggerService(
            message_repo=my_message_repo,
            extraction_repo=my_cpde7_repo,
            extractor=ProfilingDataExtractor(llm_service),
            config=TriggerConfig(auto_trigger_threshold=10),
        )

        result = await trigger.trigger_extraction("user123", chat_id=42)
    """

    def __init__(
        self,
        message_repo: MessageRepository,
        extraction_repo: ExtractionRepository,
        extractor: ProfilingDataExtractor,
        config: TriggerConfig | None = None,
    ):
        self.message_repo = message_repo
        self.extraction_repo = extraction_repo
        self.extractor = extractor
        self.config = config or TriggerConfig()

    async def trigger_extraction(
        self,
        user_id: str,
        chat_id: int,
        limit: int | None = None,
    ) -> TriggerResult:
        """
        Trigger extraction for a chat.

        Fetches messages and runs extraction synchronously (awaits completion).

        Args:
            user_id: User being profiled
            chat_id: Chat to extract from
            limit: Maximum messages to fetch (default: config.max_messages_per_run)

        Returns:
            TriggerResult with status and statistics
        """
        limit = limit or self.config.max_messages_per_run

        # Fetch messages
        messages = self.message_repo.fetch_messages(chat_id=chat_id, limit=limit)

        if not messages:
            logger.info(f"No messages found for chat {chat_id}")
            return TriggerResult(
                status="skipped",
                items_extracted=0,
                message_count=0,
                error="No messages found",
            )

        # Check minimum threshold
        if len(messages) < self.config.min_messages:
            logger.info(
                f"Skipping extraction: {len(messages)} messages < "
                f"{self.config.min_messages} threshold"
            )
            return TriggerResult(
                status="skipped",
                items_extracted=0,
                message_count=len(messages),
                error=f"Below threshold: {len(messages)} < {self.config.min_messages}",
            )

        # Run extraction
        return await self._run_extraction(user_id, chat_id, messages)

    async def trigger_incremental(
        self,
        user_id: str,
        chat_id: int,
        limit: int | None = None,
    ) -> TriggerResult:
        """
        Trigger extraction for NEW messages only (since last completed run).

        Args:
            user_id: User being profiled
            chat_id: Chat to extract from
            limit: Maximum new messages to process

        Returns:
            TriggerResult with status and statistics
        """
        limit = limit or self.config.max_messages_per_run

        # Get last completed run
        last_run = self.extraction_repo.get_latest_completed_run(chat_id=chat_id)

        # Determine starting point
        after_message_id = None
        if last_run and hasattr(last_run, 'message_id_range') and last_run.message_id_range:
            after_message_id = last_run.message_id_range.get("max")

        # Fetch only new messages
        if after_message_id:
            messages = self.message_repo.fetch_messages_after(
                chat_id=chat_id,
                after_message_id=after_message_id,
                limit=limit,
            )
        else:
            messages = self.message_repo.fetch_messages(chat_id=chat_id, limit=limit)

        if not messages:
            logger.info(f"No new messages for chat {chat_id}")
            return TriggerResult(
                status="skipped",
                items_extracted=0,
                message_count=0,
                error="No new messages since last extraction",
            )

        logger.info(
            f"Incremental extraction: {len(messages)} new messages "
            f"for chat {chat_id} (after_id={after_message_id})"
        )

        return await self._run_extraction(user_id, chat_id, messages)

    def trigger_extraction_background(
        self,
        user_id: str,
        chat_id: int,
        limit: int | None = None,
    ) -> None:
        """
        Trigger extraction in background (fire-and-forget).

        Args:
            user_id: User being profiled
            chat_id: Chat to extract from
            limit: Maximum messages to fetch
        """
        asyncio.create_task(
            self._run_extraction_background(user_id, chat_id, limit)
        )

    async def _run_extraction_background(
        self,
        user_id: str,
        chat_id: int,
        limit: int | None,
    ) -> None:
        """Background task wrapper with error handling."""
        try:
            result = await self.trigger_extraction(user_id, chat_id, limit)
            logger.info(
                f"Background extraction completed: chat={chat_id}, "
                f"status={result.status}, items={result.items_extracted}"
            )
        except Exception as e:
            logger.error(f"Background extraction failed: {e}", exc_info=True)

    async def should_auto_trigger(self, chat_id: int) -> bool:
        """
        Check if auto-trigger conditions are met.

        Returns True if:
        - No active extraction running
        - Enough new messages since last extraction

        Args:
            chat_id: Chat to check

        Returns:
            True if extraction should be triggered
        """
        # Check for active run
        active_run = self.extraction_repo.get_active_run(chat_id=chat_id)
        if active_run:
            logger.debug(
                f"Auto-trigger skip: active run for chat {chat_id}"
            )
            return False

        # Get total message count
        total_messages = self.message_repo.count_messages(chat_id=chat_id)

        # Get last completed run
        last_run = self.extraction_repo.get_latest_completed_run(chat_id=chat_id)

        # Calculate new messages since last extraction
        if last_run and hasattr(last_run, 'message_id_range') and last_run.message_id_range:
            last_max_id = last_run.message_id_range.get("max", 0)
            # Count messages after last extraction
            new_messages = self.message_repo.fetch_messages_after(
                chat_id=chat_id,
                after_message_id=last_max_id,
                limit=self.config.auto_trigger_threshold + 1,
            )
            new_count = len(new_messages)
        else:
            new_count = total_messages

        should_trigger = new_count >= self.config.auto_trigger_threshold
        logger.debug(
            f"Auto-trigger check: chat={chat_id}, new_messages={new_count}, "
            f"threshold={self.config.auto_trigger_threshold}, trigger={should_trigger}"
        )
        return should_trigger

    def cancel_run(self, run_id: int) -> bool:
        """
        Cancel a pending or running extraction.

        Args:
            run_id: Run to cancel

        Returns:
            True if cancelled, False if not cancellable

        Raises:
            ValueError: If run not found
        """
        run = self.extraction_repo.get_run(run_id=run_id)

        if not run:
            raise ValueError(f"Run {run_id} not found")

        if run.status not in ("pending", "running"):
            logger.debug(f"Cannot cancel run {run_id}: status is '{run.status}'")
            return False

        self.extraction_repo.update_run_status(run_id=run_id, status="cancelled")
        logger.info(f"Cancelled extraction run {run_id}")
        return True

    def get_run(self, run_id: int) -> Any | None:
        """Get extraction run by ID."""
        return self.extraction_repo.get_run(run_id=run_id)

    def get_runs_for_chat(self, chat_id: int, limit: int = 10) -> List[Any]:
        """Get extraction runs for a chat."""
        return self.extraction_repo.get_runs_for_chat(chat_id=chat_id, limit=limit)

    async def _run_extraction(
        self,
        user_id: str,
        chat_id: int,
        messages: List[Any],
    ) -> TriggerResult:
        """
        Internal: Run extraction on messages.

        Handles the full extraction lifecycle:
        1. Check for active run
        2. Create run record
        3. Process messages in batches
        4. Save extracted items
        5. Complete/fail run
        """
        from datetime import datetime

        # Check for active run
        active_run = self.extraction_repo.get_active_run(chat_id=chat_id)
        if active_run and active_run.status == "running":
            logger.warning(f"Extraction already in progress for chat {chat_id}")
            return TriggerResult(
                run_id=active_run.id,
                status="skipped",
                items_extracted=0,
                error="Extraction already in progress",
            )

        # Create run record
        run = self.extraction_repo.create_run(
            user_id=user_id,
            chat_id=chat_id,
            config={"batch_size": self.extractor.batch_size},
            model_used=self.extractor.model_info,
        )
        run_id = run.id
        logger.info(f"Created extraction run {run_id} for chat {chat_id}")

        # Start run
        message_ids = self._get_message_ids(messages)
        self.extraction_repo.start_run(
            run_id=run_id,
            message_count=len(messages),
            message_id_range={"min": min(message_ids), "max": max(message_ids)},
        )
        start_time = datetime.utcnow()

        try:
            # Process in batches
            total_items = 0
            batches = list(self.extractor.chunk_messages(messages))

            for batch_num, batch in enumerate(batches):
                # Check for cancellation
                run_status = self.extraction_repo.get_run(run_id=run_id)
                if run_status and run_status.status == "cancelled":
                    logger.info(f"Run {run_id} cancelled after batch {batch_num}")
                    return TriggerResult(
                        run_id=run_id,
                        status="cancelled",
                        items_extracted=total_items,
                        message_count=len(messages),
                    )

                # Extract batch
                items: List[ExtractedItem] = await self.extractor.extract_batch(batch)

                # Save items
                if items:
                    storage_items = [item.to_storage_dict() for item in items]
                    self.extraction_repo.save_extracted_items_batch(
                        run_id=run_id,
                        user_id=user_id,
                        chat_id=chat_id,
                        items=storage_items,
                    )
                    total_items += len(items)

                logger.info(
                    f"Run {run_id}: Batch {batch_num + 1}/{len(batches)}, "
                    f"{len(items)} items extracted"
                )

            # Complete run
            duration_ms = self._calc_duration_ms(start_time)
            self.extraction_repo.complete_run(run_id=run_id, duration_ms=duration_ms)

            logger.info(
                f"Run {run_id} completed: {total_items} items from "
                f"{len(messages)} messages in {duration_ms}ms"
            )

            return TriggerResult(
                run_id=run_id,
                status="completed",
                items_extracted=total_items,
                duration_ms=duration_ms,
                message_count=len(messages),
            )

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            duration_ms = self._calc_duration_ms(start_time)

            try:
                self.extraction_repo.fail_run(run_id=run_id, error=str(e))
            except Exception:
                pass  # Best effort

            return TriggerResult(
                run_id=run_id,
                status="failed",
                items_extracted=0,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _get_message_ids(self, messages: List[Any]) -> List[int]:
        """Extract message IDs from message list."""
        ids = []
        for m in messages:
            if isinstance(m, dict):
                ids.append(m.get("id") or m.get("message_id"))
            else:
                ids.append(m.id)
        return ids

    def _calc_duration_ms(self, start_time) -> int:
        """Calculate duration in milliseconds from start time."""
        from datetime import datetime
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)
