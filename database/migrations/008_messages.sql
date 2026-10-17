-- 008_messages.sql
-- Direct Messages & Automated Dispatches

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(16) NOT NULL, -- CONTACT, INSTAGRAM_ACCOUNT, BOT
    text TEXT NOT NULL,
    media_url TEXT,
    meta_message_id VARCHAR(128),
    automation_id UUID REFERENCES automations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_ws ON messages(workspace_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at ASC);
