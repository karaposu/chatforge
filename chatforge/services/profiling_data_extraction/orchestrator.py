"""
BaseExtractionOrchestrator - Abstract orchestration layer for extraction runs.

This module provides:
- ExtractionRepository: Protocol defining DB operations for extraction
- BaseExtractionOrchestrator: Abstract class with run lifecycle management

Usage:
    # In your app, implement the abstract methods:

    class MyExtractionService(BaseExtractionOrchestrator):
        def __init__(self, dependencies):
            self.dependencies = dependencies
            extractor = ProfilingDataExtractor(
                CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")
            )
            super().__init__(extractor)

        def get_repository(self):
            return self.dependencies.cpde7_repository(session=self._session)

        def create_session(self):
            return self.dependencies.session_factory()()

        def close_session(self, session):
            session.close()
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from chatforge.services.profiling_data_extraction.extractor import (
    ProfilingDataExtractor,
    ExtractedItem,
)
from chatforge.services.profiling_data_extraction.cpde7.models import ExtractionRunResult


@runtime_checkable
class ExtractionRepository(Protocol):
    """
    Protocol defining DB operations for extraction runs.

    Implement this interface in your app's repository to work with
    BaseExtractionOrchestrator.
    """

    def create_run(
        self,
        *,
        user_id: str,
        chat_id: int | None,
        config: dict,
        model_used: str | None = None,
    ) -> Any:
        """Create a new extraction run record (status="pending")."""
        ...

    def start_run(
        self,
        *,
        run_id: int,
        message_count: int,
        message_id_range: dict,
    ) -> Any:
        """Mark run as started (status="running")."""
        ...

    def complete_run(
        self,
        *,
        run_id: int,
        duration_ms: int,
    ) -> Any:
        """Mark run as completed (status="completed")."""
        ...

    def fail_run(
        self,
        *,
        run_id: int,
        error: str,
    ) -> Any:
        """Mark run as failed (status="failed")."""
        ...

    def get_run(self, *, run_id: int) -> Any | None:
        """Get run by ID."""
        ...

    def save_extracted_items_batch(
        self,
        *,
        run_id: int,
        user_id: str,
        chat_id: int,
        items: list[dict],
    ) -> int:
        """Save multiple extracted items. Returns count saved."""
        ...


class BaseExtractionOrchestrator(ABC):
    """
    Abstract orchestration layer for profiling data extraction.

    Provides:
    - Run lifecycle management (pending → running → completed/failed)
    - Batch processing with error recovery
    - Cancellation support (check between batches)
    - Duration tracking

    Subclass and implement abstract methods for app-specific DB access.

    Example:
        class MyService(BaseExtractionOrchestrator):
            def __init__(self, dependencies):
                extractor = ProfilingDataExtractor(
                    CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")
                )
                super().__init__(extractor)
                self.dependencies = dependencies

            def get_repository(self):
                return self.dependencies.cpde7_repository(session=self._session)

            def create_session(self):
                return self.dependencies.session_factory()()

            def close_session(self, session):
                session.close()

        # Usage
        service = MyService(dependencies)
        result = await service.run_extraction(user_id, chat_id, messages)
    """

    def __init__(
        self,
        extractor: ProfilingDataExtractor,
        min_messages: int = 3,
    ):
        """
        Initialize orchestrator.

        Args:
            extractor: ProfilingDataExtractor instance
            min_messages: Minimum messages required to run extraction
        """
        self.extractor = extractor
        self.min_messages = min_messages
        self._session = None

    # =========================================================================
    # Abstract Methods - Implement in subclass
    # =========================================================================

    @abstractmethod
    def get_repository(self) -> ExtractionRepository:
        """
        Return app-specific repository instance.

        This should return a repository that implements ExtractionRepository.
        Called within an active session context.
        """
        pass

    @abstractmethod
    def create_session(self) -> Any:
        """
        Create a new DB session.

        Returns a session object that will be passed to close_session.
        """
        pass

    @abstractmethod
    def close_session(self, session: Any) -> None:
        """
        Close the DB session.

        Args:
            session: The session returned by create_session
        """
        pass

    # =========================================================================
    # Optional Hooks - Override for custom behavior
    # =========================================================================

    def on_batch_complete(
        self,
        batch_num: int,
        total_batches: int,
        items: list[ExtractedItem],
        run_id: int,
    ) -> None:
        """
        Hook called after each batch completes.

        Override for logging, progress tracking, etc.
        """
        pass

    def on_run_start(self, run_id: int, message_count: int) -> None:
        """Hook called when run starts."""
        pass

    def on_run_complete(self, run_id: int, total_items: int, duration_ms: int) -> None:
        """Hook called when run completes successfully."""
        pass

    def on_run_failed(self, run_id: int, error: str) -> None:
        """Hook called when run fails."""
        pass

    def should_cancel(self, run_id: int) -> bool:
        """
        Check if run should be cancelled.

        Override to implement cancellation checking (e.g., check DB status).
        Called between batches.

        Returns:
            True if run should be cancelled
        """
        return False

    # =========================================================================
    # Main Orchestration
    # =========================================================================

    async def run_extraction(
        self,
        user_id: str,
        chat_id: int,
        messages: list,
        config: dict | None = None,
        target_roles: list[str] | None = None,
    ) -> ExtractionRunResult:
        """
        Run full extraction with lifecycle management.

        This is the main entry point. It:
        1. Checks message threshold
        2. Creates run record
        3. Processes batches with error handling
        4. Updates run status on completion/failure

        Args:
            user_id: User being profiled
            chat_id: Chat to extract from
            messages: All messages (will be batched)
            config: Optional config dict to store with run
            target_roles: Roles to extract from (default: extractor default)

        Returns:
            ExtractionRunResult with status and statistics
        """
        # Check threshold
        if len(messages) < self.min_messages:
            return ExtractionRunResult(
                run_id=None,
                status="skipped",
                items_extracted=0,
                message_count=len(messages),
                error=f"Below threshold: {len(messages)} < {self.min_messages}",
            )

        # Create session
        self._session = self.create_session()

        try:
            repo = self.get_repository()

            # Create run
            run = repo.create_run(
                user_id=user_id,
                chat_id=chat_id,
                config=config or {"batch_size": self.extractor.batch_size},
                model_used=self.extractor.model_info,
            )
            run_id = run.id

            # Start run
            message_ids = self._get_message_ids(messages)
            repo.start_run(
                run_id=run_id,
                message_count=len(messages),
                message_id_range={"min": min(message_ids), "max": max(message_ids)},
            )
            start_time = datetime.utcnow()
            self.on_run_start(run_id, len(messages))

            # Process batches
            total_items = 0
            batches = list(self.extractor.chunk_messages(messages))

            for batch_num, batch in enumerate(batches):
                # Check cancellation
                if self.should_cancel(run_id):
                    return ExtractionRunResult(
                        run_id=run_id,
                        status="cancelled",
                        items_extracted=total_items,
                        message_count=len(messages),
                    )

                try:
                    # Extract batch
                    items = await self.extractor.extract_batch(batch, target_roles)

                    # Save items
                    if items:
                        storage_items = [item.to_storage_dict() for item in items]
                        repo.save_extracted_items_batch(
                            run_id=run_id,
                            user_id=user_id,
                            chat_id=chat_id,
                            items=storage_items,
                        )
                        total_items += len(items)

                    self.on_batch_complete(batch_num, len(batches), items, run_id)

                except Exception as batch_error:
                    # Handle partial failure
                    duration_ms = self._calc_duration_ms(start_time)

                    if total_items > 0:
                        # Some data saved - mark as failed with context
                        error_msg = (
                            f"Partial: {total_items} items saved before "
                            f"batch {batch_num} failed: {batch_error}"
                        )
                        repo.fail_run(run_id=run_id, error=error_msg)
                        self.on_run_failed(run_id, error_msg)

                        return ExtractionRunResult(
                            run_id=run_id,
                            status="partial",
                            items_extracted=total_items,
                            duration_ms=duration_ms,
                            message_count=len(messages),
                            error=str(batch_error),
                        )
                    else:
                        # No data saved - propagate error
                        raise

            # Complete run
            duration_ms = self._calc_duration_ms(start_time)
            repo.complete_run(run_id=run_id, duration_ms=duration_ms)
            self.on_run_complete(run_id, total_items, duration_ms)

            return ExtractionRunResult(
                run_id=run_id,
                status="completed",
                items_extracted=total_items,
                duration_ms=duration_ms,
                message_count=len(messages),
            )

        except Exception as e:
            # Handle fatal error
            if "run_id" in locals():
                repo.fail_run(run_id=run_id, error=str(e))
                self.on_run_failed(run_id, str(e))

            return ExtractionRunResult(
                run_id=run_id if "run_id" in locals() else None,
                status="failed",
                items_extracted=0,
                error=str(e),
            )

        finally:
            self.close_session(self._session)
            self._session = None

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_message_ids(self, messages: list) -> list[int]:
        """Extract message IDs from message list."""
        ids = []
        for m in messages:
            if isinstance(m, dict):
                ids.append(m.get("id") or m.get("message_id"))
            else:
                ids.append(m.id)
        return ids

    def _calc_duration_ms(self, start_time: datetime) -> int:
        """Calculate duration in milliseconds from start time."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)
