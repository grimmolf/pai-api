import httpx
from src.config import get_settings
from src.models import Message

settings = get_settings()

async def send_to_remote(
    content: str, 
    sender: str = settings.SYSTEM_NAME,
    priority: str = "normal", 
    message_type: str = "text"
) -> dict:
    """
    Sends a message to the remote PAI instance.
    """
    url = f"{settings.REMOTE_PAI_URL}/inbox"
    
    payload = {
        "sender": sender,
        "content": content,
        "priority": priority,
        "message_type": message_type
    }
    
    headers = {
        "X-PAI-API-Key": settings.REMOTE_PAI_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"status": "error", "details": f"HTTP Error: {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "details": f"Connection Error: {str(e)}"}

