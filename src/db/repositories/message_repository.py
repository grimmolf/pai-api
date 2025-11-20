"""Message repository for database operations."""

import aiosqlite
from typing import Optional
from datetime import datetime, timezone
from src.db.models import MessageDirection, MessageStatus
from src.logging_config import logger

class MessageRepository:
    """Repository for message CRUD operations."""

    def __init__(self, connection: aiosqlite.Connection):
        self.conn = connection

    async def store_inbox_message(
        self,
        message_id: str,
        sender: str,
        content: str,
        message_type: str,
        priority: str,
        context_id: Optional[str] = None
    ) -> dict:
        """Store a received message in the inbox."""
        async with self.conn.execute(
            """
            INSERT INTO messages (id, sender, content, message_type, priority, context_id, direction, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, sender, content, message_type, priority, context_id,
             MessageDirection.INBOX.value, MessageStatus.RECEIVED.value)
        ):
            await self.conn.commit()

        logger.debug(f"Stored inbox message: {message_id} from {sender}")
        return {"id": message_id, "status": "stored"}

    async def store_outbox_message(
        self,
        message_id: str,
        sender: str,
        content: str,
        message_type: str,
        priority: str,
        status: MessageStatus,
        context_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> dict:
        """Store an outgoing message in the outbox."""
        async with self.conn.execute(
            """
            INSERT INTO messages (id, sender, content, message_type, priority, context_id, direction, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, sender, content, message_type, priority, context_id,
             MessageDirection.OUTBOX.value, status.value, error_message)
        ):
            await self.conn.commit()

        logger.debug(f"Stored outbox message: {message_id} with status {status.value}")
        return {"id": message_id, "status": status.value}

    async def update_outbox_status(
        self,
        message_id: str,
        status: MessageStatus,
        error_message: Optional[str] = None
    ):
        """Update the status of an outbox message."""
        await self.conn.execute(
            """
            UPDATE messages
            SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND direction = 'outbox'
            """,
            (status.value, error_message, message_id)
        )
        await self.conn.commit()
        logger.debug(f"Updated message {message_id} to status {status.value}")

    async def increment_retry_count(self, message_id: str):
        """Increment retry count and update last_retry_at timestamp."""
        await self.conn.execute(
            """
            UPDATE messages
            SET retry_count = retry_count + 1,
                last_retry_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND direction = 'outbox'
            """,
            (message_id,)
        )
        await self.conn.commit()
        logger.debug(f"Incremented retry count for message {message_id}")

    async def get_pending_outbox_messages(self, max_retries: int = 3) -> list[dict]:
        """
        Get all outbox messages that need to be sent or retried.
        Excludes messages that have exceeded max retry count.
        """
        async with self.conn.execute(
            """
            SELECT * FROM messages
            WHERE direction = 'outbox'
              AND status IN ('pending', 'failed')
              AND retry_count < ?
            ORDER BY priority DESC, created_at ASC
            """,
            (max_retries,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_message_history(
        self,
        limit: int = 100,
        sender: Optional[str] = None,
        direction: Optional[MessageDirection] = None
    ) -> list[dict]:
        """Get message history with optional filtering."""
        query = "SELECT * FROM messages WHERE 1=1"
        params = []

        if sender:
            query += " AND sender = ?"
            params.append(sender)

        if direction:
            query += " AND direction = ?"
            params.append(direction.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_message_by_id(self, message_id: str) -> Optional[dict]:
        """Retrieve a specific message by ID."""
        async with self.conn.execute(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
