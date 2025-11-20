"""Database connection management with dual sync/async support."""

import aiosqlite
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from src.config import get_settings
from src.logging_config import logger

settings = get_settings()

class DatabaseConnection:
    """
    Centralized database connection manager.
    Provides both sync (for migrations/init) and async (for runtime) access.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._async_connection: aiosqlite.Connection | None = None

    # === SYNC CONNECTION (Migrations, Startup Checks) ===

    def get_sync_connection(self) -> sqlite3.Connection:
        """
        Get a synchronous connection for migrations or startup tasks.
        Caller is responsible for closing the connection.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    # === ASYNC CONNECTION (Runtime Operations) ===

    async def get_async_connection(self) -> aiosqlite.Connection:
        """
        Get or create the async connection singleton.
        Reuses connection across requests for efficiency.
        """
        if self._async_connection is None:
            self._async_connection = await aiosqlite.connect(
                self.db_path,
                isolation_level=None  # Autocommit mode for explicit transactions
            )
            self._async_connection.row_factory = aiosqlite.Row
            await self._async_connection.execute("PRAGMA foreign_keys = ON")
            await self._async_connection.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            logger.debug(f"Async database connection established: {self.db_path}")
        return self._async_connection

    async def close(self):
        """Close the async connection during shutdown."""
        if self._async_connection:
            await self._async_connection.close()
            self._async_connection = None
            logger.debug("Async database connection closed")

# Global singleton instance
_db_connection: DatabaseConnection | None = None

def get_db_connection() -> DatabaseConnection:
    """Get the global database connection manager."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection(settings.DB_PATH)
    return _db_connection

@asynccontextmanager
async def get_async_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Dependency injection helper for FastAPI endpoints.

    Usage:
        async def endpoint(db: aiosqlite.Connection = Depends(get_async_db)):
            ...
    """
    db_conn = get_db_connection()
    connection = await db_conn.get_async_connection()
    try:
        yield connection
    except Exception as e:
        logger.error(f"Database error in request: {e}")
        await connection.rollback()
        raise
