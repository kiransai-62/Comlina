-- 015_instagram_account_persistence.sql
-- Persistent Instagram Connection State & Lifecycle Tracking

ALTER TABLE instagram_accounts
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS auth_method VARCHAR(64) NOT NULL DEFAULT 'META_INSTAGRAM_OAUTH',
ADD COLUMN IF NOT EXISTS connection_status VARCHAR(32) NOT NULL DEFAULT 'CONNECTED',
ADD COLUMN IF NOT EXISTS last_validated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_error_code VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_ig_accounts_user_id ON instagram_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_ig_accounts_status ON instagram_accounts(connection_status);
