-- 003_instagram_accounts.sql
-- Connected Instagram Professional Accounts & Graph API Credentials

CREATE TABLE IF NOT EXISTS instagram_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    ig_user_id VARCHAR(64) NOT NULL, -- Instagram Scoped ID (IGSID)
    username VARCHAR(128) NOT NULL,
    account_type VARCHAR(32) NOT NULL DEFAULT 'BUSINESS', -- BUSINESS, CREATOR
    profile_pic_url TEXT,
    follower_count INT DEFAULT 0,
    access_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    permissions JSONB DEFAULT '["instagram_manage_messages", "instagram_manage_comments", "pages_show_list"]'::jsonb,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workspace_id, ig_user_id)
);

CREATE INDEX IF NOT EXISTS idx_ig_accounts_ws ON instagram_accounts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_ig_accounts_username ON instagram_accounts(username);
CREATE INDEX IF NOT EXISTS idx_ig_accounts_ig_user_id ON instagram_accounts(ig_user_id);
