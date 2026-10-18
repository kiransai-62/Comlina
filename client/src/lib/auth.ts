// client/src/lib/auth.ts
import { supabase, isSupabaseConfigured } from './supabase';
import { api } from './api';
import type { Session } from '@supabase/supabase-js';

export interface AuthUser {
  id: string;
  email: string;
  fullName?: string;
  phone?: string;
  avatarUrl?: string;
  timezone?: string;
}

export interface BackendAuthResponse {
  access_token: string;
  refresh_token?: string;
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
  // Backend-only auth: store tokens + user in memory + localStorage
  private _backendToken: string | null = null;
  private _backendRefreshToken: string | null = null;
  private _backendUser: AuthUser | null = null;
  private _refreshPromise: Promise<string | null> | null = null;

  constructor() {
    // Restore backend tokens from localStorage on init
    if (typeof window !== 'undefined') {
      try {
        this._backendToken = localStorage.getItem('comlina_token');
        this._backendRefreshToken = localStorage.getItem('comlina_refresh_token');
        const storedUser = localStorage.getItem('comlina_user');
        if (storedUser) {
          this._backendUser = JSON.parse(storedUser);
        }
      } catch {
        // ignore
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
        if (!error && session) {
          const now = Math.floor(Date.now() / 1000);
          // If token has expired or is expiring in less than 60 seconds, refresh it proactively
          if (session.expires_at && session.expires_at - now < 60) {
            console.info('[Auth] Supabase token expired or expiring soon, refreshing session...');
            const { data: refreshed, error: refreshErr } = await supabase.auth.refreshSession();
            if (!refreshErr && refreshed.session) {
              return refreshed.session;
            }
          }
          return session;
        }
      } catch (err) {
        console.warn('[Auth] Error getting/refreshing Supabase session:', err);
      }
    }

    // Backend-only mode: synthesize a minimal Session-like object if we have a token
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

  async refreshToken(): Promise<string | null> {
    if (typeof window === 'undefined') return null;

    // Single in-flight refresh promise to prevent concurrent refreshes racing
    if (this._refreshPromise) {
      return this._refreshPromise;
    }

    this._refreshPromise = (async () => {
      // 1. Try Supabase refresh if configured
      if (isSupabaseConfigured) {
        try {
          const { data, error } = await supabase.auth.refreshSession();
          if (!error && data.session?.access_token) {
            return data.session.access_token;
          }
        } catch (err) {
          console.warn('[Auth] Supabase refreshSession error:', err);
        }
      }

      // 2. Try Backend token refresh
      const refreshToken = this._backendRefreshToken || (typeof window !== 'undefined' ? localStorage.getItem('comlina_refresh_token') : null);
      if (refreshToken) {
        try {
          const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
          const resp = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (resp.ok) {
            const data = await resp.json();
            if (data.access_token) {
              this._backendToken = data.access_token;
              if (data.refresh_token) {
                this._backendRefreshToken = data.refresh_token;
              }
              if (typeof window !== 'undefined') {
                localStorage.setItem('comlina_token', data.access_token);
                if (data.refresh_token) {
                  localStorage.setItem('comlina_refresh_token', data.refresh_token);
                }
              }
              return data.access_token;
            }
          }
        } catch (err) {
          console.warn('[Auth] Backend token refresh error:', err);
        }
      }

      return null;
    })().finally(() => {
      this._refreshPromise = null;
    });

    return this._refreshPromise;
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
          phone: user.phone || user.user_metadata?.phone || '',
          avatarUrl: user.user_metadata?.avatar_url || '',
          timezone: user.user_metadata?.timezone || '',
        };
      }
    }

    // Backend user
    if (this._backendUser) {
      return this._backendUser;
    }

    const token = await this.getToken();
    if (token) {
      const synced = await this.syncWithBackend();
      if (synced?.user) {
        return synced.user;
      }
    }

    return null;
  }

  async updateProfile(updates: {
    fullName?: string;
    phone?: string;
    avatarUrl?: string;
    timezone?: string;
  }): Promise<{ success: boolean; user?: AuthUser; error?: string }> {
    let updatedUser: AuthUser | null = null;
    let updateError: string | null = null;

    // 1. Supabase update if configured
    if (isSupabaseConfigured) {
      try {
        const { data, error } = await supabase.auth.updateUser({
          data: {
            full_name: updates.fullName,
            phone: updates.phone,
            avatar_url: updates.avatarUrl,
            timezone: updates.timezone,
          },
        });
        if (error) {
          updateError = error.message;
        } else if (data.user) {
          const u = data.user;
          updatedUser = {
            id: u.id,
            email: u.email || '',
            fullName: u.user_metadata?.full_name || u.user_metadata?.name || '',
            phone: u.phone || u.user_metadata?.phone || '',
            avatarUrl: u.user_metadata?.avatar_url || '',
            timezone: u.user_metadata?.timezone || '',
          };
        }
      } catch (err: any) {
        updateError = err.message || 'Supabase profile update failed';
      }
    }

    // 2. Backend update if token available
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const token = await this.getToken();
      if (token) {
        const resp = await fetch(`${API_BASE}/auth/profile`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            full_name: updates.fullName,
            timezone: updates.timezone,
            avatar_url: updates.avatarUrl,
            phone: updates.phone,
          }),
        });

        if (resp.ok) {
          const d = await resp.json();
          this._backendUser = {
            id: d.id,
            email: d.email,
            fullName: d.full_name,
            phone: d.phone || updates.phone || this._backendUser?.phone,
            avatarUrl: d.avatar_url,
            timezone: d.timezone,
          };
          if (typeof window !== 'undefined') {
            localStorage.setItem('comlina_user', JSON.stringify(this._backendUser));
          }
          if (!updatedUser) {
            updatedUser = this._backendUser;
          }
        }
      }
    } catch {
      // Backend error fallback
    }

    if (updatedUser) {
      return { success: true, user: updatedUser };
    }
    return { success: false, error: updateError || 'Failed to update profile' };
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
    let token = await this.getToken();
    if (!token) return null;

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      let resp = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      // If token expired, attempt seamless token refresh once
      if (resp.status === 401) {
        const refreshedToken = await this.refreshToken();
        if (refreshedToken) {
          resp = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${refreshedToken}`,
              'Content-Type': 'application/json',
            },
          });
        }
      }

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
      this._backendRefreshToken = null;
      this._backendUser = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('comlina_token');
        localStorage.removeItem('comlina_refresh_token');
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
    if (data.refresh_token) {
      this._backendRefreshToken = data.refresh_token;
    }
    this._backendUser = {
      id: data.user.id,
      email: data.user.email,
      fullName: data.user.full_name,
    };
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('comlina_token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('comlina_refresh_token', data.refresh_token);
        }
        localStorage.setItem('comlina_user', JSON.stringify(this._backendUser));
        if (data.workspace) {
          localStorage.setItem('comlina_workspace', JSON.stringify(data.workspace));
        }
      } catch {
        // ignore
      }
    }
  }
}

export const authService = new AuthService();
