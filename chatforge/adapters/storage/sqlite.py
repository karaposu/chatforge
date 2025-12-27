"""
SQLite Storage Adapter - Implementation of StoragePort.

Provides persistent storage using SQLite for single-instance deployments.
Suitable for development, testing, and small production deployments.

Example:
    adapter = SQLiteStorageAdapter("./data/chatforge.db")
    await adapter.setup()

    await adapter.save_message("conv-1", MessageRecord(content="Hi", role="user"))
    history = await adapter.get_conversation("conv-1")
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from chatforge.ports import (
    ConversationRecord,
    MessageRecord,
    StoragePort,
)


logger = logging.getLogger(__name__)


class SQLiteStorageAdapter(StoragePort):
    """
    SQLite implementation of StoragePort.

    Provides persistent storage using aiosqlite for async SQLite access.
    Creates tables automatically on first use.

    Args:
        database_path: Path to SQLite database file. Created if doesn't exist.
    """

    def __init__(self, database_path: str = "./data/chatforge.db"):
        """Initialize SQLite storage adapter."""
        self._db_path = Path(database_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def setup(self) -> None:
        """Create database tables if they don't exist."""
        await self._ensure_tables()
        logger.info(f"SQLiteStorageAdapter initialized: {self._db_path}")

    async def _ensure_tables(self) -> None:
        """Create tables if not already created."""
        if self._initialized:
            return

        try:
            import aiosqlite
        except ImportError as e:
            raise ImportError(
                "aiosqlite is required for SQLiteStorageAdapter. "
                "Install with: pip install chatforge[sqlite]"
            ) from e

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    platform TEXT DEFAULT 'api',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_conv_updated ON conversations(updated_at)"
            )
            await db.commit()

        self._initialized = True

    async def close(self) -> None:
        """No-op for SQLite - connections are per-operation."""

    async def save_message(
        self,
        conversation_id: str,
        message: MessageRecord,
        user_id: str | None = None,
    ) -> None:
        """Save a message to conversation history."""
        await self._ensure_tables()
        import aiosqlite

        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            # Upsert conversation
            await db.execute(
                """
                INSERT INTO conversations (conversation_id, user_id, platform, created_at, updated_at, metadata)
                VALUES (?, ?, 'api', ?, ?, '{}')
                ON CONFLICT(conversation_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    user_id = COALESCE(excluded.user_id, conversations.user_id)
                """,
                (conversation_id, user_id, now, now),
            )

            # Insert message
            await db.execute(
                """
                INSERT INTO messages (conversation_id, role, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    message.role,
                    message.content,
                    message.created_at.isoformat(),
                    json.dumps(message.metadata or {}),
                ),
            )
            await db.commit()

        logger.debug(f"Saved message to conversation {conversation_id}")

    async def get_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[MessageRecord]:
        """Retrieve conversation history."""
        await self._ensure_tables()
        import aiosqlite

        messages = []
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT role, content, created_at, metadata
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ) as cursor:
                async for row in cursor:
                    messages.append(
                        MessageRecord(
                            role=row["role"],
                            content=row["content"],
                            created_at=datetime.fromisoformat(row["created_at"]),
                            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        )
                    )

        # Reverse to get chronological order (oldest first)
        messages.reverse()
        return messages

    async def get_conversation_metadata(
        self,
        conversation_id: str,
    ) -> ConversationRecord | None:
        """Get conversation metadata without messages."""
        await self._ensure_tables()
        import aiosqlite

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                return ConversationRecord(
                    conversation_id=row["conversation_id"],
                    user_id=row["user_id"],
                    platform=row["platform"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        await self._ensure_tables()
        import aiosqlite

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
            )
            cursor = await db.execute(
                "DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,)
            )
            await db.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted conversation {conversation_id}")
        return deleted

    async def cleanup_expired(self, ttl_minutes: int = 30) -> int:
        """Remove conversations older than TTL."""
        await self._ensure_tables()
        import aiosqlite

        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=ttl_minutes)).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            # Get expired conversation IDs
            expired_ids = []
            async with db.execute(
                "SELECT conversation_id FROM conversations WHERE updated_at < ?",
                (cutoff,),
            ) as cursor:
                async for row in cursor:
                    expired_ids.append(row[0])

            if not expired_ids:
                return 0

            # Delete messages and conversations
            placeholders = ",".join("?" * len(expired_ids))
            await db.execute(
                f"DELETE FROM messages WHERE conversation_id IN ({placeholders})",
                expired_ids,
            )
            await db.execute(
                f"DELETE FROM conversations WHERE conversation_id IN ({placeholders})",
                expired_ids,
            )
            await db.commit()

        logger.info(f"Cleaned up {len(expired_ids)} expired conversations")
        return len(expired_ids)

    async def list_conversations(
        self,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationRecord]:
        """List conversations, optionally filtered by user."""
        await self._ensure_tables()
        import aiosqlite

        conversations = []
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row

            if user_id:
                query = """
                    SELECT * FROM conversations
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """
                params = (user_id, limit)
            else:
                query = """
                    SELECT * FROM conversations
                    ORDER BY updated_at DESC
                    LIMIT ?
                """
                params = (limit,)

            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    conversations.append(
                        ConversationRecord(
                            conversation_id=row["conversation_id"],
                            user_id=row["user_id"],
                            platform=row["platform"],
                            created_at=datetime.fromisoformat(row["created_at"]),
                            updated_at=datetime.fromisoformat(row["updated_at"]),
                            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        )
                    )

        return conversations

    async def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            import aiosqlite

            async with aiosqlite.connect(self._db_path) as db:
                await db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False
