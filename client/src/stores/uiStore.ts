// client/stores/uiStore.ts
import { create } from 'zustand';

export interface UIState {
  toastMessage: string | null;
  showToast: (message: string) => void;
  clearToast: () => void;
  isMobileMenuOpen: boolean;
  setIsMobileMenuOpen: (open: boolean) => void;
  toggleMobileMenu: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  toastMessage: null,
  showToast: (message: string) => {
    set({ toastMessage: message });
    setTimeout(() => {
      set((state) => (state.toastMessage === message ? { toastMessage: null } : {}));
    }, 3500);
  },
  clearToast: () => set({ toastMessage: null }),
  isMobileMenuOpen: false,
  setIsMobileMenuOpen: (open: boolean) => set({ isMobileMenuOpen: open }),
  toggleMobileMenu: () => set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
}));
