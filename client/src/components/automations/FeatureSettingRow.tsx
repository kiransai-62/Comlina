'use client';

import React from 'react';
import { LucideIcon, Lock, ArrowUpRight } from 'lucide-react';
import { PlanTier } from '@/lib/plans';
import { PlanBadge } from '@/components/billing/PlanBadge';

export interface FeatureSettingRowProps {
  icon: LucideIcon;
  title: string;
  description: string;
  tier: PlanTier;
  isLocked: boolean;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  onUnlock: () => void;
  children?: React.ReactNode;
  badgeText?: string;
  className?: string;
}

export function FeatureSettingRow({
  icon: Icon,
  title,
  description,
  tier,
  isLocked,
  enabled,
  onChange,
  onUnlock,
  children,
  badgeText,
  className = '',
}: FeatureSettingRowProps) {
  return (
    <div
      className={`p-4 sm:p-5 rounded-2xl border transition-all ${
        isLocked
          ? 'bg-[#FCFCFA] border-[#ECECE8]/80 hover:border-[#DCDCD6]'
          : enabled
          ? 'bg-white border-[#C4E1D0] shadow-2xs'
          : 'bg-white border-[#ECECE8] hover:border-gray-300'
      } ${className}`}
    >
      <div className="flex items-center justify-between gap-3 sm:gap-4">
        {/* Left: Icon & Title/Description */}
        <div className="flex items-start sm:items-center gap-3 min-w-0">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 sm:mt-0 ${
              isLocked
                ? 'bg-[#F4F4F0] text-[#70706B]'
                : enabled
                ? 'bg-[#EAF6EE] text-[#064125]'
                : 'bg-[#F4F4F0] text-[#70706B]'
            }`}
          >
            <Icon size={18} />
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs sm:text-[13px] font-bold text-[#111110] tracking-tight">
                {title}
              </span>
              <PlanBadge tier={tier} size="xs" />
              {badgeText && (
                <span className="text-[10px] font-semibold text-[#70706B] bg-[#F4F4F0] px-2 py-0.5 rounded-full">
                  {badgeText}
                </span>
              )}
            </div>
            <p className="text-[11px] sm:text-xs text-[#70706B] line-clamp-2 mt-0.5">
              {description}
            </p>
          </div>
        </div>

        {/* Right: Toggle Switch or Lock Upgrade CTA */}
        <div className="shrink-0 flex items-center">
          {isLocked ? (
            <button
              type="button"
              onClick={onUnlock}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-[#111110] hover:bg-[#282824] text-white shadow-2xs transition-all active:scale-95 cursor-pointer shrink-0"
              title={`Unlock ${title} with ${tier === 'PRO' ? 'Pro' : 'Premium'}`}
            >
              <Lock size={12} className="text-amber-400" />
              <span className="hidden sm:inline">Unlock</span>
              <span className="sm:hidden">{tier === 'PRO' ? 'Pro' : 'Prem'}</span>
              <ArrowUpRight size={12} />
            </button>
          ) : (
            <label className="relative inline-flex items-center cursor-pointer shrink-0 select-none">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => onChange(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-10 h-5.5 sm:w-11 sm:h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4.5 after:w-4.5 sm:after:h-5 sm:after:w-5 after:transition-all peer-checked:bg-[#064125]" />
            </label>
          )}
        </div>
      </div>

      {/* Expandable sub-options when feature is unlocked and enabled */}
      {!isLocked && enabled && children && (
        <div className="mt-4 pt-4 border-t border-[#ECECE8] animate-in fade-in duration-200">
          {children}
        </div>
      )}
    </div>
  );
}

export default FeatureSettingRow;
