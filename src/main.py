from fastapi import FastAPI, Header, HTTPException, Depends
from contextlib import asynccontextmanager
from src.config import get_settings, Settings
from src.models import Message, MessageResponse
from src.logging_config import logger
from src.db.connection import get_db_connection, get_async_db
from src.db.models import CREATE_TABLES_SQL
from src.db.repositories.message_repository import MessageRepository
from src.background_tasks import process_retry_queue
import aiosqlite
import uuid
import os
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Database lifecycle management and background tasks."""
    settings = get_settings()

    # Ensure data directory exists
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

    # Initialize database schema
    db_conn = get_db_connection()
    sync_conn = db_conn.get_sync_connection()
    try:
        sync_conn.executescript(CREATE_TABLES_SQL)
        logger.info(f"Database initialized: {settings.DB_PATH}")
    finally:
        sync_conn.close()

    # Initialize async connection
    await db_conn.get_async_connection()
    logger.info("Async database connection ready")

    # Start background retry task
    retry_task = asyncio.create_task(process_retry_queue())
    logger.info("Retry queue processor started")

    yield

    # Shutdown: Cancel background tasks
    retry_task.cancel()
    try:
        await retry_task
    except asyncio.CancelledError:
        logger.info("Retry queue processor stopped")

    # Close async connection
    await db_conn.close()
    logger.info("Database connection closed")

app = FastAPI(
    title="PAI API",
    description="API for PAI communication",
    version="1.0.0",
    lifespan=lifespan
)

async def verify_api_key(
    x_pai_api_key: str = Header(..., alias="X-PAI-API-Key"),
    settings: Settings = Depends(get_settings)
):
    if x_pai_api_key != settings.API_KEY.get_secret_value():
        logger.warning("Authentication failed: Invalid API Key")
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_pai_api_key

@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    logger.debug("Health check requested")
    return {
        "status": "online",
        "system": settings.SYSTEM_NAME,
        "version": "1.0.0"
    }

@app.post("/inbox", response_model=MessageResponse)
async def receive_message(
    message: Message,
    api_key: str = Depends(verify_api_key)
):
    msg_id = str(uuid.uuid4())
    logger.info(f"Received message from {message.sender} (Type: {message.message_type})")

    # Store message in database
    async with get_async_db() as db:
        repo = MessageRepository(db)
        await repo.store_inbox_message(
            message_id=msg_id,
            sender=message.sender,
            content=message.content,
            message_type=message.message_type,
            priority=message.priority,
            context_id=message.context_id
        )

    return MessageResponse(
        status="received",
        id=msg_id
    )

@app.get("/messages")
async def get_message_history(
    limit: int = 100,
    sender: str | None = None,
    direction: str | None = None,
    api_key: str = Depends(verify_api_key)
):
    """Retrieve message history with optional filtering."""
    from src.db.models import MessageDirection

    async with get_async_db() as db:
        repo = MessageRepository(db)

        direction_filter = None
        if direction:
            direction_filter = MessageDirection(direction)

        messages = await repo.get_message_history(
            limit=limit,
            sender=sender,
            direction=direction_filter
        )

    logger.debug(f"Retrieved {len(messages)} messages from history")
    return {"messages": messages, "count": len(messages)}
