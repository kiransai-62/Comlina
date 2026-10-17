// client/features/automations/queries.ts
import { useQuery } from '@tanstack/react-query';
import { automationsApi } from './api';

export const automationsKeys = {
  all: ['automations'] as const,
  detail: (id: string) => ['automations', id] as const,
};

export function useAutomationsQuery() {
  return useQuery({
    queryKey: automationsKeys.all,
    queryFn: automationsApi.list,
    staleTime: 1000 * 30, // 30 seconds
  });
}
