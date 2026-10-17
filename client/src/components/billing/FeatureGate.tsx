// client/src/components/billing/FeatureGate.tsx
'use client';

import React from 'react';
import { Lock, ArrowUpRight } from 'lucide-react';
import { usePlan } from '@/hooks/usePlan';
import { FEATURE_CATALOG, PlanTier } from '@/lib/plans';
import { PlanBadge } from './PlanBadge';

interface FeatureGateProps {
  featureKey: string;
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  blurContent?: boolean;
}

export function FeatureGate({
  featureKey,
  title,
  description,
  children,
  className = '',
  blurContent = false,
}: FeatureGateProps) {
  const { isLocked, getRequiredTier, openUpgradeModal } = usePlan();

  const locked = isLocked(featureKey);
  const requiredTier: PlanTier = getRequiredTier(featureKey);

  const featureDef = FEATURE_CATALOG.find((f) => f.key === featureKey);
  const displayTitle = title || featureDef?.name || 'Exclusive Feature';
  const displayDescription =
    description ||
    featureDef?.description ||
    `Upgrade to ${requiredTier === 'PRO' ? 'Pro' : 'Premium'} to activate this feature.`;

  if (!locked) {
    return <>{children}</>;
  }

  const handleUnlockClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    openUpgradeModal(requiredTier, featureKey);
  };

  return (
    <div className={`relative rounded-2xl border border-dashed border-[#DCDCD6] overflow-hidden ${className}`}>
      {/* Locked Feature Header Banner */}
      <div className="bg-[#FAF9F5] border-b border-[#ECECE8] p-3.5 sm:p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-amber-100 text-amber-800 rounded-lg">
            <Lock size={15} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#111110]">{displayTitle}</span>
              <PlanBadge tier={requiredTier} size="xs" />
            </div>
            <p className="text-[11px] text-[#70706B] line-clamp-1 mt-0.5">
              {displayDescription}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleUnlockClick}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-[#111110] hover:bg-[#282824] text-white shadow-xs transition-transform active:scale-95 cursor-pointer shrink-0"
        >
          <span>Unlock with {requiredTier === 'PRO' ? 'Pro' : 'Premium'}</span>
          <ArrowUpRight size={13} />
        </button>
      </div>

      {/* Disabled / Read-Only Child Controls with Preserved Draft State */}
      <div 
        className={`pointer-events-none select-none opacity-60 ${
          blurContent ? 'filter blur-[1.5px]' : ''
        }`}
        aria-disabled="true"
        tabIndex={-1}
      >
        {children}
      </div>
    </div>
  );
}
