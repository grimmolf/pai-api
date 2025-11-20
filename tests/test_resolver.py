import pytest
from unittest.mock import patch, AsyncMock
from src.client import send_to_remote
from src.resolver import resolve_mdns
import httpx

def test_resolver_passthrough():
    assert resolve_mdns("google.com") == "google.com"
    assert resolve_mdns("192.168.1.1") == "192.168.1.1"

@patch("socket.gethostbyname")
def test_resolver_mdns(mock_gethost):
    mock_gethost.return_value = "192.168.0.100"
    assert resolve_mdns("test.local") == "192.168.0.100"
    mock_gethost.assert_called_with("test.local")

@pytest.mark.asyncio
async def test_send_to_remote_resolves_mdns():
    # Mock resolution
    with patch("src.client.resolve_mdns") as mock_resolve:
        mock_resolve.return_value = "192.168.0.99"
        
        # Mock HTTPX
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = AsyncMock()
            mock_response.json = lambda: {"status": "ok"}
            mock_response.raise_for_status = lambda: None
            mock_post.return_value = mock_response
            
            # Assuming settings.REMOTE_PAI_URL is configured to something with .local in tests or we override it
            with patch("src.client.settings") as mock_settings:
                mock_settings.REMOTE_PAI_URL = "http://myhost.local:8000"
                mock_settings.REMOTE_PAI_API_KEY.get_secret_value.return_value = "key"
                mock_settings.SYSTEM_NAME = "Bob"
                
                await send_to_remote("hello")
                
                # Verify URL was rewritten to IP
                call_args = mock_post.call_args
                assert "http://192.168.0.99:8000/inbox" in call_args[0][0]
                # Verify Host header preserved
                assert call_args[1]["headers"]["Host"] == "myhost.local"

