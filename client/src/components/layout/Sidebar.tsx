// client/src/components/layout/Sidebar.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Zap, 
  MessageSquare, 
  Users, 
  BarChart2, 
  Instagram, 
  Settings,
  X,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useUIStore } from '@/stores/uiStore';
import { usePlan } from '@/hooks/usePlan';
import { PlanBadge } from '@/components/billing/PlanBadge';

export function Sidebar() {
  const pathname = usePathname();
  const currentWorkspace = useWorkspaceStore((s) => s.currentWorkspace);
  const isMobileMenuOpen = useUIStore((s) => s.isMobileMenuOpen);
  const setIsMobileMenuOpen = useUIStore((s) => s.setIsMobileMenuOpen);
  const { planTier, usage, fetchUsage } = usePlan();

  React.useEffect(() => {
    fetchUsage();
  }, []);

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: Home, exact: true },
    { label: 'Automations', href: '/dashboard/automations', icon: Zap },
    { label: 'Conversations', href: '/dashboard/inbox', icon: MessageSquare },
    { label: 'Contacts', href: '/dashboard/contacts', icon: Users },
    { label: 'Analytics', href: '/dashboard/analytics', icon: BarChart2 },
    { label: 'Instagram Accounts', href: '/dashboard/instagram-accounts', icon: Instagram },
    { label: 'Settings', href: '/dashboard/settings', icon: Settings },
  ];

  const renderNavContent = (isMobile = false) => (
    <>
      {/* Brand Header */}
      <div className="px-6 py-6 flex items-center justify-between">
        <Link 
          href="/dashboard" 
          onClick={() => isMobile && setIsMobileMenuOpen(false)}
          className="flex items-center gap-2.5 hover:opacity-90 transition-opacity group"
        >
          <BrandLogo variant="mark" height={32} className="transition-transform group-hover:scale-105 shrink-0" />
          <span className="text-2xl font-extrabold tracking-tight text-[#111110]">
            Comlina
          </span>
        </Link>

        {isMobile && (
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-1 rounded-lg text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] cursor-pointer"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        )}
      </div>

      <div className="px-6 pb-2">
        <p className="text-[11.5px] text-[#70706B] leading-snug">
          Instagram conversations that grow your business.
        </p>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.exact 
            ? pathname === item.href 
            : pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => isMobile && setIsMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13.5px] transition-all ${
                isActive
                  ? 'bg-[#EAF6EE] text-[#064125] font-semibold shadow-xs'
                  : 'text-[#70706B] hover:bg-[#F9F9F8] hover:text-[#111110] font-medium'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-[#064125]' : 'text-[#70706B]'} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Pricing & Plans Left-Bottom Component */}
      <div className="p-3.5 border-t border-[#ECECE8] bg-white">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-[#F4FBF6] via-[#F9FDFB] to-white p-3.5 border border-[#D1EADC] shadow-xs hover:border-[#15803D]/40 transition-all group">
          {/* Subtle decorative ambient flare in corner */}
          <div className="absolute -top-6 -right-6 w-16 h-16 bg-[#22C55E]/10 rounded-full blur-md pointer-events-none" />

          {/* Header Row: Pricing & Plans + Plan Badge */}
          <div className="flex items-center justify-between relative z-10">
            <Link
              href="/pricing"
              onClick={() => isMobile && setIsMobileMenuOpen(false)}
              className="flex items-center gap-1.5 group-hover:text-[#064125] transition-colors"
            >
              <div className="w-5 h-5 rounded-md bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0 shadow-2xs">
                <Sparkles size={11} className="text-[#15803D]" />
              </div>
              <span className="text-[12px] font-bold text-[#111110] tracking-tight">
                Pricing & Plans
              </span>
            </Link>
            <PlanBadge tier={planTier} size="xs" />
          </div>

          {/* Current Tier & Quota Usage */}
          <div className="mt-2.5 relative z-10">
            <div className="flex items-baseline justify-between">
              <span className="text-[13px] font-extrabold text-[#111110] capitalize">
                {planTier.toLowerCase()} Plan
              </span>
              <span className="text-[11px] font-semibold text-[#70706B]">
                {usage ? (
                  `${usage.posts_used} / ${usage.posts_limit === -1 ? '∞' : usage.posts_limit} posts`
                ) : (
                  '0 / 10 posts'
                )}
              </span>
            </div>

            {/* Smooth Rounded Progress Bar */}
            <div className="w-full bg-[#E5ECE7] h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-[#15803D] to-[#22C55E] h-full rounded-full transition-all duration-300"
                style={{
                  width: `${
                    usage && usage.posts_limit > 0 
                      ? Math.min(100, Math.max(8, (usage.posts_used / usage.posts_limit) * 100)) 
                      : 10
                  }%`
                }}
              />
            </div>

            <div className="flex items-center justify-between text-[10.5px] text-[#70706B] mt-1.5">
              <span>{usage ? `${usage.max_dms_per_post} DMs/post` : '99 DMs/post'}</span>
              {planTier === 'FREE' && (
                <span className="text-[#15803D] font-medium">10 posts quota</span>
              )}
            </div>
          </div>

          {/* High-Converting Unified CTA Button */}
          <Link
            href="/pricing"
            onClick={() => isMobile && setIsMobileMenuOpen(false)}
            className="mt-3 flex items-center justify-center gap-1.5 w-full py-2 bg-[#064125] hover:bg-[#0A5A34] active:scale-[0.99] text-white text-[12px] font-semibold rounded-xl text-center transition-all shadow-xs group-hover:shadow hover:-translate-y-0.5 relative z-10"
          >
            <span>
              {planTier === 'FREE'
                ? 'Upgrade Plan'
                : planTier === 'PREMIUM'
                ? 'Upgrade to Pro'
                : 'View Entitlements'}
            </span>
            {planTier === 'FREE' && (
              <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded text-white font-medium">
                ₹199
              </span>
            )}
            {planTier === 'PREMIUM' && (
              <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded text-white font-medium">
                ₹399
              </span>
            )}
            <ArrowRight size={13} className="text-[#86EFAC] transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* 1. Desktop Persistent Sidebar (>= 1024px) */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-[#ECECE8] flex-col h-screen select-none shrink-0">
        {renderNavContent(false)}
      </aside>

      {/* 2. Mobile & Tablet Slide-Over Drawer (< 1024px) */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-50 lg:hidden bg-black/50 backdrop-blur-xs flex animate-in fade-in duration-150"
          onClick={() => setIsMobileMenuOpen(false)}
        >
          <div 
            className="w-72 max-w-[85vw] bg-white h-full flex flex-col shadow-2xl animate-in slide-in-from-left duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {renderNavContent(true)}
          </div>
        </div>
      )}
    </>
  );
}

export default Sidebar;
