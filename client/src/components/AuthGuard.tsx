'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import { authService } from '@/lib/auth';
import { api } from '@/lib/api';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { BrandLogo } from '@/components/BrandLogo';

export const AUTH_ENABLED = true; // Authentication guard enabled

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

  const [loading, setLoading] = useState(AUTH_ENABLED && !isPublicRoute);
  const [authenticated, setAuthenticated] = useState(!AUTH_ENABLED || isPublicRoute);

  useEffect(() => {
    if (!AUTH_ENABLED || isPublicRoute) {
      setAuthenticated(true);
      setLoading(false);
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
              // fall through to backend sync below
            }
          }
        }

        // --- Step 2: Check if we have a valid token (Supabase or backend) ---
        const hasToken = await authService.isAuthenticated();

        if (!hasToken) {
          // If Supabase is configured, brief retry for storage hydration
          if (isSupabaseConfigured) {
            await new Promise((resolve) => setTimeout(resolve, 350));
            const retryHasToken = await authService.isAuthenticated();
            if (!retryHasToken) {
              if (mounted) {
                setAuthenticated(false);
                setLoading(false);
                router.replace('/login');
              }
              return;
            }
          } else {
            if (mounted) {
              setAuthenticated(false);
              setLoading(false);
              router.replace('/login');
            }
            return;
          }
        }

        // --- Step 3: Bootstrap with backend — provision user + workspace via GET /api/auth/me ---
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
        }

        if (mounted) {
          setAuthenticated(true);
          setLoading(false);
        }
      } catch (err) {
        console.error('AuthGuard session verification error:', err);
        if (mounted) {
          setAuthenticated(false);
          setLoading(false);
          router.replace('/login');
        }
      }
    }

    verifyAndBootstrap();

    // Listen for Supabase auth state changes (only relevant when Supabase is configured)
    let unsubscribe: (() => void) | undefined;
    if (isSupabaseConfigured) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        if (event === 'SIGNED_OUT') {
          if (mounted) {
            setAuthenticated(false);
            setLoading(false);
            router.replace('/login');
          }
        } else if (session) {
          if (mounted) {
            setAuthenticated(true);
            setLoading(false);
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

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#FBFBFA]">
        <div className="flex flex-col items-center space-y-4">
          <BrandLogo variant="mark" height={48} className="animate-pulse" />
          <div className="flex items-center space-x-2 text-xs text-[#70706B] font-medium">
            <div className="w-2 h-2 rounded-full bg-[#15803D] animate-ping" />
            <span>Verifying session...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return null;
  }

  return <>{children}</>;
}
