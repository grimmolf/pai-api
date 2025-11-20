from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Message(BaseModel):
    sender: str
    content: str
    message_type: str = "text"
    priority: str = "normal"
    timestamp: datetime = Field(default_factory=datetime.now)
    context_id: Optional[str] = None

class MessageResponse(BaseModel):
    status: str
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)

