// client/src/components/automations/CommentReplyFlow.tsx
'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { 
  ArrowLeft, 
  Sparkles, 
  MessageSquare, 
  Repeat, 
  Globe, 
  Bot, 
  X, 
  Check, 
  Save, 
  ExternalLink,
  Plus,
  Image as ImageIcon
} from 'lucide-react';
import { InstagramMediaItem } from './PostSelector';
import { instagramApi } from '@/features/instagram/api';
import { FlowActionButtons } from './FlowActionButtons';

interface CommentReplyFlowProps {
  onBack: () => void;
  onSave: (flowData: any) => Promise<void>;
  accountName?: string;
  isSaving?: boolean;
  onPreviewChange?: (previewData: any) => void;
}

export function CommentReplyFlow({
  onBack,
  onSave,
  accountName = 'yourbrand',
  isSaving = false,
  onPreviewChange,
}: CommentReplyFlowProps) {
  // 1. Post Selection State
  const [selectedPostId, setSelectedPostId] = useState<string>('all');
  const [showAllPosts, setShowAllPosts] = useState(false);
  const [posts, setPosts] = useState<InstagramMediaItem[]>([]);

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
  const [keywords, setKeywords] = useState<string[]>(['FREE', 'LINK', 'INFO', 'YES']);

  // 4. AI-Powered Reply State
  const [aiReplyEnabled, setAiReplyEnabled] = useState(false);
  const [aiInstructions, setAiInstructions] = useState('Reply enthusiastically and encourage checking bio link.');

  // 5. Public Comment Reply State
  const [replyText, setReplyText] = useState('Thanks for your comment! 🙏 Check out the link in my bio for more info!');

  // Synchronize Live Preview Setup
  React.useEffect(() => {
    onPreviewChange?.({
      keywords: replyToAll ? ['ANY COMMENT'] : keywords,
      publicReplyEnabled: true,
      publicReplyText: replyText,
      openingDmEnabled: false,
      deliveryText: '',
      defaultTab: 'comments',
      isStoryFlow: false,
    });
  }, [keywords, replyToAll, replyText, onPreviewChange]);

  // Word and Char Counters
  const wordCount = useMemo(() => {
    return replyText.trim() ? replyText.trim().split(/\s+/).length : 0;
  }, [replyText]);

  const charCount = replyText.length;

  // Handlers
  const handleAddKeyword = (kw?: string) => {
    const target = (kw || keywordInput).trim().toUpperCase();
    if (target && !keywords.includes(target)) {
      setKeywords([...keywords, target]);
      if (!kw) setKeywordInput('');
    }
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

  const handleSaveClick = async (status: 'DRAFT' | 'ACTIVE' = 'ACTIVE') => {
    const payload = {
      type: 'COMMENT_REPLY',
      status,
      selectedPostId,
      replyToAll,
      keywords: replyToAll ? [] : keywords,
      aiReply: {
        enabled: aiReplyEnabled,
        instructions: aiInstructions,
      },
      publicReply: {
        text: replyText,
      },
    };

    await onSave(payload);
  };

  const isFormValid = (replyToAll || keywords.length > 0) && !!replyText.trim();

  return (
    <div className="max-w-4xl mx-auto pb-24 text-[#111110] space-y-6">
      
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
            <h1 className="text-xl sm:text-2xl font-black text-[#111110] tracking-tight">
              Comment Reply Flow
            </h1>
          </div>
        </div>

        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
        />
      </div>

      {/* 1. SELECT POST CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[#111110]"><ImageIcon size={16} /></span>
            <h2 className="text-sm font-bold text-[#111110]">Select Post</h2>
          </div>
          <button
            type="button"
            onClick={() => setShowAllPosts(!showAllPosts)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] text-[#70706B] transition-colors cursor-pointer shadow-2xs"
          >
            <ExternalLink size={12} />
            <span>{showAllPosts ? 'Collapse view' : 'Browse all'}</span>
          </button>
        </div>

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
              <span className="text-[10px] text-[#0066FF] font-semibold mt-1">✓</span>
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

      {/* 2. REPLY TO ALL CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#F0FDF4] text-[#15803D] flex items-center justify-center shrink-0">
            <Globe size={18} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[#111110]">Reply to All</h2>
            <p className="text-xs text-[#70706B]">Respond to all comments without keyword matching</p>
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

      {/* 3. TRIGGER KEYWORDS CARD (Hidden if Reply to All is checked) */}
      {!replyToAll && (
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <span className="text-[#111110]"><MessageSquare size={16} /></span>
            <h2 className="text-sm font-bold text-[#111110]">Trigger Keywords</h2>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={handleKeywordKeyDown}
                placeholder="Type keyword and press Enter"
                className="flex-1 px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
              />
              <button
                type="button"
                onClick={() => handleAddKeyword()}
                className="px-4 py-2.5 bg-[#F4F4F0] hover:bg-[#ECECE8] text-[#111110] text-xs font-bold rounded-xl transition-colors cursor-pointer"
              >
                Add
              </button>
            </div>
          </div>

          {/* Chips */}
          <div className="flex flex-wrap gap-2 pt-1">
            {keywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#F4F4F0] text-[#111110] text-xs font-bold rounded-lg border border-[#ECECE8]"
              >
                <span>+ {kw}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(kw)}
                  className="text-[#70706B] hover:text-red-600 cursor-pointer ml-1"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 4. AI-POWERED REPLY CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[#0066FF]"><Bot size={18} /></span>
            <h2 className="text-sm font-bold text-[#111110]">AI-Powered Reply</h2>
          </div>
          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={aiReplyEnabled}
              onChange={(e) => setAiReplyEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
          </label>
        </div>

        <div>
          <p className="text-xs text-[#70706B]">Generate contextual replies using AI</p>
        </div>

        {aiReplyEnabled && (
          <div className="space-y-2 pt-3 border-t border-[#ECECE8] animate-in fade-in duration-150">
            <label className="block text-xs font-semibold text-[#111110]">
              AI Tone & Reply Instructions
            </label>
            <textarea
              rows={2}
              value={aiInstructions}
              onChange={(e) => setAiInstructions(e.target.value)}
              placeholder="e.g. Reply enthusiastically and mention checking the link in bio."
              className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
            />
          </div>
        )}
      </div>

      {/* 5. PUBLIC COMMENT REPLY CARD (GREEN ACCENT) */}
      <div className="bg-[#F0FDF4]/30 border-2 border-[#BBF7D0] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[#15803D]"><Repeat size={16} /></span>
            <h2 className="text-sm font-bold text-[#111110]">Public Comment Reply</h2>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#DCFCE7] text-[#15803D] border border-[#BBF7D0]">
            Public
          </span>
        </div>

        <div>
          <textarea
            rows={4}
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="e.g., Thanks for your comment! 🙏 Check out the link in my bio for more info!"
            className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#15803D]"
          />
          <div className="flex items-center justify-between text-[11px] text-[#70706B] mt-2">
            <span>Posted as a public reply to comments containing your trigger keyword. Meta limits public comment replies — max 50 words / 300 characters.</span>
            <span className="font-medium shrink-0 ml-2">
              {wordCount}/50 words • {charCount}/300 chars
            </span>
          </div>
        </div>
      </div>

      {/* 6. BOTTOM ACTION BUTTONS */}
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
