'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import { authService } from '@/lib/auth';
import { api } from '@/lib/api';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { BrandLogo } from '@/components/BrandLogo';
import { ComlinaLoadingOverlay } from '@/components/ComlinaLoadingOverlay';

export const AUTH_ENABLED = true; // Authentication guard enabled

export type AuthState = 'initializing' | 'authenticated' | 'unauthenticated' | 'error';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const setCurrentWorkspace = useWorkspaceStore((s) => s.setCurrentWorkspace);
  const isPublicRoute = 
    pathname === '/data-deletion-status' ||
    pathname === '/privacy' ||
    pathname === '/terms' ||
    pathname === '/refund' ||
    pathname === '/refund-policy' ||
    pathname === '/contact' ||
    pathname === '/legal' ||
    pathname.startsWith('/login') ||
    pathname.startsWith('/signup') ||
    pathname.startsWith('/auth');

  const [authState, setAuthState] = useState<AuthState>(
    !AUTH_ENABLED || isPublicRoute ? 'authenticated' : 'initializing'
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!AUTH_ENABLED || isPublicRoute) {
      setAuthState('authenticated');
      return;
    }

    let mounted = true;

    async function verifyAndBootstrap() {
      try {
        // --- Step 1: Check for OAuth code exchange (Supabase only) ---
        if (isSupabaseConfigured && typeof window !== 'undefined') {
          const url = new URL(window.location.href);
          const code = url.searchParams.get('code');
          if (code) {
            const { data: exchangeData, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
            if (!exchangeError && exchangeData?.session) {
              window.history.replaceState({}, document.title, url.pathname);
            }
          }
        }

        // --- Step 2: Bootstrap session with backend via GET /api/auth/me (supports HttpOnly cookies & Bearer tokens) ---
        const syncResult = await authService.syncWithBackend();

        if (syncResult?.workspace) {
          api.setWorkspaceId(syncResult.workspace.id);
          const tier = (syncResult.workspace as any).plan_tier || (syncResult.workspace as any).planTier || 'FREE';
          setCurrentWorkspace({
            id: syncResult.workspace.id,
            name: syncResult.workspace.name,
            slug: syncResult.workspace.slug,
            planTier: tier,
          });
          if (mounted) {
            setAuthState('authenticated');
          }
          return;
        }

        // If syncResult was null, check whether user has cached credentials
        const hasCachedUser = typeof window !== 'undefined' && (
          !!localStorage.getItem('comlina_user') || !!localStorage.getItem('comlina_token')
        );

        if (hasCachedUser) {
          // Cached user exists but backend sync was unreachable or errored - do not redirect to login!
          if (mounted) {
            setAuthState('error');
            setErrorMessage('Unable to reach authentication server. Please check your connection.');
          }
          return;
        }

        // No valid session or cookies - redirect to login
        if (mounted) {
          setAuthState('unauthenticated');
          router.replace('/login');
        }
      } catch (err: any) {
        console.error('AuthGuard session verification error:', err);
        if (mounted) {
          const hasCachedUser = typeof window !== 'undefined' && (
            !!localStorage.getItem('comlina_user') || !!localStorage.getItem('comlina_token')
          );
          if (hasCachedUser) {
            setAuthState('error');
            setErrorMessage('Unable to reach authentication server. Please check your connection.');
          } else {
            setAuthState('unauthenticated');
            router.replace('/login');
          }
        }
      }
    }

    verifyAndBootstrap();

    // Listen for Supabase auth state changes (only relevant when Supabase is configured)
    let unsubscribe: (() => void) | undefined;
    if (isSupabaseConfigured) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
        if (event === 'SIGNED_OUT') {
          // Verify backend token before treating as unauthenticated
          const isAuth = await authService.isAuthenticated();
          if (!isAuth && mounted) {
            setAuthState('unauthenticated');
            router.replace('/login');
          }
        } else if (session) {
          if (mounted) {
            setAuthState('authenticated');
          }
        }
      });
      unsubscribe = () => subscription.unsubscribe();
    }

    return () => {
      mounted = false;
      unsubscribe?.();
    };
  }, [router, isPublicRoute, setCurrentWorkspace]);

  if (!AUTH_ENABLED) {
    return <>{children}</>;
  }

  if (authState === 'initializing') {
    return (
      <div className="min-h-screen bg-[#FBFBFA]">
        <ComlinaLoadingOverlay isLoading={true} />
      </div>
    );
  }

  if (authState === 'error') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#FBFBFA] px-4 text-center">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-6 max-w-sm w-full shadow-xs space-y-4">
          <BrandLogo variant="mark" height={40} className="mx-auto" />
          <div>
            <h2 className="text-sm font-bold text-[#111110]">Connection Problem</h2>
            <p className="text-xs text-[#70706B] mt-1">
              {errorMessage || 'Unable to connect to the authentication server.'}
            </p>
          </div>
          <div className="flex flex-col gap-2 pt-2">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="w-full py-2 bg-[#064125] hover:bg-[#0A5A34] text-white text-xs font-bold rounded-xl transition-all cursor-pointer shadow-xs"
            >
              Retry Connection
            </button>
            <button
              type="button"
              onClick={() => authService.signOut()}
              className="w-full py-2 bg-transparent hover:bg-[#F4F4F0] text-[#70706B] hover:text-[#111110] text-xs font-semibold rounded-xl transition-colors cursor-pointer"
            >
              Sign In Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (authState === 'unauthenticated') {
    return null;
  }

  return <>{children}</>;
}
