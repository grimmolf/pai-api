from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID

class Message(BaseModel):
    sender: str = Field(..., min_length=1, description="Identity of the sender (e.g., 'Bob', 'Patterson')")
    content: str = Field(..., min_length=1, description="The actual text content of the message")
    message_type: Literal['text', 'task', 'query'] = Field(default='text', description="Category of the message")
    priority: Literal['normal', 'high', 'urgent'] = Field(default='normal', description="Urgency level")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of creation")
    context_id: Optional[str] = Field(default=None, description="Optional context or thread ID for tracking")

class MessageResponse(BaseModel):
    status: str
    id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
