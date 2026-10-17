// client/src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  '';

/**
 * Returns true when real Supabase Cloud credentials are configured.
 * When false, the app uses backend-only auth (POST /api/auth/signup, /api/auth/login).
 */
export { supabaseUrl, supabaseAnonKey };

export const isSupabaseConfigured =
  !!supabaseUrl &&
  !!supabaseAnonKey &&
  !supabaseUrl.includes('placeholder') &&
  supabaseUrl.startsWith('https://');

if (!isSupabaseConfigured) {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.info(
      '[Comlina] Supabase Cloud is not configured — using backend-only authentication (POST /api/auth/signup, /api/auth/login).'
    );
  }
}

export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-anon-key'
);

