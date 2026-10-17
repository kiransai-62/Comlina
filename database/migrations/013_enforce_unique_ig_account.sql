-- 013_enforce_unique_ig_account.sql
-- Enforce strict 1-to-1 mapping: Each Instagram Account (ig_user_id) can only link to a single workspace/user.

DROP INDEX IF EXISTS idx_ig_accounts_ig_user_id;
CREATE UNIQUE INDEX IF NOT EXISTS uq_ig_accounts_ig_user_id ON instagram_accounts(ig_user_id);
