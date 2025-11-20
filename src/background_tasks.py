"""Background tasks for message retry processing."""

import asyncio
from src.db.connection import get_db_connection
from src.db.models import MessageStatus
from src.db.repositories.message_repository import MessageRepository
from src.client import send_to_remote
from src.logging_config import logger

async def process_retry_queue():
    """
    Background task to retry failed outbox messages.
    Runs every 60 seconds, retries messages up to 3 times.
    """
    logger.info("Starting retry queue processor")
    max_retries = 3
    retry_interval = 60  # seconds

    while True:
        try:
            await asyncio.sleep(retry_interval)

            db_conn = get_db_connection()
            conn = await db_conn.get_async_connection()
            repo = MessageRepository(conn)

            # Get messages needing retry
            pending_messages = await repo.get_pending_outbox_messages(max_retries)

            if not pending_messages:
                logger.debug("No messages in retry queue")
                continue

            logger.info(f"Processing {len(pending_messages)} messages in retry queue")

            for msg in pending_messages:
                msg_id = msg['id']
                logger.debug(f"Retrying message {msg_id} (attempt {msg['retry_count'] + 1}/{max_retries})")

                # Increment retry count
                await repo.increment_retry_count(msg_id)

                # Attempt to resend (this creates a NEW outbox entry)
                # Actually, we should just update the existing one
                # Let me think about this differently...

                # We need to send without creating another outbox entry
                # So I'll call the HTTP logic directly here

                from urllib.parse import urlparse
                import httpx
                from src.config import get_settings
                from src.resolver import resolve_mdns

                settings = get_settings()
                base_url = settings.REMOTE_PAI_URL
                parsed = urlparse(base_url)

                # Resolve mDNS if needed
                if parsed.hostname and parsed.hostname.endswith('.local'):
                    try:
                        resolved_ip = resolve_mdns(parsed.hostname)
                        new_netloc = parsed.netloc.replace(parsed.hostname, resolved_ip)
                        base_url = parsed._replace(netloc=new_netloc).geturl()
                    except Exception as e:
                        error_msg = f"mDNS resolution failed: {str(e)}"
                        logger.warning(f"Retry {msg_id} failed at mDNS: {error_msg}")
                        if msg['retry_count'] >= max_retries:
                            await repo.update_outbox_status(msg_id, MessageStatus.FAILED, error_msg)
                        continue

                url = f"{base_url}/inbox"

                payload = {
                    "sender": msg['sender'],
                    "content": msg['content'],
                    "priority": msg['priority'],
                    "message_type": msg['message_type'],
                    "context_id": msg['context_id']
                }

                headers = {
                    "X-PAI-API-Key": settings.REMOTE_PAI_API_KEY.get_secret_value(),
                    "Host": parsed.hostname
                }

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(url, json=payload, headers=headers, timeout=5.0)
                        response.raise_for_status()

                        # Success! Update to sent
                        await repo.update_outbox_status(msg_id, MessageStatus.SENT)
                        logger.info(f"Retry successful for message {msg_id}")

                    except (httpx.HTTPStatusError, httpx.RequestError) as e:
                        error_msg = str(e)
                        logger.warning(f"Retry {msg_id} failed (attempt {msg['retry_count']}/{max_retries}): {error_msg}")

                        # If this was the last retry, mark as permanently failed
                        if msg['retry_count'] >= max_retries:
                            await repo.update_outbox_status(msg_id, MessageStatus.FAILED, f"Max retries exceeded: {error_msg}")
                            logger.error(f"Message {msg_id} permanently failed after {max_retries} retries")

        except Exception as e:
            logger.exception(f"Error in retry queue processor: {e}")
            # Continue running despite errors
            await asyncio.sleep(retry_interval)
