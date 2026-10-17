import { useWorkspaceStore } from '@/stores/workspaceStore';

export function useWorkspace() {
  const {
    currentWorkspace,
    workspaces,
    selectedAccount,
    setCurrentWorkspace,
    setSelectedAccount,
    setWorkspaces,
  } = useWorkspaceStore();

  return {
    workspace: currentWorkspace,
    workspaces,
    selectedAccount,
    setCurrentWorkspace,
    setSelectedAccount,
    setWorkspaces,
    workspaceId: currentWorkspace?.id,
  };
}
