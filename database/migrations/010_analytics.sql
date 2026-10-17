-- 010_analytics.sql
-- Analytics Events & Aggregated Daily Performance Metrics

CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    instagram_account_id UUID NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    automation_id UUID REFERENCES automations(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL, -- COMMENT_RECEIVED, DM_SENT, LINK_CLICKED, LEAD_CAPTURED, CONVERSION
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_ws ON analytics_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_analytics_auto ON analytics_events(automation_id);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics_events(created_at DESC);
