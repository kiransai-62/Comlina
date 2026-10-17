-- 001_users.sql
-- Comlina Core User Directory (Integrated with Supabase Auth auth.users)

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY, -- Maps to auth.users.id
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    timezone VARCHAR(64) DEFAULT 'UTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
