'use client';

import { useState } from 'react';
import { supabase, isSupabaseConfigured, supabaseUrl } from '@/lib/supabase';

export interface GoogleButtonProps {
  redirectTo?: string;
  onError?: (message: string) => void;
}

export function GoogleButton({ redirectTo = '/dashboard', onError }: GoogleButtonProps) {
  const [loading, setLoading] = useState(false);

  // If Supabase isn't configured at all, do not render
  if (!isSupabaseConfigured) {
    return null;
  }

  async function handleClick() {
    setLoading(true);
    onError?.('');

    // Pre-flight check: ensure the Supabase endpoint is reachable
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      await fetch(`${supabaseUrl}/auth/v1/health`, {
        signal: controller.signal,
        mode: 'no-cors',
      });
      clearTimeout(timeoutId);
    } catch {
      setLoading(false);
      const msg = `Google OAuth is currently unavailable: The configured Supabase endpoint (${supabaseUrl}) could not be reached. Please sign in below using email/password or use the 1-Click Dev Login.`;
      onError?.(msg);
      return;
    }

    const target = redirectTo.startsWith('/') ? redirectTo : `/${redirectTo}`;
    const redirectUrl = typeof window !== 'undefined'
      ? `${window.location.origin}/auth/callback?next=${encodeURIComponent(target)}`
      : '/dashboard';

    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: redirectUrl,
          queryParams: { access_type: 'offline', prompt: 'consent' },
        },
      });
      if (error) {
        console.error('Google OAuth sign-in error:', error);
        onError?.(error.message);
        setLoading(false);
      }
    } catch (err: any) {
      console.error('Google OAuth exception:', err);
      onError?.(err?.message || 'Google OAuth failed to start');
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className="flex w-full items-center justify-center gap-2 rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:opacity-60 cursor-pointer sm:py-2.5"
    >
      <GoogleIcon />
      {loading ? 'Connecting Google…' : 'Continue with Google'}
    </button>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" className="shrink-0">
      <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.85.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z" />
      <path fill="#FBBC05" d="M3.97 10.72A5.4 5.4 0 0 1 3.68 9c0-.6.1-1.18.29-1.72V4.95H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.05l3.01-2.33z" />
      <path fill="#EA4335" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.59-2.59C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z" />
    </svg>
  );
}
