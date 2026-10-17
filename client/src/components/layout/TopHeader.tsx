// client/src/components/layout/TopHeader.tsx
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { 
  Instagram, 
  ChevronDown, 
  Bell, 
  Settings, 
  LogOut,
  Search
} from 'lucide-react';

function MenuIcon({ size = 22, className = '' }: { size?: number; className?: string }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <line x1="4" x2="20" y1="6" y2="6" />
      <line x1="4" x2="20" y1="12" y2="12" />
      <line x1="4" x2="20" y1="18" y2="18" />
    </svg>
  );
}
import { authService, AuthUser } from '@/lib/auth';
import { useInstagramConnection } from '@/features/instagram';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useUIStore } from '@/stores/uiStore';
import { BrandLogo } from '@/components/BrandLogo';

export function TopHeader() {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [headerSearch, setHeaderSearch] = useState('');
  const [user, setUser] = useState<AuthUser | null>(null);

  const resetWorkspace = useWorkspaceStore((s) => s.reset);
  const toggleMobileMenu = useUIStore((s) => s.toggleMobileMenu);

  useEffect(() => {
    async function loadUser() {
      const u = await authService.getUser();
      setUser(u);
    }
    loadUser();
  }, []);

  const { primaryAccount, isConnected, isChecking, needsReauth } = useInstagramConnection();

  const displayName = user?.fullName || (user?.email ? user.email.split('@')[0] : 'Creator');
  const displayEmail = user?.email || 'No email registered';
  const initials = displayName
    .split(' ')
    .map((n) => n.charAt(0))
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'CR';

  const handleSignOut = async () => {
    setIsUserMenuOpen(false);
    resetWorkspace();
    await authService.signOut();
  };

  return (
    <header className="h-16 bg-white border-b border-[#ECECE8] px-4 sm:px-6 lg:px-8 flex items-center justify-between z-20 shrink-0 gap-3">
      {/* 1. Mobile & Tablet: Hamburger + Comlina Brand (< 1024px) */}
      <div className="flex items-center gap-3 lg:hidden">
        <button
          type="button"
          onClick={toggleMobileMenu}
          className="p-1.5 -ml-1 text-[#111110] hover:bg-[#F4F4F0] rounded-xl transition-colors cursor-pointer"
          aria-label="Open mobile navigation menu"
        >
          <MenuIcon size={22} />
        </button>

        <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
          <BrandLogo variant="mark" height={26} className="shrink-0" />
          <span className="text-xl font-black tracking-tight text-[#111110]">
            Comlina
          </span>
        </Link>
      </div>

      {/* 2. Desktop: Universal Search Bar (>= 1024px) */}
      <div className="hidden lg:flex flex-1 max-w-md xl:max-w-lg">
        <div className="relative w-full">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#9E9E96]" />
          <input
            type="text"
            placeholder="Search anything... (Ctrl + K)"
            value={headerSearch}
            onChange={(e) => setHeaderSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-xs text-[#111110] placeholder:text-[#9E9E96] outline-none focus:border-[#15803D] focus:bg-white transition-all shadow-2xs"
          />
        </div>
      </div>

      {/* 3. Right: Operational Status, Notification Bell & User Pill */}
      <div className="flex items-center gap-2.5 sm:gap-4 ml-auto">
        {/* Instagram Account Connection Status (Desktop & Tablet) */}
        <Link 
          href="/dashboard/instagram-accounts"
          className="hidden md:flex items-center gap-2 text-xs font-medium text-[#70706B] hover:text-[#111110] transition-colors"
        >
          <span className={`w-2 h-2 rounded-full ${
            isConnected 
              ? 'bg-[#15803D]' 
              : isChecking 
              ? 'bg-neutral-400 animate-pulse' 
              : needsReauth 
              ? 'bg-[#D97706]' 
              : 'bg-[#D97706]'
          }`} />
          <span className="truncate max-w-[140px]">
            {isConnected 
              ? `@${primaryAccount?.username}` 
              : isChecking 
              ? 'Checking...' 
              : needsReauth 
              ? `@${primaryAccount?.username || 'Account'} (Reconnect)` 
              : 'No Account'}
          </span>
        </Link>

        {/* Notification Bell */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
            className="p-2 rounded-xl text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F1] relative transition-colors cursor-pointer"
            title="Notifications"
          >
            <Bell size={18} />
          </button>

          {isNotificationsOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl border border-[#ECECE8] shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="font-bold text-sm text-[#111110]">Notifications</span>
              </div>
              <div className="text-xs text-[#70706B] p-4 text-center bg-[#FBFBFA] rounded-xl border border-[#ECECE8]/60">
                <span>No new notifications</span>
              </div>
            </div>
          )}
        </div>

        {/* User Avatar Pill */}
        <div className="relative">
          <div
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className="flex items-center gap-2 pl-1 pr-2 sm:pr-3 py-1 rounded-full border border-[#ECECE8] hover:bg-[#FBFBFA] cursor-pointer transition-all shadow-2xs"
          >
            <div className="w-7 h-7 rounded-full bg-[#111110] text-white flex items-center justify-center font-bold text-xs tracking-tight shrink-0">
              {initials}
            </div>
            <span className="text-xs sm:text-[13px] font-medium text-[#111110] hidden sm:inline max-w-[100px] truncate">
              {displayName}
            </span>
            <ChevronDown size={13} className="text-[#70706B] hidden sm:inline" />
          </div>

          {isUserMenuOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-2xl border border-[#ECECE8] shadow-xl py-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="px-3.5 py-2.5 border-b border-[#ECECE8]">
                <div className="font-semibold text-xs text-[#111110]">{displayName}</div>
                <div className="text-[11px] text-[#70706B] truncate mt-0.5">{displayEmail}</div>
              </div>
              <Link
                href="/dashboard/settings"
                onClick={() => setIsUserMenuOpen(false)}
                className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-[#111110] hover:bg-[#F4F4F1] font-medium"
              >
                <Settings size={14} className="text-[#70706B]" />
                <span>Account Settings</span>
              </Link>
              <div className="border-t border-[#ECECE8] my-1" />
              <button
                type="button"
                onClick={handleSignOut}
                className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-red-600 hover:bg-red-50 w-full text-left font-medium cursor-pointer"
              >
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default TopHeader;
