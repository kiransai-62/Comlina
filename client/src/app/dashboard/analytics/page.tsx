// client/src/app/dashboard/analytics/page.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart2, 
  ArrowUpRight, 
  AlertCircle,
  RefreshCw,
  Plus,
  Calendar,
  MessageSquare,
  Send,
  Users
} from 'lucide-react';
import { analyticsApi, AnalyticsSummary, AnalyticsTimeseriesResponse } from '@/features/analytics/api';

export default function AnalyticsPage() {
  const [timeframe, setTimeframe] = useState<7 | 14 | 30 | 90>(30);

  const { data: summary, isLoading, isError, error, refetch } = useQuery<AnalyticsSummary>({
    queryKey: ['analytics-summary'],
    queryFn: () => analyticsApi.getSummary(),
    refetchInterval: 10_000,
  });

  const { data: timeseriesData, isLoading: loadingTimeseries, refetch: refetchTimeseries } = useQuery<AnalyticsTimeseriesResponse>({
    queryKey: ['analytics-timeseries', timeframe],
    queryFn: () => analyticsApi.getTimeseries(timeframe),
    refetchInterval: 15_000,
  });

  const comments = summary?.stats_comments ?? 0;
  const dmsSent = summary?.stats_dms_sent ?? 0;
  const totalLeads = summary?.total_leads ?? 0;
  const conversionRateDisplay = summary?.conversion_rate_pct != null ? `${summary.conversion_rate_pct}%` : '—';
  const activeAutomations = summary?.active_automations ?? 0;
  const hasActivity = comments > 0 || dmsSent > 0 || totalLeads > 0;

  const seriesItems = timeseriesData?.series || [];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header with Timeframe Selectors */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#111110] tracking-tight">Analytics</h1>
          <p className="text-xs text-[#70706B] mt-0.5">Real-time automation performance, comment triggers, and conversion funnel.</p>
        </div>

        <div className="flex items-center gap-1.5 bg-white border border-[#ECECE8] p-1 rounded-xl shadow-2xs">
          {[
            { label: '7D', value: 7 },
            { label: '14D', value: 14 },
            { label: '30D', value: 30 },
            { label: '90D', value: 90 },
          ].map((tf) => (
            <button
              key={tf.value}
              type="button"
              onClick={() => setTimeframe(tf.value as any)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                timeframe === tf.value
                  ? 'bg-[#064125] text-white shadow-xs'
                  : 'text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F1]'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {isError && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-900 rounded-xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs">
            <AlertCircle size={16} className="text-red-600 shrink-0" />
            <span>{(error as any)?.message || 'Could not load live analytics from backend server.'}</span>
          </div>
          <button
            onClick={() => { refetch(); refetchTimeseries(); }}
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

      {/* Visual Time-Series Activity Chart */}
      <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#ECECE8] pb-4">
          <div>
            <h2 className="font-bold text-sm text-[#111110]">
              Daily Automation Telemetry ({timeframe} Days)
            </h2>
            <p className="text-xs text-[#70706B] mt-0.5">
              Daily volume of comments triggered, private DMs sent, and leads converted.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-[#70706B]">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#064125]" /> Comments &amp; DMs
            </span>
            <span className="text-xs text-[#15803D] bg-[#EAF6EE] px-2.5 py-0.5 rounded-full font-semibold">
              Live Sync
            </span>
          </div>
        </div>

        {!hasActivity && !isLoading && !loadingTimeseries ? (
          <div className="py-12 text-center space-y-2">
            <BarChart2 size={24} className="mx-auto text-[#9E9E96]" />
            <div className="text-sm font-semibold text-[#111110]">
              No activity yet in this period. Publish an automation to start collecting data.
            </div>
            <p className="text-xs text-[#70706B] max-w-sm mx-auto">
              Activity bars will plot here dynamically once users engage with your posts and trigger automations.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="h-56 flex items-end justify-between gap-1 sm:gap-2 pt-8 pb-2 overflow-x-auto no-scrollbar">
              {seriesItems.length > 0 ? (
                seriesItems.map((item) => (
                  <div key={item.date} className="flex-1 min-w-[14px] flex flex-col items-center gap-2 group/bar relative">
                    <div 
                      style={{ height: `${item.pct > 0 ? item.pct : 4}%` }}
                      className={`w-full max-w-[28px] rounded-t-md transition-all cursor-pointer ${
                        item.pct > 0 
                          ? 'bg-[#064125] hover:bg-[#15803D]' 
                          : 'bg-[#ECECE8] hover:bg-[#E0E0DA]'
                      }`}
                    />
                    <span className="text-[10px] text-[#70706B] font-medium hidden sm:inline">
                      {timeframe <= 14 ? item.day : item.short_date.split(' ')[1]}
                    </span>
                    {/* Rich Hover Tooltip */}
                    <div className="absolute -top-16 opacity-0 group-hover/bar:opacity-100 transition-opacity bg-[#111110] text-white text-[11px] p-2 rounded-lg shadow-xl pointer-events-none whitespace-nowrap z-20 space-y-0.5">
                      <div className="font-bold border-b border-white/20 pb-0.5 mb-0.5">{item.date} ({item.day})</div>
                      <div className="flex justify-between gap-3">
                        <span className="text-[#A1A19A]">Comments:</span>
                        <span className="font-semibold">{item.comments}</span>
                      </div>
                      <div className="flex justify-between gap-3">
                        <span className="text-[#A1A19A]">DMs Sent:</span>
                        <span className="font-semibold">{item.dms}</span>
                      </div>
                      <div className="flex justify-between gap-3">
                        <span className="text-[#A1A19A]">Total:</span>
                        <span className="font-bold text-[#86EFAC]">{item.total}</span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="w-full text-center py-10 text-xs text-[#70706B]">
                  Loading timeseries telemetry...
                </div>
              )}
            </div>

            <div className="flex items-center justify-between text-xs text-[#70706B] pt-2 border-t border-[#ECECE8]">
              <span>Start: {timeseriesData?.start_date || '—'}</span>
              <span>
                Total Period Events: <strong className="text-[#111110]">
                  {((timeseriesData?.summary.total_comments || 0) + (timeseriesData?.summary.total_dms || 0)).toLocaleString()}
                </strong>
              </span>
              <span>End: {timeseriesData?.end_date || 'Today'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
