// client/features/automations/mutations.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { automationsApi } from './api';
import { automationsKeys } from './queries';
import { useUIStore } from '@/stores/uiStore';

export function useCreateAutomationMutation() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: automationsApi.create,
    onSuccess: (newAuto) => {
      queryClient.invalidateQueries({ queryKey: automationsKeys.all });
      showToast(`Automation "${newAuto.name}" created!`);
    },
  });
}

export function usePublishAutomationMutation() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (id: string) => automationsApi.publish(id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: automationsKeys.all });
      showToast(`Automation "${updated.name}" is now live (v${updated.version})!`);
    },
  });
}

export function useDeleteAutomationMutation() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (id: string) => automationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: automationsKeys.all });
      showToast('Automation removed');
    },
  });
}
