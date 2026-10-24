-- 016_auth_and_webhook_subscriptions.sql
-- F13: Dedicated password_hash column on users to prevent profile updates from overwriting auth credentials.
-- F5: Webhook subscription status persistence on instagram_accounts.
-- Contact automation_state indexing for follower gating & execution tracking.

ALTER TABLE users
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(512);

ALTER TABLE instagram_accounts
ADD COLUMN IF NOT EXISTS webhook_subscription_status VARCHAR(32) DEFAULT 'UNKNOWN',
ADD COLUMN IF NOT EXISTS webhook_subscribed_at TIMESTAMPTZ;

ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS automation_state VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_contacts_automation_state ON contacts(automation_state);
CREATE INDEX IF NOT EXISTS idx_ig_accounts_webhook_sub ON instagram_accounts(webhook_subscription_status);
