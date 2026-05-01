"""SQLAlchemy async implementation of ProfilingRepository."""

from typing import Optional
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from chatforge.ports.storage import ProfilingRepository
from chatforge.adapters.storage.models.models import (
    ProfilingDataExtractionRun,
    ExtractedProfilingData,
    _utc_now,
)

logger = logging.getLogger(__name__)


class SQLAlchemyProfilingRepo(ProfilingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run(
        self, *, user_id: str, chat_id: int | None = None,
        config: dict, model_used: str | None = None,
    ) -> ProfilingDataExtractionRun:
        run = ProfilingDataExtractionRun(
            user_id=user_id, chat_id=chat_id, status="pending",
            config=config, model_used=model_used, created_at=_utc_now(),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def start_run(self, *, run_id: int, message_count: int, message_id_range: dict):
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            raise ValueError(f"Extraction run {run_id} not found")
        run.status = "running"
        run.started_at = _utc_now()
        run.message_count = message_count
        run.message_id_range = message_id_range
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def complete_run(self, *, run_id: int, duration_ms: int):
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            raise ValueError(f"Extraction run {run_id} not found")
        run.status = "completed"
        run.completed_at = _utc_now()
        run.duration_ms = duration_ms
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def fail_run(self, *, run_id: int, error: str):
        run = await self.session.get(ProfilingDataExtractionRun, run_id)
        if not run:
            raise ValueError(f"Extraction run {run_id} not found")
        run.status = "failed"
        run.error = error
        run.completed_at = _utc_now()
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_run(self, *, run_id: int):
        return await self.session.get(ProfilingDataExtractionRun, run_id)

    async def get_runs_for_user(self, *, user_id: str, limit: int = 20):
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.user_id == user_id)
            .order_by(ProfilingDataExtractionRun.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_run(self, *, chat_id: int):
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.chat_id == chat_id)
            .where(ProfilingDataExtractionRun.status.in_(["pending", "running"]))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_completed_run(self, *, chat_id: int):
        stmt = (
            select(ProfilingDataExtractionRun)
            .where(ProfilingDataExtractionRun.chat_id == chat_id)
            .where(ProfilingDataExtractionRun.status == "completed")
            .order_by(ProfilingDataExtractionRun.completed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save_extracted_item(
        self, *, run_id: int, user_id: str, chat_id: int,
        source_message_ids: list[int], source_quotes: list[str], data: dict,
    ):
        item = ExtractedProfilingData(
            extraction_run_id=run_id, user_id=user_id, chat_id=chat_id,
            source_message_ids=source_message_ids,
            source_quotes=source_quotes, data=data, created_at=_utc_now(),
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save_extracted_items_batch(
        self, *, run_id: int, user_id: str, chat_id: int, items: list[dict],
    ) -> int:
        count = 0
        for item_data in items:
            item = ExtractedProfilingData(
                extraction_run_id=run_id, user_id=user_id, chat_id=chat_id,
                source_message_ids=item_data.get("source_message_ids", []),
                source_quotes=item_data.get("source_quotes", []),
                data=item_data.get("data", {}), created_at=_utc_now(),
            )
            self.session.add(item)
            count += 1
        await self.session.commit()
        return count

    async def get_cpde7_data(self, *, user_id: str, limit: int = 100):
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cpde7_data_by_chat(self, *, user_id: str, chat_id: int, limit: int = 100):
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.chat_id == chat_id)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cpde7_data_by_dimension(self, *, user_id: str, dimension: str, limit: int = 50):
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
        dimensions = [
            "core_identity", "opinions_views", "preferences_patterns",
            "desires_needs", "life_narrative", "events", "entities_relationships",
        ]
        result = {}
        for dim in dimensions:
            items = await self.get_cpde7_data_by_dimension(
                user_id=user_id, dimension=dim, limit=limit_per_dimension,
            )
            result[dim] = [item.data for item in items]
        return result

    async def get_profile_data_for_chat(self, *, user_id: str, chat_id: int, limit: int = 100):
        stmt = (
            select(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.chat_id == chat_id)
            .order_by(ExtractedProfilingData.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [item.data for item in result.scalars().all()]

    async def delete_cpde7_data_for_chat(self, *, user_id: str, chat_id: int) -> int:
        stmt = (
            delete(ExtractedProfilingData)
            .where(ExtractedProfilingData.user_id == user_id)
            .where(ExtractedProfilingData.chat_id == chat_id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
