// client/src/components/automations/AutomationTypes.ts

export type TriggerCategory = 'comments' | 'messages' | 'stories' | 'live' | 'advanced';

export interface AutomationTypeOption {
  id: string;
  title: string;
  description: string;
  category: TriggerCategory;
  badge?: string;
  iconName: string;
  isLocked?: boolean;
}

export interface AutomationDraft {
  name: string;
  typeId: string;
  category: TriggerCategory;
  instagramAccountId: string;
  
  trigger: {
    type: string;
    scope: 'specific' | 'any' | 'next';
    postId?: string;
    reelId?: string;
  };

  conditions: {
    matchMode: 'specific' | 'any';
    keywords: string[];
    followerCondition: 'none' | 'require_follow';
  };

  publicReply: {
    enabled: boolean;
    messages: string[];
  };

  privateDm: {
    enabled: boolean;
    openingMessage: string;
    buttonText: string;
  };

  optionalActions: {
    followerGate: boolean;
    followerGateMessage: string;
    emailCapture: boolean;
    emailCaptureMessage: string;
    tagContact: boolean;
    tagName: string;
  };

  resource: {
    message: string;
    url: string;
    buttonText: string;
    customTitle: string;
  };

  followUp: {
    enabled: boolean;
    delayMinutes: number;
    message: string;
  };
}

export interface ValidationItem {
  id: string;
  label: string;
  status: 'valid' | 'invalid' | 'warning';
  message?: string;
  required: boolean;
}

export const DEFAULT_AUTOMATION_DRAFT: AutomationDraft = {
  name: '',
  typeId: '',
  category: 'comments',
  instagramAccountId: '',
  
  trigger: {
    type: 'COMMENT',
    scope: 'specific',
    postId: '',
  },

  conditions: {
    matchMode: 'specific',
    keywords: ['GUIDE', 'PLAYBOOK'],
    followerCondition: 'none',
  },

  publicReply: {
    enabled: true,
    messages: [
      "Check your DMs — I've sent you the guide! ✈️",
      "Sent it to your DMs! Check your inbox 📩"
    ],
  },

  privateDm: {
    enabled: true,
    openingMessage: "Hey! Thanks so much for your interest 😊\n\nClick below to access the full guide:",
    buttonText: "Send me the guide",
  },

  optionalActions: {
    followerGate: false,
    followerGateMessage: "Follow our page to instantly unlock the resource! 🙌",
    emailCapture: false,
    emailCaptureMessage: "What's the best email address to send your bonus materials to? 📬",
    tagContact: true,
    tagName: "lead",
  },

  resource: {
    message: "Here is your direct access link: 👇",
    url: "https://comlina.com/playbook",
    buttonText: "View the guide",
    customTitle: "Comlina Playbook & Direct Resource",
  },

  followUp: {
    enabled: false,
    delayMinutes: 1440, // 24 hours
    message: "Hey! Just wanted to make sure you got the guide? Let me know if you have any questions! 🚀",
  },
};

export const AUTOMATION_TYPE_OPTIONS: AutomationTypeOption[] = [
  // Comments
  {
    id: 'comment_to_dm',
    title: 'Comment → DM',
    description: 'When someone comments on your post, send a direct message.',
    category: 'comments',
    iconName: 'MessageSquare',
  },
  {
    id: 'comment_reply',
    title: 'Comment Reply',
    description: 'Automatically reply publicly to comments matching your keywords.',
    category: 'comments',
    iconName: 'Repeat',
  },
  {
    id: 'comment_to_lead',
    title: 'Comment to Lead Collection',
    description: 'Capture contact details and emails directly from post comments.',
    category: 'comments',
    iconName: 'Users',
  },

  // Messages
  {
    id: 'dm_reply',
    title: 'DM Reply',
    description: 'Auto-reply when someone sends a specific keyword in direct messages.',
    category: 'messages',
    iconName: 'Send',
  },
  {
    id: 'dm_to_lead',
    title: 'DM to Lead Collection',
    description: 'Start an automated lead qualification sequence inside direct messages.',
    category: 'messages',
    iconName: 'Users',
  },

  // Stories
  {
    id: 'story_reply',
    title: 'Story Reply',
    description: 'Auto-reply in DM when a follower responds to your Instagram Story.',
    category: 'stories',
    iconName: 'Repeat',
  },
  {
    id: 'story_mention',
    title: 'Story Mention',
    description: 'Send a thank-you DM whenever someone tags or mentions your handle in their Story.',
    category: 'stories',
    iconName: 'AtSign',
  },

  // Live
  {
    id: 'live_comment',
    title: 'Live Comment',
    description: 'Send direct messages to viewers who comment during your Instagram Live stream.',
    category: 'live',
    iconName: 'Radio',
    badge: 'PRO',
    isLocked: true,
  },

  // Advanced Workflows
  {
    id: 'ai_chat',
    title: 'AI Smart Assistant',
    description: 'Answer customer questions and handle inquiries 24/7 with trained AI.',
    category: 'advanced',
    badge: 'PRO',
    iconName: 'Sparkles',
    isLocked: true,
  },
  {
    id: 'appointment_booking',
    title: 'Appointment Booking',
    description: 'Direct followers to schedule a consultation or discovery call on your calendar.',
    category: 'advanced',
    badge: 'PRO',
    iconName: 'Calendar',
    isLocked: true,
  },
];

export function validateAutomationDraft(draft: AutomationDraft): {
  isValid: boolean;
  items: ValidationItem[];
} {
  const items: ValidationItem[] = [];

  // 1. Account
  const hasAccount = Boolean(draft.instagramAccountId);
  items.push({
    id: 'account',
    label: 'Instagram account connected',
    status: hasAccount ? 'valid' : 'invalid',
    message: hasAccount ? undefined : 'Please connect or select an Instagram account.',
    required: true,
  });

  // 2. Type
  const hasType = Boolean(draft.typeId);
  items.push({
    id: 'type',
    label: 'Automation type selected',
    status: hasType ? 'valid' : 'invalid',
    message: hasType ? undefined : 'Please choose an automation trigger type.',
    required: true,
  });

  // 3. Trigger Target
  let triggerTargetValid = true;
  if (draft.trigger.scope === 'specific' && !draft.trigger.postId) {
    triggerTargetValid = false;
  }
  items.push({
    id: 'trigger',
    label: 'Trigger & target content configured',
    status: triggerTargetValid ? 'valid' : 'invalid',
    message: triggerTargetValid ? undefined : 'Please select a specific post or Reel.',
    required: true,
  });

  // 4. Conditions
  let conditionValid = true;
  if (draft.conditions.matchMode === 'specific' && draft.conditions.keywords.length === 0) {
    conditionValid = false;
  }
  items.push({
    id: 'conditions',
    label: 'Keyword conditions defined',
    status: conditionValid ? 'valid' : 'invalid',
    message: conditionValid ? undefined : 'Add at least one keyword (e.g. GUIDE, PRICE).',
    required: true,
  });

  // 5. Public reply (if enabled)
  if (draft.publicReply.enabled) {
    const hasPublicMsg = draft.publicReply.messages.some((m) => m.trim().length > 0);
    items.push({
      id: 'public_reply',
      label: 'Public comment reply message',
      status: hasPublicMsg ? 'valid' : 'invalid',
      message: hasPublicMsg ? undefined : 'Public reply is ON — please enter a reply message.',
      required: true,
    });
  }

  // 6. Opening DM
  const hasOpeningDm = Boolean(draft.privateDm.openingMessage?.trim());
  items.push({
    id: 'opening_dm',
    label: 'Opening DM message configured',
    status: hasOpeningDm ? 'valid' : 'invalid',
    message: hasOpeningDm ? undefined : 'Please provide an opening direct message.',
    required: true,
  });

  // 7. Resource Link
  const hasValidUrl = Boolean(
    draft.resource.url &&
    (draft.resource.url.startsWith('http://') || draft.resource.url.startsWith('https://') || draft.resource.url.includes('.'))
  );
  items.push({
    id: 'resource',
    label: 'Resource link & delivery message',
    status: hasValidUrl ? 'valid' : 'invalid',
    message: hasValidUrl ? undefined : 'Please enter a valid destination URL for your resource.',
    required: true,
  });

  // 8. Follow-up (if enabled)
  if (draft.followUp.enabled) {
    const hasFollowupMsg = Boolean(draft.followUp.message?.trim());
    items.push({
      id: 'followup',
      label: 'Follow-up reminder message',
      status: hasFollowupMsg ? 'valid' : 'invalid',
      message: hasFollowupMsg ? undefined : 'Follow-up is ON — please enter reminder message.',
      required: true,
    });
  }

  const isValid = items.every((item) => (item.required ? item.status === 'valid' : true));

  return { isValid, items };
}
