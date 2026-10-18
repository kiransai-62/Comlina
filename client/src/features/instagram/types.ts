// client/src/features/instagram/types.ts
export interface ConnectedInstagramAccount {
  id: string;
  workspace_id?: string;
  user_id?: string | null;
  igUserId?: string;
  ig_user_id?: string;
  username: string;
  accountType?: 'BUSINESS' | 'CREATOR' | string;
  account_type?: 'BUSINESS' | 'CREATOR' | string;
  followerCount?: number;
  follower_count?: number;
  profile_pic_url?: string | null;
  token_expires_at?: string | null;
  isActive?: boolean;
  is_active?: boolean;
  auth_method?: string;
  connection_status?: string;
  last_validated_at?: string | null;
  last_refreshed_at?: string | null;
  last_error_code?: string | null;
  connectedAt?: string;
  connected_at?: string;
  status?: 'CONNECTED' | 'EXPIRED' | 'REAUTHORIZATION_REQUIRED' | 'EXPIRING_SOON' | string;
}

export type InstagramConnectionStatus =
  | 'connected'
  | 'not_connected'
  | 'token_expiring'
  | 'reauthorization_required'
  | 'temporarily_unavailable';

export interface InstagramConnectionStatusResponse {
  status: InstagramConnectionStatus;
  account?: ConnectedInstagramAccount | null;
  requires_reconnect: boolean;
  requires_connect: boolean;
  error_code?: string | null;
  message: string;
}

export type InstagramConnectionState =
  | 'checking'
  | 'connected'
  | 'not_connected'
  | 'token_expiring'
  | 'reauthorization_required'
  | 'temporarily_unavailable'
  | 'error'
  | 'disconnected';
