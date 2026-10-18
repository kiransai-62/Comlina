// client/stores/workspaceStore.ts
import { create } from 'zustand';
import { api } from '@/lib/api';

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  planTier: string;
}

export interface WorkspaceState {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  selectedAccount: string;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  updateCurrentWorkspaceName: (name: string) => void;
  setSelectedAccount: (account: string) => void;
  reset: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  currentWorkspace: null,
  selectedAccount: '',
  setWorkspaces: (workspaces) => set({ workspaces }),
  setCurrentWorkspace: (workspace) => {
    api.setWorkspaceId(workspace?.id || null);
    set({ currentWorkspace: workspace });
  },
  updateCurrentWorkspaceName: (name: string) => {
    set((state) => {
      if (!state.currentWorkspace) return state;
      const updated = { ...state.currentWorkspace, name };
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('comlina_workspace', JSON.stringify(updated));
        } catch {
          // ignore
        }
      }
      return { currentWorkspace: updated };
    });
  },
  setSelectedAccount: (account) => set({ selectedAccount: account }),
  reset: () => {
    api.setWorkspaceId(null);
    set({ workspaces: [], currentWorkspace: null, selectedAccount: '' });
  },
}));
