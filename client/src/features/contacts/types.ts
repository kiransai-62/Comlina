// client/features/contacts/types.ts
export interface ContactItem {
  id: string;
  username: string;
  fullName?: string;
  full_name?: string;
  email?: string;
  phone?: string;
  followerStatus?: 'UNKNOWN' | 'FOLLOWING' | 'NOT_FOLLOWING' | 'CHECK_UNAVAILABLE' | string;
  follower_status?: 'UNKNOWN' | 'FOLLOWING' | 'NOT_FOLLOWING' | 'CHECK_UNAVAILABLE' | string;
  isConverted?: boolean;
  is_converted?: boolean;
  interactionCount?: number;
  interactions?: number;
  tags?: string[];
  notes?: string;
  lastInteractionAt?: string;
  last_interaction_at?: string;
  first_seen?: string;
  createdAt?: string;
  category?: string;
  followers?: number;
  following?: number;
  posts?: number;
}
