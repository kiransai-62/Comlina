-- 006_contacts.sql
-- Contacts Directory with 4-State Follower Tracking & Captured Leads

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    instagram_account_id UUID NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    ig_user_id VARCHAR(64) NOT NULL, -- Instagram Scoped ID (IGSID)
    username VARCHAR(128) NOT NULL,
    full_name VARCHAR(255),
    profile_pic_url TEXT,
    email VARCHAR(255),
    phone VARCHAR(64),
    -- 4 explicit follower states: UNKNOWN, FOLLOWING, NOT_FOLLOWING, CHECK_UNAVAILABLE
    follower_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
    is_converted BOOLEAN NOT NULL DEFAULT FALSE,
    interaction_count INT NOT NULL DEFAULT 1,
    tags JSONB NOT NULL DEFAULT '["lead"]'::jsonb,
    custom_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    notes TEXT,
    last_interaction_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workspace_id, instagram_account_id, ig_user_id)
);

CREATE INDEX IF NOT EXISTS idx_contacts_ws ON contacts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_contacts_username ON contacts(username);
CREATE INDEX IF NOT EXISTS idx_contacts_follower_status ON contacts(follower_status);
CREATE INDEX IF NOT EXISTS idx_contacts_converted ON contacts(is_converted);
