-- 011_row_level_security.sql
-- Defense-in-depth Row-Level Security (RLS) policies for Supabase / PostgreSQL

-- Enable RLS on multi-tenant and system tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE instagram_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE automations ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY; -- No public policies: restricted to backend service_role only

-- Helper function to check if current authenticated user belongs to workspace
-- Hardened with SECURITY DEFINER and fixed search_path = public to prevent schema search_path hijacking
CREATE OR REPLACE FUNCTION is_workspace_member(ws_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM workspace_members
        WHERE workspace_id = ws_id
        AND user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Users policy: users can only view their own profile
CREATE POLICY "own profile" ON users FOR SELECT USING (id = auth.uid());

-- Workspaces policy
CREATE POLICY "Users can view workspaces they are members of"
    ON workspaces FOR SELECT
    USING (is_workspace_member(id));

-- Workspace Members policy
CREATE POLICY "Users can view members of their workspaces"
    ON workspace_members FOR SELECT
    USING (is_workspace_member(workspace_id));

-- Instagram Accounts policy
CREATE POLICY "Workspace members can access connected accounts"
    ON instagram_accounts FOR ALL
    USING (is_workspace_member(workspace_id));

-- Automations policy
CREATE POLICY "Workspace members can access automations"
    ON automations FOR ALL
    USING (is_workspace_member(workspace_id));

-- Automation Versions policy
CREATE POLICY "Workspace members can access automation versions"
    ON automation_versions FOR ALL
    USING (is_workspace_member(workspace_id));

-- Contacts policy
CREATE POLICY "Workspace members can access contacts"
    ON contacts FOR ALL
    USING (is_workspace_member(workspace_id));

-- Conversations policy
CREATE POLICY "Workspace members can access conversations"
    ON conversations FOR ALL
    USING (is_workspace_member(workspace_id));

-- Messages policy
CREATE POLICY "Workspace members can access messages"
    ON messages FOR ALL
    USING (is_workspace_member(workspace_id));

-- Analytics Events policy
CREATE POLICY "Workspace members can view analytics"
    ON analytics_events FOR SELECT
    USING (is_workspace_member(workspace_id));
