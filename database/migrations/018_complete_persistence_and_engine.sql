-- database/migrations/016_complete_persistence_and_engine.sql
-- Purpose: Permanent persistence columns, indexes, and RLS compatibility for
-- Instagram account connections, automations, and webhook execution audit logs.

BEGIN;

-- 1. Enhance instagram_accounts for persistent OAuth & dual-ID webhook lookup
ALTER TABLE instagram_accounts
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS ig_business_account_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS token_type VARCHAR(32) NOT NULL DEFAULT 'long_lived',
    ADD COLUMN IF NOT EXISTS connection_status VARCHAR(32) NOT NULL DEFAULT 'CONNECTED',
    ADD COLUMN IF NOT EXISTS is_connected BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS last_validated_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_error TEXT;

UPDATE instagram_accounts
SET ig_business_account_id = ig_user_id
WHERE ig_business_account_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_instagram_accounts_ig_user_id
    ON instagram_accounts(ig_user_id);

CREATE INDEX IF NOT EXISTS idx_instagram_accounts_ig_business_id
    ON instagram_accounts(ig_business_account_id);

CREATE INDEX IF NOT EXISTS idx_instagram_accounts_workspace_status
    ON instagram_accounts(workspace_id, connection_status);

-- 2. Enhance automations table with explicit structured columns + idempotency
ALTER TABLE automations
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS media_id VARCHAR(100) NOT NULL DEFAULT 'ALL',
    ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(32) NOT NULL DEFAULT 'SPECIFIC_WORDS',
    ADD COLUMN IF NOT EXISTS match_mode VARCHAR(32) NOT NULL DEFAULT 'CONTAINS',
    ADD COLUMN IF NOT EXISTS keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS follow_condition JSONB NOT NULL DEFAULT '{"enabled": false}'::jsonb,
    ADD COLUMN IF NOT EXISTS response_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Backfill existing rows from flow_definition JSONB
UPDATE automations
SET
    is_active = (status = 'ACTIVE'),
    media_id = COALESCE(
        NULLIF(media_id, 'ALL'),
        flow_definition->'trigger'->>'media_id',
        flow_definition->'trigger'->>'post_id',
        'ALL'
    ),
    trigger_type = CASE
        WHEN UPPER(COALESCE(flow_definition->'trigger'->>'trigger_type', flow_definition->'trigger'->>'type', ''))
             IN ('ANY_WORD', 'ANY', 'COMMENT_ANY', 'ALL_COMMENTS')
        THEN 'ANY_WORD'
        ELSE 'SPECIFIC_WORDS'
    END,
    keywords = COALESCE(flow_definition->'trigger'->'keywords', '[]'::jsonb),
    follow_condition = COALESCE(flow_definition->'follow_condition', '{"enabled": false}'::jsonb),
    response_config = COALESCE(
        NULLIF(response_config, '{}'::jsonb),
        jsonb_build_object('actions', COALESCE(flow_definition->'actions', '[]'::jsonb))
    );

CREATE INDEX IF NOT EXISTS idx_automations_execution_lookup
    ON automations(instagram_account_id, is_active, status, media_id);

CREATE INDEX IF NOT EXISTS idx_automations_workspace_created
    ON automations(workspace_id, created_at DESC);

-- 3. Add comment execution deduplication table to guarantee at-most-once action per (automation_id, comment_id)
CREATE TABLE IF NOT EXISTS automation_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    automation_id UUID NOT NULL REFERENCES automations(id) ON DELETE CASCADE,
    instagram_account_id UUID NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    comment_id VARCHAR(100) NOT NULL,
    media_id VARCHAR(100),
    commenter_ig_id VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(32) NOT NULL,
    matched_keyword VARCHAR(255),
    follower_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
    execution_status VARCHAR(32) NOT NULL, -- 'SUCCESS', 'FOLLOW_GATE_SENT', 'SKIPPED', 'FAILED'
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(automation_id, comment_id)
);

CREATE INDEX IF NOT EXISTS idx_automation_executions_workspace
    ON automation_executions(workspace_id, created_at DESC);

ALTER TABLE automation_executions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_automation_executions ON automation_executions;
CREATE POLICY tenant_isolation_automation_executions ON automation_executions
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

COMMIT;
