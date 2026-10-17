// client/src/lib/auth.ts
import { supabase, isSupabaseConfigured } from './supabase';
import { api } from './api';
import type { Session } from '@supabase/supabase-js';

export interface AuthUser {
  id: string;
  email: string;
  fullName?: string;
}

export interface BackendAuthResponse {
  access_token: string;
  token_type: string;
  user: { id: string; email: string; full_name?: string };
  workspace?: { id: string; name: string; slug: string } | null;
}

export const AUTH_ENABLED = true;

/**
 * Hybrid AuthService:
 *  - If Supabase Cloud is configured → uses Supabase Auth SDK
 *  - If not → authenticates directly against FastAPI POST /api/auth/signup + /api/auth/login
 */
class AuthService {
  // Backend-only auth: store token + user in memory + localStorage
  private _backendToken: string | null = null;
  private _backendUser: AuthUser | null = null;

  constructor() {
    // Restore backend token from localStorage on init
    if (typeof window !== 'undefined') {
      this._backendToken = localStorage.getItem('comlina_token');
      const storedUser = localStorage.getItem('comlina_user');
      if (storedUser) {
        try {
          this._backendUser = JSON.parse(storedUser);
        } catch {
          // ignore
        }
      }
    }
  }

  // ---------- Session / Token ----------

  async getSession(): Promise<Session | null> {
    if (!AUTH_ENABLED) return null;
    if (typeof window === 'undefined') return null;

    // If Supabase is configured, try Supabase first
    if (isSupabaseConfigured) {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (!error && session) return session;
      } catch {
        // fall through to backend token
      }
    }

    // Backend-only mode: synthesize a minimal Session-like object if we have a token
    // (returns null so callers fall through to getToken() which returns the backend token)
    return null;
  }

  async getToken(): Promise<string | null> {
    if (typeof window === 'undefined') return null;

    // Try Supabase first
    if (isSupabaseConfigured) {
      try {
        const session = await this.getSession();
        if (session?.access_token) return session.access_token;
      } catch {
        // fall through
      }
    }

    // Backend token fallback
    return this._backendToken;
  }

  async getUser(): Promise<AuthUser | null> {
    if (!AUTH_ENABLED) return null;

    // Supabase user
    if (isSupabaseConfigured) {
      const session = await this.getSession();
      if (session?.user) {
        const user = session.user;
        return {
          id: user.id,
          email: user.email || '',
          fullName: user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || '',
        };
      }
    }

    // Backend user
    return this._backendUser;
  }

  async isAuthenticated(): Promise<boolean> {
    if (!AUTH_ENABLED) return true;
    const token = await this.getToken();
    return !!token;
  }

  // ---------- Hybrid Sign Up ----------

  async signUp(email: string, password: string, fullName?: string): Promise<{ success: boolean; error?: string; needsConfirmation?: boolean }> {
    // Try Supabase first if configured
    if (isSupabaseConfigured) {
      try {
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { data: { full_name: fullName?.trim() || '' } },
        });
        if (!error && data?.session) {
          return { success: true };
        }
        if (!error && data?.user) {
          return { success: true, needsConfirmation: true };
        }
        if (error) {
          // If Supabase is unreachable (network error), fall through to backend
          if (error.message?.includes('fetch') || error.message?.includes('network') || error.status === 0) {
            console.warn('[Auth] Supabase unreachable, falling back to backend signup');
          } else {
            return { success: false, error: error.message };
          }
        }
      } catch {
        console.warn('[Auth] Supabase signup threw, falling back to backend');
      }
    }

    // Backend signup
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const resp = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password, full_name: fullName?.trim() || '' }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        return { success: false, error: body.detail || `Signup failed (${resp.status})` };
      }
      const data: BackendAuthResponse = await resp.json();
      this._setBackendAuth(data);
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Network error during signup' };
    }
  }

  // ---------- Hybrid Sign In ----------

  async signInWithPassword(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    // Try Supabase first if configured
    if (isSupabaseConfigured) {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (!error && data?.session) {
          return { success: true };
        }
        if (error) {
          if (error.message?.includes('fetch') || error.message?.includes('network') || error.status === 0) {
            console.warn('[Auth] Supabase unreachable, falling back to backend login');
          } else {
            return { success: false, error: error.message };
          }
        }
      } catch {
        console.warn('[Auth] Supabase login threw, falling back to backend');
      }
    }

    // Backend login
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const resp = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        return { success: false, error: body.detail || `Login failed (${resp.status})` };
      }
      const data: BackendAuthResponse = await resp.json();
      this._setBackendAuth(data);
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Network error during login' };
    }
  }

  // ---------- Sync with Backend (for AuthGuard bootstrap) ----------

  async syncWithBackend(): Promise<{ user: AuthUser; workspace: { id: string; name: string; slug: string } } | null> {
    const token = await this.getToken();
    if (!token) return null;

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const resp = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      return {
        user: {
          id: data.id,
          email: data.email,
          fullName: data.full_name,
        },
        workspace: data.workspace,
      };
    } catch {
      return null;
    }
  }

  // ---------- Sign Out ----------

  async signOut(): Promise<void> {
    try {
      // Clear backend auth
      this._backendToken = null;
      this._backendUser = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('comlina_token');
        localStorage.removeItem('comlina_user');
        localStorage.removeItem('comlina_workspace');
      }
      if (isSupabaseConfigured) {
        await supabase.auth.signOut();
      }
    } catch {
      // ignore
    }
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  // ---------- Private helpers ----------

  private _setBackendAuth(data: BackendAuthResponse) {
    this._backendToken = data.access_token;
    this._backendUser = {
      id: data.user.id,
      email: data.user.email,
      fullName: data.user.full_name,
    };
    if (typeof window !== 'undefined') {
      localStorage.setItem('comlina_token', data.access_token);
      localStorage.setItem('comlina_user', JSON.stringify(this._backendUser));
      if (data.workspace) {
        localStorage.setItem('comlina_workspace', JSON.stringify(data.workspace));
      }
    }
  }
}

export const authService = new AuthService();
