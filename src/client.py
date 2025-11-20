import httpx
from urllib.parse import urlparse
from src.config import get_settings
from src.models import Message
from src.resolver import resolve_mdns
from src.db.connection import get_db_connection
from src.db.models import MessageStatus
from src.db.repositories.message_repository import MessageRepository
from src.logging_config import logger
import uuid

settings = get_settings()

async def send_to_remote(
    content: str,
    sender: str = settings.SYSTEM_NAME,
    priority: str = "normal",
    message_type: str = "text",
    context_id: str | None = None
) -> dict:
    """
    Sends a message to the remote PAI instance.
    Stores in outbox before sending, updates status after.
    Resolves mDNS .local addresses before connecting.
    """
    msg_id = str(uuid.uuid4())

    # Get database connection
    db_conn = get_db_connection()
    conn = await db_conn.get_async_connection()
    repo = MessageRepository(conn)

    # Store in outbox with pending status
    await repo.store_outbox_message(
        message_id=msg_id,
        sender=sender,
        content=content,
        message_type=message_type,
        priority=priority,
        status=MessageStatus.PENDING_SEND,
        context_id=context_id
    )

    # Parse URL to get hostname
    base_url = settings.REMOTE_PAI_URL
    parsed = urlparse(base_url)

    # Resolve hostname if it's .local
    if parsed.hostname and parsed.hostname.endswith('.local'):
        try:
            resolved_ip = resolve_mdns(parsed.hostname)
            new_netloc = parsed.netloc.replace(parsed.hostname, resolved_ip)
            base_url = parsed._replace(netloc=new_netloc).geturl()
        except Exception as e:
            error_msg = f"mDNS resolution failed: {str(e)}"
            logger.warning(error_msg)
            await repo.update_outbox_status(msg_id, MessageStatus.FAILED, error_msg)
            return {"status": "error", "details": error_msg, "id": msg_id}

    url = f"{base_url}/inbox"

    payload = {
        "sender": sender,
        "content": content,
        "priority": priority,
        "message_type": message_type,
        "context_id": context_id
    }

    headers = {
        "X-PAI-API-Key": settings.REMOTE_PAI_API_KEY.get_secret_value(),
        "Host": parsed.hostname # Preserve original host header
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            response.raise_for_status()

            # Update outbox status to sent
            await repo.update_outbox_status(msg_id, MessageStatus.SENT)
            logger.info(f"Message {msg_id} sent successfully")

            result = response.json()
            result["outbox_id"] = msg_id  # Add our outbox message ID
            return result

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            await repo.update_outbox_status(msg_id, MessageStatus.FAILED, error_msg)
            logger.error(f"Message {msg_id} failed: {error_msg}")
            return {"status": "error", "details": error_msg, "id": msg_id}

        except httpx.RequestError as e:
            error_msg = f"Connection Error: {str(e)}"
            await repo.update_outbox_status(msg_id, MessageStatus.FAILED, error_msg)
            logger.error(f"Message {msg_id} failed: {error_msg}")
            return {"status": "error", "details": error_msg, "id": msg_id}

async def check_remote_status() -> dict:
    """
    Checks the health status of the remote PAI instance.
    """
    base_url = settings.REMOTE_PAI_URL
    parsed = urlparse(base_url)
    
    if parsed.hostname and parsed.hostname.endswith('.local'):
        resolved_ip = resolve_mdns(parsed.hostname)
        new_netloc = parsed.netloc.replace(parsed.hostname, resolved_ip)
        base_url = parsed._replace(netloc=new_netloc).geturl()
    
    url = f"{base_url}/health"
    
    headers = {
        "Host": parsed.hostname
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=3.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "offline", "details": str(e)}
