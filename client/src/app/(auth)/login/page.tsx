'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authService, AUTH_ENABLED } from '@/lib/auth';
import { isSupabaseConfigured, supabase } from '@/lib/supabase';
import {
  AuthCard,
  EmailField,
  PasswordField,
  GoogleButton,
  ErrorBanner,
} from '@/components/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!AUTH_ENABLED) {
      window.location.href = '/dashboard';
      return;
    }

    // Check if user is already authenticated
    async function checkExistingSession() {
      try {
        const isAuth = await authService.isAuthenticated();
        if (isAuth) {
          window.location.href = '/dashboard';
        }
      } catch {
        // ignore
      }
    }
    checkExistingSession();

    // Check for error parameters in query string (e.g. from OAuth redirect)
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const err = params.get('error_description') || params.get('error');
      if (err) {
        setErrorMessage(decodeURIComponent(err.replace(/_/g, ' ')));
      }
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!AUTH_ENABLED) {
      window.location.href = '/dashboard';
      return;
    }
    if (!email || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);

    try {
      const result = await authService.signInWithPassword(email, password);
      if (result.success) {
        window.location.href = '/dashboard';
      } else {
        setErrorMessage(result.error || 'Unable to sign in. Please check your credentials.');
        setLoading(false);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred during sign in.');
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="Sign in to Comlina"
      subtitle="Turn Conversations into Growth"
      footer={
        <div>
          Don&apos;t have an account?{' '}
          <Link href="/signup" className="font-semibold text-[#004020] hover:underline">
            Sign up
          </Link>
        </div>
      }
    >
      <ErrorBanner message={errorMessage} />

      <GoogleButton redirectTo="/dashboard" onError={setErrorMessage} />

      {/* Divider — only show when Google button is visible */}
      {isSupabaseConfigured && (
        <div className="relative flex items-center justify-center my-1">
          <div className="border-t border-neutral-200 w-full" />
          <span className="bg-white px-2.5 text-xs text-neutral-400 font-medium">
            or with email
          </span>
        </div>
      )}

      <form onSubmit={handleLogin} className="flex flex-col gap-4">
        <EmailField
          value={email}
          onChange={setEmail}
        />
        <PasswordField
          id="password"
          label="Password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-[#004020] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#003018] disabled:opacity-60 cursor-pointer sm:py-2.5 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Signing in...</span>
            </>
          ) : (
            <span>Sign In</span>
          )}
        </button>
      </form>

      {/* Quick Dev Login for local development & testing */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-4 pt-4 border-t border-neutral-100 flex flex-col gap-2">
          <div className="text-center text-[11px] text-neutral-400 font-medium">
            Quick Dev Login (1-Click):
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={async () => {
                setLoading(true);
                setErrorMessage(null);
                try {
                  const res = await authService.signInWithPassword('founder@comlina.ai', 'Password123!');
                  if (res.success) {
                    window.location.href = '/dashboard';
                    return;
                  }
                  setErrorMessage(res.error || 'Dev login failed.');
                } catch {
                  window.location.href = '/qa-login.html?auto=1';
                } finally {
                  setLoading(false);
                }
              }}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-2 text-xs font-semibold text-emerald-800 transition hover:bg-emerald-100 cursor-pointer disabled:opacity-50"
            >
              <span>⚡ Founder Demo</span>
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={async () => {
                setLoading(true);
                setErrorMessage(null);
                try {
                  const res = await authService.signInWithPassword('kiran@example.com', 'Password123!');
                  if (res.success) {
                    window.location.href = '/dashboard';
                    return;
                  }
                  setErrorMessage(res.error || 'Dev login failed.');
                } catch {
                  window.location.href = '/qa-login.html?auto=1';
                } finally {
                  setLoading(false);
                }
              }}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-neutral-200 bg-neutral-50 px-2 py-2 text-xs font-semibold text-neutral-800 transition hover:bg-neutral-100 cursor-pointer disabled:opacity-50"
            >
              <span>👤 Kiran (Owner)</span>
            </button>
          </div>
          <div className="text-center text-[10px] text-neutral-400">
            Dev password: <code className="bg-neutral-100 px-1 py-0.5 rounded text-neutral-600">Password123!</code>
          </div>
        </div>
      )}
    </AuthCard>
  );
}
