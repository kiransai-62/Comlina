// client/src/components/billing/PlanBadge.tsx
'use client';

import React from 'react';
import { Sparkles, Crown, Zap } from 'lucide-react';
import { PlanTier } from '@/lib/plans';

interface PlanBadgeProps {
  tier: PlanTier | string | null | undefined;
  size?: 'xs' | 'sm' | 'md';
  showIcon?: boolean;
  className?: string;
}

export function PlanBadge({
  tier,
  size = 'xs',
  showIcon = true,
  className = '',
}: PlanBadgeProps) {
  const normalized = (tier || 'FREE').toUpperCase() as PlanTier;

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[9.5px]',
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs',
  }[size];

  const iconSizes = {
    xs: 10,
    sm: 12,
    md: 14,
  }[size];

  if (normalized === 'PRO') {
    return (
      <span
        className={`inline-flex items-center gap-1 font-bold rounded-md bg-[#EEF2FF] text-[#4338CA] border border-[#C7D2FE] uppercase tracking-wide shadow-2xs ${sizeClasses} ${className}`}
      >
        {showIcon && <Sparkles size={iconSizes} className="shrink-0 text-[#6366F1]" />}
        <span>PRO</span>
      </span>
    );
  }

  if (normalized === 'PREMIUM') {
    return (
      <span
        className={`inline-flex items-center gap-1 font-bold rounded-md bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A] uppercase tracking-wide shadow-2xs ${sizeClasses} ${className}`}
      >
        {showIcon && <Crown size={iconSizes} className="shrink-0 text-[#D97706]" />}
        <span>PREMIUM</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-md bg-[#F4F4F1] text-[#70706B] border border-[#ECECE8] uppercase tracking-wide ${sizeClasses} ${className}`}
    >
      {showIcon && <Zap size={iconSizes} className="shrink-0 text-[#9E9E96]" />}
      <span>FREE</span>
    </span>
  );
}
