import pytest
from unittest.mock import patch, AsyncMock
from src.client import send_to_remote

import httpx

@pytest.mark.asyncio
async def test_send_to_remote_success():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Mock response object (not AsyncMock for sync methods like json())
        mock_response = AsyncMock()
        # .json() is synchronous in httpx, so we mock it as a return_value of a standard Mock if possible
        # OR we just ensure the return value is dict, not coroutine.
        # Actually, simplest is to attach a plain Mock for json
        mock_response.json = lambda: {"status": "received", "id": "123"}
        mock_response.raise_for_status = lambda: None # Sync method
        
        mock_post.return_value = mock_response
        
        result = await send_to_remote("Hello", priority="high")
        
        assert result["status"] == "received"
        assert result["id"] == "123"

@pytest.mark.asyncio
async def test_send_to_remote_failure():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Raise a proper httpx error
        mock_post.side_effect = httpx.RequestError("Network Boom", request=None)
        
        result = await send_to_remote("Hello")
        
        assert result["status"] == "error"
        assert "Network Boom" in result["details"]

