"""
Async CPDE-7 Repository.

Storage and retrieval of CPDE-7 extracted profiling data using AsyncSession.

Usage:
    from chatforge.adapters.storage.repositories.async_ import CPDE7Repository

    repo = CPDE7Repository(async_session)
    run = await repo.create_run(user_id="user-1", config={"dimensions": "all"})
"""

from typing import Optional
import logging

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from chatforge.adapters.storage.models.models import (
    ProfilingDataExtractionRun,
    ExtractedProfilingData,
    _utc_now,
)

logger = logging.getLogger(__name__)


class CPDE7Repository:
    """
    Async repository for CPDE-7 extracted data access.

    Provides methods to:
    - Create and track extraction runs
    - Store extracted data items with source attribution
    - Retrieve extracted data by user, chat, or dimension
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # Extraction Run Management
    # =========================================================================

    async def create_run(
        self,
        *,
        user_id: str,
        chat_id: Optional[int] = None,
        config: dict,
        model_used: Optional[str] = None,
    ) -> ProfilingDataExtractionRun:
        """Create a new extraction run record."""
        run = ProfilingDataExtractionRun(
            user_id=user_id,
            chat_id=chat_id,
            status="pending",
            config=config,
            model_used=model_used,
            created_at=_utc_now(),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)

        logger.debug("Created extraction run id=%s (user_id=%s, chat_id=%s)", run.id, user_id, chat_id)
        return run

    async def start_run(
        self,
        *,
        run_id: int,
        message_count: int,
        message_id_range: dict,
    ) -> ProfilingDataExtractionRun:
        """Mark an extraction run as started."""
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            raise ValueError(f"Extraction run {run_id} not found")

        run.status = "running"
        run.started_at = _utc_now()
        run.message_count = message_count
        run.message_id_range = message_id_range

        await self.session.commit()
        await self.session.refresh(run)

        logger.debug("Started extraction run id=%s (messages=%s)", run_id, message_count)
        return run

    async def complete_run(self, *, run_id: int, duration_ms: int) -> ProfilingDataExtractionRun:
        """Mark an extraction run as completed."""
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            raise ValueError(f"Extraction run {run_id} not found")

        run.status = "completed"
        run.completed_at = _utc_now()
        run.duration_ms = duration_ms

        await self.session.commit()
        await self.session.refresh(run)

        logger.debug("Completed extraction run id=%s (duration=%sms)", run_id, duration_ms)
        return run

    async def fail_run(self, *, run_id: int, error: str) -> ProfilingDataExtractionRun:
        """Mark an extraction run as failed."""
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            raise ValueError(f"Extraction run {run_id} not found")

        run.status = "failed"
        run.error = error
        run.completed_at = _utc_now()

        await self.session.commit()
        await self.session.refresh(run)

        logger.warning("Extraction run id=%s failed: %s", run_id, error)
        return run

    async def get_run(self, *, run_id: int) -> Optional[ProfilingDataExtractionRun]:
        """Get an extraction run by ID."""
        return await self.session.get(ProfilingDataExtractionRun, run_id)

    async def get_runs_for_user(self, *, user_id: str, limit: int = 20) -> list[ProfilingDataExtractionRun]:
        """Get recent extraction runs for a user."""
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.user_id == user_id)
            .order_by(ProfilingDataExtractionRun.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_run(self, *, chat_id: int) -> Optional[ProfilingDataExtractionRun]:
        """Get any pending or running extraction run for a chat."""
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.chat_id == chat_id)
            .where(ProfilingDataExtractionRun.status.in_(["pending", "running"]))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_runs_for_chat(self, *, chat_id: int, limit: int = 10) -> list[ProfilingDataExtractionRun]:
        """Get extraction runs for a specific chat."""
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.chat_id == chat_id)
            .order_by(ProfilingDataExtractionRun.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_completed_run(self, *, chat_id: int) -> Optional[ProfilingDataExtractionRun]:
        """Get the most recent completed extraction run for a chat."""
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.chat_id == chat_id)
            .where(ProfilingDataExtractionRun.status == "completed")
            .order_by(ProfilingDataExtractionRun.completed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_run_status(self, *, run_id: int, status: str) -> Optional[ProfilingDataExtractionRun]:
        """Update the status of an extraction run."""
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            return None

        run.status = status
        if status in ("completed", "failed", "cancelled"):
            run.completed_at = _utc_now()

        await self.session.commit()
        await self.session.refresh(run)

        logger.debug("Updated run %s status to '%s'", run_id, status)
        return run

    # =========================================================================
    # Extracted Data Storage
    # =========================================================================

    async def save_extracted_item(
        self,
        *,
        run_id: int,
        user_id: str,
        chat_id: int,
        source_message_ids: list[int],
        source_quotes: list[str],
        data: dict,
    ) -> ExtractedProfilingData:
        """Save a single extracted data item."""
        item = ExtractedProfilingData(
            extraction_run_id=run_id,
            user_id=user_id,
            chat_id=chat_id,
            source_message_ids=source_message_ids,
            source_quotes=source_quotes,
            data=data,
            created_at=_utc_now(),
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        logger.debug("Saved extracted item id=%s (dimension=%s)", item.id, data.get("dimension"))
        return item

    async def save_extracted_items_batch(
        self,
        *,
        run_id: int,
        user_id: str,
        chat_id: int,
        items: list[dict],
    ) -> int:
        """
        Save multiple extracted items in a single transaction.

        Each item dict should have: source_message_ids, source_quotes, data.
        Returns number of items saved.
        """
        count = 0
        for item_data in items:
            item = ExtractedProfilingData(
                extraction_run_id=run_id,
                user_id=user_id,
                chat_id=chat_id,
                source_message_ids=item_data.get("source_message_ids", []),
                source_quotes=item_data.get("source_quotes", []),
                data=item_data.get("data", {}),
                created_at=_utc_now(),
            )
            self.session.add(item)
            count += 1

        await self.session.commit()

        logger.debug("Saved %s extracted items (run_id=%s, user=%s)", count, run_id, user_id)
        return count

    # =========================================================================
    # Extracted Data Retrieval
    # =========================================================================

    async def get_cpde7_data(self, *, user_id: str, limit: int = 100) -> list[ExtractedProfilingData]:
        """Get all CPDE-7 extracted data for a user."""
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cpde7_data_by_chat(
        self,
        *,
        user_id: str,
        chat_id: int,
        limit: int = 100,
    ) -> list[ExtractedProfilingData]:
        """Get CPDE-7 extracted data for a specific chat."""
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.chat_id == chat_id)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cpde7_data_by_dimension(
        self,
        *,
        user_id: str,
        dimension: str,
        limit: int = 50,
    ) -> list[ExtractedProfilingData]:
        """Get CPDE-7 extracted data for a specific dimension."""
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.data['dimension'].as_string() == dimension)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cpde7_data_grouped(self, *, user_id: str, limit_per_dimension: int = 20) -> dict:
        """Get CPDE-7 data grouped by dimension."""
        dimensions = [
            "core_identity",
            "opinions_views",
            "preferences_patterns",
            "desires_needs",
            "life_narrative",
            "events",
            "entities_relationships",
        ]

        result = {}
        for dim in dimensions:
            items = await self.get_cpde7_data_by_dimension(
                user_id=user_id, dimension=dim, limit=limit_per_dimension,
            )
            result[dim] = [item.data for item in items]

        return result

    async def get_profile_data_for_chat(
        self,
        *,
        user_id: str,
        chat_id: int,
        limit: int = 100,
    ) -> list[dict]:
        """Get extracted profile data for a chat (data field only)."""
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.chat_id == chat_id)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return [item.data for item in items]

    async def delete_cpde7_data_for_chat(self, *, user_id: str, chat_id: int) -> int:
        """Delete all extracted data for a specific chat."""
        stmt = (
            delete(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.chat_id == chat_id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        count = result.rowcount
        logger.debug("Deleted %s extracted items (user=%s, chat=%s)", count, user_id, chat_id)
        return count
