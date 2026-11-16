-- database/migrations/019_fix_rls_dual_auth_and_public_grants.sql
-- Purpose: Fix fatal 22P02 UUID cast crash in RLS helper function is_workspace_member(),
-- support dual authentication contexts (Supabase auth.uid() + FastAPI app.current_user_id),
-- and grant safe schema permissions to authenticated & anon roles so API Gateway & Realtime do not fail.

BEGIN;

-- 1. Dual-Context App User ID Resolver
-- Supports BOTH Supabase PostgREST/Realtime (`auth.uid()`) AND FastAPI (`app.current_user_id`)
-- Safely trims empty string `""` before casting to avoid `22P02 invalid input syntax for type uuid: ""`
CREATE OR REPLACE FUNCTION public.current_app_user_id()
RETURNS UUID
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    raw_setting TEXT;
    supa_uid UUID;
BEGIN
    -- 1. Try Supabase native auth.uid() first
    BEGIN
        supa_uid := auth.uid();
        IF supa_uid IS NOT NULL THEN
            RETURN supa_uid;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        supa_uid := NULL;
    END;

    -- 2. Fallback to FastAPI session variable `app.current_user_id`
    raw_setting := NULLIF(BTRIM(current_setting('app.current_user_id', true)), '');
    IF raw_setting IS NULL THEN
        RETURN NULL;
    END IF;

    RETURN raw_setting::UUID;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$;

-- 2. Update is_workspace_member to use current_app_user_id()
CREATE OR REPLACE FUNCTION public.is_workspace_member(ws_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    active_uid UUID;
BEGIN
    active_uid := public.current_app_user_id();
    IF active_uid IS NULL OR ws_id IS NULL THEN
        RETURN FALSE;
    END IF;

    RETURN EXISTS (
        SELECT 1
        FROM public.workspace_members wm
        WHERE wm.workspace_id = ws_id
          AND wm.user_id = active_uid
    );
END;
$$;

-- 3. Restore safe authenticated grants so Supabase API Gateway & Realtime don't 500
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated, service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, service_role;

-- 4. Ensure all persistent Instagram & Automation columns exist (Migration 016/018)
ALTER TABLE public.instagram_accounts
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS ig_business_account_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS token_type VARCHAR(32) NOT NULL DEFAULT 'long_lived',
    ADD COLUMN IF NOT EXISTS connection_status VARCHAR(32) NOT NULL DEFAULT 'CONNECTED',
    ADD COLUMN IF NOT EXISTS is_connected BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS last_validated_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_error TEXT;

ALTER TABLE public.automations
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS media_id VARCHAR(100) NOT NULL DEFAULT 'ALL',
    ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(32) NOT NULL DEFAULT 'SPECIFIC_WORDS',
    ADD COLUMN IF NOT EXISTS match_mode VARCHAR(32) NOT NULL DEFAULT 'CONTAINS',
    ADD COLUMN IF NOT EXISTS keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS follow_condition JSONB NOT NULL DEFAULT '{"enabled": false}'::jsonb,
    ADD COLUMN IF NOT EXISTS response_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

COMMIT;
