-- 014_rls_post_usage_and_payments.sql
-- Defense-in-depth Row-Level Security for post_usage and payment_orders tables

-- Enable RLS
ALTER TABLE post_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_orders ENABLE ROW LEVEL SECURITY;

-- Post Usage policy
DROP POLICY IF EXISTS "Workspace members can access post_usage" ON post_usage;
CREATE POLICY "Workspace members can access post_usage"
    ON post_usage FOR ALL
    USING (is_workspace_member(workspace_id));

-- Payment Orders policy
DROP POLICY IF EXISTS "Workspace members can view payment_orders" ON payment_orders;
CREATE POLICY "Workspace members can view payment_orders"
    ON payment_orders FOR SELECT
    USING (is_workspace_member(workspace_id));
