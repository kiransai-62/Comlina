// client/features/instagram/types.ts
export interface ConnectedInstagramAccount {
  id: string;
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
  connectedAt?: string;
  connected_at?: string;
}
