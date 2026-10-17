// client/src/components/layout/BottomNav.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Zap, 
  MessageSquare, 
  Users, 
  MoreHorizontal, 
  BarChart2, 
  Instagram, 
  Settings,
  X
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';

export function BottomNav() {
  const pathname = usePathname();
  const toggleMobileMenu = useUIStore((s) => s.toggleMobileMenu);
  const [isMoreSheetOpen, setIsMoreSheetOpen] = useState(false);

  const mainTabs = [
    { label: 'Overview', href: '/dashboard', icon: Home, exact: true },
    { label: 'Automations', href: '/dashboard/automations', icon: Zap },
    { label: 'Inbox', href: '/dashboard/inbox', icon: MessageSquare },
    { label: 'Contacts', href: '/dashboard/contacts', icon: Users },
  ];

  const moreItems = [
    { label: 'Analytics', href: '/dashboard/analytics', icon: BarChart2, desc: 'Track your growth and metrics' },
    { label: 'Instagram Accounts', href: '/dashboard/instagram-accounts', icon: Instagram, desc: 'Manage connected IG accounts' },
    { label: 'Settings', href: '/dashboard/settings', icon: Settings, desc: 'Preferences, plan, and notifications' },
  ];

  const isMoreActive = ['/dashboard/analytics', '/dashboard/instagram-accounts', '/dashboard/settings'].some((p) =>
    pathname.startsWith(p)
  );

  // Suppress BottomNav on full-screen builder studio to prevent colliding/stacked action bars
  if (pathname.startsWith('/dashboard/automations/create')) {
    return null;
  }

  return (
    <>
      {/* "More" Slide-up Sheet */}
      {isMoreSheetOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 lg:hidden flex flex-col justify-end animate-in fade-in duration-150"
          onClick={() => setIsMoreSheetOpen(false)}
        >
          <div 
            className="bg-white rounded-t-3xl border-t border-[#ECECE8] p-5 pb-8 shadow-2xl space-y-4 animate-in slide-in-from-bottom duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#ECECE8] pb-3">
              <span className="font-bold text-sm text-[#111110]">More Pages</span>
              <button
                onClick={() => setIsMoreSheetOpen(false)}
                className="p-1 rounded-full text-[#70706B] hover:text-[#111110] cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {moreItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMoreSheetOpen(false)}
                    className={`flex items-center gap-3.5 p-3 rounded-2xl transition-all ${
                      isActive 
                        ? 'bg-[#EAF6EE] text-[#064125]' 
                        : 'hover:bg-[#FBFBFA] text-[#111110]'
                    }`}
                  >
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                      isActive ? 'bg-[#064125] text-white' : 'bg-[#F4F4F0] text-[#70706B]'
                    }`}>
                      <Icon size={18} />
                    </div>
                    <div>
                      <div className="text-xs font-bold">{item.label}</div>
                      <div className="text-[11px] text-[#70706B]">{item.desc}</div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Fixed Bottom Navigation Bar */}
      <nav 
        aria-label="Mobile Bottom Navigation"
        className="fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur-md border-t border-[#ECECE8] z-40 lg:hidden shadow-lg pb-[max(env(safe-area-inset-bottom),0.5rem)] pt-1.5"
      >
        <div className="flex items-center justify-around px-2 max-w-lg mx-auto">
          {mainTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = tab.exact
              ? pathname === tab.href
              : pathname === tab.href || (tab.href !== '/dashboard' && pathname.startsWith(tab.href));

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-all group ${
                  isActive ? 'text-[#064125]' : 'text-[#70706B] hover:text-[#111110]'
                }`}
              >
                <div className={`p-1 rounded-xl transition-all ${
                  isActive ? 'bg-[#EAF6EE] text-[#064125]' : 'group-hover:bg-[#F4F4F0]'
                }`}>
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                </div>
                <span className={`text-[10px] tracking-tight mt-0.5 ${
                  isActive ? 'font-bold text-[#064125]' : 'font-medium text-[#70706B]'
                }`}>
                  {tab.label}
                </span>
              </Link>
            );
          })}

          {/* More Tab */}
          <button
            type="button"
            onClick={() => setIsMoreSheetOpen(true)}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-all group cursor-pointer ${
              isMoreActive ? 'text-[#064125]' : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            <div className={`p-1 rounded-xl transition-all ${
              isMoreActive ? 'bg-[#EAF6EE] text-[#064125]' : 'group-hover:bg-[#F4F4F0]'
            }`}>
              <MoreHorizontal size={20} strokeWidth={isMoreActive ? 2.5 : 2} />
            </div>
            <span className={`text-[10px] tracking-tight mt-0.5 ${
              isMoreActive ? 'font-bold text-[#064125]' : 'font-medium text-[#70706B]'
            }`}>
              More
            </span>
          </button>
        </div>
      </nav>
    </>
  );
}

export default BottomNav;
