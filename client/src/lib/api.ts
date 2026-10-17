// client/src/lib/api.ts
import { authService, AUTH_ENABLED } from './auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export class ApiError extends Error {
  status: number;
  details?: any;

  constructor(message: string, status: number = 500, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

class ApiClient {
  private activeWorkspaceId: string | null = null;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string | null) => void)[] = [];

  constructor() {
    // Restore active workspace ID from localStorage on initialization
    if (typeof window !== 'undefined') {
      try {
        const storedWs = localStorage.getItem('comlina_workspace');
        if (storedWs) {
          const ws = JSON.parse(storedWs);
          if (ws?.id) {
            this.activeWorkspaceId = ws.id;
          }
        }
      } catch {
        // ignore
      }
    }
  }

  setWorkspaceId(workspaceId: string | null) {
    this.activeWorkspaceId = workspaceId;
  }

  getWorkspaceId(): string | null {
    return this.activeWorkspaceId;
  }

  private subscribeTokenRefresh(cb: (token: string | null) => void) {
    this.refreshSubscribers.push(cb);
  }

  private onTokenRefreshed(token: string | null) {
    this.refreshSubscribers.forEach((cb) => cb(token));
    this.refreshSubscribers = [];
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = await authService.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else if (AUTH_ENABLED) {
      // Token not available yet - throw ApiError rather than immediately destroying page state
      throw new ApiError('Authentication required', 401);
    }

    if (this.activeWorkspaceId) {
      headers['X-Workspace-ID'] = this.activeWorkspaceId;
    }

    const url = `${API_BASE_URL}/${endpoint.replace(/^\//, '')}`;

    const controller = new AbortController();
    // Allow up to 10 seconds for backend operations
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const response = await fetch(url, {
        ...options,
        signal: options.signal || controller.signal,
        headers,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        if (AUTH_ENABLED && response.status === 401 && typeof window !== 'undefined') {
          // If request was already retried once with a refreshed token, give up and sign out
          if ((options as any)._isRetry) {
            const pathname = window.location.pathname;
            if (!pathname.startsWith('/login') && !pathname.startsWith('/signup')) {
              await authService.signOut();
              return null as unknown as T;
            }
          }

          // Concurrency control: if a refresh is already underway, queue this request
          if (this.isRefreshing) {
            return new Promise<T>((resolve, reject) => {
              this.subscribeTokenRefresh(async (newToken) => {
                if (newToken) {
                  try {
                    const retried = await this.request<T>(endpoint, {
                      ...options,
                      _isRetry: true,
                      headers: {
                        ...((options.headers as Record<string, string>) || {}),
                        Authorization: `Bearer ${newToken}`,
                      },
                    } as RequestInit);
                    resolve(retried);
                  } catch (err) {
                    reject(err);
                  }
                } else {
                  reject(new ApiError('Session expired. Please sign in again.', 401));
                }
              });
            });
          }

          // Otherwise, start the singleton refresh attempt
          this.isRefreshing = true;
          try {
            const refreshedToken = await authService.refreshToken();
            this.onTokenRefreshed(refreshedToken);

            if (refreshedToken) {
              return await this.request<T>(endpoint, {
                ...options,
                _isRetry: true,
                headers: {
                  ...((options.headers as Record<string, string>) || {}),
                  Authorization: `Bearer ${refreshedToken}`,
                },
              } as RequestInit);
            } else {
              const pathname = window.location.pathname;
              if (!pathname.startsWith('/login') && !pathname.startsWith('/signup')) {
                await authService.signOut();
                return null as unknown as T;
              }
            }
          } catch {
            this.onTokenRefreshed(null);
            const pathname = window.location.pathname;
            if (!pathname.startsWith('/login') && !pathname.startsWith('/signup')) {
              await authService.signOut();
              return null as unknown as T;
            }
          } finally {
            this.isRefreshing = false;
          }
        }
        let errorDetails: any = null;
        let errorMessage = `API Error ${response.status}: ${response.statusText}`;
        try {
          const text = await response.text();
          try {
            errorDetails = JSON.parse(text);
            errorMessage = errorDetails?.detail || errorDetails?.message || errorMessage;
          } catch {
            if (text) errorMessage = text;
          }
        } catch {
          // ignore
        }
        throw new ApiError(errorMessage, response.status, errorDetails);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/csv')) {
        return (await response.text()) as unknown as T;
      }

      if (response.status === 204) {
        return null as unknown as T;
      }

      return await response.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err instanceof ApiError) {
        throw err;
      }
      if (err.name === 'AbortError') {
        throw new ApiError('Request timed out. Unable to reach backend server.', 408);
      }
      throw new ApiError(err.message || 'Network error occurred. Unable to connect to server.', 0);
    }
  }

  get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const api = new ApiClient();
