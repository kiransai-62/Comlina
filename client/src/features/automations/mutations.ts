import { useMutation, useQueryClient } from '@tanstack/react-query';
import { automationsApi } from './api';
import { automationsKeys } from './queries';
import { AutomationItem, AutomationCreateInput, AutomationUpdateInput } from './types';
import { useUIStore } from '@/stores/uiStore';

export function useCreateAutomationMutation() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (data: AutomationCreateInput) => automationsApi.create(data),
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

export function useUpdateAutomationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AutomationUpdateInput }) => automationsApi.update(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData<AutomationItem[]>(automationsKeys.all, (old) => {
        if (!old) return [updated];
        return old.map((item) => (item.id === updated.id ? { ...item, ...updated } : item));
      });
      queryClient.invalidateQueries({ queryKey: automationsKeys.all });
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
