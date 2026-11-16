// client/src/features/analytics/api.ts
import { api } from '@/lib/api';

export interface DailyStatItem {
  day: string;
  date: string;
  dms: number;
  comments: number;
  count: number;
  pct: number;
}

export interface AnalyticsTimeseriesItem {
  date: string;
  day: string;
  short_date: string;
  comments: number;
  dms: number;
  conversions: number;
  total: number;
  pct: number;
}

export interface AnalyticsTimeseriesResponse {
  workspace_id: string;
  days: number;
  start_date: string;
  end_date: string;
  summary: {
    total_comments: number;
    total_dms: number;
    total_conversions: number;
    conversion_rate_pct: number;
  };
  series: AnalyticsTimeseriesItem[];
}

export interface AnalyticsSummary {
  workspace_id: string;
  total_automations: number;
  active_automations: number;
  total_leads: number;
  converted_leads: number;
  conversion_rate_pct: number;
  stats_comments: number;
  stats_dms_sent: number;
  stats_clicks: number;
  delivery_health?: number | null;
  queue_latency?: number | null;
  daily_stats?: DailyStatItem[];
}

export const analyticsApi = {
  getSummary: () => api.get<AnalyticsSummary>('/analytics/summary'),
  getTimeseries: (days = 30) => api.get<AnalyticsTimeseriesResponse>(`/analytics/timeseries?days=${days}`),
};

