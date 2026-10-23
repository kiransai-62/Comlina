'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { 
  Zap, 
  MessageSquare, 
  Users, 
  TrendingUp, 
  ArrowRight,
  ArrowUpRight,
  Plus,
  ShieldCheck,
  Sparkles,
  RefreshCw,
  Lock,
  ChevronDown,
  Check,
  Instagram,
  BarChart2,
  Send,
  Filter,
  ExternalLink,
  Settings,
  X,
  AlertCircle
} from 'lucide-react';
import { instagramApi, useInstagramConnection } from '@/features/instagram';
import { analyticsApi } from '@/features/analytics/api';
import { automationsApi } from '@/features/automations/api';
import { conversationsApi } from '@/features/conversations/api';
import { authService } from '@/lib/auth';
import { BrandLogo } from '@/components/BrandLogo';
import { ComlinaLoadingOverlay } from '@/components/ComlinaLoadingOverlay';
import { MovingArrowConnector } from '@/components/MovingArrowConnector';
import { LivePerformanceAndConversations } from '@/components/dashboard/LivePerformanceAndConversations';



export default function DashboardOverviewPage() {
  const [time, setTime] = useState('');
  const [userName, setUserName] = useState('Creator');
  const [isProUnlockedExpanded, setIsProUnlockedExpanded] = useState(false);
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);
  const [connectStep, setConnectStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [isConnectingMeta, setIsConnectingMeta] = useState(false);
  const [isStatsHovered, setIsStatsHovered] = useState(false);
  const [isStatsPinned, setIsStatsPinned] = useState(false);
  const isStatsExpanded = isStatsHovered || isStatsPinned;

  useEffect(() => {
    setTime(new Date().toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);

    async function loadUser() {
      const u = await authService.getUser();
      if (u?.fullName) {
        setUserName(u.fullName.split(' ')[0]);
      }
    }
    loadUser();

    return () => clearInterval(timer);
  }, []);

  // Live Data Queries
  const {
    accounts,
    primaryAccount,
    connectionState,
    isConnected,
    isChecking: loadingAccounts,
    needsReauth,
    isUnavailable,
    isNotConnected,
    isError: errorAccounts,
    error: accountsError,
    refetch: refetchAccounts,
    startConnect: handleStartMetaOAuth,
  } = useInstagramConnection();

  const hasAccounts = (isConnected || needsReauth) && !!primaryAccount;

  const { 
    data: summary, 
    isLoading: loadingSummary, 
    isError: errorSummary, 
    error: summaryError, 
    refetch: refetchSummary 
  } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: () => analyticsApi.getSummary(),
    refetchInterval: 10_000,
  });

  const { 
    data: automations, 
    isLoading: loadingAutomations, 
    refetch: refetchAutomations 
  } = useQuery({
    queryKey: ['automations'],
    queryFn: () => automationsApi.list(),
    refetchInterval: 15_000,
  });

  const { 
    data: conversations, 
    isLoading: loadingConversations, 
    refetch: refetchConversations 
  } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list(),
    refetchInterval: 10_000,
  });

  const totalDmsSent = summary?.stats_dms_sent ?? 0;
  const totalComments = summary?.stats_comments ?? 0;
  const totalLeads = summary?.total_leads ?? 0;
  const conversionRateDisplay = hasAccounts && summary?.conversion_rate_pct != null 
    ? `${summary.conversion_rate_pct}%` 
    : '—';
  const followerCountDisplay = primaryAccount?.follower_count != null 
    ? primaryAccount.follower_count.toLocaleString() 
    : '—';

  const defaultWeeklyDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const dailyStats = summary?.daily_stats && summary.daily_stats.length === 7
    ? summary.daily_stats
    : defaultWeeklyDays.map((day) => ({ day, date: '', dms: 0, comments: 0, count: 0, pct: 0 }));


  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* 1. Header Greeting & Quick Actions */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111110] tracking-tight">
              Good morning, {userName}!
            </h1>
            <div
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 border rounded-full text-xs font-medium transition-all ${
                isConnected 
                  ? 'bg-white border-[#ECECE8] text-[#333330]' 
                  : loadingAccounts
                  ? 'bg-[#F9F9F8] border-[#ECECE8] text-[#70706B]'
                  : needsReauth
                  ? 'bg-[#FEF3C7] border-[#F59E0B] text-[#92400E]'
                  : 'bg-[#FEF3C7] border-[#F59E0B] text-[#92400E]'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${
                isConnected 
                  ? 'bg-[#22C55E]' 
                  : loadingAccounts 
                  ? 'bg-neutral-400 animate-pulse' 
                  : 'bg-[#D97706]'
              }`} />
              <span>
                {isConnected 
                  ? `@${primaryAccount?.username}` 
                  : loadingAccounts 
                  ? 'Checking Account...' 
                  : needsReauth
                  ? `@${primaryAccount?.username || 'Account'}`
                  : 'No Account Connected'}
              </span>
              <span className="text-[#9E9E96]">•</span>
              <span className={`font-semibold ${
                isConnected 
                  ? 'text-[#15803D]' 
                  : loadingAccounts 
                  ? 'text-[#70706B]' 
                  : 'text-[#D97706]'
              }`}>
                {isConnected 
                  ? 'Live' 
                  : loadingAccounts 
                  ? 'Loading...' 
                  : needsReauth 
                  ? 'Reconnect Required' 
                  : 'Connect Required'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/dashboard/instagram-accounts"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white border border-[#E0E0DA] hover:bg-[#F7F7F5] text-[#111110] text-xs font-medium rounded-lg transition-all"
          >
            <RefreshCw size={14} className="text-[#70706B]" />
            <span>{hasAccounts ? 'Manage Account' : 'Accounts'}</span>
          </Link>
          {isConnected ? (
            <Link
              href="/dashboard/automations/create"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
            >
              <Plus size={15} />
              <span>New Automation</span>
            </Link>
          ) : needsReauth ? (
            <button
              onClick={handleStartMetaOAuth}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#D97706] hover:bg-[#B45309] text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
            >
              <Instagram size={15} />
              <span>Reconnect Instagram</span>
            </button>
          ) : loadingAccounts ? null : (
            <button
              onClick={() => setIsConnectModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
            >
              <Instagram size={15} />
              <span>Connect Instagram</span>
            </button>
          )}
        </div>
      </div>

      {/* Instagram Reauthorization Banner */}
      {needsReauth && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <AlertCircle className="text-amber-600 shrink-0" size={20} />
            <div>
              <div className="text-xs font-semibold text-amber-900">
                Instagram Reconnection Required
              </div>
              <div className="text-xs text-amber-700">
                Your Meta Graph API authorization for @{primaryAccount?.username} has expired or needs permissions refresh. Reconnect now to restore automated DM responses.
              </div>
            </div>
          </div>
          <button
            onClick={handleStartMetaOAuth}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all shrink-0 cursor-pointer"
          >
            <Instagram size={14} />
            <span>Reconnect Now</span>
          </button>
        </div>
      )}

      {/* Backend / API Error State Banner */}
      {(errorAccounts || errorSummary) && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <AlertCircle className="text-red-600 shrink-0" size={20} />
            <div>
              <div className="text-xs font-semibold text-red-900">
                Backend Connection Unavailable
              </div>
              <div className="text-xs text-red-700">
                {(accountsError as any)?.message || (summaryError as any)?.message || 'Unable to connect to the backend server. Real-time metrics cannot be loaded.'}
              </div>
            </div>
          </div>
          <button
            onClick={async () => {
              await authService.refreshToken();
              refetchAccounts();
              refetchSummary();
              refetchAutomations();
              refetchConversations();
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all shrink-0 cursor-pointer"
          >
            <RefreshCw size={13} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {loadingAccounts && <ComlinaLoadingOverlay isLoading={true} />}

      {loadingAccounts ? (
        <div className="min-h-[400px]" />
      ) : hasAccounts ? (
        <>
          {/* 2. Stats Overview Section Header */}
          <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
            <div>
              <h2 className="text-2xl font-bold text-[#111110] tracking-tight">
                Overview
              </h2>
            </div>
          </div>

          {/* Empty State Banner when all totals are 0 */}
          {totalDmsSent === 0 && totalComments === 0 && totalLeads === 0 && !loadingSummary && (
            <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#70706B] mb-6">
              <div className="flex items-center gap-2">
                <BarChart2 size={16} className="text-[#15803D] shrink-0" />
                <span>No activity yet. Publish an automation to start collecting data.</span>
              </div>
              <Link
                href="/dashboard/automations/create"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg transition-all shrink-0"
              >
                <Plus size={13} />
                <span>Create Automation</span>
              </Link>
            </div>
          )}

          {/* Synchronized Expandable Cards Container */}
          <div 
            onMouseEnter={() => setIsStatsHovered(true)}
            onMouseLeave={() => setIsStatsHovered(false)}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6"
          >
            {/* Card 1: Total Messages Sent */}
            <div 
              className={`bg-white border rounded-2xl p-5 flex flex-col justify-between transition-all duration-350 ease-[cubic-bezier(0.4,0,0.2,1)] ${
                isStatsExpanded 
                  ? 'min-h-[415px] shadow-lg border-[#B7E4C7]' 
                  : 'min-h-[172px] shadow-sm border-[#ECECE8]'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                      <Send size={15} />
                    </div>
                    <span className="text-xs font-semibold text-[#111110]">
                      Total messages sent
                    </span>
                  </div>

                  <span className={`text-[11px] font-semibold bg-[#F2F2EE] text-[#70706B] px-2 py-0.5 rounded-full whitespace-nowrap transition-opacity duration-250 ${
                    isStatsExpanded ? 'opacity-100' : 'opacity-0'
                  }`}>
                    Live Queue
                  </span>
                </div>

                <div className="flex items-end justify-between mt-3">
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-[#111110] tracking-tight">
                        {totalDmsSent.toLocaleString()}
                      </span>
                      <span className="text-[11px] font-semibold text-[#15803D] bg-[#EAF6EE] px-2 py-0.5 rounded-full whitespace-nowrap">
                        +{totalComments} comments
                      </span>
                    </div>
                    <div className="text-xs text-[#9E9E96] mt-1.5">
                      Automated comment &amp; DM replies
                    </div>
                  </div>

                  {!isStatsExpanded && (
                    <div className="flex items-end gap-0.5 h-7 pb-0.5" title="7-day activity sparkline">
                      {dailyStats.map((item, i) => (
                        <div 
                          key={i} 
                          style={{ height: item.pct > 0 ? `${item.pct}%` : '3px' }}
                          className={`w-1.5 rounded-t-xs transition-all duration-300 ${
                            item.pct > 0 ? 'bg-[#86EFAC]' : 'bg-[#E5E7EB]'
                          }`}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Expanded state content */}
              <div 
                className={`overflow-hidden transition-all duration-350 ease-[cubic-bezier(0.4,0,0.2,1)] flex flex-col justify-between ${
                  isStatsExpanded ? 'max-h-[280px] opacity-100 mt-3.5 flex-1' : 'max-h-0 opacity-0 mt-0'
                }`}
              >
                <div className="py-1">
                  <div className="flex items-end justify-between h-[68px] px-1 pb-1 border-b border-[#ECECE8] gap-1.5">
                    {dailyStats.map((item, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group/bar relative">
                        <div 
                          style={{ height: item.pct > 0 ? `${item.pct}%` : '3px' }}
                          className={`w-3 rounded-t-xs transition-all duration-300 ${
                            item.pct > 0 
                              ? 'bg-[#86EFAC] group-hover/bar:bg-[#15803D]' 
                              : 'bg-[#E5E7EB] group-hover/bar:bg-[#D1D5DB]'
                          }`}
                        />
                        {/* Hover Tooltip showing actual real-time count */}
                        <div className="absolute -top-7 opacity-0 group-hover/bar:opacity-100 transition-opacity bg-[#111110] text-white text-[10px] px-1.5 py-0.5 rounded shadow-sm pointer-events-none whitespace-nowrap z-10">
                          {item.count} {item.count === 1 ? 'msg' : 'msgs'}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between mt-1 px-1">
                    {dailyStats.map((item) => (
                      <span key={item.day} className="text-[10px] text-[#9E9E96] flex-1 text-center">
                        {item.day}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex justify-between border-t border-[#ECECE8] pt-3 text-xs">
                  <div>
                    <div className="font-bold text-[#111110]">{totalDmsSent}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">DMs delivered</div>
                  </div>
                  <div>
                    <div className="font-bold text-[#111110]">{totalComments}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Comments</div>
                  </div>
                  <div>
                    <div className="font-bold text-[#111110]">{totalLeads}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Leads</div>
                  </div>
                </div>

                <Link 
                  href="/dashboard/analytics"
                  className="w-full py-2 px-3 bg-[#EAF6EE] hover:bg-[#DCFCE7] text-[#15803D] text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 mt-2.5 transition-colors cursor-pointer"
                >
                  <ExternalLink size={13} />
                  <span>View message analytics</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>

            {/* Card 2: Account Followers */}
            <div 
              className={`bg-white border rounded-2xl p-5 flex flex-col justify-between transition-all duration-350 ease-[cubic-bezier(0.4,0,0.2,1)] ${
                isStatsExpanded 
                  ? 'min-h-[415px] shadow-lg border-[#B7E4C7]' 
                  : 'min-h-[172px] shadow-sm border-[#ECECE8]'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                      <Users size={15} />
                    </div>
                    <span className="text-xs font-semibold text-[#111110]">
                      Account Followers
                    </span>
                  </div>

                  <a 
                    href={`https://instagram.com/${encodeURIComponent(primaryAccount?.username || '')}`}
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-[11px] text-[#15803D] font-semibold bg-[#EAF6EE] px-2 py-0.5 rounded-full inline-flex items-center gap-1 whitespace-nowrap"
                  >
                    <span>@{primaryAccount?.username}</span>
                    <ArrowUpRight size={10} />
                  </a>
                </div>

                <div className="flex items-end justify-between mt-3">
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-[#111110] tracking-tight">
                        {followerCountDisplay}
                      </span>
                    </div>

                    <div className="text-xs text-[#9E9E96] mt-1.5 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
                      <span className="text-[#15803D] font-medium">Synced via Meta</span>
                      <span>·</span>
                      <span className="text-[#70706B]">{time}</span>
                    </div>
                  </div>

                  {!isStatsExpanded && (
                    <div className="flex items-end gap-0.5 h-7 pb-0.5" title="Audience engagement sparkline">
                      {dailyStats.map((item, i) => (
                        <div 
                          key={i} 
                          style={{ height: totalLeads > 0 && item.pct > 0 ? `${item.pct}%` : '3px' }}
                          className={`w-1.5 rounded-t-xs transition-all duration-300 ${
                            totalLeads > 0 && item.pct > 0 ? 'bg-[#86EFAC]' : 'bg-[#E5E7EB]'
                          }`}
                        />
                      ))}
                    </div>
                  )}

                </div>
              </div>

              {/* Expanded state content */}
              <div 
                className={`overflow-hidden transition-all duration-350 ease-[cubic-bezier(0.4,0,0.2,1)] flex flex-col justify-between ${
                  isStatsExpanded ? 'max-h-[280px] opacity-100 mt-3.5 flex-1' : 'max-h-0 opacity-0 mt-0'
                }`}
              >
                <div className="py-1">
                  <div className="flex h-[68px] gap-1.5 items-end justify-center border-b border-[#ECECE8] text-xs text-[#70706B]">
                    <span>Account: {primaryAccount?.account_type || 'Creator Account'}</span>
                  </div>
                </div>

                <div className="flex justify-between border-t border-[#ECECE8] pt-3 text-xs">
                  <div>
                    <div className="font-bold text-[#111110]">{totalLeads}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Total Contacts</div>
                  </div>
                  <div>
                    <div className="font-bold text-[#15803D]">{automations ? automations.length : 0}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Automations</div>
                  </div>
                  <div>
                    <div className="font-bold text-[#111110]">v21.0</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Meta Version</div>
                  </div>
                </div>

                <Link 
                  href="/dashboard/contacts"
                  className="w-full py-2 px-3 bg-[#EAF6EE] hover:bg-[#DCFCE7] text-[#15803D] text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 mt-2.5 transition-colors cursor-pointer"
                >
                  <BarChart2 size={13} />
                  <span>View Audience Contacts</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>

            {/* Card 3: Follow-Gate Conversion */}
            <div 
              className={`bg-white border rounded-2xl p-5 flex flex-col justify-between transition-all duration-350 ease-[cubic-bezier(0.4,0,0.2,1)] ${
                isStatsExpanded 
                  ? 'min-h-[415px] shadow-lg border-[#B7E4C7]' 
                  : 'min-h-[172px] shadow-sm border-[#ECECE8]'
              }`}
            >
              <div>
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                    <Filter size={15} />
                  </div>
                  <span className="text-xs font-semibold text-[#111110]">
                    Lead Conversion Rate
                  </span>
                </div>

                <div className="mt-3">
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-[#111110] tracking-tight">
                      {conversionRateDisplay}
                    </span>
                  </div>
                  <div className="text-xs text-[#9E9E96] mt-1.5">
                    Lead qualification rate
                  </div>
                </div>

                <div className="mt-3.5 flex gap-1 h-1.5 rounded-full overflow-hidden bg-[#ECECE8]">
                  <div 
                    style={{ 
                      width: conversionRateDisplay !== '—' && summary?.conversion_rate_pct 
                        ? `${Math.min(100, Math.max(5, summary.conversion_rate_pct))}%` 
                        : '0%' 
                    }} 
                    className="bg-[#062E1A] rounded-full transition-all" 
                  />
                </div>
              </div>

              {/* Expanded state content */}
              <div 
                className={`overflow-hidden transition-all duration-350 ease-[cubic-bezier(0.4,0,0.2,1)] flex flex-col justify-between ${
                  isStatsExpanded ? 'max-h-[280px] opacity-100 mt-3.5 flex-1' : 'max-h-0 opacity-0 mt-0'
                }`}
              >
                <div className="flex-1" />

                <div className="flex justify-between border-t border-[#ECECE8] pt-3 text-xs">
                  <div>
                    <div className="font-bold text-[#111110]">{totalLeads}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Total leads</div>
                  </div>
                  <div>
                    <div className="font-bold text-[#111110]">{conversations ? conversations.length : 0}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">Conversations</div>
                  </div>
                  <div>
                    <div className="font-bold text-[#111110]">{totalDmsSent}</div>
                    <div className="text-[11px] text-[#9E9E96] mt-0.5">DMs Sent</div>
                  </div>
                </div>

                <Link 
                  href="/dashboard/analytics"
                  className="w-full py-2 px-3 bg-[#EAF6EE] hover:bg-[#DCFCE7] text-[#15803D] text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 mt-2.5 transition-colors cursor-pointer"
                >
                  <BarChart2 size={13} />
                  <span>View conversion details</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>
          </div>

          {/* 3. Middle Row: Live Recent Conversations + Performance Overview */}
          <LivePerformanceAndConversations />
        </>
      ) : isUnavailable ? (
        <div className="min-h-[300px] flex flex-col items-center justify-center p-8 text-center bg-white border border-[#ECECE8] rounded-2xl shadow-xs">
          <RefreshCw size={28} className="text-[#9E9E96] animate-spin mb-3" />
          <h3 className="text-sm font-bold text-[#111110]">Connection check in progress</h3>
          <p className="text-xs text-[#70706B] max-w-sm mt-1 mb-4">
            We could not verify your Instagram connection due to a temporary network issue. Your saved connection and automations remain intact.
          </p>
          <button
            onClick={() => refetchAccounts()}
            className="px-4 py-2 bg-[#064125] hover:bg-[#0A5A34] text-white text-xs font-semibold rounded-xl shadow-xs transition-all cursor-pointer"
          >
            Retry Connection Check
          </button>
        </div>
      ) : (
        /* ── Not Connected State: Desktop, Tablet, Mobile (Image 2 Alignment) ── */
        <div className="space-y-6">
          {/* 1. Hero Connect Card */}
          {/* 1A. Desktop Viewport (>= 1024px): 2-Column Layout */}
          <div className="hidden lg:grid grid-cols-12 gap-8 items-center bg-white border border-[#ECECE8] rounded-2xl p-8 shadow-xs">
            <div className="col-span-7">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#F58529] via-[#DD2A7B] to-[#8134AF] flex items-center justify-center text-white shadow-xl shadow-pink-500/25 mb-4">
                <Instagram size={28} />
              </div>

              <h2 className="text-2xl font-black text-[#111110] tracking-tight">
                Connect your Instagram account
              </h2>
              <p className="text-xs text-[#70706B] mt-2 leading-relaxed max-w-md">
                Link your Instagram Business or Creator account to start creating automations, reply to comments, send DMs and more.
              </p>

              <div className="mt-5">
                <button
                  type="button"
                  onClick={() => {
                    setConnectStep(1);
                    setIsConnectModalOpen(true);
                  }}
                  className="px-5 py-2.5 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-bold rounded-xl inline-flex items-center gap-2 shadow-xs transition-all cursor-pointer"
                >
                  <Plus size={16} />
                  <span>Connect Instagram</span>
                </button>
              </div>
            </div>

            <div className="col-span-5 bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl p-5 space-y-3">
              {[
                { label: 'Auto reply to comments', icon: MessageSquare },
                { label: 'Send automated DMs', icon: Send },
                { label: 'Capture and manage leads', icon: Users },
                { label: 'Track performance', icon: BarChart2 },
                { label: 'Grow faster', icon: TrendingUp },
              ].map((item, idx) => {
                const Icon = item.icon;
                return (
                  <div key={idx} className="flex items-center gap-2.5 text-xs text-[#111110]">
                    <div className="w-5 h-5 rounded-full bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                      <Icon size={12} />
                    </div>
                    <span className="font-medium">{item.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 1B. Tablet Viewport (768px - 1023px): Centered Hero + Horizontal Strip */}
          <div className="hidden md:block lg:hidden bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#F58529] via-[#DD2A7B] to-[#8134AF] flex items-center justify-center text-white shadow-xl shadow-pink-500/25 mx-auto">
              <Instagram size={28} />
            </div>

            <div>
              <h2 className="text-xl font-black text-[#111110] tracking-tight">
                Connect your Instagram account
              </h2>
              <p className="text-xs text-[#70706B] mt-1 max-w-md mx-auto">
                Link your Instagram Business or Creator account to start creating automations, reply to comments, send DMs and more.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setConnectStep(1);
                setIsConnectModalOpen(true);
              }}
              className="px-5 py-2.5 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-bold rounded-xl inline-flex items-center gap-2 shadow-xs transition-all cursor-pointer"
            >
              <Plus size={16} />
              <span>Connect Instagram</span>
            </button>

            {/* Horizontal strip of 5 feature badges */}
            <div className="flex items-center justify-center gap-2 flex-wrap pt-3 border-t border-[#ECECE8]">
              {[
                { label: 'Auto reply to comments', icon: MessageSquare },
                { label: 'Send automated DMs', icon: Send },
                { label: 'Capture leads', icon: Users },
                { label: 'Track performance', icon: BarChart2 },
                { label: 'Grow faster', icon: TrendingUp },
              ].map((item, idx) => {
                const Icon = item.icon;
                return (
                  <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#FBFBFA] border border-[#ECECE8] rounded-full text-xs font-medium text-[#111110]">
                    <Icon size={12} className="text-[#15803D]" />
                    <span>{item.label}</span>
                  </span>
                );
              })}
            </div>
          </div>

          {/* 1C. Mobile Viewport (< 768px): Compact Stacked Card */}
          <div className="md:hidden bg-white border border-[#ECECE8] rounded-2xl p-5 shadow-xs space-y-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#F58529] via-[#DD2A7B] to-[#8134AF] flex items-center justify-center text-white shadow-xl shadow-pink-500/25 mx-auto">
              <Instagram size={28} />
            </div>

            <div>
              <h2 className="text-lg font-black text-[#111110] tracking-tight">
                Connect your Instagram account
              </h2>
              <p className="text-xs text-[#70706B] mt-1 leading-snug">
                Link your Instagram account to start creating automations, reply to comments, send DMs and more.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setConnectStep(1);
                setIsConnectModalOpen(true);
              }}
              className="w-full py-3 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-bold rounded-xl inline-flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer"
            >
              <Plus size={16} />
              <span>Connect Instagram</span>
            </button>

            {/* Mobile Vertical Benefits List */}
            <div className="bg-[#FBFBFA] border border-[#ECECE8] rounded-xl p-3.5 space-y-2 text-left">
              {[
                { label: 'Auto reply to comments', icon: MessageSquare },
                { label: 'Send automated DMs', icon: Send },
                { label: 'Capture and manage leads', icon: Users },
                { label: 'Track performance', icon: BarChart2 },
                { label: 'Grow faster', icon: TrendingUp },
              ].map((item, idx) => {
                const Icon = item.icon;
                return (
                  <div key={idx} className="flex items-center gap-2.5 text-xs text-[#111110]">
                    <div className="w-5 h-5 rounded-full bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                      <Icon size={12} />
                    </div>
                    <span className="font-medium text-[11.5px]">{item.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 2. Stat Cards Grid: 4 columns on Desktop & Tablet, 2x2 grid on Mobile */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            <div className="bg-white border border-[#ECECE8] rounded-2xl p-4 sm:p-5 shadow-xs">
              <div className="text-[11px] font-semibold text-[#70706B]">
                <span className="sm:hidden">Automations</span>
                <span className="hidden sm:inline">Total Automations</span>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-[#111110] mt-1.5">
                0
              </div>
            </div>

            <div className="bg-white border border-[#ECECE8] rounded-2xl p-4 sm:p-5 shadow-xs">
              <div className="text-[11px] font-semibold text-[#70706B]">
                <span className="sm:hidden">Leads</span>
                <span className="hidden sm:inline">Leads Captured</span>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-[#111110] mt-1.5">
                0
              </div>
            </div>

            <div className="bg-white border border-[#ECECE8] rounded-2xl p-4 sm:p-5 shadow-xs">
              <div className="text-[11px] font-semibold text-[#70706B]">
                <span className="sm:hidden">Messages</span>
                <span className="hidden sm:inline">Messages Sent</span>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-[#111110] mt-1.5">
                0
              </div>
            </div>

            <div className="bg-white border border-[#ECECE8] rounded-2xl p-4 sm:p-5 shadow-xs">
              <div className="text-[11px] font-semibold text-[#70706B]">
                <span className="sm:hidden">Accounts</span>
                <span className="hidden sm:inline">Active Accounts</span>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-[#111110] mt-1.5">
                0
              </div>
            </div>
          </div>

          {/* 3. Lower Section: Recent Activity (60%) & Quick Actions (40%) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Recent Activity Card */}
            <div className="lg:col-span-7 bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs">
              <h3 className="text-sm font-bold text-[#111110]">Recent Activity</h3>
              <div className="py-10 text-center space-y-2">
                <div className="w-10 h-10 rounded-full bg-[#F4F4F0] text-[#70706B] flex items-center justify-center mx-auto">
                  <MessageSquare size={18} />
                </div>
                <div className="text-xs font-bold text-[#111110]">No activity yet</div>
                <p className="text-[11px] text-[#70706B] max-w-xs mx-auto">
                  Connect your Instagram account to see activity here.
                </p>
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="lg:col-span-5 bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-3">
              <h3 className="text-sm font-bold text-[#111110]">Quick Actions</h3>

              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => {
                    setConnectStep(1);
                    setIsConnectModalOpen(true);
                  }}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-[#ECECE8] bg-[#FBFBFA] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] transition-colors cursor-pointer text-left"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                    <Plus size={14} />
                  </div>
                  <span>Connect Instagram</span>
                </button>

                <Link
                  href="/dashboard/automations/create"
                  className="flex items-center gap-3 p-3 rounded-xl border border-[#ECECE8] bg-[#FBFBFA] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] transition-colors cursor-pointer"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#EEF2FF] text-[#4F46E5] flex items-center justify-center shrink-0">
                    <Zap size={14} />
                  </div>
                  <span>Create Automation</span>
                </Link>

                <Link
                  href="/dashboard/analytics"
                  className="flex items-center gap-3 p-3 rounded-xl border border-[#ECECE8] bg-[#FBFBFA] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] transition-colors cursor-pointer"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#FEF3C7] text-[#D97706] flex items-center justify-center shrink-0">
                    <BarChart2 size={14} />
                  </div>
                  <span>View Analytics</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── 5-Step E2E Connect Instagram Flow (Image 2 Alignment) ── */}
      {isConnectModalOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-in fade-in"
          onClick={() => setIsConnectModalOpen(false)}
        >
          <div 
            className="w-full max-w-md bg-white rounded-3xl p-6 sm:p-7 shadow-2xl relative animate-in zoom-in-95 duration-150 space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            {/* STEP 1: Introduction */}
            {connectStep === 1 && (
              <div className="space-y-5">
                <div className="flex items-center justify-between pb-2 border-b border-[#ECECE8]">
                  <span className="text-xs font-bold text-[#70706B]">Instagram Accounts</span>
                  <button
                    type="button"
                    onClick={() => setIsConnectModalOpen(false)}
                    className="p-1 rounded-full text-[#70706B] hover:text-[#111110] cursor-pointer"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div>
                  <h3 className="text-xl font-black text-[#111110] tracking-tight">Connect Instagram</h3>
                  <p className="text-xs text-[#70706B] mt-1 leading-snug">
                    Link your Instagram account to start automating conversations.
                  </p>
                </div>

                <div className="space-y-2.5 py-1">
                  {[
                    { label: 'Auto reply to comments', icon: MessageSquare },
                    { label: 'Send automated DMs', icon: Send },
                    { label: 'Capture and manage leads', icon: Users },
                    { label: 'Track performance', icon: BarChart2 },
                    { label: 'Grow faster', icon: TrendingUp },
                  ].map((item, idx) => {
                    const Icon = item.icon;
                    return (
                      <div key={idx} className="flex items-center gap-3 text-xs text-[#111110]">
                        <div className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                          <Icon size={13} />
                        </div>
                        <span className="font-medium">{item.label}</span>
                      </div>
                    );
                  })}
                </div>

                <div className="space-y-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setConnectStep(2)}
                    className="w-full py-3 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-bold rounded-xl transition-all cursor-pointer shadow-xs"
                  >
                    Continue
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsConnectModalOpen(false)}
                    className="w-full py-2.5 border border-[#ECECE8] hover:bg-[#FBFBFA] text-xs font-semibold text-[#111110] rounded-xl transition-all cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: Login (Redirect to Meta) */}
            {connectStep === 2 && (
              <div className="space-y-5 text-center">
                <div className="flex items-center justify-between pb-2 border-b border-[#ECECE8]">
                  <button
                    type="button"
                    onClick={() => setConnectStep(1)}
                    className="text-xs font-semibold text-[#70706B] hover:text-[#111110] cursor-pointer"
                  >
                    ← Connect Instagram
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsConnectModalOpen(false)}
                    className="p-1 rounded-full text-[#70706B] hover:text-[#111110] cursor-pointer"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="py-2">
                  <div className="inline-flex items-center gap-3.5 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#F58529] via-[#DD2A7B] to-[#8134AF] flex items-center justify-center text-white shadow-md shadow-pink-500/20">
                      <Instagram size={26} />
                    </div>
                    <MovingArrowConnector trackWidth={38} arrowSize={15} />
                    <div className="w-12 h-12 rounded-xl bg-white border border-[#ECECE8] flex items-center justify-center shadow-md p-1">
                      <BrandLogo variant="mark" height={38} />
                    </div>
                  </div>

                  <h3 className="text-lg font-black text-[#111110]">Log in with Instagram</h3>
                  <p className="text-xs text-[#70706B] mt-1.5 max-w-xs mx-auto leading-relaxed">
                    You&apos;ll be redirected to Instagram (Meta) to log in and give permissions.
                  </p>
                </div>

                <div className="space-y-2">
                  <button
                    type="button"
                    disabled={isConnectingMeta}
                    onClick={handleStartMetaOAuth}
                    className="w-full py-3.5 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer disabled:opacity-50"
                  >
                    {isConnectingMeta ? <RefreshCw className="animate-spin" size={15} /> : <Instagram size={15} />}
                    <span>{isConnectingMeta ? 'Redirecting to Meta...' : 'Continue with Instagram'}</span>
                  </button>

                  <div className="flex items-center justify-center gap-1.5 text-[11px] text-[#70706B] pt-2">
                    <ShieldCheck size={14} className="text-[#15803D]" />
                    <span>We use official Meta authentication. Your credentials are never stored.</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

