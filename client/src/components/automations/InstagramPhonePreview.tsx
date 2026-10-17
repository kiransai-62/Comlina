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
  Info, 
  Smile, 
  Image as ImageIcon,
  ExternalLink,
  ShieldCheck,
  CheckCheck
} from 'lucide-react';
import { InstagramMediaItem } from './PostSelector';

export interface InstagramPhonePreviewProps {
  accountName?: string;
  avatarUrl?: string;
  selectedPost?: InstagramMediaItem;
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
}

export function InstagramPhonePreview({
  accountName = 'yourbrand.hq',
  avatarUrl = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
  selectedPost,
  keywords = ['PRICE'],
  publicReplyEnabled = false,
  publicReplyText = '',
  openingDmEnabled = true,
  openingDmText = '',
  openingDmButtonText = '',
  askFollowEnabled = false,
  askFollowText = '',
  askEmailEnabled = false,
  askEmailText = '',
  deliveryText = '',
  deliveryLinkUrl = '',
  deliveryLinkButtonText = '',
  followupEnabled = false,
  followupHours = 2,
  followupText = '',
  defaultTab,
  isStoryFlow = false,
  storyImageUrl = 'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=600&auto=format&fit=crop&q=80',
}: InstagramPhonePreviewProps) {
  const [activeTab, setActiveTab] = useState<'post' | 'comments' | 'dm' | 'story'>(
    defaultTab || (isStoryFlow ? 'story' : 'dm')
  );
  const [simulatedClick, setSimulatedClick] = useState(false);

  // Sync activeTab when defaultTab changes
  React.useEffect(() => {
    if (defaultTab) {
      setActiveTab(defaultTab);
    }
  }, [defaultTab]);

  const displayKeyword = keywords.length > 0 ? keywords[0] : 'PRICE';

  let domain = 'yourdomain.com';
  try {
    if (deliveryLinkUrl && (deliveryLinkUrl.startsWith('http://') || deliveryLinkUrl.startsWith('https://'))) {
      domain = new URL(deliveryLinkUrl).hostname;
    }
  } catch {
    domain = 'yourdomain.com';
  }

  return (
    <div className="flex flex-col items-center w-full">
      {/* Tab Switcher Pills */}
      <div className="flex items-center gap-1 p-1 bg-[#F4F4F0] border border-[#ECECE8] rounded-full mb-4 shadow-2xs">
        {isStoryFlow && (
          <button
            type="button"
            onClick={() => setActiveTab('story')}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer ${
              activeTab === 'story'
                ? 'bg-white text-[#111110] shadow-xs'
                : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            Story
          </button>
        )}
        {!isStoryFlow && (
          <button
            type="button"
            onClick={() => setActiveTab('post')}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer ${
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
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer ${
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
          className={`px-3 py-1 text-xs font-semibold rounded-full transition-all cursor-pointer ${
            activeTab === 'dm'
              ? 'bg-white text-[#111110] shadow-xs'
              : 'text-[#70706B] hover:text-[#111110]'
          }`}
        >
          DM
        </button>
      </div>

      {/* Phone Simulator Frame */}
      <div className="w-[340px] h-[640px] bg-black rounded-[42px] p-3 shadow-2xl border-4 border-[#262626] relative flex flex-col overflow-hidden">
        {/* Notch / Dynamic Island */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-28 h-5 bg-black rounded-full z-30 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-[#1A1A1A] ml-auto mr-3" />
        </div>

        {/* Screen Area */}
        <div className="w-full h-full bg-white rounded-[32px] overflow-hidden flex flex-col relative pt-7">
          
          {/* TAB 0: STORY PREVIEW */}
          {activeTab === 'story' && (
            <div className="flex-1 flex flex-col relative overflow-hidden bg-black text-white">
              {/* Story Progress Bar */}
              <div className="absolute top-2 inset-x-3 z-20 flex gap-1">
                <div className="h-0.5 flex-1 bg-white/90 rounded-full" />
                <div className="h-0.5 flex-1 bg-white/40 rounded-full" />
                <div className="h-0.5 flex-1 bg-white/40 rounded-full" />
              </div>

              {/* Story Header */}
              <div className="absolute top-4 inset-x-3 z-20 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="p-0.5 rounded-full bg-gradient-to-tr from-yellow-400 to-pink-600">
                    <img
                      src={avatarUrl}
                      alt={accountName}
                      className="w-6 h-6 rounded-full object-cover"
                    />
                  </div>
                  <span className="font-bold text-white drop-shadow">{accountName}</span>
                  <span className="text-[10px] text-white/70">2h</span>
                </div>
                <MoreHorizontal size={16} className="text-white drop-shadow" />
              </div>

              {/* Story Media Background */}
              <div className="absolute inset-0 z-10 overflow-hidden">
                <img
                  src={storyImageUrl || selectedPost?.imageUrl || ''}
                  alt="Story background"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-transparent to-black/70" />
              </div>

              {/* Interactive Sticker / Prompt */}
              <div className="relative z-20 mt-auto mb-16 mx-4">
                <div className="bg-white/95 backdrop-blur-md rounded-2xl p-4 text-center shadow-lg text-[#111110]">
                  <div className="text-[11px] font-bold text-[#15803D] uppercase tracking-wider mb-1">
                    Automated Story Trigger
                  </div>
                  <div className="text-xs font-bold leading-snug">
                    Reply &ldquo;{displayKeyword}&rdquo; to receive the link in your DM! 🎁
                  </div>
                </div>
              </div>

              {/* Story Reply Input Bar */}
              <div className="relative z-20 px-3 pb-3 pt-1 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('dm')}
                  className="flex-1 bg-black/40 backdrop-blur-md border border-white/30 rounded-full px-3 py-2 text-xs text-white/80 text-left flex items-center justify-between hover:bg-black/60 transition-colors"
                >
                  <span>Reply &ldquo;{displayKeyword}&rdquo;...</span>
                  <Send size={13} className="text-white" />
                </button>
                <div className="p-2 rounded-full bg-black/40 backdrop-blur-md border border-white/30 text-white">
                  <Heart size={16} className="text-red-500 fill-red-500" />
                </div>
              </div>
            </div>
          )}
          
          {/* TAB 1: POST PREVIEW */}
          {activeTab === 'post' && (
            <div className="flex-1 flex flex-col overflow-y-auto scrollbar-none text-[#111110]">
              {!selectedPost ? (
                <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-[#70706B] bg-[#FAFAFA]">
                  <div className="w-14 h-14 rounded-2xl bg-[#ECECE8] flex items-center justify-center mb-3 text-[#70706B]">
                    <ImageIcon size={26} />
                  </div>
                  <div className="text-xs font-semibold text-[#111110] mb-1">No post selected</div>
                  <div className="text-xs text-[#70706B] max-w-[200px] leading-relaxed">
                    Select a post from the trigger step to see the live preview.
                  </div>
                </div>
              ) : (
                <>
                  {/* Instagram Post Header */}
                  <div className="px-3 py-2 flex items-center justify-between border-b border-[#F4F4F0]">
                    <div className="flex items-center gap-2">
                      <img
                        src={avatarUrl}
                        alt={accountName}
                        className="w-7 h-7 rounded-full object-cover ring-1 ring-black/10"
                      />
                      <div>
                        <div className="text-xs font-bold leading-none">{accountName}</div>
                        <div className="text-[10px] text-[#70706B]">Sponsored • Original audio</div>
                      </div>
                    </div>
                    <MoreHorizontal size={16} className="text-[#70706B]" />
                  </div>

                  {/* Post Image */}
                  <div className="aspect-square w-full bg-[#F4F4F0] relative overflow-hidden">
                    <img
                      src={selectedPost.imageUrl}
                      alt="Post preview"
                      className="w-full h-full object-cover"
                    />
                  </div>

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

                    <div className="text-xs font-bold">{(selectedPost.likesCount ?? 0).toLocaleString()} likes</div>

                    {/* Caption */}
                    <div className="text-xs leading-relaxed">
                      <span className="font-bold mr-1.5">{accountName}</span>
                      <span>{selectedPost.caption || ''}</span>
                    </div>

                    {/* Comments Trigger Link */}
                    <button
                      type="button"
                      onClick={() => setActiveTab('comments')}
                      className="text-xs text-[#70706B] block hover:text-[#111110] transition-colors"
                    >
                      View all {selectedPost.commentsCount ?? 0} comments
                    </button>
                    <div className="text-[10px] text-[#9E9E96] uppercase font-mono">{selectedPost.publishedDate || ''}</div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB 2: COMMENTS PREVIEW */}
          {activeTab === 'comments' && (
            <div className="flex-1 flex flex-col overflow-hidden text-[#111110] bg-white">
              {/* Header */}
              <div className="px-3 py-2.5 border-b border-[#ECECE8] flex items-center justify-between">
                <span className="text-xs font-bold">Comments</span>
                <span className="text-[11px] text-[#70706B]">{(selectedPost?.commentsCount ?? 0) + 1}</span>
              </div>

              {/* Comments Thread */}
              <div className="flex-1 p-3 space-y-3 overflow-y-auto">
                {/* 1. Original Follower Comment triggering automation */}
                <div className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                    A
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs">
                      <span className="font-bold text-[#111110] mr-1.5">alex.designs</span>
                      <span className="font-semibold text-[#062E1A] bg-[#DCFCE7] px-1 py-0.5 rounded">
                        {displayKeyword} please!
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-[#70706B] mt-1">
                      <span>1m</span>
                      <span>Reply</span>
                    </div>
                  </div>
                  <Heart size={12} className="text-[#9E9E96] mt-1 shrink-0" />
                </div>

                {/* 2. Automated Public Comment Reply (if enabled) */}
                {publicReplyEnabled ? (
                  <div className="flex items-start gap-2.5 ml-6 pl-3 border-l-2 border-[#DCFCE7] animate-in fade-in slide-in-from-top-2 duration-200">
                    <img
                      src={avatarUrl}
                      alt={accountName}
                      className="w-6 h-6 rounded-full object-cover shrink-0 ring-1 ring-[#15803D]/30"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs leading-snug">
                        <span className="font-bold text-[#111110] mr-1">{accountName}</span>
                        <span className="inline-block px-1 py-0.2 bg-[#F0FDF4] text-[#166534] rounded text-[10px] font-bold mr-1">
                          Author
                        </span>
                        <span className="text-[#30302E]">
                          {publicReplyText || 'Thanks! Check your DMs 👋'}
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
                    Public comment reply is toggled OFF
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
                  <span>Add a comment for {accountName}...</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DM PREVIEW */}
          {activeTab === 'dm' && (
            <div className="flex-1 flex flex-col overflow-hidden text-[#111110] bg-white">
              {/* Instagram DM Header */}
              <div className="px-3 py-2 border-b border-[#ECECE8] flex items-center justify-between bg-white shrink-0">
                <div className="flex items-center gap-2">
                  <ChevronLeft size={18} className="text-[#111110] cursor-pointer" />
                  <div className="relative">
                    <img
                      src={avatarUrl}
                      alt={accountName}
                      className="w-7 h-7 rounded-full object-cover"
                    />
                    <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white" />
                  </div>
                  <div>
                    <div className="text-xs font-bold flex items-center gap-1">
                      {accountName}
                      <ShieldCheck size={11} className="text-[#15803D]" />
                    </div>
                    <div className="text-[9px] text-[#70706B]">Active now</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5 text-[#111110]">
                  <Phone size={15} />
                  <Video size={16} />
                  <Info size={16} />
                </div>
              </div>

              {/* Chat Thread Messages */}
              <div className="flex-1 p-3 space-y-3 overflow-y-auto text-xs">
                
                {/* 1. Opening DM Bubble (From Brand) */}
                {openingDmEnabled && (
                  <div className="flex flex-col items-start max-w-[85%] space-y-1 animate-in fade-in duration-150">
                    <div className="bg-[#EFEFEF] text-[#111110] p-3 rounded-2xl rounded-tl-sm whitespace-pre-wrap leading-relaxed shadow-2xs">
                      {openingDmText || "Hey there! Thanks so much for your interest 😊\n\nClick below and I'll send you the link in just a sec ✨"}
                    </div>
                    {/* Interactive CTA Button */}
                    <button
                      type="button"
                      onClick={() => setSimulatedClick(!simulatedClick)}
                      className="w-full py-2 px-3 bg-white border border-[#D3D3CE] hover:bg-[#F4F4F0] text-[#111110] font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <span>{openingDmButtonText || 'Send me the link'}</span>
                    </button>
                  </div>
                )}

                {/* 2. User Click Reaction (Simulated incoming message) */}
                {(openingDmEnabled || simulatedClick) && (
                  <div className="flex justify-end">
                    <div className="bg-[#0084FF] text-white px-3 py-1.5 rounded-2xl rounded-tr-sm max-w-[75%] font-medium shadow-2xs">
                      {openingDmButtonText || 'Send me the link'}
                    </div>
                  </div>
                )}

                {/* 3. Follow Gate Message (if enabled) */}
                {askFollowEnabled && (
                  <div className="flex flex-col items-start max-w-[85%] space-y-1">
                    <div className="bg-[#EFEFEF] text-[#111110] p-2.5 rounded-2xl rounded-tl-sm whitespace-pre-wrap leading-relaxed">
                      {askFollowText || 'Follow me and I will send you the link! 🙌'}
                    </div>
                  </div>
                )}

                {/* 4. Email Gate Message (if enabled) */}
                {askEmailEnabled && (
                  <div className="flex flex-col items-start max-w-[85%] space-y-1">
                    <div className="bg-[#EFEFEF] text-[#111110] p-2.5 rounded-2xl rounded-tl-sm leading-relaxed">
                      {askEmailText || "What's the best email address to send this to? 📬"}
                    </div>
                  </div>
                )}

                {/* 5. Resource DM with Link Card (From Brand) */}
                <div className="flex flex-col items-start max-w-[90%] space-y-1.5">
                  <div className="bg-[#EFEFEF] text-[#111110] p-3 rounded-2xl rounded-tl-sm whitespace-pre-wrap leading-relaxed">
                    {deliveryText || "Here's the resource you requested! 🚀 Let me know if you need anything else."}
                  </div>

                  {/* Rich Link Card inside DM */}
                  <div className="w-full bg-white border border-[#ECECE8] rounded-xl overflow-hidden shadow-xs">
                    <div className="p-2.5 border-b border-[#F4F4F0] bg-[#FAFAFA]">
                      <div className="text-[10px] text-[#70706B] truncate font-mono">{domain}</div>
                      <div className="text-xs font-bold text-[#111110] truncate mt-0.5">
                        Exclusive Resource Access
                      </div>
                    </div>
                    <div className="p-2 flex items-center justify-between bg-white">
                      <span className="text-[11px] font-semibold text-[#0084FF]">
                        {deliveryLinkButtonText || 'View the resource'}
                      </span>
                      <ExternalLink size={12} className="text-[#0084FF]" />
                    </div>
                  </div>
                </div>

                {/* 6. Follow-up DM (if enabled) */}
                {followupEnabled && (
                  <div className="space-y-2 pt-2">
                    <div className="flex items-center justify-center">
                      <span className="px-2 py-0.5 bg-[#F4F4F0] rounded-full text-[9px] font-mono text-[#70706B] uppercase tracking-wider">
                        {followupHours} hours later
                      </span>
                    </div>

                    <div className="flex flex-col items-start max-w-[85%] space-y-1">
                      <div className="bg-[#EFEFEF] text-[#111110] p-2.5 rounded-2xl rounded-tl-sm leading-relaxed">
                        {followupText || 'Hey! Just checking if you got the resource 😊'}
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
              <div className="p-2.5 border-t border-[#ECECE8] flex items-center gap-2 bg-white shrink-0">
                <div className="flex-1 bg-[#F4F4F0] rounded-full px-3 py-1.5 flex items-center justify-between text-xs text-[#9E9E96]">
                  <span>Message...</span>
                  <Smile size={16} className="text-[#70706B]" />
                </div>
                <ImageIcon size={18} className="text-[#70706B]" />
                <Heart size={18} className="text-[#70706B]" />
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
