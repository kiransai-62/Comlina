-- ==============================================================================
-- COMLINA MULTI-TENANT ISOLATION & ROW LEVEL SECURITY (RLS) MIGRATION
-- Migration: 003_enable_rls_and_revoke_public_grants.sql
-- Status: NOT EXECUTED (Prepared for manual or operator-guided deployment)
-- ==============================================================================
--
-- ARCHITECTURAL DECISION:
-- 1. Primary Control: Application-Layer Tenant Authorization (FastAPI)
--    The Comlina backend connects to PostgreSQL as a pooled application service role
--    (e.g., 'postgres' or 'service_role') which by design bypasses RLS in Postgres.
--    Tenant boundaries are strictly enforced in application code via:
--      - Authenticated JWT subject resolution (get_current_user)
--      - Validated workspace membership join (get_current_workspace)
--      - Explicit WHERE filters on workspace_id for all database queries and mutations.
--
-- 2. Secondary Defense-in-Depth Control: Database-Level Row-Level Security (RLS)
--    Enables RLS policies across all tenant-scoped tables keyed on the authenticated
--    Supabase user ID (auth.uid()). If queries are executed with scoped credentials
--    or set_config('request.jwt.claims', ...), Postgres enforces these policies.
--
-- 3. Revocation of Public Grants:
--    Revokes direct SELECT/INSERT/UPDATE/DELETE access to public schema tables
--    from 'anon' and 'authenticated' roles. All operations MUST proceed through
--    the audited FastAPI backend API.
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. REVOKE PUBLIC & POSTGREST CLIENT GRANTS ON PUBLIC SCHEMA
-- ------------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON ROUTINES FROM anon, authenticated;

-- ------------------------------------------------------------------------------
-- 2. ENABLE ROW-LEVEL SECURITY ON ALL TENANT-SCOPED TABLES
-- ------------------------------------------------------------------------------
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE instagram_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE automations ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_orders ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- 3. DEFINE ROW-LEVEL SECURITY POLICIES
-- ------------------------------------------------------------------------------

-- Workspaces: User can access workspace if they are an active member
DROP POLICY IF EXISTS p_workspaces_tenant_isolation ON workspaces;
CREATE POLICY p_workspaces_tenant_isolation ON workspaces
    FOR ALL
    USING (
        id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Workspace Members: User can see memberships within their own workspaces
DROP POLICY IF EXISTS p_workspace_members_isolation ON workspace_members;
CREATE POLICY p_workspace_members_isolation ON workspace_members
    FOR ALL
    USING (
        user_id = auth.uid() OR
        workspace_id IN (
            SELECT wm.workspace_id FROM workspace_members wm
            WHERE wm.user_id = auth.uid()
        )
    );

-- Instagram Accounts: Scoped to workspace membership
DROP POLICY IF EXISTS p_instagram_accounts_isolation ON instagram_accounts;
CREATE POLICY p_instagram_accounts_isolation ON instagram_accounts
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Automations: Scoped to workspace membership
DROP POLICY IF EXISTS p_automations_isolation ON automations;
CREATE POLICY p_automations_isolation ON automations
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Automation Versions: Scoped to workspace membership
DROP POLICY IF EXISTS p_automation_versions_isolation ON automation_versions;
CREATE POLICY p_automation_versions_isolation ON automation_versions
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Contacts: Scoped to workspace membership
DROP POLICY IF EXISTS p_contacts_isolation ON contacts;
CREATE POLICY p_contacts_isolation ON contacts
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Conversations: Scoped to workspace membership
DROP POLICY IF EXISTS p_conversations_isolation ON conversations;
CREATE POLICY p_conversations_isolation ON conversations
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Messages: Scoped to workspace membership
DROP POLICY IF EXISTS p_messages_isolation ON messages;
CREATE POLICY p_messages_isolation ON messages
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Webhook Events: Scoped to workspace membership
DROP POLICY IF EXISTS p_webhook_events_isolation ON webhook_events;
CREATE POLICY p_webhook_events_isolation ON webhook_events
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Analytics Events: Scoped to workspace membership
DROP POLICY IF EXISTS p_analytics_events_isolation ON analytics_events;
CREATE POLICY p_analytics_events_isolation ON analytics_events
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Post Usage: Scoped to workspace membership
DROP POLICY IF EXISTS p_post_usage_isolation ON post_usage;
CREATE POLICY p_post_usage_isolation ON post_usage
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

-- Payment Orders: Scoped to workspace membership
DROP POLICY IF EXISTS p_payment_orders_isolation ON payment_orders;
CREATE POLICY p_payment_orders_isolation ON payment_orders
    FOR ALL
    USING (
        workspace_id IN (
            SELECT workspace_id FROM workspace_members
            WHERE user_id = auth.uid()
        )
    );

COMMIT;
