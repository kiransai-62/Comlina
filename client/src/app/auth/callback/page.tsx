'use client';

import React, { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { BrandLogo } from '@/components/BrandLogo';

export default function AuthCallbackPage() {
  const [statusMessage, setStatusMessage] = useState('Completing secure sign-in...');

  useEffect(() => {
    let mounted = true;

    async function handleAuthCallback() {
      try {
        if (typeof window === 'undefined') return;

        const url = new URL(window.location.href);
        const searchParams = url.searchParams;

        // Check for OAuth error returned in query string
        const error = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');
        if (error) {
          const detail = errorDescription || error;
          window.location.href = `/login?error=${encodeURIComponent(detail)}`;
          return;
        }

        // Get the post-login destination URL
        const nextParam = searchParams.get('next') || '/dashboard';
        const targetUrl = nextParam.startsWith('/') ? nextParam : `/${nextParam}`;

        // If PKCE authorization code is present in query string
        const code = searchParams.get('code');
        if (code) {
          setStatusMessage('Verifying authentication credentials...');
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            console.error('OAuth code exchange failed:', exchangeError);
            if (mounted) {
              window.location.href = `/login?error=${encodeURIComponent(exchangeError.message)}`;
            }
            return;
          }
          if (mounted) {
            window.location.href = targetUrl;
          }
          return;
        }

        // If session is already available or delivered via hash
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          if (mounted) {
            window.location.href = targetUrl;
          }
          return;
        }

        // Listen for sign in state change event
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, currentSession) => {
          if ((event === 'SIGNED_IN' || event === 'INITIAL_SESSION') && currentSession) {
            if (mounted) {
              window.location.href = targetUrl;
            }
          }
        });

        // Safety fallback timer if OAuth does not resolve within 4 seconds
        const timeout = setTimeout(async () => {
          const { data: { session: retrySession } } = await supabase.auth.getSession();
          if (retrySession && mounted) {
            window.location.href = targetUrl;
          } else if (mounted) {
            subscription.unsubscribe();
            window.location.href = '/login?error=' + encodeURIComponent('Authentication session could not be established. Please try again.');
          }
        }, 4000);

        return () => {
          subscription.unsubscribe();
          clearTimeout(timeout);
        };
      } catch (err: any) {
        console.error('Unexpected error in auth callback:', err);
        if (mounted) {
          window.location.href = `/login?error=${encodeURIComponent(err.message || 'Authentication failed')}`;
        }
      }
    }

    handleAuthCallback();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#FAFAF8] px-4">
      <div className="flex flex-col items-center space-y-4 max-w-sm text-center">
        <BrandLogo variant="mark" height={48} className="animate-pulse" />
        <div className="flex items-center space-x-2 text-sm text-[#70706B] font-medium">
          <div className="w-2.5 h-2.5 rounded-full bg-[#004020] animate-ping" />
          <span>{statusMessage}</span>
        </div>
        <p className="text-xs text-neutral-400">
          Redirecting to your dashboard in just a moment...
        </p>
      </div>
    </div>
  );
}
