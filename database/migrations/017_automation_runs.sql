-- 017_automation_runs.sql
-- Audit log of automation action executions, attempt tracking, and stuck-event sweeping

CREATE TABLE IF NOT EXISTS automation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    instagram_account_id UUID REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    ig_account_id VARCHAR(255),
    event_id VARCHAR(255) NOT NULL,
    automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
    automation_version_id UUID REFERENCES automation_versions(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    meta_error_code VARCHAR(100),
    meta_error_subcode VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_automation_runs_workspace ON automation_runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_automation_runs_event_auto ON automation_runs(event_id, automation_id);
CREATE INDEX IF NOT EXISTS idx_automation_runs_created_at ON automation_runs(created_at DESC);

-- Enable Row-Level Security
ALTER TABLE automation_runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Workspace members can access automation_runs" ON automation_runs;
CREATE POLICY "Workspace members can access automation_runs"
    ON automation_runs FOR ALL
    USING (workspace_id IS NULL OR is_workspace_member(workspace_id));

-- Add attempt_count and updated_at to webhook_events for stuck-event sweeper
ALTER TABLE webhook_events
ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 1,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

-- Support atomic quota tracking and account lookups on post_usage
ALTER TABLE post_usage
ADD COLUMN IF NOT EXISTS ig_account_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS max_dms INTEGER;
