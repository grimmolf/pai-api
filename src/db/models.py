"""Database models for message persistence."""

from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    TASK = "task"
    QUERY = "query"

class Priority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MessageStatus(str, Enum):
    RECEIVED = "received"
    PENDING_SEND = "pending"
    SENT = "sent"
    FAILED = "failed"

class MessageDirection(str, Enum):
    INBOX = "inbox"
    OUTBOX = "outbox"

# Database initialization DDL
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'text',
    priority TEXT NOT NULL DEFAULT 'normal',
    context_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    direction TEXT NOT NULL CHECK(direction IN ('inbox', 'outbox')),
    status TEXT CHECK(status IN ('received', 'pending', 'sent', 'failed')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry_at TIMESTAMP,
    error_message TEXT,
    CHECK(message_type IN ('text', 'task', 'query')),
    CHECK(priority IN ('normal', 'high', 'urgent'))
);

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_messages_context_id ON messages(context_id);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(direction);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- Composite index for outbox retry queries
CREATE INDEX IF NOT EXISTS idx_outbox_retry
ON messages(direction, status, retry_count)
WHERE direction = 'outbox' AND status IN ('pending', 'failed');

-- Trigger to update updated_at on row changes
CREATE TRIGGER IF NOT EXISTS update_message_timestamp
AFTER UPDATE ON messages
FOR EACH ROW
BEGIN
    UPDATE messages SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""
