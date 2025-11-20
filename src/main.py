from fastapi import FastAPI, Header, HTTPException, Depends
from src.config import get_settings, Settings
from src.models import Message, MessageResponse
from src.logging_config import logger
import uuid

app = FastAPI(
    title="PAI API",
    description="API for PAI communication",
    version="1.0.0"
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
    
    # TODO: Store message
    
    return MessageResponse(
        status="received",
        id=msg_id
    )
