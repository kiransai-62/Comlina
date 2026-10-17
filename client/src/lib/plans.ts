// client/src/lib/plans.ts
/**
 * Comlina Centralized Plan Configuration & Feature Entitlements
 *
 * Defines Free, Premium (₹199/month), and Pro (₹399/month) tiers,
 * quotas, and feature flags used across the UI, feature gates, and pricing pages.
 */

export type PlanTier = 'FREE' | 'PREMIUM' | 'PRO';

export interface PlanFeatureDefinition {
  key: string;
  name: string;
  description: string;
  requiredTier: PlanTier;
  category: 'core' | 'conversion' | 'advanced';
}

export interface PlanConfig {
  id: PlanTier;
  name: string;
  tagline: string;
  priceInr: number;
  pricePaise: number;
  billingPeriod: string;
  badgeText?: string;
  maxPostsQuota: number; // 10 for Free, 100 for Premium, -1 (unlimited) for Pro
  maxDmsPerPost: number; // 99 for Free, 2500 for Premium, 10000 for Pro
  maxAutomations: number;
  maxAccounts: number;
  features: Record<string, boolean>;
  highlights: string[];
}

export const PLAN_CONFIGS: Record<PlanTier, PlanConfig> = {
  FREE: {
    id: 'FREE',
    name: 'Free',
    tagline: 'Get started with essential Comment-to-DM automation',
    priceInr: 0,
    pricePaise: 0,
    billingPeriod: 'month',
    maxPostsQuota: 10,
    maxDmsPerPost: 99,
    maxAutomations: 10,
    maxAccounts: 1,
    features: {
      comment_to_dm_basic: true,
      trigger_response_dm: true,
      basic_keywords: true,
      reply_to_all: false,
      ask_to_follow: false,
      comment_teaser_reply: false,
      dm_buttons: false,
      follow_up_dms: false,
      expanded_keywords: false,
      live_comment: false,
      ai_smart_assistant: false,
      appointment_booking: false,
      advanced_workflows: false,
      create_lead_flow: false,
      dm_reply: false,
      dm_to_lead: false,
    },
    highlights: [
      'Up to 10 automated posts total',
      'Up to 99 DMs per post',
      'Basic Comment-to-DM trigger',
      'Direct trigger response message',
      'Up to 3 basic trigger keywords',
      'Standard messaging delivery',
    ],
  },
  PREMIUM: {
    id: 'PREMIUM',
    name: 'Premium',
    tagline: 'Boost follower conversion with smart verification and teaser replies',
    priceInr: 199,
    pricePaise: 19900,
    billingPeriod: 'month',
    badgeText: 'MOST POPULAR',
    maxPostsQuota: 100,
    maxDmsPerPost: 2500,
    maxAutomations: 50,
    maxAccounts: 3,
    features: {
      comment_to_dm_basic: true,
      trigger_response_dm: true,
      basic_keywords: true,
      reply_to_all: true,
      ask_to_follow: true,
      comment_teaser_reply: true,
      dm_buttons: true,
      follow_up_dms: true,
      expanded_keywords: true,
      live_comment: false,
      ai_smart_assistant: false,
      appointment_booking: false,
      advanced_workflows: false,
      create_lead_flow: false,
      dm_reply: false,
      dm_to_lead: false,
    },
    highlights: [
      'Everything in Free',
      '100 automated posts & 2,500 DMs/post',
      'Ask to Follow (Follower gate check)',
      'Public Comment Teaser replies',
      'Interactive DM buttons with link tracking',
      'Scheduled follow-up DMs',
      'Reply to all comments (no keyword required)',
      'Unlimited trigger keywords & phrases',
    ],
  },
  PRO: {
    id: 'PRO',
    name: 'Pro',
    tagline: 'Full power automation with AI Assistant, Live Comments & Booking',
    priceInr: 399,
    pricePaise: 39900,
    billingPeriod: 'month',
    badgeText: 'BEST VALUE',
    maxPostsQuota: -1, // Unlimited
    maxDmsPerPost: 10000,
    maxAutomations: 200,
    maxAccounts: 10,
    features: {
      comment_to_dm_basic: true,
      trigger_response_dm: true,
      basic_keywords: true,
      reply_to_all: true,
      ask_to_follow: true,
      comment_teaser_reply: true,
      dm_buttons: true,
      follow_up_dms: true,
      expanded_keywords: true,
      live_comment: true,
      ai_smart_assistant: true,
      appointment_booking: true,
      advanced_workflows: true,
      create_lead_flow: true,
      dm_reply: true,
      dm_to_lead: true,
    },
    highlights: [
      'Everything in Premium',
      'Unlimited automated posts',
      'Up to 10,000 DMs per post',
      'Live Comment automation (Instagram Live)',
      'Create Lead Flow & Comment Lead capture',
      'DM Reply & DM to Lead Collection sequences',
      'AI Smart Assistant for contextual replies',
      'Appointment Booking & calendar integration',
      'AI Smart Assistant for contextual replies',
      'Appointment Booking & calendar integration',
      'Multi-step advanced workflow DAGs',
      'Priority delivery queue & rate limit safety',
    ],
  },
};

export const FEATURE_CATALOG: PlanFeatureDefinition[] = [
  {
    key: 'comment_to_dm_basic',
    name: 'Comment-to-DM Automation',
    description: 'Instantly send a direct message when someone comments on your post or reel.',
    requiredTier: 'FREE',
    category: 'core',
  },
  {
    key: 'trigger_response_dm',
    name: 'Trigger Response DM',
    description: 'Deliver links, guides, discounts, or downloads in the first automated DM.',
    requiredTier: 'FREE',
    category: 'core',
  },
  {
    key: 'basic_keywords',
    name: 'Basic Keyword Triggers',
    description: 'Trigger automation when comments match specific words (up to 3 keywords in Free).',
    requiredTier: 'FREE',
    category: 'core',
  },
  {
    key: 'reply_to_all',
    name: 'Reply to All Comments',
    description: 'Engage every commenter without requiring an exact keyword trigger.',
    requiredTier: 'PREMIUM',
    category: 'conversion',
  },
  {
    key: 'ask_to_follow',
    name: 'Ask to Follow (Follower Gate)',
    description: 'Check if the commenter follows you before delivering the link or discount.',
    requiredTier: 'PREMIUM',
    category: 'conversion',
  },
  {
    key: 'comment_teaser_reply',
    name: 'Comment Teaser Reply',
    description: 'Post a public reply ("Check your DM! 📩") to boost post engagement algorithmically.',
    requiredTier: 'PREMIUM',
    category: 'conversion',
  },
  {
    key: 'dm_buttons',
    name: 'Interactive DM Buttons',
    description: 'Add actionable web link buttons to your automated Instagram direct messages.',
    requiredTier: 'PREMIUM',
    category: 'conversion',
  },
  {
    key: 'follow_up_dms',
    name: 'Follow-up DMs',
    description: 'Automatically check in hours later if the contact has not clicked or converted.',
    requiredTier: 'PREMIUM',
    category: 'conversion',
  },
  {
    key: 'expanded_keywords',
    name: 'Unlimited Keywords & Phrases',
    description: 'Configure multiple keywords, partial matching, and conversational trigger phrases.',
    requiredTier: 'PREMIUM',
    category: 'conversion',
  },
  {
    key: 'live_comment',
    name: 'Live Comment Automation',
    description: 'Automate DM responses to comments while hosting Instagram Live broadcasts.',
    requiredTier: 'PRO',
    category: 'advanced',
  },
  {
    key: 'ai_smart_assistant',
    name: 'AI Smart Assistant',
    description: 'Context-aware AI replies that answer questions, recommend products, and handle objections.',
    requiredTier: 'PRO',
    category: 'advanced',
  },
  {
    key: 'appointment_booking',
    name: 'Appointment Booking',
    description: 'Qualify leads and book discovery calls or appointments directly inside Instagram DMs.',
    requiredTier: 'PRO',
    category: 'advanced',
  },
  {
    key: 'create_lead_flow',
    name: 'Create Lead Flow',
    description: 'Capture contact details and emails directly from post comments.',
    requiredTier: 'PRO',
    category: 'advanced',
  },
  {
    key: 'dm_reply',
    name: 'DM Reply Flow',
    description: 'Auto-reply when someone sends a specific keyword in direct messages.',
    requiredTier: 'PRO',
    category: 'advanced',
  },
  {
    key: 'dm_to_lead',
    name: 'DM to Lead Collection',
    description: 'Start an automated lead qualification sequence inside direct messages.',
    requiredTier: 'PRO',
    category: 'advanced',
  },
];

export function getPlan(tier?: string | null): PlanConfig {
  const normalized = (tier || 'FREE').toUpperCase() as PlanTier;
  return PLAN_CONFIGS[normalized] || PLAN_CONFIGS.FREE;
}

export function hasFeature(currentTier: string | null | undefined, featureKey: string): boolean {
  const plan = getPlan(currentTier);
  return Boolean(plan.features[featureKey]);
}

export function getRequiredPlan(featureKey: string): PlanTier {
  const feat = FEATURE_CATALOG.find((f) => f.key === featureKey);
  return feat?.requiredTier || 'PREMIUM';
}

export function isFeatureLocked(currentTier: string | null | undefined, featureKey: string): boolean {
  return !hasFeature(currentTier, featureKey);
}
