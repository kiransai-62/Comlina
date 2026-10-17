// client/features/instagram/api.ts
import { api } from '@/lib/api';
import { ConnectedInstagramAccount } from './types';

export interface InstagramMediaApiItem {
  id: string;
  caption?: string | null;
  media_type?: string | null;
  media_url?: string | null;
  thumbnail_url?: string | null;
  permalink?: string | null;
  timestamp?: string | null;
  like_count?: number | null;
  comments_count?: number | null;
}
export interface InstagramMediaPage {
  data: InstagramMediaApiItem[];
  next_cursor?: string | null;
}

export interface NormalizedInstagramMedia {
  id: string;
  type: 'POST' | 'REEL';
  caption: string;
  imageUrl: string;
  commentsCount: number;
  likesCount: number;
  publishedDate: string;
  permalink?: string;
}

export const instagramApi = {
  getMedia: async (accountId?: string): Promise<NormalizedInstagramMedia[]> => {
    const endpoint = accountId ? `/instagram/accounts/${accountId}/media` : '/instagram/media';
    const res = await api.get<any>(endpoint);
    if (Array.isArray(res)) return res;
    if (Array.isArray(res?.data)) return res.data;
    return [];
  },
  listMedia: async (accountId?: string, limit = 24, after?: string) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (accountId) q.set('account_id', accountId);
    if (after) q.set('after', after);
    try {
      const res = await api.get<any>(`/instagram/media?${q.toString()}`);
      if (Array.isArray(res)) {
        return { data: res, next_cursor: null };
      }
      return res;
    } catch {
      return { data: [], next_cursor: null };
    }
  },
  listAccounts: () => api.get<ConnectedInstagramAccount[]>('/instagram/accounts'),
  getConnectUrl: (redirectUri?: string) => 
    api.get<{ authorization_url: string; state: string }>(
      redirectUri ? `/instagram/oauth/connect-url?redirect_uri=${encodeURIComponent(redirectUri)}` : '/instagram/oauth/connect-url'
    ),
  callback: (code: string, state?: string, redirectUri?: string) => 
    api.post<ConnectedInstagramAccount>('/instagram/oauth/callback', { code, state, redirect_uri: redirectUri }),
  connectDevAccount: () => api.post<ConnectedInstagramAccount>('/instagram/connect-dev-account'),
  disconnect: (id: string) => api.delete<void>(`/instagram/accounts/${id}`)
};
