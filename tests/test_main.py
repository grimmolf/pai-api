from fastapi.testclient import TestClient
from src.main import app
import pytest

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "system": "Bob",
        "version": "1.0.0"
    }

def test_inbox_unauthorized():
    # Missing header sends 422 by default in FastAPI
    # We want to test invalid key returns 401
    response = client.post(
        "/inbox", 
        json={"sender": "pat", "content": "hacker"},
        headers={"X-PAI-API-Key": "wrong-key"}
    )
    assert response.status_code == 401

def test_inbox_valid_message():
    # We need to mock the config or set env var, but for now let's assume default dev key
    # Actually, better to override the dependency, but let's start simple
    headers = {"X-PAI-API-Key": "dev-key"}
    payload = {
        "sender": "patterson",
        "content": "Hello Bob",
        "message_type": "text",
        "priority": "normal"
    }
    response = client.post("/inbox", json=payload, headers=headers)
    # It will fail 404 or 405 now because endpoint doesn't exist
    # But properly, we assert 200 once implemented
    assert response.status_code == 200
    assert response.json()["status"] == "received"
