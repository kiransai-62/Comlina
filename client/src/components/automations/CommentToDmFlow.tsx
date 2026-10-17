// client/src/components/automations/CommentToDmFlow.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  RefreshCw, 
  Sparkles, 
  MessageSquare, 
  Send, 
  Repeat, 
  UserPlus, 
  Link2, 
  Clock, 
  Plus, 
  X, 
  Trash2, 
  Check, 
  Save, 
  HelpCircle,
  ExternalLink,
  Bot,
  Calendar,
  Radio,
  Lock,
  ArrowUpRight
} from 'lucide-react';
import { SAMPLE_INSTAGRAM_POSTS, InstagramMediaItem } from './PostSelector';
import { instagramApi } from '@/features/instagram/api';
import { FlowActionButtons } from './FlowActionButtons';
import { FeatureGate } from '@/components/billing/FeatureGate';
import { PlanBadge } from '@/components/billing/PlanBadge';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { usePlan } from '@/hooks/usePlan';

export interface DMButton {
  id: string;
  label: string;
  url: string;
}

export interface FollowUpItem {
  id: string;
  hours: number;
  minutes: number;
  seconds: number;
  message: string;
}

interface CommentToDmFlowProps {
  onBack: () => void;
  onSave: (flowData: any) => Promise<void>;
  accountName?: string;
  isSaving?: boolean;
  onPreviewChange?: (previewData: any) => void;
}

export function CommentToDmFlow({
  onBack,
  onSave,
  accountName = 'yourbrand',
  isSaving = false,
  onPreviewChange,
}: CommentToDmFlowProps) {
  const { planTier, isLocked, usage, fetchUsage, openUpgradeModal } = usePlan();

  useEffect(() => {
    fetchUsage();
  }, []);

  // 1. Post Selection State
  const [selectedPostId, setSelectedPostId] = useState<string>('all');
  const [isScanning, setIsScanning] = useState(false);
  const [posts, setPosts] = useState<InstagramMediaItem[]>(SAMPLE_INSTAGRAM_POSTS);

  useEffect(() => {
    let mounted = true;
    instagramApi.getMedia()
      .then((data) => {
        if (mounted && data && data.length > 0) {
          setPosts(data as InstagramMediaItem[]);
        }
      })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  // 2. Reply to All State
  const [replyToAll, setReplyToAll] = useState(false);

  // 3. Trigger Keywords State
  const [keywordInput, setKeywordInput] = useState('');
  const [keywords, setKeywords] = useState<string[]>(['PRICE', 'LINK', 'INFO']);

  // 4. Ask to Follow State (PREMIUM)
  const [askFollowEnabled, setAskFollowEnabled] = useState(false);
  const [askFollowMessage, setAskFollowMessage] = useState(
    `Hey! 👋 Please follow @${accountName} first to receive this content.\n\nTap the follow button below, then send any message here and we'll check instantly and send your content. 🙏`
  );
  const [retryMessage, setRetryMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [followButtonLabel, setFollowButtonLabel] = useState('');

  // 5. Comment Teaser Reply State (PREMIUM)
  const [teaserEnabled, setTeaserEnabled] = useState(false);
  const [teaserMessage, setTeaserMessage] = useState('Check your DM! 📩');

  // 6. Trigger Response DM State
  const [responseDm, setResponseDm] = useState("Hey! 👋 Here's what you asked for:\nhttps://comlina.com/playbook");

  // 7. DM Buttons State
  const [buttons, setButtons] = useState<DMButton[]>([
    { id: 'btn_1', label: 'View the guide', url: 'https://comlina.com/playbook' }
  ]);
  const [showAddButton, setShowAddButton] = useState(false);
  const [newButtonLabel, setNewButtonLabel] = useState('');
  const [newButtonUrl, setNewButtonUrl] = useState('');

  // 8. Follow-up DMs State (PREMIUM)
  const [followUpEnabled, setFollowUpEnabled] = useState(false);
  const [followUps, setFollowUps] = useState<FollowUpItem[]>([
    {
      id: 'fu_1',
      hours: 2,
      minutes: 0,
      seconds: 0,
      message: 'Hey! Just checking in — did you get a chance to look at what I sent?',
    },
    {
      id: 'fu_2',
      hours: 12,
      minutes: 0,
      seconds: 0,
      message: 'Hey! Just checking in — did you get a chance to look at what I sent?',
    },
  ]);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [stopKeywords, setStopKeywords] = useState('stop, unsubscribe, cancel, no thanks');
  const [stopDetails, setStopDetails] = useState<string[]>(['Phone number', 'Email address']);
  const [otherDetails, setOtherDetails] = useState('');

  // Pro Features State
  const [liveCommentEnabled, setLiveCommentEnabled] = useState(false);
  const [aiAssistantEnabled, setAiAssistantEnabled] = useState(false);
  const [appointmentBookingEnabled, setAppointmentBookingEnabled] = useState(false);

  // Synchronize Live Preview Setup
  React.useEffect(() => {
    onPreviewChange?.({
      keywords,
      publicReplyEnabled: teaserEnabled,
      publicReplyText: teaserMessage,
      openingDmEnabled: true,
      openingDmText: responseDm,
      openingDmButtonText: buttons[0]?.label || 'View the guide',
      deliveryLinkUrl: buttons[0]?.url || '',
      deliveryLinkButtonText: buttons[0]?.label || 'View the guide',
      deliveryText: responseDm,
      askFollowEnabled,
      askFollowText: askFollowMessage,
      followupEnabled: followUpEnabled && followUps.length > 0,
      followupHours: followUps[0]?.hours || 2,
      followupText: followUps[0]?.message || '',
      defaultTab: 'dm',
      isStoryFlow: false,
    });
  }, [
    keywords,
    teaserEnabled,
    teaserMessage,
    responseDm,
    buttons,
    askFollowEnabled,
    askFollowMessage,
    followUpEnabled,
    followUps,
    onPreviewChange,
  ]);

  // Handlers
  const handleAddKeyword = () => {
    const trimmed = keywordInput.trim().toUpperCase();
    if (!trimmed) return;
    if (keywords.includes(trimmed)) {
      setKeywordInput('');
      return;
    }
    if (keywords.length >= 3 && isLocked('expanded_keywords')) {
      openUpgradeModal('PREMIUM', 'expanded_keywords');
      return;
    }
    setKeywords([...keywords, trimmed]);
    setKeywordInput('');
  };

  const handleKeywordKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  const handleRemoveKeyword = (kwToRemove: string) => {
    setKeywords(keywords.filter((kw) => kw !== kwToRemove));
  };

  const handleAddDMButton = () => {
    if (!newButtonLabel.trim()) return;
    setButtons([
      ...buttons,
      {
        id: `btn_${Date.now()}`,
        label: newButtonLabel.trim(),
        url: newButtonUrl.trim() || 'https://comlina.com',
      },
    ]);
    setNewButtonLabel('');
    setNewButtonUrl('');
    setShowAddButton(false);
  };

  const handleRemoveDMButton = (id: string) => {
    setButtons(buttons.filter((b) => b.id !== id));
  };

  const handleAddFollowUp = () => {
    setFollowUps([
      ...followUps,
      {
        id: `fu_${Date.now()}`,
        hours: 24,
        minutes: 0,
        seconds: 0,
        message: 'Hey! Just wanted to make sure you got the resource? Let me know if you need anything!',
      },
    ]);
  };

  const handleRemoveFollowUp = (id: string) => {
    setFollowUps(followUps.filter((fu) => fu.id !== id));
  };

  const handleToggleStopDetail = (detail: string) => {
    if (stopDetails.includes(detail)) {
      setStopDetails(stopDetails.filter((d) => d !== detail));
    } else {
      setStopDetails([...stopDetails, detail]);
    }
  };

  const handleRescan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
    }, 800);
  };

  const handleSaveClick = async (status: 'DRAFT' | 'ACTIVE' = 'ACTIVE') => {
    const payload = {
      type: 'COMMENT_TO_DM',
      status,
      selectedPostId,
      replyToAll,
      keywords: replyToAll ? [] : keywords,
      askFollow: {
        enabled: askFollowEnabled,
        message: askFollowMessage,
        retryMessage,
        successMessage,
        buttonLabel: followButtonLabel,
      },
      teaserReply: {
        enabled: teaserEnabled,
        message: teaserMessage,
      },
      responseDm: {
        message: responseDm,
        buttons,
      },
      followUp: {
        enabled: followUpEnabled,
        items: followUps,
        aiPrompt,
        stopKeywords,
        stopDetails,
        otherDetails,
      },
      liveCommentEnabled,
      aiSmartAssistantEnabled: aiAssistantEnabled,
      appointmentBookingEnabled,
    };

    await onSave(payload);
  };

  const isFormValid = (replyToAll || keywords.length > 0) && !!responseDm.trim();

  const availableDetails = ['Phone number', 'Email address', 'Address', 'Name', 'Pick a time slot'];

  return (
    <div className="max-w-4xl mx-auto pb-24 text-[#111110] space-y-6">
      <UpgradeModal />
      
      {/* HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#ECECE8]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="p-2 rounded-xl border border-[#ECECE8] hover:bg-white text-[#70706B] hover:text-[#111110] transition-colors cursor-pointer"
            title="Back to Automation Selection"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-[#111110] tracking-tight">
                Comment to DM Flow
              </h1>
              <PlanBadge tier={planTier} size="xs" />
            </div>
            <p className="text-xs text-[#70706B]">
              Set up automated responses when users comment keywords
            </p>
          </div>
        </div>

        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
        />
      </div>

      {/* Post Quota Limit Banner for Free Plan */}
      {usage?.is_post_quota_reached && planTier === 'FREE' && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-100 text-amber-800 rounded-xl">
              <Lock size={16} />
            </div>
            <div>
              <div className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                <span>Free Plan Limit Reached: 10/10 Posts Automated</span>
              </div>
              <p className="text-[11px] text-amber-800 mt-0.5">
                You have reached the Free tier quota. Upgrade to Premium (100 posts) or Pro (unlimited) to automate new posts.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => openUpgradeModal('PREMIUM')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white shadow-xs transition-colors cursor-pointer"
          >
            <span>Upgrade to Premium</span>
            <ArrowUpRight size={13} />
          </button>
        </div>
      )}

      {/* 1. SELECT POST CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[#111110]"><MessageSquare size={16} /></span>
            <h2 className="text-sm font-bold text-[#111110]">Select Post</h2>
            {usage && (
              <span className="text-[11px] text-[#70706B] font-medium">
                ({usage.posts_used} / {usage.posts_limit === -1 ? 'Unlimited' : usage.posts_limit} posts automated • Max {usage.max_dms_per_post} DMs/post)
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={handleRescan}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] text-[#70706B] transition-colors cursor-pointer shadow-2xs"
          >
            <RefreshCw size={12} className={isScanning ? 'animate-spin' : ''} />
            <span>Re-scan all</span>
          </button>
        </div>
        <p className="text-xs text-[#70706B] -mt-2">
          Choose a specific post or apply to all posts.
        </p>

        {/* Post Selection Horizontal Scroller / Grid */}
        <div className="flex items-center gap-3 overflow-x-auto pb-2 pt-1 scrollbar-thin">
          {/* Card 1: All Posts */}
          <div
            onClick={() => setSelectedPostId('all')}
            className={`w-32 h-32 rounded-2xl border-2 flex flex-col items-center justify-center p-3 text-center shrink-0 cursor-pointer transition-all ${
              selectedPostId === 'all'
                ? 'border-[#0066FF] bg-[#F0F7FF] shadow-xs'
                : 'border-[#ECECE8] bg-[#FBFBFA] hover:border-gray-300'
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-[#EBF5FF] text-[#0066FF] flex items-center justify-center mb-2">
              <Sparkles size={16} />
            </div>
            <span className="text-xs font-bold text-[#111110]">All Posts</span>
            {selectedPostId === 'all' && (
              <span className="text-[10px] text-[#0066FF] font-semibold mt-1">Active</span>
            )}
          </div>

          {/* Subsequent Post Thumbnails */}
          {posts.map((post) => {
            const isSelected = selectedPostId === post.id;
            return (
              <div
                key={post.id}
                onClick={() => setSelectedPostId(post.id)}
                className={`w-32 h-32 rounded-2xl border-2 overflow-hidden shrink-0 relative cursor-pointer group transition-all ${
                  isSelected
                    ? 'border-[#0066FF] ring-2 ring-[#0066FF]/20 shadow-md'
                    : 'border-[#ECECE8] hover:border-gray-400'
                }`}
              >
                <img
                  src={post.imageUrl}
                  alt={post.caption}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent p-2 flex flex-col justify-end text-white">
                  <span className="text-xs font-medium line-clamp-2 leading-tight">
                    {post.caption}
                  </span>
                </div>
                {isSelected && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#0066FF] text-white flex items-center justify-center shadow">
                    <Check size={12} strokeWidth={3} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. REPLY TO ALL CARD (GATED: PREMIUM / PRO) */}
      <FeatureGate featureKey="reply_to_all">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#F0FDF4] text-[#15803D] flex items-center justify-center shrink-0">
              <Repeat size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-[#111110]">Reply to All</h2>
                <PlanBadge tier="PREMIUM" size="xs" />
              </div>
              <div className="text-xs font-semibold text-[#111110] mt-0.5">Enable Reply to All</div>
              <p className="text-xs text-[#70706B]">Respond to ALL comments without keyword matching</p>
            </div>
          </div>

          {/* Toggle Switch */}
          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={replyToAll}
              onChange={(e) => setReplyToAll(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
          </label>
        </div>
      </FeatureGate>

      {/* 3. TRIGGER KEYWORDS CARD (Hidden if Reply to All is checked) */}
      {!replyToAll && (
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><MessageSquare size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">Trigger Keywords</h2>
            </div>
            {isLocked('expanded_keywords') && (
              <span className="text-[11px] text-[#70706B] font-semibold">
                Free limit: {keywords.length} / 3 keywords
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#111110] mb-1.5">
              What keywords should they comment?
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={handleKeywordKeyDown}
                placeholder={
                  keywords.length >= 3 && isLocked('expanded_keywords')
                    ? '3 keywords limit reached (Upgrade to add more)'
                    : 'Type keyword and press Enter'
                }
                disabled={keywords.length >= 3 && isLocked('expanded_keywords')}
                className="flex-1 px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF] disabled:bg-gray-50"
              />
              <button
                type="button"
                onClick={handleAddKeyword}
                className="px-4 py-2.5 bg-[#F4F4F0] hover:bg-[#ECECE8] text-[#111110] text-xs font-bold rounded-xl transition-colors cursor-pointer"
              >
                Add
              </button>
            </div>
          </div>

          {/* Keyword quota warning for Free tier */}
          {keywords.length >= 3 && isLocked('expanded_keywords') && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between text-xs text-amber-800">
              <span>Free plan limit: 3 keywords reached ({keywords.length}/3).</span>
              <button
                type="button"
                onClick={() => openUpgradeModal('PREMIUM', 'expanded_keywords')}
                className="font-bold underline text-amber-900 cursor-pointer"
              >
                Unlock Unlimited Keywords
              </button>
            </div>
          )}

          {/* Chips */}
          <div className="flex flex-wrap gap-2 pt-1">
            {keywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#F4F4F0] text-[#111110] text-xs font-bold rounded-lg border border-[#ECECE8]"
              >
                <span>{kw}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(kw)}
                  className="text-[#70706B] hover:text-red-600 cursor-pointer"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>

          <p className="text-[11px] text-[#70706B]">
            Users who comment any of these keywords will trigger the automation
          </p>
        </div>
      )}

      {/* 4. ASK TO FOLLOW CARD (GATED: PREMIUM / PRO) */}
      <FeatureGate featureKey="ask_to_follow">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><UserPlus size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">Ask to Follow</h2>
              <PlanBadge tier="PREMIUM" size="xs" />
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={askFollowEnabled}
                onChange={(e) => setAskFollowEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
            </label>
          </div>

          <div>
            <div className="text-xs font-semibold text-[#111110]">Ask user to follow first</div>
            <p className="text-xs text-[#70706B]">Politely ask the user to follow you before receiving the DM</p>
          </div>

          {askFollowEnabled && (
            <div className="space-y-4 pt-3 border-t border-[#ECECE8] animate-in fade-in duration-150">
              {/* Blue Callout: How it works */}
              <div className="p-4 bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl text-xs text-[#1E40AF] space-y-1.5 leading-relaxed">
                <div className="font-bold flex items-center gap-1.5 text-[#1D4ED8]">
                  <span>💡</span>
                  <span>How it works:</span>
                </div>
                <ol className="list-decimal list-inside space-y-1 text-[11px] text-[#1E3A8A]">
                  <li>User comments the keyword on your post</li>
                  <li>Bot sends a DM with a follow button</li>
                  <li>User taps the button, follows your account, then replies or wait</li>
                  <li>Bot verifies the follow and sends the content instantly ✅</li>
                </ol>
              </div>

              {/* Ask-to-Follow Message */}
              <div>
                <label className="block text-xs font-semibold text-[#111110] mb-1">
                  Ask-to-Follow Message
                </label>
                <textarea
                  rows={3}
                  value={askFollowMessage}
                  onChange={(e) => setAskFollowMessage(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#0066FF]"
                />
                <p className="text-[11px] text-[#70706B] mt-1">
                  Use {'{account_name}'} to auto-insert your Instagram username. After following, the user can send any reply in the chat and gets the content instantly.
                </p>
              </div>

              {/* Retry Message */}
              <div>
                <label className="block text-xs font-semibold text-[#111110] mb-1">
                  Retry Message (follow not detected)
                </label>
                <textarea
                  rows={2}
                  value={retryMessage}
                  onChange={(e) => setRetryMessage(e.target.value)}
                  placeholder="Leave empty to use the default English message"
                  className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                />
              </div>

              {/* Success Message */}
              <div>
                <label className="block text-xs font-semibold text-[#111110] mb-1">
                  Success Message (after follow confirmed)
                </label>
                <textarea
                  rows={2}
                  value={successMessage}
                  onChange={(e) => setSuccessMessage(e.target.value)}
                  placeholder="Leave empty to use the default English message"
                  className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                />
              </div>

              {/* Button Label */}
              <div>
                <label className="block text-xs font-semibold text-[#111110] mb-1">
                  "I have followed" Button Label
                </label>
                <input
                  type="text"
                  value={followButtonLabel}
                  onChange={(e) => setFollowButtonLabel(e.target.value)}
                  placeholder='Default: "Yes, I have followed ✅"'
                  className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                />
                <p className="text-[11px] text-[#70706B] mt-1">
                  All these texts support any language (e.g. Traditional Chinese) and are available on every plan. Instagram limits the button to 20 characters.
                </p>
              </div>
            </div>
          )}
        </div>
      </FeatureGate>

      {/* 5. COMMENT TEASER REPLY CARD (GATED: PREMIUM / PRO) */}
      <FeatureGate featureKey="comment_teaser_reply">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><Repeat size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">Comment Teaser Reply</h2>
              <PlanBadge tier="PREMIUM" size="xs" />
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={teaserEnabled}
                onChange={(e) => setTeaserEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
            </label>
          </div>

          <div>
            <div className="text-xs font-semibold text-[#111110]">Reply "check your DM" to comment</div>
            <p className="text-xs text-[#70706B]">Automatically reply to the comment publicly so others can see</p>
          </div>

          {teaserEnabled && (
            <div className="space-y-2 pt-3 border-t border-[#ECECE8] animate-in fade-in duration-150">
              <label className="block text-xs font-semibold text-[#111110]">
                Teaser Message
              </label>
              <input
                type="text"
                value={teaserMessage}
                onChange={(e) => setTeaserMessage(e.target.value)}
                placeholder="Check your DM! 📩"
                className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
              />
              <div className="flex items-center justify-between text-[11px] text-[#70706B]">
                <span>Posted as a public reply after the DM is sent. Delay between 10 seconds.</span>
                <span>{teaserMessage.length}/300 characters</span>
              </div>
            </div>
          )}
        </div>
      </FeatureGate>

      {/* 6. TRIGGER RESPONSE DM CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-[#111110]"><Send size={16} /></span>
          <h2 className="text-sm font-bold text-[#111110]">Trigger Response DM</h2>
        </div>

        <div>
          <label className="block text-xs font-semibold text-[#111110] mb-1.5">
            Message sent when user DMs the keyword
          </label>
          <textarea
            rows={4}
            value={responseDm}
            onChange={(e) => setResponseDm(e.target.value)}
            placeholder="e.g., Hey! 👋 Here's what you asked for... You can also put link or send card"
            className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#0066FF]"
          />
          <div className="flex items-center justify-between text-[11px] text-[#70706B] mt-1">
            <span>This is the first message users receive when they DM your keyword</span>
            <span>{responseDm.length}/1000 characters</span>
          </div>
        </div>
      </div>

      {/* 7. DM BUTTONS (OPTIONAL) CARD (GATED: PREMIUM / PRO) */}
      <FeatureGate featureKey="dm_buttons">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><Link2 size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">DM Buttons (Optional)</h2>
              <PlanBadge tier="PREMIUM" size="xs" />
            </div>
            <span className="text-xs text-[#70706B]">{buttons.length}/3 buttons</span>
          </div>
          <p className="text-xs text-[#70706B] -mt-2">
            Add clickable buttons to your DM response (max 3)
          </p>

          {/* Existing Buttons */}
          {buttons.length > 0 && (
            <div className="space-y-2">
              {buttons.map((btn) => (
                <div
                  key={btn.id}
                  className="flex items-center justify-between gap-3 p-3 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-xs"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-bold text-[#111110]">{btn.label}</span>
                    <span className="text-[#70706B] font-mono truncate">{btn.url}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveDMButton(btn.id)}
                    className="text-[#70706B] hover:text-red-600 p-1"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Add Button Form / Trigger */}
          {showAddButton ? (
            <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl space-y-3 animate-in fade-in duration-150">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#111110] mb-1">
                    Button Label
                  </label>
                  <input
                    type="text"
                    value={newButtonLabel}
                    onChange={(e) => setNewButtonLabel(e.target.value)}
                    placeholder="e.g. View the guide"
                    className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-lg text-xs outline-none focus:border-[#0066FF]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#111110] mb-1">
                    Target URL
                  </label>
                  <input
                    type="text"
                    value={newButtonUrl}
                    onChange={(e) => setNewButtonUrl(e.target.value)}
                    placeholder="https://..."
                    className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-lg text-xs font-mono outline-none focus:border-[#0066FF]"
                  />
                </div>
              </div>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddButton(false)}
                  className="px-3 py-1.5 text-xs text-[#70706B] hover:text-[#111110]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAddDMButton}
                  className="px-4 py-1.5 bg-[#0066FF] text-white text-xs font-bold rounded-lg cursor-pointer"
                >
                  Add Button
                </button>
              </div>
            </div>
          ) : (
            buttons.length < 3 && (
              <button
                type="button"
                onClick={() => setShowAddButton(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 border border-[#ECECE8] rounded-xl text-xs font-semibold text-[#111110] hover:bg-[#FBFBFA] transition-colors cursor-pointer"
              >
                <Plus size={14} />
                <span>Add Button</span>
              </button>
            )
          )}
        </div>
      </FeatureGate>

      {/* 8. FOLLOW-UP DMS CARD (GATED: PREMIUM / PRO) */}
      <FeatureGate featureKey="follow_up_dms">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><Clock size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">Follow-up DMs</h2>
              <PlanBadge tier="PREMIUM" size="xs" />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-[#70706B]">Enabled</span>
              <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={followUpEnabled}
                  onChange={(e) => setFollowUpEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
              </label>
            </div>
          </div>

          {followUpEnabled && (
            <div className="space-y-5 pt-3 border-t border-[#ECECE8] animate-in fade-in duration-150">
              {/* Blue Callout */}
              <div className="p-4 bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl text-xs text-[#1E3A8A] leading-relaxed">
                <strong>How it works:</strong> After a lead gets your first DM, Comlina sends these follow-up messages at the delays you set — all inside Instagram's 24-hour messaging window. Any customer reply resets the clock. If the lead replies with a stop keyword, all pending follow-ups are cancelled instantly.
              </div>

              {/* Follow-up messages list */}
              <div className="space-y-3">
                <label className="block text-xs font-bold text-[#111110]">
                  Follow-up messages
                </label>

                {followUps.map((item, idx) => (
                  <div
                    key={item.id}
                    className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#70706B] uppercase tracking-wider text-[10px]">
                        Message #{idx + 1}
                      </span>
                      {followUps.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveFollowUp(item.id)}
                          className="text-[#70706B] hover:text-red-600 p-1"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-start">
                      {/* Time controls */}
                      <div className="sm:col-span-4 space-y-1">
                        <span className="text-[10px] font-bold text-[#70706B] uppercase">AFTER</span>
                        <div className="flex items-center gap-1.5">
                          <div className="flex-1 text-center">
                            <input
                              type="number"
                              min="0"
                              value={item.hours}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setFollowUps(followUps.map((f) => f.id === item.id ? { ...f, hours: val } : f));
                              }}
                              className="w-full text-center px-2 py-1.5 bg-white border border-[#ECECE8] rounded-lg text-xs font-bold"
                            />
                            <span className="text-[9px] text-[#70706B]">hrs</span>
                          </div>
                          <div className="flex-1 text-center">
                            <input
                              type="number"
                              min="0"
                              max="59"
                              value={item.minutes}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setFollowUps(followUps.map((f) => f.id === item.id ? { ...f, minutes: val } : f));
                              }}
                              className="w-full text-center px-2 py-1.5 bg-white border border-[#ECECE8] rounded-lg text-xs font-bold"
                            />
                            <span className="text-[9px] text-[#70706B]">min</span>
                          </div>
                          <div className="flex-1 text-center">
                            <input
                              type="number"
                              min="0"
                              max="59"
                              value={item.seconds}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setFollowUps(followUps.map((f) => f.id === item.id ? { ...f, seconds: val } : f));
                              }}
                              className="w-full text-center px-2 py-1.5 bg-white border border-[#ECECE8] rounded-lg text-xs font-bold"
                            />
                            <span className="text-[9px] text-[#70706B]">sec</span>
                          </div>
                        </div>
                      </div>

                      {/* Message Box */}
                      <div className="sm:col-span-8 space-y-1">
                        <span className="text-[10px] font-bold text-[#70706B] uppercase">MESSAGE</span>
                        <textarea
                          rows={2}
                          value={item.message}
                          onChange={(e) => {
                            const val = e.target.value;
                            setFollowUps(followUps.map((f) => f.id === item.id ? { ...f, message: val } : f));
                          }}
                          className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-lg text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                        />
                      </div>
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={handleAddFollowUp}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-[#0066FF] hover:bg-[#F0F7FF] rounded-lg transition-colors cursor-pointer"
                >
                  <Plus size={14} />
                  <span>Add follow-up</span>
                </button>
                <p className="text-[11px] text-[#70706B]">
                  Delay is counted from the time the user commented/any customer reply resets the 24-hour window limit.
                </p>
              </div>

              {/* AI Rewrite Prompt */}
              <div className="space-y-2 pt-2 border-t border-[#ECECE8]">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-[#111110]">
                    AI rewrite prompt <span className="text-[#70706B] font-normal">(optional)</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setIsGeneratingAi(true);
                      setTimeout(() => {
                        setAiPrompt('Write in a warm, casual voice. Keep it under 200 chars. Reference the lead by @username when it feels natural.');
                        setIsGeneratingAi(false);
                      }, 500);
                    }}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-[#0066FF] hover:underline cursor-pointer"
                  >
                    <Sparkles size={12} />
                    <span>Generate messages with AI</span>
                  </button>
                </div>

                <textarea
                  rows={2}
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder="e.g. Write in a warm, casual voice. Keep it under 200 chars. Reference the lead by @username when it feels natural."
                  className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                />
                <p className="text-[11px] text-[#70706B]">
                  Each sent follow-up is rewritten by AI using your instructions before sending. Leave empty to send messages exactly as written.
                </p>
              </div>

              {/* Stop Keywords */}
              <div className="space-y-1.5 pt-2 border-t border-[#ECECE8]">
                <label className="block text-xs font-semibold text-[#111110]">
                  Stop keywords
                </label>
                <input
                  type="text"
                  value={stopKeywords}
                  onChange={(e) => setStopKeywords(e.target.value)}
                  placeholder="stop, unsubscribe, cancel, no thanks"
                  className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                />
                <p className="text-[11px] text-[#70706B]">
                  Comma-separated. If a user replies with any of these words, all pending follow-ups are cancelled.
                </p>
              </div>

              {/* Stop When You Receive These Details */}
              <div className="space-y-2 pt-2 border-t border-[#ECECE8]">
                <label className="block text-xs font-semibold text-[#111110]">
                  Stop when you receive these details
                </label>

                <div className="flex flex-wrap gap-2">
                  {availableDetails.map((detail) => {
                    const isChecked = stopDetails.includes(detail);
                    return (
                      <button
                        key={detail}
                        type="button"
                        onClick={() => handleToggleStopDetail(detail)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                          isChecked
                            ? 'bg-[#0066FF] text-white shadow-xs'
                            : 'bg-[#F4F4F0] border border-[#ECECE8] text-[#70706B] hover:text-[#111110]'
                        }`}
                      >
                        {detail}
                      </button>
                    );
                  })}
                </div>

                <input
                  type="text"
                  value={otherDetails}
                  onChange={(e) => setOtherDetails(e.target.value)}
                  placeholder="Other details to look for (comma-separated, e.g. budget, city)"
                  className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF] mt-2"
                />

                <p className="text-[11px] text-[#70706B] leading-relaxed">
                  Leave empty to keep sending even if follow-up. If selected, follow-up messages will stop as soon as the customer provides all of them — they can arrive across several messages, or in any order, and our smart AI will analyze the conversation. Works with long/imperfect phone format like '+1 (555) 012-3456', or names written in words. Daily/weekly/monthly AI usage resets automatically on all paid plans.
                </p>
              </div>
            </div>
          )}
        </div>
      </FeatureGate>

      {/* 9. LIVE COMMENT AUTOMATION (GATED: PRO) */}
      <FeatureGate featureKey="live_comment">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><Radio size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">Live Comment Automation</h2>
              <PlanBadge tier="PRO" size="xs" />
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={liveCommentEnabled}
                onChange={(e) => setLiveCommentEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
            </label>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#111110]">Automate responses during Instagram Live</div>
            <p className="text-xs text-[#70706B]">Instantly DM viewers who comment your trigger keyword while you are live streaming.</p>
          </div>
        </div>
      </FeatureGate>

      {/* 10. AI SMART ASSISTANT (GATED: PRO) */}
      <FeatureGate featureKey="ai_smart_assistant">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><Bot size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">AI Smart Assistant</h2>
              <PlanBadge tier="PRO" size="xs" />
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={aiAssistantEnabled}
                onChange={(e) => setAiAssistantEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
            </label>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#111110]">Context-aware conversational AI</div>
            <p className="text-xs text-[#70706B]">Answers FAQs, qualifies prospects, and overcomes objections automatically in DM.</p>
          </div>
        </div>
      </FeatureGate>

      {/* 11. APPOINTMENT BOOKING (GATED: PRO) */}
      <FeatureGate featureKey="appointment_booking">
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[#111110]"><Calendar size={16} /></span>
              <h2 className="text-sm font-bold text-[#111110]">Appointment Booking</h2>
              <PlanBadge tier="PRO" size="xs" />
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={appointmentBookingEnabled}
                onChange={(e) => setAppointmentBookingEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
            </label>
          </div>
          <div>
            <div className="text-xs font-semibold text-[#111110]">Book discovery calls in DM</div>
            <p className="text-xs text-[#70706B]">Qualify leads and book discovery calls directly inside Instagram direct messages.</p>
          </div>
        </div>
      </FeatureGate>

      {/* 9. BOTTOM ACTION BUTTONS */}
      <div className="pt-4 pb-2 flex items-center justify-end gap-3 border-t border-[#ECECE8]">
        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
        />
      </div>

    </div>
  );
}
