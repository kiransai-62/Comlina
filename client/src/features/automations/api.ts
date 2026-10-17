// client/features/automations/api.ts
import { api } from '@/lib/api';
import { AutomationItem } from './types';

export const automationsApi = {
  list: () => api.get<AutomationItem[]>('/automations'),
  get: (id: string) => api.get<AutomationItem>(`/automations/${id}`),
  create: (data: any) => api.post<AutomationItem>('/automations', data),
  publish: (id: string) => api.post<AutomationItem>(`/automations/${id}/publish`),
  delete: (id: string) => api.delete<void>(`/automations/${id}`)
};
