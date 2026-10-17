// client/features/automations/hooks.ts
import { useAutomationsQuery } from './queries';
import {
  useCreateAutomationMutation,
  usePublishAutomationMutation,
  useDeleteAutomationMutation,
} from './mutations';

export function useAutomations() {
  const query = useAutomationsQuery();
  const createMutation = useCreateAutomationMutation();
  const publishMutation = usePublishAutomationMutation();
  const deleteMutation = useDeleteAutomationMutation();

  return {
    automations: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    createAutomation: createMutation.mutateAsync,
    publishAutomation: publishMutation.mutateAsync,
    deleteAutomation: deleteMutation.mutateAsync,
  };
}
