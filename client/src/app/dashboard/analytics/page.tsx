// client/src/app/dashboard/analytics/page.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart2, 
  ArrowUpRight, 
  AlertCircle,
  RefreshCw,
  Plus
} from 'lucide-react';
import { analyticsApi, AnalyticsSummary } from '@/features/analytics/api';

export default function AnalyticsPage() {
  const { data: summary, isLoading, isError, error, refetch } = useQuery<AnalyticsSummary>({
    queryKey: ['analytics-summary'],
    queryFn: () => analyticsApi.getSummary(),
    refetchInterval: 10_000,
  });


  const comments = summary?.stats_comments ?? 0;
  const dmsSent = summary?.stats_dms_sent ?? 0;
  const totalLeads = summary?.total_leads ?? 0;
  const conversionRateDisplay = summary?.conversion_rate_pct != null ? `${summary.conversion_rate_pct}%` : '—';
  const activeAutomations = summary?.active_automations ?? 0;
  const hasActivity = comments > 0 || dmsSent > 0 || totalLeads > 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#111110] tracking-tight">Analytics</h1>
      </div>

      {isError && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-900 rounded-xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs">
            <AlertCircle size={16} className="text-red-600 shrink-0" />
            <span>{(error as any)?.message || 'Could not load live analytics from backend server.'}</span>
          </div>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-all cursor-pointer shrink-0"
          >
            <RefreshCw size={12} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Empty State Banner when all totals are 0 */}
      {!hasActivity && !isLoading && (
        <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#70706B]">
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

      {/* Metric Cards */}
      <div className="grid grid-cols-1 min-[420px]:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-sm">
          <div className="text-xs font-semibold text-[#70706B]">Comments Triggered</div>
          <div className="text-3xl font-extrabold text-[#111110] mt-2">
            {isLoading ? '...' : comments.toLocaleString()}
          </div>
          <div className="text-xs font-medium text-[#15803D] mt-1 flex items-center gap-1">
            <ArrowUpRight size={13} />
            <span>Automated comment responses</span>
          </div>
        </div>

        <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-sm">
          <div className="text-xs font-semibold text-[#70706B]">Private DMs Delivered</div>
          <div className="text-3xl font-extrabold text-[#111110] mt-2">
            {isLoading ? '...' : dmsSent.toLocaleString()}
          </div>
          <div className="text-xs font-medium text-[#15803D] mt-1 flex items-center gap-1">
            <ArrowUpRight size={13} />
            <span>Direct Instagram messages</span>
          </div>
        </div>

        <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-sm">
          <div className="text-xs font-semibold text-[#70706B]">Total Captured Leads</div>
          <div className="text-3xl font-extrabold text-[#111110] mt-2">
            {isLoading ? '...' : totalLeads.toLocaleString()}
          </div>
          <div className="text-xs font-medium text-[#15803D] mt-1 flex items-center gap-1">
            <ArrowUpRight size={13} />
            <span>Audience in Contacts database</span>
          </div>
        </div>

        <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-sm">
          <div className="text-xs font-semibold text-[#70706B]">Lead Conversion Rate</div>
          <div className="text-3xl font-extrabold text-[#111110] mt-2">
            {isLoading ? '...' : conversionRateDisplay}
          </div>
          <div className="text-xs font-medium text-[#15803D] mt-1 flex items-center gap-1">
            <ArrowUpRight size={13} />
            <span>{activeAutomations} active automations running</span>
          </div>
        </div>
      </div>

      {/* Visual Activity */}
      <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-sm text-[#111110]">Automation Activity Overview</h2>
          <span className="text-xs text-[#15803D] bg-[#EAF6EE] px-2.5 py-0.5 rounded-full font-semibold">
            Real-time Telemetry
          </span>
        </div>

        {!hasActivity && !isLoading ? (
          <div className="py-12 text-center space-y-2">
            <BarChart2 size={24} className="mx-auto text-[#9E9E96]" />
            <div className="text-sm font-semibold text-[#111110]">
              No activity yet. Publish an automation to start collecting data.
            </div>
            <p className="text-xs text-[#70706B] max-w-sm mx-auto">
              Activity bars will plot here dynamically once users engage with your posts and trigger automations.
            </p>
          </div>
        ) : (
          <div className="h-48 flex items-end justify-between gap-3 pt-6 border-b border-[#ECECE8] pb-2">
            {(summary?.daily_stats || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => ({ day: d, count: 0, pct: 0 }))).map((item) => (
              <div key={item.day} className="flex-1 flex flex-col items-center gap-2 group/bar relative">
                <div 
                  style={{ height: `${item.pct > 0 ? item.pct : 4}%` }}
                  className={`w-full rounded-t-md transition-all cursor-pointer ${
                    item.pct > 0 
                      ? 'bg-[#062E1A] hover:bg-[#15803D]' 
                      : 'bg-[#ECECE8] hover:bg-[#E0E0DA]'
                  }`}
                />
                <span className="text-xs text-[#70706B] font-medium">{item.day}</span>
                <div className="absolute -top-7 opacity-0 group-hover/bar:opacity-100 transition-opacity bg-[#111110] text-white text-[10px] px-2 py-0.5 rounded shadow pointer-events-none whitespace-nowrap z-10">
                  {item.count} {item.count === 1 ? 'msg' : 'msgs'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
