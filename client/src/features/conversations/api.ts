// client/src/features/conversations/api.ts
import { api } from '@/lib/api';

export interface ConversationItem {
  id: string;
  workspace_id?: string;
  instagram_account_id?: string;
  contact_id?: string;
  status: string;
  last_message_text?: string;
  last_message_at: string;
  unread_count: number;
  contact_username?: string;
  name?: string;
  followers?: number;
  following?: number;
  posts?: number;
  category?: string;
  language?: string;
  first_seen?: string;
  automation?: string;
  tags?: string[];
  notes?: string;
  followed_you?: boolean;
}

export interface MessageItem {
  id: string;
  workspace_id?: string;
  conversation_id: string;
  sender_type: string; // CONTACT, BOT, INSTAGRAM_ACCOUNT
  text: string;
  media_url?: string;
  created_at: string;
  attachment?: {
    title: string;
    subtitle?: string;
    type?: string;
    url?: string;
  };
}

export const conversationsApi = {
  list: (accountId?: string) => {
    const q = accountId ? `?account_id=${accountId}` : '';
    return api.get<ConversationItem[]>(`/conversations${q}`);
  },
  getMessages: (conversationId: string) =>
    api.get<MessageItem[]>(`/conversations/${conversationId}/messages`),
  sendMessage: (conversationId: string, text: string, mediaUrl?: string) =>
    api.post<MessageItem>(`/conversations/${conversationId}/messages`, { text, media_url: mediaUrl }),
};
