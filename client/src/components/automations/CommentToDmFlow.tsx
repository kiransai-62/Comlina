// client/src/components/automations/CommentToDmFlow.tsx
'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  ArrowLeft, 
  RefreshCw, 
  X, 
  Check, 
  ChevronLeft, 
  ChevronRight, 
  ChevronDown, 
  ChevronUp, 
  Smile, 
  Image as ImageIcon, 
  Link2, 
  MessageSquare, 
  Clock, 
  Repeat, 
  Send, 
  Bookmark,
  Sparkles,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { InstagramMediaItem } from './PostSelector';
import { instagramApi } from '@/features/instagram/api';
import { useInstagramConnection } from '@/features/instagram';
import { ConnectedInstagramAccount } from '@/features/instagram/types';
import { InstagramPhonePreview } from './InstagramPhonePreview';
import { usePlan } from '@/hooks/usePlan';
import { useUIStore } from '@/stores/uiStore';

interface CommentToDmFlowProps {
  onBack: () => void;
  onSave: (flowData: any) => Promise<void>;
  accountName?: string;
  accountId?: string;
  accounts?: ConnectedInstagramAccount[];
  onSelectAccount?: (account: ConnectedInstagramAccount) => void;
  isSaving?: boolean;
  onPreviewChange?: (previewData: any) => void;
}

export function CommentToDmFlow({
  onBack,
  onSave,
  accountName = '',
  accountId,
  accounts: externalAccounts,
  onSelectAccount,
  isSaving = false,
  onPreviewChange,
}: CommentToDmFlowProps) {
  const { isLocked, openUpgradeModal } = usePlan();
  const showToast = useUIStore((s) => s.showToast);

  // ══════════════════════════════════════════════════════════════
  // DYNAMIC CONNECTED INSTAGRAM ACCOUNTS
  // ══════════════════════════════════════════════════════════════
  const {
    accounts: hookAccounts = [],
    isLoading: isCheckingAccounts,
    startConnect,
  } = useInstagramConnection();

  const allAccounts: ConnectedInstagramAccount[] =
    externalAccounts && externalAccounts.length > 0 ? externalAccounts : hookAccounts;

  const [selectedAccountId, setSelectedAccountId] = useState<string>(
    accountId || allAccounts[0]?.id || ''
  );

  // Sync selected account when accounts load if not explicitly set
  useEffect(() => {
    if (!selectedAccountId && allAccounts.length > 0) {
      setSelectedAccountId(allAccounts[0].id);
    }
  }, [allAccounts, selectedAccountId]);

  // Sync if parent updates accountId prop
  useEffect(() => {
    if (accountId && accountId !== selectedAccountId) {
      setSelectedAccountId(accountId);
    }
  }, [accountId, selectedAccountId]);

  const selectedAccount = allAccounts.find((a) => a.id === selectedAccountId) || allAccounts[0] || null;
  const activeAccountName = selectedAccount?.username || accountName || '';
  const activeAvatarUrl = selectedAccount?.profile_pic_url || null;

  // ══════════════════════════════════════════════════════════════
  // REAL POSTS MANAGEMENT (ACCOUNT ISOLATED — NO HARDCODED FIXTURES)
  // ══════════════════════════════════════════════════════════════
  const [postMode, setPostMode] = useState<'specific' | 'all'>('specific');
  const [posts, setPosts] = useState<InstagramMediaItem[]>([]);
  const [selectedPostId, setSelectedPostId] = useState<string>('');
  const [isLoadingPosts, setIsLoadingPosts] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);
  const carouselRef = useRef<HTMLDivElement>(null);

  const loadPostsForAccount = useCallback(async (targetAccountId?: string) => {
    if (!targetAccountId) {
      setPosts([]);
      setSelectedPostId('');
      return;
    }

    setIsLoadingPosts(true);
    setPostError(null);
    try {
      const data = await instagramApi.getMedia(targetAccountId);
      if (data && data.length > 0) {
        setPosts(data as InstagramMediaItem[]);
        setSelectedPostId((curr) => {
          const exists = data.some((p) => p.id === curr);
          return exists ? curr : data[0].id;
        });
      } else {
        setPosts([]);
        setSelectedPostId('');
      }
    } catch (err: any) {
      console.warn('Could not fetch real posts for Instagram account:', err);
      setPosts([]);
      setSelectedPostId('');
      setPostError(err.message || 'Unable to fetch posts. Reauthorization may be required.');
    } finally {
      setIsLoadingPosts(false);
    }
  }, []);

  // Re-fetch media whenever selectedAccountId changes
  useEffect(() => {
    if (selectedAccountId) {
      loadPostsForAccount(selectedAccountId);
    } else {
      setPosts([]);
      setSelectedPostId('');
    }
  }, [selectedAccountId, loadPostsForAccount]);

  const handleRefreshPosts = async () => {
    if (!selectedAccountId) {
      showToast('Please connect an Instagram account first.');
      return;
    }
    await loadPostsForAccount(selectedAccountId);
    showToast('Instagram posts refreshed.');
  };

  const handleAccountSwitch = (newAccId: string) => {
    setSelectedAccountId(newAccId);
    const chosen = allAccounts.find((a) => a.id === newAccId);
    if (chosen && onSelectAccount) {
      onSelectAccount(chosen);
    }
  };

  const handleScrollCarousel = (direction: 'left' | 'right') => {
    if (carouselRef.current) {
      const scrollAmount = direction === 'left' ? -220 : 220;
      carouselRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  // ══════════════════════════════════════════════════════════════
  // CONFIGURATION FORM STATE (7 INPUT DESCRIPTIONS)
  // ══════════════════════════════════════════════════════════════

  // 2. Ask to Follow State (Premium)
  const [askFollowEnabled, setAskFollowEnabled] = useState(false);
  const [askFollowMessage, setAskFollowMessage] = useState(
    'Please follow our account to get the guide!'
  );

  // 3. Trigger Keywords State
  const [keywords, setKeywords] = useState<string[]>(['PRICE', 'LINK', 'INFO']);
  const [keywordInput, setKeywordInput] = useState('');
  const [matchWholeWords, setMatchWholeWords] = useState(true);

  const handleAddKeyword = () => {
    const clean = keywordInput.trim().toUpperCase();
    if (!clean) return;

    if (keywords.length >= 3 && isLocked('expanded_keywords')) {
      openUpgradeModal('PREMIUM', 'expanded_keywords');
      return;
    }

    if (!keywords.includes(clean)) {
      setKeywords([...keywords, clean]);
    }
    setKeywordInput('');
  };

  const handleRemoveKeyword = (kw: string) => {
    setKeywords(keywords.filter((k) => k !== kw));
  };

  const handleKeywordKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  // 4. Automated DM Message State
  const [responseDm, setResponseDm] = useState('');

  // 5. DM Buttons State
  const [buttonLabel, setButtonLabel] = useState('Hey! 👋...');
  const [destinationUrl, setDestinationUrl] = useState('');

  // 6. Advanced Settings State
  const [matchBehavior, setMatchBehavior] = useState<'exact' | 'contains'>('contains');
  const [teaserEnabled, setTeaserEnabled] = useState(false);
  const [teaserMessage, setTeaserMessage] = useState('Check your DM! 📩');
  const [followUpEnabled, setFollowUpEnabled] = useState(false);
  const [followUpHours, setFollowUpHours] = useState(2);
  const [followUpMessage, setFollowUpMessage] = useState(
    'Hey! Just checking in — did you get a chance to look at what I sent? 😊'
  );
  const [replyToAll, setReplyToAll] = useState(false);

  // Accordion Expand/Collapse for Additional Options
  const [expandedCards, setExpandedCards] = useState({
    teaser: false,
    followUp: false,
  });

  const allExpanded = Object.values(expandedCards).every(Boolean);

  const toggleAllCards = () => {
    const nextState = !allExpanded;
    setExpandedCards({
      teaser: nextState,
      followUp: nextState,
    });
  };

  const toggleCard = (key: keyof typeof expandedCards) => {
    setExpandedCards((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // Active Selected Post Object from Real Account Posts
  const selectedPost = posts.find((p) => p.id === selectedPostId) || (posts.length > 0 ? posts[0] : null);

  // Accordion Expand/Collapse for Section 6 (Advanced Settings)
  const [isAdvancedSectionExpanded, setIsAdvancedSectionExpanded] = useState(false);
  const [isMobileBottomPreviewOpen, setIsMobileBottomPreviewOpen] = useState(false);

  // Mobile / Tablet Tab Switcher
  const [mobileStudioTab, setMobileStudioTab] = useState<'editor' | 'preview'>('editor');

  // Sync to Parent or External listeners
  useEffect(() => {
    onPreviewChange?.({
      keywords,
      selectedPost: postMode === 'specific' ? selectedPost : null,
      deliveryText: responseDm,
      deliveryLinkButtonText: buttonLabel,
      deliveryLinkUrl: destinationUrl,
      askFollowEnabled,
      askFollowText: askFollowMessage || 'Follow our Instagram to get more such resources and updates!',
      publicReplyEnabled: teaserEnabled,
      publicReplyText: teaserMessage,
      followupEnabled: followUpEnabled,
      followupHours: followUpHours,
      followupText: followUpMessage,
      matchBehavior,
      accountName: activeAccountName,
    });
  }, [
    keywords,
    selectedPost,
    postMode,
    responseDm,
    buttonLabel,
    destinationUrl,
    askFollowEnabled,
    askFollowMessage,
    teaserEnabled,
    teaserMessage,
    followUpEnabled,
    followUpHours,
    followUpMessage,
    matchBehavior,
    activeAccountName,
    onPreviewChange,
  ]);

  // Form Validation
  const isFormValid =
    !!selectedAccount &&
    (replyToAll || keywords.length > 0) &&
    !!responseDm.trim() &&
    !!buttonLabel.trim() &&
    !!destinationUrl.trim() &&
    (destinationUrl.startsWith('http://') || destinationUrl.startsWith('https://'));

  const handleSaveClick = async (status: 'DRAFT' | 'ACTIVE') => {
    if (!selectedAccount) {
      showToast('Please connect an Instagram account.');
      return;
    }

    if (status === 'ACTIVE' && !isFormValid) {
      showToast('Please fill in required fields (including valid HTTPS URL) before publishing.');
      return;
    }

    const payload = {
      status,
      name: 'Comment to DM Flow',
      instagram_account_id: selectedAccount.id,
      trigger: {
        type: 'COMMENT',
        mode: postMode,
        postId: postMode === 'specific' ? selectedPostId : undefined,
        keywords: replyToAll ? [] : keywords,
        matchWholeWords,
        matchBehavior,
        replyToAll,
      },
      automatedDm: {
        message: responseDm,
        button: {
          label: buttonLabel,
          url: destinationUrl,
        },
      },
      advanced: {
        askFollow: {
          enabled: askFollowEnabled,
          message: askFollowMessage,
        },
        commentTeaser: {
          enabled: teaserEnabled,
          message: teaserMessage,
        },
        followUp: {
          enabled: followUpEnabled,
          hours: followUpHours,
          message: followUpMessage,
        },
      },
    };

    await onSave(payload);
  };

  return (
    <div className="w-full max-w-[1500px] mx-auto pb-16 text-[#111110]">
      {/* ── TOP WORKFLOW HEADER ── */}
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="p-1.5 -ml-1 text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] rounded-xl transition-colors cursor-pointer"
            title="Back to Automations"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111110] tracking-tight">
                Comment to DM
              </h1>
            </div>
            <p className="text-xs text-[#70706B] mt-1">
              Set up automated responses when users comment keywords on your Instagram posts.
            </p>
          </div>
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            disabled={isSaving}
            onClick={() => handleSaveClick('DRAFT')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-[#E0E0DA] hover:bg-[#F7F7F5] text-[#111110] text-xs font-semibold rounded-xl transition-all shadow-2xs cursor-pointer disabled:opacity-50"
          >
            <Bookmark size={14} className="text-[#70706B]" />
            <span>Save Draft</span>
          </button>
          <button
            type="button"
            disabled={isSaving}
            onClick={() => handleSaveClick('ACTIVE')}
            className="inline-flex items-center gap-2 px-4.5 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-xl shadow-xs transition-all cursor-pointer disabled:opacity-50"
          >
            <Send size={14} />
            <span>Publish Automation</span>
          </button>
        </div>
      </div>

      {/* ── REAL CONNECTED INSTAGRAM ACCOUNT CARD & ACCOUNT SWITCHER ── */}
      {isCheckingAccounts ? (
        <div className="mb-6 bg-white border border-[#ECECE8] rounded-2xl p-4 animate-pulse flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gray-200" />
          <div className="space-y-1.5 flex-1">
            <div className="w-32 h-4 bg-gray-200 rounded" />
            <div className="w-48 h-3 bg-gray-100 rounded" />
          </div>
        </div>
      ) : allAccounts.length === 0 ? (
        <div className="mb-6 bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl p-4.5 flex items-center justify-between flex-wrap gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FEF3C7] text-[#D97706] flex items-center justify-center shrink-0">
              <AlertCircle size={22} />
            </div>
            <div>
              <div className="text-sm font-bold text-[#92400E]">
                No Instagram Account Connected
              </div>
              <p className="text-xs text-[#B45309] mt-0.5">
                Connect your Instagram account to load posts and run automations.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={startConnect}
            className="px-4 py-2 bg-[#D97706] hover:bg-[#B45309] text-white text-xs font-semibold rounded-xl transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
          >
            <ExternalLink size={14} />
            <span>Connect Instagram</span>
          </button>
        </div>
      ) : (
        <div className="mb-6 bg-white border border-[#ECECE8] rounded-2xl p-4 shadow-2xs flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3.5">
            {/* Account Profile Avatar */}
            <div className="relative shrink-0">
              {activeAvatarUrl ? (
                <img
                  src={activeAvatarUrl}
                  alt={activeAccountName}
                  className="w-11 h-11 rounded-full object-cover border-2 border-white shadow-2xs"
                />
              ) : (
                <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888] flex items-center justify-center text-white font-bold text-sm uppercase shadow-2xs">
                  {activeAccountName ? activeAccountName.charAt(0) : 'IG'}
                </div>
              )}
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[#22C55E] border-2 border-white" />
            </div>

            {/* Account Details */}
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-extrabold text-[#111110]">
                  @{activeAccountName}
                </span>
                {selectedAccount?.status === 'CONNECTED' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#15803D] bg-[#DCFCE7] border border-[#BBF7D0] px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#D97706] bg-[#FEF3C7] border border-[#FDE68A] px-2 py-0.5 rounded-full uppercase tracking-wider">
                    {selectedAccount?.status || 'Active'}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-[#70706B] mt-0.5 flex-wrap">
                <span>Account ID: <span className="font-mono text-[11px] text-[#111110]">{selectedAccount?.id?.slice(0, 8)}...</span></span>
                {selectedAccount?.account_type && (
                  <>
                    <span>•</span>
                    <span className="capitalize">{selectedAccount.account_type.toLowerCase()} account</span>
                  </>
                )}
                {typeof selectedAccount?.follower_count === 'number' && (
                  <>
                    <span>•</span>
                    <span>{selectedAccount.follower_count.toLocaleString()} followers</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Account Selector (When user has multiple accounts connected) */}
          {allAccounts.length > 1 && (
            <div className="flex items-center gap-2">
              <label htmlFor="account-selector" className="text-xs font-semibold text-[#70706B]">
                Switch account:
              </label>
              <select
                id="account-selector"
                value={selectedAccountId}
                onChange={(e) => handleAccountSwitch(e.target.value)}
                className="px-3 py-1.5 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-xs font-semibold text-[#111110] outline-none focus:border-[#15803D] shadow-2xs cursor-pointer"
              >
                {allAccounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    @{acc.username} ({acc.status || 'CONNECTED'})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* ── TABLET & MOBILE VIEW SWITCHER (< 1200px) ── */}
      <div className="xl:hidden flex items-center justify-center p-1 bg-[#F4F4F0] border border-[#ECECE8] rounded-2xl mb-5 max-w-sm mx-auto shadow-2xs">
        <button
          type="button"
          onClick={() => setMobileStudioTab('editor')}
          className={`flex-1 py-2 px-3 text-xs font-bold rounded-xl transition-all cursor-pointer ${
            mobileStudioTab === 'editor'
              ? 'bg-white text-[#111110] shadow-xs'
              : 'text-[#70706B] hover:text-[#111110]'
          }`}
        >
          Configure Flow
        </button>
        <button
          type="button"
          onClick={() => setMobileStudioTab('preview')}
          className={`flex-1 py-2 px-3 text-xs font-bold rounded-xl transition-all cursor-pointer ${
            mobileStudioTab === 'preview'
              ? 'bg-white text-[#064125] shadow-xs'
              : 'text-[#70706B] hover:text-[#111110]'
          }`}
        >
          Live Preview
        </button>
      </div>

      {/* ── MAIN STUDIO GRID (2-COLUMN COORDINATED LAYOUT) ── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        {/* LEFT COLUMN: 6-STEP CONFIGURATION BUILDER */}
        <div
          className={`xl:col-span-7 2xl:col-span-7 space-y-6 min-w-0 ${
            mobileStudioTab === 'preview' ? 'hidden xl:block' : 'block'
          }`}
        >
          {/* ══════════════════════════════════════════════════════════════
              1. SELECT POST
          ══════════════════════════════════════════════════════════════ */}
          <section className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] font-bold text-xs flex items-center justify-center shrink-0">
                  1
                </span>
                <h2 className="text-sm sm:text-base font-bold text-[#111110]">Select Post</h2>
              </div>

              <button
                type="button"
                onClick={handleRefreshPosts}
                disabled={isLoadingPosts || !selectedAccountId}
                className="inline-flex items-center gap-1.5 text-xs text-[#70706B] hover:text-[#111110] font-medium cursor-pointer transition-colors disabled:opacity-50"
              >
                <RefreshCw size={13} className={isLoadingPosts ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>

            {/* Pill Tabs: Specific Post | All Posts */}
            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={() => setPostMode('specific')}
                className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  postMode === 'specific'
                    ? 'bg-[#062E1A] text-white shadow-2xs'
                    : 'bg-transparent text-[#70706B] hover:bg-[#F4F4F0]'
                }`}
              >
                Specific Post
              </button>
              <button
                type="button"
                onClick={() => setPostMode('all')}
                className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  postMode === 'all'
                    ? 'bg-[#062E1A] text-white shadow-2xs'
                    : 'bg-transparent text-[#70706B] hover:bg-[#F4F4F0]'
                }`}
              >
                All Posts
              </button>
            </div>

            {/* Media Content: Loading Skeleton, Error State, Empty State, or Real Carousel */}
            {postMode === 'specific' ? (
              isLoadingPosts ? (
                <div className="flex items-center gap-3.5 overflow-x-auto py-2 scrollbar-none">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="w-28 shrink-0 space-y-2 animate-pulse">
                      <div className="aspect-square rounded-2xl bg-gray-200" />
                      <div className="h-3 bg-gray-200 rounded w-3/4" />
                    </div>
                  ))}
                </div>
              ) : postError ? (
                <div className="p-4 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] text-xs text-[#92400E] space-y-2">
                  <div className="font-bold flex items-center gap-1.5">
                    <AlertCircle size={15} className="text-[#D97706]" />
                    <span>Unable to load posts from Instagram</span>
                  </div>
                  <p className="text-[#B45309]">{postError}</p>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={handleRefreshPosts}
                      className="px-3 py-1 bg-white border border-[#D97706] text-[#92400E] font-semibold rounded-lg cursor-pointer"
                    >
                      Retry
                    </button>
                    <button
                      type="button"
                      onClick={startConnect}
                      className="px-3 py-1 bg-[#D97706] text-white font-semibold rounded-lg cursor-pointer"
                    >
                      Reconnect Account
                    </button>
                  </div>
                </div>
              ) : posts.length === 0 ? (
                <div className="p-6 rounded-2xl bg-[#FBFBFA] border border-dashed border-[#ECECE8] text-center space-y-2.5">
                  <div className="w-10 h-10 rounded-xl bg-white border border-[#ECECE8] shadow-2xs flex items-center justify-center text-[#9E9E96] mx-auto">
                    <ImageIcon size={20} />
                  </div>
                  <div className="text-xs font-bold text-[#111110]">
                    No Instagram posts found for @{activeAccountName || 'this account'}
                  </div>
                  <p className="text-[11px] text-[#70706B] max-w-sm mx-auto">
                    We didn&apos;t find any media published on this Instagram profile. Publish a post or Reel, then click Refresh below.
                  </p>
                  <button
                    type="button"
                    onClick={handleRefreshPosts}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#ECECE8] hover:bg-[#F4F4F0] text-xs font-semibold rounded-xl shadow-2xs transition-all cursor-pointer"
                  >
                    <RefreshCw size={13} />
                    <span>Refresh Media</span>
                  </button>
                </div>
              ) : (
                <div className="relative flex items-center pt-1">
                  {/* Scroll Left Button */}
                  <button
                    type="button"
                    onClick={() => handleScrollCarousel('left')}
                    className="p-1 rounded-full bg-white border border-[#ECECE8] hover:bg-[#F4F4F0] text-[#70706B] hover:text-[#111110] shadow-xs shrink-0 cursor-pointer z-10 mr-2"
                    title="Previous posts"
                  >
                    <ChevronLeft size={16} />
                  </button>

                  {/* Posts Carousel Container */}
                  <div
                    ref={carouselRef}
                    className="flex items-start gap-3.5 overflow-x-auto py-2 scrollbar-none flex-1"
                  >
                    {posts.map((post) => {
                      const isSelected = selectedPostId === post.id;
                      return (
                        <div
                          key={post.id}
                          onClick={() => setSelectedPostId(post.id)}
                          className={`shrink-0 cursor-pointer group transition-all ${
                            isSelected ? 'w-36' : 'w-24'
                          }`}
                        >
                          <div
                            className={`relative aspect-square rounded-2xl overflow-hidden transition-all ${
                              isSelected
                                ? 'border-2 border-[#15803D] ring-2 ring-[#15803D]/20 shadow-md'
                                : 'border border-[#ECECE8] hover:border-gray-400 opacity-80 hover:opacity-100'
                            }`}
                          >
                            <img
                              src={post.imageUrl}
                              alt={post.caption || 'Instagram Post'}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                            />
                            {post.type === 'REEL' && (
                              <div className="absolute top-2 left-2 w-4 h-4 rounded-full bg-black/60 flex items-center justify-center text-white">
                                <svg width="8" height="8" viewBox="0 0 24 24" fill="white">
                                  <path d="M8 5v14l11-7z" />
                                </svg>
                              </div>
                            )}
                            {isSelected && (
                              <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#15803D] text-white flex items-center justify-center shadow-xs">
                                <Check size={11} strokeWidth={3} />
                              </div>
                            )}
                          </div>

                          {/* Caption and real metrics under selected post */}
                          {isSelected && (
                            <div className="mt-2 text-left">
                              <div className="text-xs font-bold text-[#111110] truncate">
                                {post.caption || '(No caption)'}
                              </div>
                              <div className="text-[11px] text-[#70706B] mt-0.5">
                                {post.publishedDate ? `${post.publishedDate} • ` : ''}
                                {(post.likesCount ? (post.likesCount >= 1000 ? `${(post.likesCount / 1000).toFixed(1)}K` : post.likesCount) : '0')} likes
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Scroll Right Button */}
                  <button
                    type="button"
                    onClick={() => handleScrollCarousel('right')}
                    className="p-1 rounded-full bg-white border border-[#ECECE8] hover:bg-[#F4F4F0] text-[#70706B] hover:text-[#111110] shadow-xs shrink-0 cursor-pointer z-10 ml-2"
                    title="Next posts"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              )
            ) : (
              <div className="p-4 rounded-xl bg-[#F4FBF6] border border-[#D1EADC] text-xs text-[#064125] flex items-center gap-2.5">
                <Sparkles size={16} className="text-[#15803D] shrink-0" />
                <span>
                  All Posts active: This automation will monitor incoming comments on all existing and future Instagram posts on @{activeAccountName || 'your account'}.
                </span>
              </div>
            )}
          </section>

          {/* ══════════════════════════════════════════════════════════════
              2. ASK TO FOLLOW
          ══════════════════════════════════════════════════════════════ */}
          <section className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] font-bold text-xs flex items-center justify-center shrink-0">
                  2
                </span>
                <h2 className="text-sm sm:text-base font-bold text-[#111110]">Ask to Follow</h2>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-[#FEF3C7] text-[#B45309] px-2 py-0.5 rounded-full uppercase tracking-wider border border-[#FDE68A]/60">
                  <Sparkles size={11} className="text-[#D97706]" />
                  Premium
                </span>
              </div>

              {/* Toggle Switch */}
              <button
                type="button"
                onClick={() => setAskFollowEnabled(!askFollowEnabled)}
                className={`w-10 h-5.5 rounded-full transition-colors relative cursor-pointer ${
                  askFollowEnabled ? 'bg-[#22C55E]' : 'bg-[#D1D1CB]'
                }`}
                aria-label="Toggle Ask to Follow"
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-4.5 h-4.5 rounded-full bg-white shadow-xs transition-transform ${
                    askFollowEnabled ? 'translate-x-4.5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {askFollowEnabled && (
              <div className="p-4 pt-3 border border-[#D1EADC] bg-[#F4FBF6] rounded-xl space-y-2 transition-all">
                <label className="block text-xs font-semibold text-[#064125]">
                  Follow Request Message
                </label>
                <input
                  type="text"
                  value={askFollowMessage}
                  onChange={(e) => setAskFollowMessage(e.target.value)}
                  placeholder="e.g. Please follow our account to get the guide!"
                  className="w-full px-3 py-2 bg-white border border-[#A7D7B9] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D]"
                />
              </div>
            )}
          </section>

          {/* ══════════════════════════════════════════════════════════════
              3. TRIGGER KEYWORDS
          ══════════════════════════════════════════════════════════════ */}
          <section className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] font-bold text-xs flex items-center justify-center shrink-0">
                  3
                </span>
                <h2 className="text-sm sm:text-base font-bold text-[#111110]">Trigger Keywords</h2>
              </div>

              <span className="text-xs font-medium text-[#70706B]">
                {keywords.length} / 3 keywords
              </span>
            </div>

            <div className="space-y-2 pt-1">
              {/* Input Bar */}
              <div className="flex items-center border border-[#ECECE8] bg-[#FBFBFA] rounded-xl px-3 py-1.5 focus-within:border-[#15803D] focus-within:bg-white transition-all shadow-2xs">
                <input
                  type="text"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyDown={handleKeywordKeyDown}
                  placeholder="Add keyword (e.g. PRICE, LINK, INFO) and press Enter"
                  className="flex-1 bg-transparent text-xs text-[#111110] placeholder:text-[#9E9E96] outline-none py-1"
                />
                <button
                  type="button"
                  onClick={handleAddKeyword}
                  className="text-xs font-bold text-[#111110] hover:text-[#064125] px-2.5 py-1 rounded bg-[#EAEAE5] hover:bg-[#E0E0DA] cursor-pointer transition-colors"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Keyword Chips */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {keywords.map((kw) => (
                <span
                  key={kw}
                  className="inline-flex items-center gap-2 px-3 py-1 bg-[#F4F4F0] hover:bg-[#EAEAE5] text-[#111110] text-xs font-bold tracking-wide uppercase rounded-lg border border-[#ECECE8] transition-colors"
                >
                  <span>{kw}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveKeyword(kw)}
                    className="text-[#70706B] hover:text-red-600 cursor-pointer"
                    title={`Remove ${kw}`}
                  >
                    <X size={13} />
                  </button>
                </span>
              ))}
              {keywords.length === 0 && (
                <span className="text-xs text-amber-700 italic">
                  No trigger keywords added yet. Add at least one keyword above.
                </span>
              )}
            </div>

            {/* Match Whole Words Only Switch */}
            <div className="pt-3 border-t border-[#F4F4F0] flex items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-[#111110]">
                  Match whole words only
                </div>
                <p className="text-[11px] text-[#70706B] mt-0.5">
                  When enabled, match complete keywords rather than parts of longer words.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setMatchWholeWords(!matchWholeWords)}
                className={`w-10 h-5.5 rounded-full transition-colors relative cursor-pointer shrink-0 ${
                  matchWholeWords ? 'bg-[#22C55E]' : 'bg-[#D1D1CB]'
                }`}
                aria-label="Toggle Match whole words only"
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-4.5 h-4.5 rounded-full bg-white shadow-xs transition-transform ${
                    matchWholeWords ? 'translate-x-4.5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </section>

          {/* ══════════════════════════════════════════════════════════════
              4. AUTOMATED DM MESSAGE
          ══════════════════════════════════════════════════════════════ */}
          <section className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] font-bold text-xs flex items-center justify-center shrink-0">
                4
              </span>
              <h2 className="text-sm sm:text-base font-bold text-[#111110]">Automated DM Message</h2>
            </div>

            <div className="space-y-1.5 pt-1">
              {/* Message Box */}
              <div className="border border-[#ECECE8] rounded-2xl p-3.5 bg-white focus-within:border-[#15803D] transition-all shadow-2xs">
                <textarea
                  rows={4}
                  value={responseDm}
                  onChange={(e) => setResponseDm(e.target.value)}
                  placeholder="Write your automated DM message..."
                  className="w-full text-xs text-[#111110] placeholder:text-[#9E9E96] outline-none resize-none leading-relaxed bg-transparent"
                />

                {/* Bottom Toolbar & Character Count */}
                <div className="flex items-center justify-between pt-2 border-t border-[#F4F4F0] mt-2 flex-wrap gap-2">
                  <div className="flex items-center gap-2.5 text-[#70706B]">
                    <button
                      type="button"
                      onClick={() => setResponseDm((prev) => `${prev} 😊`)}
                      className="hover:text-[#111110] p-1 rounded cursor-pointer transition-colors"
                      title="Add emoji"
                    >
                      <Smile size={16} />
                    </button>
                    <button
                      type="button"
                      className="hover:text-[#111110] p-1 rounded cursor-pointer transition-colors"
                      title="Attach image"
                    >
                      <ImageIcon size={16} />
                    </button>
                    <button
                      type="button"
                      className="hover:text-[#111110] p-1 rounded cursor-pointer transition-colors"
                      title="Insert link"
                    >
                      <Link2 size={16} />
                    </button>
                  </div>

                  <div className="flex items-center gap-1.5 text-[11px] text-[#70706B]">
                    <span>Message length</span>
                    <span className="font-mono font-semibold text-[#111110]">
                      {responseDm.length}/1000
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ══════════════════════════════════════════════════════════════
              5. ACTION BUTTON (CTA)
          ══════════════════════════════════════════════════════════════ */}
          <section className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] font-bold text-xs flex items-center justify-center shrink-0">
                5
              </span>
              <h2 className="text-sm sm:text-base font-bold text-[#111110]">Action Button (CTA)</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="block text-xs font-bold text-[#111110] mb-1">
                  Button Label <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={buttonLabel}
                  onChange={(e) => setButtonLabel(e.target.value)}
                  placeholder="e.g. View the guide"
                  className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D] shadow-2xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#111110] mb-1">
                  Destination URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={destinationUrl}
                  onChange={(e) => setDestinationUrl(e.target.value)}
                  placeholder="https://example.com/guide"
                  className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs font-mono text-[#111110] outline-none focus:border-[#15803D] shadow-2xs"
                />
              </div>
            </div>
          </section>

          {/* ══════════════════════════════════════════════════════════════
              6. ADVANCED SETTINGS (ACCORDION COLLAPSED BY DEFAULT)
          ══════════════════════════════════════════════════════════════ */}
          <section className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
            <div 
              className="flex items-center justify-between gap-3 cursor-pointer select-none"
              onClick={() => setIsAdvancedSectionExpanded((prev) => !prev)}
            >
              <div className="flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-full bg-[#EAF6EE] text-[#15803D] font-bold text-xs flex items-center justify-center shrink-0">
                  6
                </span>
                <h2 className="text-sm sm:text-base font-bold text-[#111110]">Advanced Settings</h2>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-[#70706B] hidden sm:inline">
                  {isAdvancedSectionExpanded ? 'Hide' : 'Show'}
                </span>
                <button
                  type="button"
                  className="p-1.5 rounded-lg text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] cursor-pointer"
                  aria-label={isAdvancedSectionExpanded ? 'Collapse advanced settings' : 'Expand advanced settings'}
                >
                  {isAdvancedSectionExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
              </div>
            </div>

            {isAdvancedSectionExpanded && (
              <div className="space-y-5 pt-3 border-t border-[#ECECE8]/60 animate-in fade-in duration-200">
                <div className="flex items-center justify-end">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleAllCards();
                    }}
                    className="text-xs font-semibold text-[#2563EB] hover:underline cursor-pointer"
                  >
                    {allExpanded ? 'Collapse sub-options' : 'Expand sub-options'}
                  </button>
                </div>

                {/* ── SUB-SECTION: MATCH BEHAVIOR ── */}
            <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl space-y-3">
              <div>
                <h3 className="text-xs font-bold text-[#111110]">Match Behavior</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <button
                  type="button"
                  onClick={() => setMatchBehavior('contains')}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    matchBehavior === 'contains'
                      ? 'border-[#15803D] bg-white ring-2 ring-[#15803D]/10'
                      : 'border-[#ECECE8] bg-white hover:border-[#D1D1CB]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#111110]">Contains keyword</span>
                    {matchBehavior === 'contains' && <Check size={14} className="text-[#15803D]" />}
                  </div>
                  <p className="text-[11px] text-[#70706B] mt-1">
                    Trigger DM if any keyword appears anywhere in the comment.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setMatchBehavior('exact')}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    matchBehavior === 'exact'
                      ? 'border-[#15803D] bg-white ring-2 ring-[#15803D]/10'
                      : 'border-[#ECECE8] bg-white hover:border-[#D1D1CB]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#111110]">Exact match only</span>
                    {matchBehavior === 'exact' && <Check size={14} className="text-[#15803D]" />}
                  </div>
                  <p className="text-[11px] text-[#70706B] mt-1">
                    Keywords must match the comment exactly without extra words.
                  </p>
                </button>
              </div>
            </div>

            {/* ── SUB-SECTION: ADDITIONAL OPTIONS ── */}
            <div className="space-y-3 pt-1">
              <div>
                <h3 className="text-xs font-bold text-[#111110]">Additional Options</h3>
              </div>

              {/* CARD C: COMMENT TEASER REPLY (PREMIUM) */}
              <div className="border border-[#ECECE8] rounded-2xl overflow-hidden transition-all">
                <div className="p-4 flex items-center justify-between gap-3 bg-white">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-green-50 text-[#15803D] flex items-center justify-center shrink-0">
                      <MessageSquare size={18} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#111110]">
                          Comment Teaser Reply
                        </span>
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-[#FEF3C7] text-[#B45309] px-2 py-0.5 rounded-full uppercase tracking-wider">
                          ⚡ PREMIUM
                        </span>
                      </div>
                      <p className="text-[11px] text-[#70706B] mt-0.5">
                        Post a public reply (&ldquo;Check your DM! 📩&rdquo;) to boost post engagement algorithmically.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setTeaserEnabled(!teaserEnabled)}
                      className={`w-9 h-5 rounded-full transition-colors relative cursor-pointer ${
                        teaserEnabled ? 'bg-[#22C55E]' : 'bg-[#D1D1CB]'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                          teaserEnabled ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleCard('teaser')}
                      className="p-1 text-[#70706B] hover:text-[#111110] cursor-pointer"
                    >
                      {expandedCards.teaser ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {expandedCards.teaser && (
                  <div className="p-4 pt-1 border-t border-[#F4F4F0] bg-[#FAFAF8] space-y-2">
                    <label className="block text-xs font-semibold text-[#111110]">
                      Public Comment Reply Message
                    </label>
                    <input
                      type="text"
                      value={teaserMessage}
                      onChange={(e) => setTeaserMessage(e.target.value)}
                      placeholder="Check your DM! 📩"
                      className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D]"
                    />
                  </div>
                )}
              </div>

              {/* CARD D: FOLLOW-UP DMS (PREMIUM) */}
              <div className="border border-[#ECECE8] rounded-2xl overflow-hidden transition-all">
                <div className="p-4 flex items-center justify-between gap-3 bg-white">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-sky-50 text-[#0284C7] flex items-center justify-center shrink-0">
                      <Clock size={18} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#111110]">Follow-up DMs</span>
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-[#FEF3C7] text-[#B45309] px-2 py-0.5 rounded-full uppercase tracking-wider">
                          ⚡ PREMIUM
                        </span>
                      </div>
                      <p className="text-[11px] text-[#70706B] mt-0.5">
                        Automatically check in if the follower hasn&apos;t clicked your link after a few hours.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setFollowUpEnabled(!followUpEnabled)}
                      className={`w-9 h-5 rounded-full transition-colors relative cursor-pointer ${
                        followUpEnabled ? 'bg-[#22C55E]' : 'bg-[#D1D1CB]'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                          followUpEnabled ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleCard('followUp')}
                      className="p-1 text-[#70706B] hover:text-[#111110] cursor-pointer"
                    >
                      {expandedCards.followUp ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {expandedCards.followUp && (
                  <div className="p-4 pt-1 border-t border-[#F4F4F0] bg-[#FAFAF8] space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#70706B]">Send follow-up after:</span>
                      <select
                        value={followUpHours}
                        onChange={(e) => setFollowUpHours(Number(e.target.value))}
                        className="px-2.5 py-1 bg-white border border-[#ECECE8] rounded-lg text-xs font-semibold outline-none"
                      >
                        <option value={1}>1 hour</option>
                        <option value={2}>2 hours</option>
                        <option value={6}>6 hours</option>
                        <option value={12}>12 hours</option>
                        <option value={24}>24 hours</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-[#111110] mb-1">
                        Follow-up Message
                      </label>
                      <textarea
                        rows={2}
                        value={followUpMessage}
                        onChange={(e) => setFollowUpMessage(e.target.value)}
                        className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D]"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* CARD E: REPLY TO ALL COMMENTS (PREMIUM) */}
              <div className="border border-[#ECECE8] rounded-2xl overflow-hidden transition-all">
                <div className="p-4 flex items-center justify-between gap-3 bg-white">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-amber-50 text-[#D97706] flex items-center justify-center shrink-0">
                      <Repeat size={18} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#111110]">Reply to All Comments</span>
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-[#FEF3C7] text-[#B45309] px-2 py-0.5 rounded-full uppercase tracking-wider">
                          ⚡ PREMIUM
                        </span>
                      </div>
                      <p className="text-[11px] text-[#70706B] mt-0.5">
                        Engage every commenter without requiring an exact keyword trigger.
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setReplyToAll(!replyToAll)}
                    className={`w-9 h-5 rounded-full transition-colors relative cursor-pointer ${
                      replyToAll ? 'bg-[#22C55E]' : 'bg-[#D1D1CB]'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                        replyToAll ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

          {/* Inline Collapsible Simulator for Mobile / Tablet */}
          <div className="xl:hidden bg-white border border-[#ECECE8] rounded-2xl p-4 shadow-xs space-y-3">
            <button
              type="button"
              onClick={() => setIsMobileBottomPreviewOpen((p) => !p)}
              className="w-full flex items-center justify-between text-xs font-bold text-[#111110] cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse" />
                <span>Live Simulator Preview</span>
              </div>
              <div className="flex items-center gap-1 text-[#70706B] font-semibold">
                <span>{isMobileBottomPreviewOpen ? 'Hide' : 'Open Preview'}</span>
                {isMobileBottomPreviewOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
            </button>

            {isMobileBottomPreviewOpen && (
              <div className="pt-3 border-t border-[#ECECE8] animate-in fade-in duration-200">
                <InstagramPhonePreview
                  accountName={activeAccountName}
                  avatarUrl={activeAvatarUrl}
                  selectedPost={postMode === 'specific' ? selectedPost : null}
                  keywords={keywords}
                  deliveryText={responseDm}
                  deliveryLinkButtonText={buttonLabel}
                  deliveryLinkUrl={destinationUrl}
                  askFollowEnabled={askFollowEnabled}
                  askFollowText={askFollowMessage || `Follow @${activeAccountName} to get more such resources and updates!`}
                  publicReplyEnabled={teaserEnabled}
                  publicReplyText={teaserMessage}
                  followupEnabled={followUpEnabled}
                  followupHours={followUpHours}
                  followupText={followUpMessage}
                  defaultTab="dm"
                  showStepHeader={false}
                  isConnectedAccount={!!selectedAccount}
                  accountStatus={selectedAccount?.status}
                />
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: 7. LIVE INSTAGRAM SIMULATOR (STICKY >= 1200px) */}
        <aside
          className={`xl:col-span-5 2xl:col-span-5 xl:sticky xl:top-6 ${
            mobileStudioTab === 'editor' ? 'hidden xl:block' : 'block'
          }`}
        >
          <div className="bg-white border border-[#ECECE8] rounded-3xl p-5 shadow-xs space-y-4 max-w-md mx-auto">
            <InstagramPhonePreview
              accountName={activeAccountName}
              avatarUrl={activeAvatarUrl}
              selectedPost={postMode === 'specific' ? selectedPost : null}
              keywords={keywords}
              deliveryText={responseDm}
              deliveryLinkButtonText={buttonLabel}
              deliveryLinkUrl={destinationUrl}
              askFollowEnabled={askFollowEnabled}
              askFollowText={askFollowMessage || `Follow @${activeAccountName} to get more such resources and updates!`}
              publicReplyEnabled={teaserEnabled}
              publicReplyText={teaserMessage}
              followupEnabled={followUpEnabled}
              followupHours={followUpHours}
              followupText={followUpMessage}
              defaultTab="dm"
              showStepHeader={true}
              isConnectedAccount={!!selectedAccount}
              accountStatus={selectedAccount?.status}
            />

            {/* Mobile Return to Editor Button */}
            <div className="xl:hidden pt-2 border-t border-[#ECECE8]">
              <button
                type="button"
                onClick={() => setMobileStudioTab('editor')}
                className="w-full py-2.5 bg-[#F4F4F0] hover:bg-[#ECECE8] text-[#111110] font-bold text-xs rounded-xl transition-colors cursor-pointer"
              >
                ← Return to Flow Editor
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default CommentToDmFlow;
