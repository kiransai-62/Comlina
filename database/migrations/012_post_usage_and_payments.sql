-- Migration: 012_post_usage_and_payments.sql
-- Description: Create post_usage and payment_orders tables for plan quotas and Razorpay subscriptions

CREATE TABLE IF NOT EXISTS post_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    instagram_account_id UUID REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    media_id VARCHAR(128) NOT NULL,
    dms_delivered_count INTEGER NOT NULL DEFAULT 0,
    last_delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_post_usage_workspace_media UNIQUE (workspace_id, media_id)
);

CREATE INDEX IF NOT EXISTS idx_post_usage_workspace ON post_usage(workspace_id);
CREATE INDEX IF NOT EXISTS idx_post_usage_media ON post_usage(media_id);

CREATE TABLE IF NOT EXISTS payment_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    plan_tier VARCHAR(32) NOT NULL,
    amount_paise INTEGER NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    razorpay_order_id VARCHAR(128) UNIQUE NOT NULL,
    razorpay_payment_id VARCHAR(128),
    razorpay_signature VARCHAR(255),
    status VARCHAR(32) NOT NULL DEFAULT 'CREATED',
    billing_period VARCHAR(32) NOT NULL DEFAULT 'MONTHLY',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_orders_workspace ON payment_orders(workspace_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_razorpay_order ON payment_orders(razorpay_order_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status);
