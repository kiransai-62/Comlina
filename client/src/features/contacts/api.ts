// client/features/contacts/api.ts
import { api } from '@/lib/api';
import { ContactItem } from './types';

export const contactsApi = {
  list: (params?: { tag?: string; follower_status?: string; is_converted?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.tag) searchParams.set('tag', params.tag);
    if (params?.follower_status) searchParams.set('follower_status', params.follower_status);
    if (params?.is_converted !== undefined) searchParams.set('is_converted', String(params.is_converted));
    const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return api.get<ContactItem[]>(`/contacts${queryStr}`);
  },
  exportCsv: () => api.get<string>('/contacts/export-csv')
};
