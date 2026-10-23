// client/features/automations/types.ts

export type AutomationStatus = 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'ERROR' | 'ARCHIVED';

export interface AutomationCreateInput {
  name: string;
  description?: string;
  instagram_account_id: string;
  trigger_type: string;
  flow_definition: Record<string, any>;
}

export interface AutomationUpdateInput {
  name?: string;
  description?: string;
  status?: AutomationStatus;
  instagram_account_id?: string;
  trigger_type?: string;
  flow_definition?: Record<string, any>;
}

export interface AutomationItem {
  id: string;
  workspace_id?: string;
  instagram_account_id?: string;
  name: string;
  description?: string;
  status: AutomationStatus;
  trigger_type?: string;
  triggerType?: string;
  trigger_text?: string;
  action_text?: string;
  tags?: string[];
  icon_type?: 'guide' | 'percent' | 'calendar' | 'support' | 'gift' | string;
  flow_definition?: any;
  flowDefinition?: any;
  version?: number;
  stats_comments?: number;
  stats_dms_sent?: number;
  stats_clicks?: number;
  stats_clicks_pct?: string;
  stats?: {
    comments: number;
    dmsSent: number;
    clickRate: string;
  };
  published_at?: string;
  publishedAt?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
}
