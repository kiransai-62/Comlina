-- 009_webhook_events.sql
-- Durable Meta Webhook Deduplication & Ingestion Log

CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    instagram_account_id UUID REFERENCES instagram_accounts(id) ON DELETE SET NULL,
    provider_event_id VARCHAR(128) NOT NULL UNIQUE, -- Meta mid / comment_id / event id
    event_type VARCHAR(64) NOT NULL,                -- messages, message_reactions, feed, comments
    payload JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',  -- PENDING, PROCESSING, PROCESSED, FAILED, IGNORED
    error TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_provider_id ON webhook_events(provider_event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_received ON webhook_events(received_at DESC);
