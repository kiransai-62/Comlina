// client/src/hooks/usePlan.ts
'use client';

import { create } from 'zustand';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { api } from '@/lib/api';
import { 
  PlanTier, 
  PlanConfig, 
  getPlan, 
  hasFeature, 
  isFeatureLocked, 
  getRequiredPlan,
  FEATURE_CATALOG 
} from '@/lib/plans';

export interface UsageSummary {
  plan_tier: PlanTier;
  plan_name: string;
  plan_status: string;
  price_inr: number;
  billing_period: string;
  posts_used: number;
  posts_limit: number;
  posts_remaining: number;
  max_dms_per_post: number;
  total_dms_delivered: number;
  active_automations: number;
  max_automations: number;
  features: Record<string, boolean>;
  is_post_quota_reached: boolean;
}

interface PlanStoreState {
  upgradeModalOpen: boolean;
  targetTier: PlanTier;
  lockedFeatureKey: string | null;
  usage: UsageSummary | null;
  isLoadingUsage: boolean;
  openUpgradeModal: (targetTier?: PlanTier, featureKey?: string) => void;
  closeUpgradeModal: () => void;
  setUsage: (usage: UsageSummary) => void;
  setLoadingUsage: (loading: boolean) => void;
}

export const usePlanStore = create<PlanStoreState>((set) => ({
  upgradeModalOpen: false,
  targetTier: 'PREMIUM',
  lockedFeatureKey: null,
  usage: null,
  isLoadingUsage: false,
  openUpgradeModal: (targetTier = 'PREMIUM', featureKey) =>
    set({
      upgradeModalOpen: true,
      targetTier,
      lockedFeatureKey: featureKey || null,
    }),
  closeUpgradeModal: () =>
    set({
      upgradeModalOpen: false,
      lockedFeatureKey: null,
    }),
  setUsage: (usage) => set({ usage }),
  setLoadingUsage: (isLoadingUsage) => set({ isLoadingUsage }),
}));

export function usePlan() {
  const currentWorkspace = useWorkspaceStore((s) => s.currentWorkspace);
  const setCurrentWorkspace = useWorkspaceStore((s) => s.setCurrentWorkspace);
  const {
    upgradeModalOpen,
    targetTier,
    lockedFeatureKey,
    usage,
    isLoadingUsage,
    openUpgradeModal,
    closeUpgradeModal,
    setUsage,
    setLoadingUsage,
  } = usePlanStore();

  const planTier = (
    usage?.plan_tier ||
    (currentWorkspace as any)?.plan_tier ||
    (currentWorkspace as any)?.planTier ||
    'FREE'
  ).toUpperCase() as PlanTier;

  const planConfig: PlanConfig = getPlan(planTier);

  const fetchUsage = async () => {
    try {
      setLoadingUsage(true);
      const res = await api.get<UsageSummary>('/payments/usage');
      if (res) {
        setUsage(res);
        if (currentWorkspace && (currentWorkspace as any).plan_tier !== res.plan_tier) {
          setCurrentWorkspace({
            ...currentWorkspace,
            planTier: res.plan_tier,
            ...( { plan_tier: res.plan_tier } as any ),
          });
        }
      }
    } catch {
      // Fallback usage
    } finally {
      setLoadingUsage(false);
    }
  };

  const switchPlanDev = async (tier: PlanTier) => {
    try {
      const res = await api.post<any>('/payments/dev/switch-plan', { plan_tier: tier });
      if (res && res.workspace) {
        if (currentWorkspace) {
          setCurrentWorkspace({
            ...currentWorkspace,
            planTier: res.workspace.plan_tier,
            ...( { plan_tier: res.workspace.plan_tier } as any ),
          });
        }
        await fetchUsage();
      }
      return true;
    } catch (err) {
      console.error('Failed to switch plan in dev:', err);
      return false;
    }
  };

  const isLocked = (featureKey: string): boolean => {
    return isFeatureLocked(planTier, featureKey);
  };

  const hasAccess = (featureKey: string): boolean => {
    return hasFeature(planTier, featureKey);
  };

  const getRequiredTier = (featureKey: string): PlanTier => {
    return getRequiredPlan(featureKey);
  };

  return {
    planTier,
    planConfig,
    usage,
    isLoadingUsage,
    upgradeModalOpen,
    targetTier,
    lockedFeatureKey,
    isLocked,
    hasAccess,
    getRequiredTier,
    openUpgradeModal,
    closeUpgradeModal,
    fetchUsage,
    switchPlanDev,
  };
}
