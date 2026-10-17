'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authService, AUTH_ENABLED } from '@/lib/auth';
import { isSupabaseConfigured } from '@/lib/supabase';
import {
  AuthCard,
  EmailField,
  PasswordField,
  GoogleButton,
  ErrorBanner,
} from '@/components/auth';

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!AUTH_ENABLED) {
      window.location.href = '/dashboard';
      return;
    }

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
  }, []);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!AUTH_ENABLED) {
      window.location.href = '/dashboard';
      return;
    }
    if (!email || !password || !fullName) {
      setErrorMessage('Please fill in all fields.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const result = await authService.signUp(email, password, fullName);

      if (result.success) {
        if (result.needsConfirmation) {
          // Supabase Cloud requires email confirmation
          setSuccessMessage('Account created! Please check your email to confirm your account, then sign in.');
          setLoading(false);
        } else {
          // Backend auth or Supabase auto-confirm: go straight to dashboard
          window.location.href = '/dashboard';
        }
      } else {
        setErrorMessage(result.error || 'An unexpected error occurred during signup.');
        setLoading(false);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred during signup.');
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="Create your account"
      subtitle="Turn Conversations into Growth"
      footer={
        <div>
          Already have an account?{' '}
          <Link href="/login" className="font-semibold text-[#004020] hover:underline">
            Sign in
          </Link>
        </div>
      }
    >
      <ErrorBanner message={errorMessage} />

      {successMessage ? (
        <div className="rounded-xl border border-green-200 bg-green-50 p-4 text-xs text-green-800 space-y-2">
          <p className="font-medium">{successMessage}</p>
          <Link
            href="/login"
            className="inline-block font-semibold text-[#004020] hover:underline"
          >
            Proceed to Sign In →
          </Link>
        </div>
      ) : (
        <>
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

          <form onSubmit={handleSignup} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="fullName" className="text-sm font-medium text-neutral-700">
                Full Name
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Kiran Sai"
                required
                className="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-neutral-900 outline-none transition focus:border-[#004020] focus:ring-2 focus:ring-[#004020]/20 sm:py-2.5"
              />
            </div>

            <EmailField
              value={email}
              onChange={setEmail}
            />

            <PasswordField
              id="password"
              label="Password"
              value={password}
              onChange={setPassword}
              autoComplete="new-password"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#004020] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#003018] disabled:opacity-60 cursor-pointer sm:py-2.5 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Creating account...</span>
                </>
              ) : (
                <span>Create Account</span>
              )}
            </button>
          </form>
        </>
      )}
    </AuthCard>
  );
}
