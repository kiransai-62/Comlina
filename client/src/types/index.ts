// client/src/types/index.ts
export * from '../features/automations/types';
export * from '../features/contacts/types';
export * from '../features/instagram/types';
export * from '../features/analytics/api';

export interface User {
  id: string;
  email: string;
  name?: string;
  avatarUrl?: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  planTier: string;
}
