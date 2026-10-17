// client/src/components/billing/PlanComparisonMatrix.tsx
'use client';

import React, { useState } from 'react';
import { Check, X, Sparkles, Crown, Zap, ArrowRight, ShieldCheck } from 'lucide-react';
import { usePlan } from '@/hooks/usePlan';
import { PLAN_CONFIGS, PlanTier } from '@/lib/plans';
import { PlanBadge } from './PlanBadge';

interface FeatureRow {
  name: string;
  category: string;
  free: string | boolean;
  premium: string | boolean;
  pro: string | boolean;
  tooltip?: string;
}

const COMPARISON_ROWS: FeatureRow[] = [
  // Quotas & Usage Limits
  {
    name: 'Total Automated Posts',
    category: 'Limits',
    free: '10 posts total',
    premium: '100 posts',
    pro: 'Unlimited posts',
  },
  {
    name: 'Max DMs Per Post',
    category: 'Limits',
    free: '99 DMs/post',
    premium: '2,500 DMs/post',
    pro: '10,000 DMs/post',
  },
  {
    name: 'Active Automations',
    category: 'Limits',
    free: '10 active',
    premium: '50 active',
    pro: '200 active',
  },
  {
    name: 'Connected Instagram Accounts',
    category: 'Limits',
    free: '1 account',
    premium: '3 accounts',
    pro: '10 accounts',
  },

  // Core Automation
  {
    name: 'Basic Comment-to-DM Trigger',
    category: 'Core',
    free: true,
    premium: true,
    pro: true,
  },
  {
    name: 'Trigger Response DM',
    category: 'Core',
    free: true,
    premium: true,
    pro: true,
  },
  {
    name: 'Trigger Keywords',
    category: 'Core',
    free: 'Up to 3 keywords',
    premium: 'Unlimited keywords',
    pro: 'Unlimited keywords',
  },

  // Premium Growth Features
  {
    name: 'Reply to All Comments',
    category: 'Conversion',
    free: false,
    premium: true,
    pro: true,
  },
  {
    name: 'Ask to Follow (Follower Gate)',
    category: 'Conversion',
    free: false,
    premium: true,
    pro: true,
  },
  {
    name: 'Comment Teaser Reply',
    category: 'Conversion',
    free: false,
    premium: true,
    pro: true,
  },
  {
    name: 'Interactive DM Buttons',
    category: 'Conversion',
    free: false,
    premium: true,
    pro: true,
  },
  {
    name: 'Follow-up DMs',
    category: 'Conversion',
    free: false,
    premium: true,
    pro: true,
  },

  // Pro Advanced Workflows
  {
    name: 'Live Comment Automation',
    category: 'Advanced',
    free: false,
    premium: false,
    pro: true,
  },
  {
    name: 'AI Smart Assistant',
    category: 'Advanced',
    free: false,
    premium: false,
    pro: true,
  },
  {
    name: 'Appointment Booking',
    category: 'Advanced',
    free: false,
    premium: false,
    pro: true,
  },
  {
    name: 'Advanced Workflow Builder',
    category: 'Advanced',
    free: false,
    premium: false,
    pro: true,
  },
];

export function PlanComparisonMatrix() {
  const { planTier: currentTier, openUpgradeModal } = usePlan();
  const [mobileTab, setMobileTab] = useState<PlanTier>('PREMIUM');

  const renderValue = (val: string | boolean) => {
    if (typeof val === 'boolean') {
      return val ? (
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D]">
          <Check size={14} />
        </span>
      ) : (
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-400">
          <X size={14} />
        </span>
      );
    }
    return <span className="text-xs font-semibold text-[#111110]">{val}</span>;
  };

  return (
    <div className="w-full space-y-8">
      
      {/* 1. Pricing Header Cards (Desktop & Tablet) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* FREE CARD */}
        <div className={`rounded-3xl p-6 sm:p-7 border bg-white flex flex-col justify-between transition-all ${
          currentTier === 'FREE' ? 'border-[#111110] ring-2 ring-[#111110]/10 shadow-sm' : 'border-[#ECECE8]'
        }`}>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#70706B]">Essential</span>
              <PlanBadge tier="FREE" size="xs" />
            </div>
            <h3 className="text-2xl font-black text-[#111110]">Free</h3>
            <p className="text-xs text-[#70706B] mt-1">
              Start testing Instagram Comment-to-DM with basic rules.
            </p>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-3xl font-black text-[#111110]">₹0</span>
              <span className="text-xs text-[#70706B]">/month</span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-[#ECECE8]">
            <button
              type="button"
              disabled={currentTier === 'FREE'}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-bold border border-[#DCDCD6] bg-white text-[#70706B] cursor-default"
            >
              {currentTier === 'FREE' ? 'Current Plan' : 'Free Tier'}
            </button>
          </div>
        </div>

        {/* PREMIUM CARD */}
        <div className={`relative rounded-3xl p-6 sm:p-7 border bg-gradient-to-b from-amber-50/50 to-white flex flex-col justify-between transition-all shadow-md ${
          currentTier === 'PREMIUM'
            ? 'border-amber-400 ring-2 ring-amber-400/20'
            : 'border-amber-200 hover:border-amber-300'
        }`}>
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-500 text-white shadow-xs">
            MOST POPULAR
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-800">Growth</span>
              <PlanBadge tier="PREMIUM" size="xs" />
            </div>
            <h3 className="text-2xl font-black text-[#111110]">Premium</h3>
            <p className="text-xs text-[#70706B] mt-1">
              Ask to Follow, teaser replies, DM buttons, and 2,500 DMs/post.
            </p>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-3xl font-black text-[#111110]">₹199</span>
              <span className="text-xs text-[#70706B]">/month</span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-amber-100">
            <button
              type="button"
              onClick={() => openUpgradeModal('PREMIUM')}
              className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer ${
                currentTier === 'PREMIUM'
                  ? 'bg-amber-100 text-amber-900 border border-amber-300'
                  : 'bg-[#0066FF] hover:bg-[#0052CC] text-white active:scale-98'
              }`}
            >
              {currentTier === 'PREMIUM' ? (
                'Current Plan'
              ) : (
                <>
                  <span>Upgrade to Premium</span>
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </div>
        </div>

        {/* PRO CARD */}
        <div className={`relative rounded-3xl p-6 sm:p-7 border bg-gradient-to-b from-indigo-50/50 to-white flex flex-col justify-between transition-all shadow-md ${
          currentTier === 'PRO'
            ? 'border-indigo-400 ring-2 ring-indigo-400/20'
            : 'border-indigo-200 hover:border-indigo-300'
        }`}>
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-[#4338CA] text-white shadow-xs">
            BEST VALUE
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-800">Scale</span>
              <PlanBadge tier="PRO" size="xs" />
            </div>
            <h3 className="text-2xl font-black text-[#111110]">Pro</h3>
            <p className="text-xs text-[#70706B] mt-1">
              Live Comment, AI Assistant, Appointment Booking & unlimited posts.
            </p>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-3xl font-black text-[#111110]">₹399</span>
              <span className="text-xs text-[#70706B]">/month</span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-indigo-100">
            <button
              type="button"
              onClick={() => openUpgradeModal('PRO')}
              className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer ${
                currentTier === 'PRO'
                  ? 'bg-indigo-100 text-indigo-900 border border-indigo-300'
                  : 'bg-[#4338CA] hover:bg-[#3730A3] text-white active:scale-98'
              }`}
            >
              {currentTier === 'PRO' ? (
                'Current Plan'
              ) : (
                <>
                  <span>Upgrade to Pro</span>
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </div>
        </div>

      </div>

      {/* 2. Full Feature Comparison Matrix (Desktop & Tablet >= 768px) */}
      <div className="hidden md:block bg-white border border-[#ECECE8] rounded-3xl overflow-hidden shadow-xs">
        <div className="p-6 bg-[#FBFBFA] border-b border-[#ECECE8]">
          <h4 className="text-base font-bold text-[#111110]">
            Feature Comparison Matrix
          </h4>
          <p className="text-xs text-[#70706B] mt-0.5">
            Transparent breakdown of quotas, automations, and capabilities by tier.
          </p>
        </div>

        <div className="divide-y divide-[#ECECE8]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#FAF9F5] text-xs font-bold text-[#70706B] uppercase tracking-wider">
                <th className="py-3.5 px-6 font-bold text-[#111110] w-2/5">Capability</th>
                <th className="py-3.5 px-4 text-center w-1/5">Free</th>
                <th className="py-3.5 px-4 text-center w-1/5 bg-amber-50/40 text-amber-900">Premium (₹199)</th>
                <th className="py-3.5 px-4 text-center w-1/5 bg-indigo-50/40 text-indigo-900">Pro (₹399)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#ECECE8] text-xs">
              {COMPARISON_ROWS.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#FDFDFD] transition-colors">
                  <td className="py-3.5 px-6 font-semibold text-[#111110]">
                    <div>{row.name}</div>
                    <span className="text-[10px] text-[#70706B] uppercase tracking-wider">{row.category}</span>
                  </td>
                  <td className="py-3.5 px-4 text-center">{renderValue(row.free)}</td>
                  <td className="py-3.5 px-4 text-center bg-amber-50/20">{renderValue(row.premium)}</td>
                  <td className="py-3.5 px-4 text-center bg-indigo-50/20">{renderValue(row.pro)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Mobile Tabbed Comparison (< 768px) */}
      <div className="block md:hidden bg-white border border-[#ECECE8] rounded-2xl p-4 shadow-xs space-y-4">
        <div className="flex rounded-xl bg-[#F4F4F1] p-1">
          {(['FREE', 'PREMIUM', 'PRO'] as PlanTier[]).map((tier) => (
            <button
              key={tier}
              type="button"
              onClick={() => setMobileTab(tier)}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                mobileTab === tier
                  ? 'bg-white text-[#111110] shadow-xs'
                  : 'text-[#70706B]'
              }`}
            >
              {PLAN_CONFIGS[tier].name}
            </button>
          ))}
        </div>

        <div className="divide-y divide-[#ECECE8]">
          {COMPARISON_ROWS.map((row, idx) => {
            const val = mobileTab === 'FREE' ? row.free : mobileTab === 'PREMIUM' ? row.premium : row.pro;
            return (
              <div key={idx} className="py-3 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-[#111110]">{row.name}</div>
                  <div className="text-[10px] text-[#70706B]">{row.category}</div>
                </div>
                <div>{renderValue(val)}</div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
