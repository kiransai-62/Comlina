-- 004_automations.sql
-- Automations with JSONB Flow Definition

CREATE TABLE IF NOT EXISTS automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    instagram_account_id UUID NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT', -- DRAFT, ACTIVE, PAUSED, ERROR, ARCHIVED
    trigger_type VARCHAR(64) NOT NULL,          -- COMMENT, STORY_REPLY, STORY_MENTION, DM_KEYWORD, LIVE_COMMENT
    flow_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    version INT NOT NULL DEFAULT 1,
    stats_comments INT NOT NULL DEFAULT 0,
    stats_dms_sent INT NOT NULL DEFAULT 0,
    stats_clicks INT NOT NULL DEFAULT 0,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_automations_ws ON automations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_automations_account ON automations(instagram_account_id);
CREATE INDEX IF NOT EXISTS idx_automations_status ON automations(status);
CREATE INDEX IF NOT EXISTS idx_automations_trigger ON automations(trigger_type);
