// client/src/features/analytics/api.ts
import { api } from '@/lib/api';

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
}

export const analyticsApi = {
  getSummary: () => api.get<AnalyticsSummary>('/analytics/summary'),
};
