import httpx
from urllib.parse import urlparse
from src.config import get_settings
from src.models import Message
from src.resolver import resolve_mdns

settings = get_settings()

async def send_to_remote(
    content: str, 
    sender: str = settings.SYSTEM_NAME,
    priority: str = "normal", 
    message_type: str = "text"
) -> dict:
    """
    Sends a message to the remote PAI instance.
    Resolves mDNS .local addresses before connecting.
    """
    # Parse URL to get hostname
    base_url = settings.REMOTE_PAI_URL
    parsed = urlparse(base_url)
    
    # Resolve hostname if it's .local
    if parsed.hostname and parsed.hostname.endswith('.local'):
        resolved_ip = resolve_mdns(parsed.hostname)
        # Reconstruct URL with IP but keep Host header for virtual hosts if needed
        # Actually, usually safer to just let httpx handle it if system resolver works,
        # but here we replace the netloc in the URL
        new_netloc = parsed.netloc.replace(parsed.hostname, resolved_ip)
        base_url = parsed._replace(netloc=new_netloc).geturl()
    
    url = f"{base_url}/inbox"
    
    payload = {
        "sender": sender,
        "content": content,
        "priority": priority,
        "message_type": message_type
    }
    
    headers = {
        "X-PAI-API-Key": settings.REMOTE_PAI_API_KEY.get_secret_value(),
        "Host": parsed.hostname # Preserve original host header
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
