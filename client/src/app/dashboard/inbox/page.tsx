// client/src/app/dashboard/inbox/page.tsx
'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Instagram, 
  Calendar, 
  ChevronDown, 
  ChevronRight, 
  ChevronLeft, 
  ExternalLink, 
  MoreVertical, 
  Paperclip, 
  Smile, 
  Send, 
  Plus, 
  CheckCheck, 
  Ban, 
  Edit3,
  MessageSquare,
  AlertCircle,
  RefreshCw,
  User
} from 'lucide-react';
import { authService } from '@/lib/auth';
import { conversationsApi } from '@/features/conversations/api';

export default function ConversationsPage() {
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'UNREAD' | 'REPLIED' | 'DM_SENT' | 'NEEDS_ACTION'>('ALL');
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [replyMode, setReplyMode] = useState<'DM' | 'COMMENT'>('DM');
  const [messageText, setMessageText] = useState('');
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Fetch conversations
  const { 
    data: conversations, 
    isLoading: loadingConversations, 
    isError: errorConversations, 
    error: convError, 
    refetch: refetchConversations 
  } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list(),
  });

  const convList: any[] = Array.isArray(conversations) ? conversations : [];

  // Determine active conversation: user selection, or first conversation if available, or null
  const activeConvId = selectedConvId || (convList.length > 0 ? convList[0].id : null);
  const selectedConv: any = convList.find((c: any) => c.id === activeConvId) || null;

  // 24-hour messaging window rule: replies allowed only within 24h of customer's last message
  const isPast24Hours = useMemo(() => {
    if (!selectedConv?.last_message_at) return false;
    const lastTime = new Date(selectedConv.last_message_at).getTime();
    if (isNaN(lastTime)) return false;
    return Date.now() - lastTime > 24 * 60 * 60 * 1000;
  }, [selectedConv?.last_message_at]);

  // 2. Fetch messages for active conversation
  const { 
    data: serverMessages = [], 
    isLoading: loadingMessages 
  } = useQuery({
    queryKey: ['messages', activeConvId],
    queryFn: () => (activeConvId ? conversationsApi.getMessages(activeConvId) : Promise.resolve([])),
    enabled: !!activeConvId,
  });

  const allMessages: any[] = Array.isArray(serverMessages) ? serverMessages : [];

  useEffect(() => {
    if (allMessages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [allMessages.length, activeConvId]);

  const sendMutation = useMutation({
    mutationFn: ({ conversationId, text }: { conversationId: string; text: string }) =>
      conversationsApi.sendMessage(conversationId, text),
    onSuccess: (_d, vars) => {
      setMessageText('');
      queryClient.invalidateQueries({ queryKey: ['messages', vars.conversationId] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    },
  });

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isPast24Hours) return;
    const text = messageText.trim();
    if (!text || !selectedConv || sendMutation.isPending) return;
    sendMutation.mutate({ conversationId: selectedConv.id, text });
  };

  // Filter conversations based on selected tab
  const filteredConversations = convList.filter((c: any) => {
    if (activeFilter === 'ALL') return true;
    if (activeFilter === 'UNREAD') return (c.unread_count || 0) > 0;
    if (activeFilter === 'REPLIED') return c.status === 'REPLIED';
    if (activeFilter === 'DM_SENT') return true;
    if (activeFilter === 'NEEDS_ACTION') return (c.unread_count || 0) > 0;
    return true;
  });

  return (
    <div className="max-w-[1440px] mx-auto space-y-5">
      {/* Top Title & Context Action Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#111110] tracking-tight">Conversations</h1>
          <p className="text-xs text-[#70706B] mt-1">
            View and manage all Instagram conversations in one place.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Account Selector Pill */}
          <button className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] text-[#111110] text-xs font-semibold shadow-2xs cursor-pointer transition-all">
            <Instagram size={14} className="text-[#111110]" />
            <span>Connected Account</span>
            <ChevronDown size={13} className="text-[#70706B] ml-0.5" />
          </button>

          {/* Time Range Selector Pill */}
          <button className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] text-[#111110] text-xs font-semibold shadow-2xs cursor-pointer transition-all">
            <Calendar size={14} className="text-[#70706B]" />
            <span>Live Sync</span>
          </button>
        </div>
      </div>

      {/* Global Error Banner if conversations API fails */}
      {errorConversations && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600 shrink-0" />
            <div>
              <div className="text-xs font-semibold text-red-900">Failed to load conversations</div>
              <div className="text-xs text-red-700">
                {(convError as any)?.message || 'Unable to connect to backend server. Conversations cannot be displayed.'}
              </div>
            </div>
          </div>
          <button
            onClick={async () => {
              await authService.refreshToken();
              refetchConversations();
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all shrink-0 cursor-pointer"
          >
            <RefreshCw size={13} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* 3-Column Split Layout */}
      <div className="grid grid-cols-12 gap-5 items-start">
        
        {/* ========================================================= */}
        {/* COLUMN 1: Conversation List & Filters (3.5 cols) */}
        {/* ========================================================= */}
        <div className={`col-span-12 md:col-span-4 xl:col-span-3.5 bg-white border border-[#ECECE8] rounded-2xl flex flex-col h-[650px] md:h-[780px] shadow-2xs overflow-hidden ${
          selectedConvId ? 'hidden md:flex' : 'flex'
        }`}>
          {/* Filter Segment Tabs */}
          <div className="p-3 border-b border-[#ECECE8]/60 flex items-center gap-1 overflow-x-auto no-scrollbar">
            {[
              { id: 'ALL', label: 'All' },
              { id: 'UNREAD', label: 'Unread' },
              { id: 'REPLIED', label: 'Replied' },
              { id: 'DM_SENT', label: 'DM Sent' },
              { id: 'NEEDS_ACTION', label: 'Needs Action' },
            ].map((tab) => {
              const isActive = activeFilter === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id as any)}
                  className={`px-3 py-1.5 rounded-lg text-xs whitespace-nowrap transition-all cursor-pointer font-semibold ${
                    isActive
                      ? 'bg-[#064125] text-white shadow-xs'
                      : 'text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F1]'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Loading State */}
          {loadingConversations && (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="flex items-center gap-3 p-3 animate-pulse">
                  <div className="w-10 h-10 rounded-full bg-gray-200 shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-28 bg-gray-200 rounded" />
                    <div className="h-2.5 w-40 bg-gray-100 rounded" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loadingConversations && !errorConversations && convList.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-3">
              <div className="w-10 h-10 rounded-full bg-[#FAFAF8] border border-[#ECECE8] flex items-center justify-center text-[#70706B]">
                <MessageSquare size={18} />
              </div>
              <div className="text-xs font-bold text-[#111110]">No conversations yet</div>
              <p className="text-xs text-[#70706B] max-w-xs">
                When someone comments or DMs your connected Instagram account, their conversation will appear here.
              </p>
            </div>
          )}

          {/* Conversation Rows */}
          {!loadingConversations && !errorConversations && convList.length > 0 && (
            <div className="flex-1 overflow-y-auto divide-y divide-[#ECECE8]/40 p-2 space-y-1">
              {filteredConversations.map((c: any) => {
                const isSelected = activeConvId === c.id;
                const rawUsername = c.contact_username || c.username || 'User';
                const handle = rawUsername.startsWith('@') ? rawUsername : `@${rawUsername}`;
                const initial = rawUsername.replace('@', '').charAt(0).toUpperCase() || 'U';
                const hasUnread = (c.unread_count || 0) > 0;

                return (
                  <div
                    key={c.id}
                    onClick={() => setSelectedConvId(c.id)}
                    className={`p-3 rounded-xl cursor-pointer transition-all flex items-center gap-3 ${
                      isSelected
                        ? 'bg-[#F2F2EE]'
                        : 'hover:bg-[#FBFBFA]'
                    }`}
                  >
                    {/* Avatar with initial */}
                    <div className="w-10 h-10 rounded-full shrink-0 border border-[#ECECE8] bg-[#EAF6EE] text-[#064125] flex items-center justify-center font-bold text-xs">
                      {initial}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[#111110] truncate">{handle}</span>
                        <span className="text-xs text-[#9E9E96] font-medium shrink-0">
                          {c.last_message_at || 'Recent'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-0.5">
                        <p className="text-xs text-[#70706B] truncate font-medium">
                          {c.last_message_text || c.message || '—'}
                        </p>
                        {/* Status Indicator Dot */}
                        <span
                          className={`w-2 h-2 rounded-full shrink-0 ml-2 ${
                            hasUnread ? 'bg-[#15803D]' : 'bg-[#DCDCD6]'
                          }`}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ========================================================= */}
        {/* COLUMN 2: Active Chat Stream (5 cols) */}
        {/* ========================================================= */}
        <div className={`col-span-12 md:col-span-8 xl:col-span-5 bg-white border border-[#ECECE8] rounded-2xl flex flex-col h-[650px] md:h-[780px] shadow-2xs overflow-hidden ${
          !selectedConvId ? 'hidden md:flex' : 'flex'
        }`}>
          {selectedConv ? (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-[#ECECE8] flex items-center justify-between bg-white shrink-0">
                <div className="flex items-center gap-2.5 sm:gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedConvId(null)}
                    className="md:hidden p-1.5 -ml-1 text-[#70706B] hover:text-[#111110] rounded-lg hover:bg-[#F4F4F0] cursor-pointer"
                    title="Back to conversations"
                  >
                    <ChevronLeft size={20} />
                  </button>
                  <div className="w-10 h-10 rounded-full border border-[#ECECE8] bg-[#EAF6EE] text-[#064125] flex items-center justify-center font-bold text-xs shrink-0">
                    {(selectedConv.contact_username || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-bold text-sm text-[#111110]">
                      {selectedConv.contact_username?.startsWith('@') ? selectedConv.contact_username : `@${selectedConv.contact_username || 'User'}`}
                    </div>
                    <div className="text-xs text-[#70706B] font-medium">
                      {selectedConv.followers != null ? `${selectedConv.followers.toLocaleString()} followers` : 'Instagram Contact'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <a
                    href={`https://instagram.com/${encodeURIComponent((selectedConv.contact_username || '').replace('@', ''))}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-[#111110] hover:underline"
                  >
                    <span>View Profile</span>
                    <ExternalLink size={12} className="text-[#70706B]" />
                  </a>
                  <button className="text-[#70706B] hover:text-[#111110] p-1 cursor-pointer">
                    <MoreVertical size={16} />
                  </button>
                </div>
              </div>

              {/* Chat Messages Stream */}
              <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-[#FFFFFF]">
                {loadingMessages && (
                  <div className="text-center py-6 text-xs text-[#9E9E96]">
                    Loading message history...
                  </div>
                )}

                {!loadingMessages && allMessages.length === 0 && (
                  <div className="text-center py-12 space-y-2 text-xs text-[#70706B]">
                    <MessageSquare size={24} className="mx-auto text-[#9E9E96]" />
                    <p>No messages recorded in this conversation yet.</p>
                  </div>
                )}

                {allMessages.map((msg: any) => {
                  const isOutgoing = msg.sender_type === 'BOT' || msg.sender_type === 'INSTAGRAM_ACCOUNT';

                  if (!isOutgoing) {
                    return (
                      <div key={msg.id} className="space-y-1">
                        <div className="flex items-end gap-2 max-w-[80%]">
                          <div className="bg-[#F2F2EE] text-[#111110] rounded-2xl rounded-bl-xs px-4 py-2.5 text-xs font-medium leading-relaxed">
                            {msg.text}
                          </div>
                        </div>
                        <div className="text-xs text-[#9E9E96] pl-1 font-medium">
                          {msg.created_at || 'Delivered'}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={msg.id} className="space-y-1 flex flex-col items-end">
                      <div className="flex items-end gap-2 max-w-[80%] flex-row-reverse">
                        <div className="bg-[#064125] text-white rounded-2xl rounded-br-xs px-4 py-2.5 text-xs font-medium leading-relaxed whitespace-pre-line shadow-2xs">
                          {msg.text}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-[#9E9E96] pr-1 font-medium">
                        <span>{msg.created_at || 'Delivered'}</span>
                        <CheckCheck size={12} className="text-[#15803D]" />
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Dock */}
              <div className="p-3 border-t border-[#ECECE8] bg-[#FAFAF8] shrink-0 space-y-2">
                {isPast24Hours && (
                  <div className="flex items-center gap-2 p-2.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
                    <AlertCircle size={14} className="text-amber-600 shrink-0" />
                    <span>Instagram only allows replies within 24 hours of the customer&apos;s last message.</span>
                  </div>
                )}

                <form onSubmit={handleSendMessage} className="bg-white border border-[#ECECE8] rounded-xl p-2 shadow-2xs space-y-2">
                  <textarea
                    value={messageText}
                    disabled={isPast24Hours}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder={isPast24Hours ? "Replies restricted: outside 24-hour window" : "Type a response message..."}
                    rows={2}
                    className={`w-full text-xs text-[#111110] placeholder:text-[#9E9E96] outline-none resize-none px-2 ${
                      isPast24Hours ? 'bg-neutral-50 cursor-not-allowed opacity-60' : ''
                    }`}
                  />

                  {sendMutation.isError && (
                    <div className="flex items-center gap-1.5 px-2 text-xs text-red-600">
                      <AlertCircle size={12} />
                      <span>{(sendMutation.error as Error)?.message || 'Message could not be sent.'}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-2">
                      {/* DM / Comment reply mode toggle (Coming soon) */}
                      <div 
                        title="Coming soon"
                        className="inline-flex items-center p-0.5 bg-[#F4F4F1] rounded-lg border border-[#ECECE8] opacity-50 cursor-not-allowed select-none"
                      >
                        <button
                          type="button"
                          disabled
                          title="Coming soon"
                          className="px-2 py-0.5 text-xs font-semibold rounded-md bg-white text-[#111110] shadow-2xs cursor-not-allowed"
                        >
                          DM
                        </button>
                        <button
                          type="button"
                          disabled
                          title="Coming soon"
                          className="px-2 py-0.5 text-xs font-semibold rounded-md text-[#70706B] cursor-not-allowed"
                        >
                          Comment
                        </button>
                      </div>

                      <div className="flex items-center gap-1 text-[#70706B]">
                        <button 
                          type="button" 
                          disabled 
                          title="Coming soon" 
                          className="p-1.5 text-[#70706B] opacity-50 cursor-not-allowed rounded-lg"
                        >
                          <Paperclip size={16} />
                        </button>
                        <button 
                          type="button" 
                          disabled 
                          title="Coming soon" 
                          className="p-1.5 text-[#70706B] opacity-50 cursor-not-allowed rounded-lg"
                        >
                          <Smile size={16} />
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isPast24Hours || !messageText.trim() || sendMutation.isPending}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-[#064125] hover:bg-[#085230] disabled:opacity-40 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-xs"
                    >
                      <Send size={13} />
                      <span>{sendMutation.isPending ? 'Sending...' : 'Send'}</span>
                    </button>
                  </div>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-[#FAFAF8] border border-[#ECECE8] flex items-center justify-center text-[#70706B]">
                <MessageSquare size={20} />
              </div>
              <div className="text-sm font-semibold text-[#111110]">No conversation selected</div>
              <p className="text-xs text-[#70706B] max-w-xs">
                Select a conversation from the left panel to inspect message history and reply.
              </p>
            </div>
          )}
        </div>

        {/* ========================================================= */}
        {/* COLUMN 3: Contact Inspector Panel (3.5 cols) */}
        {/* ========================================================= */}
        <div className="hidden md:flex col-span-12 lg:col-span-12 xl:col-span-3.5 bg-white border border-[#ECECE8] rounded-2xl flex-col h-[780px] shadow-2xs p-5 overflow-y-auto space-y-5">
          {selectedConv ? (
            <>
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full border border-[#ECECE8] bg-[#EAF6EE] text-[#064125] flex items-center justify-center font-bold text-sm">
                    {(selectedConv.contact_username || 'U').charAt(0).toUpperCase()}
                  </div>
                  <span className="font-bold text-sm text-[#111110]">
                    {selectedConv.contact_username?.startsWith('@') ? selectedConv.contact_username : `@${selectedConv.contact_username || 'User'}`}
                  </span>
                </div>
                <button className="text-[#70706B] hover:text-[#111110] p-1">
                  <MoreVertical size={16} />
                </button>
              </div>

              {/* Follower Stats Grid */}
              <div className="grid grid-cols-3 text-center border-y border-[#ECECE8] py-3.5">
                <div>
                  <div className="font-extrabold text-base text-[#111110]">
                    {selectedConv.followers != null ? selectedConv.followers.toLocaleString() : '—'}
                  </div>
                  <div className="text-xs text-[#70706B] font-medium mt-0.5">Followers</div>
                </div>
                <div>
                  <div className="font-extrabold text-base text-[#111110]">
                    {selectedConv.following != null ? selectedConv.following.toLocaleString() : '—'}
                  </div>
                  <div className="text-xs text-[#70706B] font-medium mt-0.5">Following</div>
                </div>
                <div>
                  <div className="font-extrabold text-base text-[#111110]">
                    {selectedConv.posts != null ? selectedConv.posts.toLocaleString() : '—'}
                  </div>
                  <div className="text-xs text-[#70706B] font-medium mt-0.5">Posts</div>
                </div>
              </div>

              {/* Follow Status Pill */}
              <div className="bg-[#EAF6EE] text-[#15803D] rounded-xl py-2 px-3.5 text-xs font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#15803D]" />
                <span>{selectedConv.followed_you ? 'Followed you' : 'Instagram User'}</span>
              </div>

              {/* Metadata Table */}
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#70706B] font-medium">Name</span>
                  <span className="text-[#111110] font-semibold">{selectedConv.name || '—'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#70706B] font-medium">Category</span>
                  <span className="text-[#111110] font-semibold">{selectedConv.category || '—'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#70706B] font-medium">Language</span>
                  <span className="text-[#111110] font-semibold">{selectedConv.language || '—'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#70706B] font-medium">First seen</span>
                  <span className="text-[#111110] font-semibold">{selectedConv.first_seen || '—'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#70706B] font-medium">Last activity</span>
                  <span className="text-[#111110] font-semibold">{selectedConv.last_message_at || '—'}</span>
                </div>
              </div>

              {/* Linked Automation */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-[#111110]">Automation</div>
                <div className="bg-[#FBFBFA] border border-[#ECECE8] rounded-xl p-3 flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#111110]">
                    {selectedConv.automation || 'Direct Conversation'}
                  </span>
                  <ChevronRight size={15} className="text-[#70706B]" />
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-[#111110]">Tags</div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  {Array.isArray(selectedConv.tags) && selectedConv.tags.length > 0 ? (
                    selectedConv.tags.map((tag: string) => (
                      <span
                        key={tag}
                        className="bg-[#F2F2EE] text-[#70706B] px-3 py-1 rounded-full text-xs font-medium"
                      >
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-[#9E9E96]">No tags added</span>
                  )}
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#111110]">Notes</span>
                  <button className="text-[#70706B] hover:text-[#111110]">
                    <Edit3 size={13} />
                  </button>
                </div>
                <p className="text-xs text-[#70706B] leading-relaxed">
                  {selectedConv.notes || 'No notes added for this contact.'}
                </p>
              </div>

              {/* Danger Action - Block User */}
              <div className="pt-4 mt-auto">
                <button
                  onClick={() => alert(`Blocked ${selectedConv.contact_username}`)}
                  className="w-full py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-100 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
                >
                  <Ban size={14} />
                  <span>Block user</span>
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-2">
              <User size={20} className="text-[#9E9E96]" />
              <div className="text-xs text-[#9E9E96]">Select a conversation to view contact details</div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
