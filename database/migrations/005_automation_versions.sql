-- 005_automation_versions.sql
-- Immutable Automation Version Snapshots for Safe Background Worker Execution

CREATE TABLE IF NOT EXISTS automation_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    automation_id UUID NOT NULL REFERENCES automations(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    version INT NOT NULL,
    flow_definition JSONB NOT NULL,
    trigger_type VARCHAR(64) NOT NULL,
    published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(automation_id, version)
);

CREATE INDEX IF NOT EXISTS idx_auto_versions_auto ON automation_versions(automation_id);
CREATE INDEX IF NOT EXISTS idx_auto_versions_ws ON automation_versions(workspace_id);
