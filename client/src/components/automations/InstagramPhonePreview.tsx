// client/src/components/automations/InstagramPhonePreview.tsx
'use client';

import React, { useState } from 'react';
import { 
  Heart, 
  MessageCircle, 
  Send, 
  Bookmark, 
  MoreHorizontal, 
  ChevronLeft, 
  Phone, 
  Video, 
  Smile, 
  Image as ImageIcon,
  CheckCheck
} from 'lucide-react';
import { InstagramMediaItem } from './PostSelector';

export interface InstagramPhonePreviewProps {
  accountName?: string;
  avatarUrl?: string | null;
  selectedPost?: InstagramMediaItem | null;
  keywords?: string[];
  publicReplyEnabled?: boolean;
  publicReplyText?: string;
  openingDmEnabled?: boolean;
  openingDmText?: string;
  openingDmButtonText?: string;
  askFollowEnabled?: boolean;
  askFollowText?: string;
  askEmailEnabled?: boolean;
  askEmailText?: string;
  deliveryText?: string;
  deliveryLinkUrl?: string;
  deliveryLinkButtonText?: string;
  followupEnabled?: boolean;
  followupHours?: number;
  followupText?: string;
  defaultTab?: 'post' | 'comments' | 'dm' | 'story';
  isStoryFlow?: boolean;
  storyImageUrl?: string;
  followerView?: 'follower' | 'non_follower';
  showStepHeader?: boolean;
  isConnectedAccount?: boolean;
  accountStatus?: string;
  triggerMode?: 'specific_keywords' | 'any_keyword';
}

export function InstagramPhonePreview({
  accountName = '',
  avatarUrl = null,
  selectedPost = null,
  keywords = ['PRICE'],
  publicReplyEnabled = false,
  publicReplyText = 'Check your DM! 📩',
  openingDmEnabled = true,
  openingDmText = '',
  openingDmButtonText = '',
  askFollowEnabled = false,
  askFollowText = '',
  askEmailEnabled = false,
  askEmailText = '',
  deliveryText = '',
  deliveryLinkUrl = 'https://example.com/guide',
  deliveryLinkButtonText = 'View the guide',
  followupEnabled = false,
  followupHours = 2,
  followupText = '',
  defaultTab,
  isStoryFlow = false,
  storyImageUrl = '',
  followerView = 'follower',
  showStepHeader = true,
  isConnectedAccount = true,
  accountStatus = 'CONNECTED',
  triggerMode = 'specific_keywords',
}: InstagramPhonePreviewProps) {
  const [activeTab, setActiveTab] = useState<'post' | 'comments' | 'dm' | 'story'>(
    defaultTab || (isStoryFlow ? 'story' : 'dm')
  );
  const [previewState, setPreviewState] = useState<'follower' | 'non_follower'>(followerView);

  React.useEffect(() => {
    if (defaultTab) {
      setActiveTab(defaultTab);
    }
  }, [defaultTab]);

  React.useEffect(() => {
    if (followerView) {
      setPreviewState(followerView);
    }
  }, [followerView]);

  const displayKeyword = keywords && keywords.length > 0 ? keywords[0] : 'PRICE';
  const displayAccountName = accountName ? (accountName.startsWith('@') ? accountName.slice(1) : accountName) : 'youraccount';

  let domain = 'example.com';
  try {
    if (deliveryLinkUrl && (deliveryLinkUrl.startsWith('http://') || deliveryLinkUrl.startsWith('https://'))) {
      domain = new URL(deliveryLinkUrl).hostname;
    }
  } catch {
    domain = 'example.com';
  }

  // Dynamic Avatar Helper - Uses real profile image or clean initial gradient (No fake stock photos!)
  const renderAvatar = (sizeClass = 'w-7 h-7', textSize = 'text-xs') => {
    if (avatarUrl) {
      return (
        <img
          src={avatarUrl}
          alt={displayAccountName}
          className={`${sizeClass} rounded-full object-cover shrink-0`}
        />
      );
    }
    const initial = displayAccountName ? displayAccountName.charAt(0).toUpperCase() : 'IG';
    return (
      <div
        className={`${sizeClass} rounded-full bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888] shrink-0 flex items-center justify-center text-white font-bold ${textSize} uppercase shadow-2xs`}
      >
        <span>{initial}</span>
      </div>
    );
  };

  return (
    <div className="flex flex-col items-center w-full max-w-sm mx-auto text-[#111110]">
      {/* ── TOP HEADER: Clean Live Preview ── */}
      <div className="w-full pb-3 mb-3 border-b border-[#ECECE8]">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
            <h3 className="text-xs font-bold text-[#111110]">Live Preview</h3>
          </div>
          <span className="text-[10px] font-mono text-[#064125] bg-[#EAF6EE] px-2 py-0.5 rounded font-bold">
            @{displayAccountName}
          </span>
        </div>
      </div>

      {/* ── SUB-BAR: TABS (Post | Comments | DM) & FOLLOWER STATE SWITCHER ── */}
      <div className="w-full flex items-center justify-between gap-2 mb-4">
        {/* Tabs: Post / Comments / DM */}
        <div className="flex items-center p-0.5 bg-[#F4F4F0] border border-[#ECECE8] rounded-xl">
          {!isStoryFlow && (
            <button
              type="button"
              onClick={() => setActiveTab('post')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === 'post'
                  ? 'bg-white text-[#111110] shadow-xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
            >
              Post
            </button>
          )}
          {!isStoryFlow && (
            <button
              type="button"
              onClick={() => setActiveTab('comments')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === 'comments'
                  ? 'bg-white text-[#111110] shadow-xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
            >
              Comments
            </button>
          )}
          <button
            type="button"
            onClick={() => setActiveTab('dm')}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'dm'
                ? 'bg-white text-[#111110] shadow-xs'
                : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            DM
          </button>
        </div>

        {/* Follower State Preview Switcher (Only visible when Ask to Follow is enabled!) */}
        {activeTab === 'dm' && askFollowEnabled && (
          <div className="flex items-center p-0.5 bg-[#F4F4F0] border border-[#ECECE8] rounded-xl text-[11px]">
            <button
              type="button"
              onClick={() => setPreviewState('follower')}
              className={`px-2 py-0.5 font-semibold rounded-lg transition-all cursor-pointer ${
                previewState === 'follower'
                  ? 'bg-white text-[#15803D] shadow-2xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
              title="Preview DM for an active follower"
            >
              Follower
            </button>
            <button
              type="button"
              onClick={() => setPreviewState('non_follower')}
              className={`px-2 py-0.5 font-semibold rounded-lg transition-all cursor-pointer ${
                previewState === 'non_follower'
                  ? 'bg-white text-[#D97706] shadow-2xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
              title="Preview DM for a non-follower with follow gate"
            >
              Non-follower
            </button>
          </div>
        )}
      </div>

      {/* ── REALISTIC IPHONE SIMULATOR FRAME ── */}
      <div className="w-full max-w-[340px] h-[580px] min-[400px]:h-[640px] bg-[#111110] rounded-[36px] min-[400px]:rounded-[44px] p-2.5 min-[400px]:p-3 shadow-2xl border-4 border-[#262626] relative flex flex-col overflow-hidden mx-auto">
        {/* Dynamic Island / Notch */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-24 h-5 bg-black rounded-full z-30 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-[#1A1A1A] ml-auto mr-2.5" />
        </div>

        {/* Screen Area */}
        <div className="w-full h-full bg-white rounded-[28px] min-[400px]:rounded-[34px] overflow-hidden flex flex-col relative pt-7">
          
          {/* TAB 1: POST PREVIEW */}
          {activeTab === 'post' && (
            <div className="flex-1 flex flex-col overflow-y-auto scrollbar-none text-[#111110]">
              {/* Instagram Post Header */}
              <div className="px-3 py-2 flex items-center justify-between border-b border-[#F4F4F0]">
                <div className="flex items-center gap-2">
                  {renderAvatar('w-7 h-7', 'text-[10px]')}
                  <div>
                    <div className="text-xs font-bold leading-none flex items-center gap-1">
                      <span>{displayAccountName}</span>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="#0095F6" className="shrink-0">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                      </svg>
                    </div>
                    <div className="text-[10px] text-[#70706B]">Original audio</div>
                  </div>
                </div>
                <MoreHorizontal size={16} className="text-[#70706B]" />
              </div>

              {/* Post Image: Real post image or Authentic Empty State */}
              {selectedPost?.imageUrl ? (
                <div className="aspect-square w-full bg-[#F4F4F0] relative overflow-hidden">
                  <img
                    src={selectedPost.imageUrl}
                    alt={selectedPost.caption || 'Instagram Post'}
                    className="w-full h-full object-cover"
                  />
                  {selectedPost.type === 'REEL' && (
                    <div className="absolute top-2 left-2 w-5 h-5 rounded-full bg-black/60 flex items-center justify-center text-white">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="white">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  )}
                </div>
              ) : (
                <div className="aspect-square w-full bg-[#FBFBFA] border-b border-[#ECECE8] flex flex-col items-center justify-center p-6 text-center text-[#70706B]">
                  <div className="w-12 h-12 rounded-2xl bg-white border border-[#ECECE8] shadow-2xs flex items-center justify-center text-[#9E9E96] mb-2">
                    <ImageIcon size={22} />
                  </div>
                  <span className="text-xs font-bold text-[#111110]">No Post Selected</span>
                  <span className="text-[11px] text-[#70706B] mt-0.5 max-w-[200px]">
                    Pick an eligible Instagram post in Step 1 to preview your post content here.
                  </span>
                </div>
              )}

              {/* Action Bar */}
              <div className="p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Heart size={20} className="hover:text-red-500 cursor-pointer" />
                    <MessageCircle 
                      size={20} 
                      className="cursor-pointer hover:text-[#15803D]" 
                      onClick={() => setActiveTab('comments')} 
                    />
                    <Send size={18} className="cursor-pointer" />
                  </div>
                  <Bookmark size={19} className="cursor-pointer" />
                </div>

                {selectedPost && (
                  <div className="text-xs font-bold">
                    {(selectedPost.likesCount ?? 0).toLocaleString()} likes
                  </div>
                )}

                {/* Caption */}
                <div className="text-xs leading-relaxed">
                  <span className="font-bold mr-1.5">{displayAccountName}</span>
                  <span>{selectedPost?.caption || (triggerMode === 'any_keyword' ? 'Leave any comment below for the link!' : `Comment ${displayKeyword} for direct access link!`)}</span>
                </div>

                <button
                  type="button"
                  onClick={() => setActiveTab('comments')}
                  className="text-xs text-[#70706B] block hover:text-[#111110] transition-colors"
                >
                  View all {(selectedPost?.commentsCount ?? 0)} comments
                </button>
                {selectedPost?.publishedDate && (
                  <div className="text-[10px] text-[#9E9E96] uppercase font-mono">
                    {selectedPost.publishedDate}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: COMMENTS PREVIEW */}
          {activeTab === 'comments' && (
            <div className="flex-1 flex flex-col overflow-hidden text-[#111110] bg-white">
              {/* Header */}
              <div className="px-3 py-2 border-b border-[#ECECE8] flex items-center justify-between bg-[#FBFBFA]">
                <span className="text-xs font-bold">Comments</span>
                <span className="text-[10px] font-semibold text-[#15803D] bg-[#DCFCE7] px-2 py-0.5 rounded-full uppercase">
                  Preview
                </span>
              </div>

              {/* Comments Thread */}
              <div className="flex-1 p-3 space-y-3 overflow-y-auto">
                {/* 1. Commenter triggering keyword */}
                <div className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                    U
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs">
                      <span className="font-bold text-[#111110] mr-1.5">user.comment</span>
                      {triggerMode === 'any_keyword' ? (
                        <>
                          <span className="text-[#111110]">
                            Can you please send me the link? 🔥
                          </span>
                          <span className="ml-1.5 text-[9px] font-semibold text-[#15803D] bg-[#DCFCE7] px-1 py-0.2 rounded inline-block">
                            Any comment
                          </span>
                        </>
                      ) : (
                        <span className="font-semibold text-[#062E1A] bg-[#DCFCE7] px-1 py-0.5 rounded">
                          {displayKeyword}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-[#70706B] mt-1">
                      <span>Just now</span>
                      <span>Reply</span>
                    </div>
                  </div>
                  <Heart size={12} className="text-[#9E9E96] mt-1 shrink-0" />
                </div>

                {/* 2. Automated Public Comment Reply */}
                {publicReplyEnabled ? (
                  <div className="flex items-start gap-2.5 ml-6 pl-3 border-l-2 border-[#22C55E] animate-in fade-in duration-150">
                    {renderAvatar('w-6 h-6', 'text-[9px]')}
                    <div className="flex-1 min-w-0">
                      <div className="text-xs leading-snug">
                        <span className="font-bold text-[#111110] mr-1">{displayAccountName}</span>
                        <span className="inline-block px-1 py-0.2 bg-[#F0FDF4] text-[#166534] rounded text-[10px] font-bold mr-1">
                          Author
                        </span>
                        <span className="text-[#30302E]">
                          {publicReplyText || 'Check your DM! 📩'}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-[#70706B] mt-1">
                        <span>Just now</span>
                        <span className="text-[#15803D] font-semibold">Automated Reply</span>
                      </div>
                    </div>
                    <Heart size={12} className="text-[#9E9E96] mt-1 shrink-0" />
                  </div>
                ) : (
                  <div className="ml-6 p-2 rounded-lg bg-[#FBFBFA] border border-dashed border-[#ECECE8] text-[11px] text-[#70706B] text-center">
                    Public comment reply is toggled OFF in Step 6
                  </div>
                )}
              </div>

              {/* Bottom Quick Emojis & Fake Comment Input */}
              <div className="p-2.5 border-t border-[#ECECE8] bg-[#FBFBFA]">
                <div className="flex items-center justify-around text-sm pb-1.5 text-gray-700">
                  <span>❤️</span>
                  <span>🔥</span>
                  <span>👏</span>
                  <span>😍</span>
                  <span>🙌</span>
                </div>
                <div className="flex items-center gap-2 bg-white border border-[#ECECE8] rounded-full px-3 py-1.5 text-xs text-[#9E9E96]">
                  <span>Add a comment for {displayAccountName}...</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DM CHAT PREVIEW */}
          {activeTab === 'dm' && (
            <div className="flex-1 flex flex-col overflow-hidden text-[#111110] bg-white">
              {/* Instagram DM Header */}
              <div className="px-3 py-2 border-b border-[#ECECE8] flex items-center justify-between bg-white shrink-0">
                <div className="flex items-center gap-2">
                  <ChevronLeft size={18} className="text-[#111110] cursor-pointer" />
                  {renderAvatar('w-7 h-7', 'text-[10px]')}
                  <div>
                    <div className="text-xs font-bold flex items-center gap-1 text-[#111110]">
                      <span>{displayAccountName}</span>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="#0095F6" className="shrink-0">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                      </svg>
                    </div>
                    <div className="text-[9.5px] text-[#70706B]">Business chat</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5 text-[#111110]">
                  <Phone size={15} />
                  <Video size={16} />
                </div>
              </div>

              {/* Chat Thread Messages */}
              <div className="flex-1 p-3 space-y-3 overflow-y-auto text-xs scrollbar-thin">
                
                {/* 1. User Message (Right-aligned, Blue Bubble with keyword) */}
                <div className="flex justify-end">
                  <div className="bg-[#0084FF] text-white px-3.5 py-1.5 rounded-2xl rounded-tr-sm text-xs font-semibold shadow-2xs">
                    {displayKeyword}
                  </div>
                </div>

                {/* 2. Centered Timestamp */}
                <div className="text-center my-1">
                  <span className="text-[10px] text-[#9E9E96] font-medium">Just now</span>
                </div>

                {/* 3. Non-Follower Gate Message (If non_follower view is active and askFollow is enabled) */}
                {askFollowEnabled && previewState === 'non_follower' ? (
                  <div className="flex items-start gap-2 max-w-[90%] animate-in fade-in duration-150">
                    {renderAvatar('w-6 h-6', 'text-[9px]')}
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="bg-[#EFEFEF] text-[#111110] px-3.5 py-2.5 rounded-2xl rounded-tl-sm text-xs leading-relaxed whitespace-pre-wrap shadow-2xs">
                        {askFollowText || `Please follow @${displayAccountName} to unlock this link!`}
                      </div>
                      <button
                        type="button"
                        onClick={() => setPreviewState('follower')}
                        className="w-full py-2 px-3 bg-[#0095F6] hover:bg-[#1877F2] text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                      >
                        <span>Follow @{displayAccountName}</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  /* 4. Automated DM Message (Left-aligned from Connected Account, unlocked for followers) */
                  <div className="flex items-start gap-2 max-w-[90%] animate-in fade-in duration-150">
                    {renderAvatar('w-6 h-6', 'text-[9px]')}
                    <div className="space-y-1.5 flex-1 min-w-0">
                      {/* DM Text Bubble */}
                      <div className="bg-[#EFEFEF] text-[#111110] px-3.5 py-2.5 rounded-2xl rounded-tl-sm text-xs leading-relaxed whitespace-pre-wrap shadow-2xs">
                        {deliveryText || `Hey! 👋 Here's the resource you requested:`}
                      </div>

                      {/* Rich Link Card inside DM */}
                      {deliveryLinkButtonText && (
                        <div className="w-full bg-white border border-[#ECECE8] rounded-xl overflow-hidden shadow-2xs">
                          <div className="p-2.5 flex items-center gap-2.5 bg-[#FAFAFA] border-b border-[#F4F4F0]">
                            {renderAvatar('w-9 h-9', 'text-sm')}
                            <div className="min-w-0 flex-1">
                              <div className="text-xs font-bold text-[#111110] truncate">
                                {deliveryLinkButtonText}
                              </div>
                              <div className="text-[10px] text-[#70706B] truncate font-mono">
                                {domain}
                              </div>
                              <div className="text-[10.5px] text-[#70706B] truncate">
                                Destination Resource Link
                              </div>
                            </div>
                          </div>
                          <button
                            type="button"
                            className="w-full py-2 px-3 text-center text-xs font-semibold text-[#0084FF] hover:bg-[#F4F8FF] transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                          >
                            <span>{deliveryLinkButtonText}</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 5. Follow-up DM (if enabled) */}
                {followupEnabled && (
                  <div className="space-y-2 pt-2 animate-in fade-in duration-150">
                    <div className="flex items-center justify-center">
                      <span className="px-2 py-0.5 bg-[#F4F4F0] rounded-full text-[9px] font-mono text-[#70706B] uppercase tracking-wider">
                        {followupHours || 2} hours later
                      </span>
                    </div>

                    <div className="flex items-start gap-2 max-w-[90%]">
                      {renderAvatar('w-6 h-6', 'text-[9px]')}
                      <div className="bg-[#EFEFEF] text-[#111110] px-3.5 py-2.5 rounded-2xl rounded-tl-sm leading-relaxed shadow-2xs">
                        {followupText || 'Hey! Just checking in — did you get a chance to look at what I sent? 😊'}
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-end gap-1 text-[10px] text-[#9E9E96] pt-1">
                  <CheckCheck size={12} className="text-[#0084FF]" />
                  <span>Seen</span>
                </div>
              </div>

              {/* Bottom Chat Input Bar */}
              <div className="p-2 border-t border-[#ECECE8] flex items-center gap-2 bg-white shrink-0">
                <div className="w-7 h-7 rounded-full bg-[#0084FF] text-white flex items-center justify-center shrink-0 shadow-2xs">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
                    <circle cx="12" cy="13" r="3"/>
                  </svg>
                </div>
                <div className="flex-1 bg-[#F4F4F0] rounded-full px-3 py-1.5 flex items-center justify-between text-xs text-[#9E9E96]">
                  <span>Message...</span>
                </div>
                <div className="flex items-center gap-2 text-[#70706B] pr-1">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" x2="12" y1="19" y2="22"/>
                  </svg>
                  <ImageIcon size={16} />
                  <Smile size={16} />
                </div>
              </div>
            </div>
          )}

          {/* Bottom Home Indicator Bar */}
          <div className="w-24 h-1 bg-black rounded-full mx-auto my-1.5 shrink-0" />
        </div>
      </div>
    </div>
  );
}

export default InstagramPhonePreview;
