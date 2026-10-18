// client/src/components/automations/TriggerSection.tsx
'use client';

import React from 'react';
import { PostSelector, InstagramMediaItem } from './PostSelector';
import { Film, Sparkles, Clock } from 'lucide-react';

interface TriggerSectionProps {
  scope: 'specific' | 'any' | 'next';
  onScopeChange: (scope: 'specific' | 'any' | 'next') => void;
  selectedPostId?: string;
  onSelectPost: (post: InstagramMediaItem) => void;
  posts?: InstagramMediaItem[];
  postsLoading?: boolean;
  postsError?: string | null;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoadingMore?: boolean;
}

export function TriggerSection({
  scope,
  onScopeChange,
  selectedPostId = '',
  onSelectPost,
  posts = [],
  postsLoading = false,
  postsError = null,
  onLoadMore,
  hasMore = false,
  isLoadingMore = false,
}: TriggerSectionProps) {
  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
      <div>
        <h2 className="text-xl font-black text-[#111110]">
          When someone comments on
        </h2>
      </div>

      {/* 3 Scope Options */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Option 1: Specific post or Reel */}
        <div
          onClick={() => onScopeChange('specific')}
          className={`p-4 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-3 ${
            scope === 'specific'
              ? 'border-[#15803D] bg-[#F0FDF4]/40 ring-1 ring-[#15803D]/20 shadow-xs'
              : 'border-[#ECECE8] bg-white hover:bg-[#FBFBFA]'
          }`}
        >
          <input
            type="radio"
            name="trigger_scope"
            checked={scope === 'specific'}
            onChange={() => onScopeChange('specific')}
            className="mt-0.5 text-[#15803D] focus:ring-0 cursor-pointer"
          />
          <div>
            <div className="font-bold text-xs text-[#111110]">
              A specific post or Reel
            </div>
            <div className="text-[11px] text-[#70706B] mt-0.5">
              Select directly from your feed
            </div>
          </div>
        </div>

        {/* Option 2: Any post or Reel (PRO) */}
        <div
          onClick={() => onScopeChange('any')}
          className={`p-4 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-3 relative ${
            scope === 'any'
              ? 'border-[#15803D] bg-[#F0FDF4]/40 ring-1 ring-[#15803D]/20 shadow-xs'
              : 'border-[#ECECE8] bg-white hover:bg-[#FBFBFA]'
          }`}
        >
          <input
            type="radio"
            name="trigger_scope"
            checked={scope === 'any'}
            onChange={() => onScopeChange('any')}
            className="mt-0.5 text-[#15803D] focus:ring-0 cursor-pointer"
          />
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-xs text-[#111110]">Any post or Reel</span>
              <span className="px-1.5 py-0.2 bg-[#F59E0B] text-white text-[9px] font-bold rounded">
                PRO
              </span>
            </div>
            <div className="text-[11px] text-[#70706B] mt-0.5">
              Applies to all past and future posts
            </div>
          </div>
        </div>

        {/* Option 3: Next post or Reel */}
        <div
          onClick={() => onScopeChange('next')}
          className={`p-4 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-3 ${
            scope === 'next'
              ? 'border-[#15803D] bg-[#F0FDF4]/40 ring-1 ring-[#15803D]/20 shadow-xs'
              : 'border-[#ECECE8] bg-white hover:bg-[#FBFBFA]'
          }`}
        >
          <input
            type="radio"
            name="trigger_scope"
            checked={scope === 'next'}
            onChange={() => onScopeChange('next')}
            className="mt-0.5 text-[#15803D] focus:ring-0 cursor-pointer"
          />
          <div>
            <div className="font-bold text-xs text-[#111110]">
              Next post or Reel
            </div>
            <div className="text-[11px] text-[#70706B] mt-0.5">
              Upcoming campaign or scheduled post
            </div>
          </div>
        </div>
      </div>

      {/* If Specific post or Reel is selected, show PostSelector */}
      {scope === 'specific' && (
        <div className="pt-2 animate-in fade-in duration-200 space-y-3">
          {!selectedPostId && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 font-medium">
              Select a post to continue
            </div>
          )}
          <PostSelector
            selectedPostId={selectedPostId}
            onSelectPost={onSelectPost}
            posts={posts}
            isLoading={postsLoading}
            error={postsError}
            onLoadMore={onLoadMore}
            hasMore={hasMore}
            isLoadingMore={isLoadingMore}
          />
        </div>
      )}

      {scope === 'next' && (
        <div className="p-4 bg-[#FBFBFA] border border-dashed border-[#ECECE8] rounded-xl text-center text-xs text-[#70706B] flex items-center justify-center gap-2">
          <Clock size={15} className="text-[#15803D]" />
          <span>Automation will stand by and bind to the very next piece of content you post to Instagram.</span>
        </div>
      )}

      {scope === 'any' && (
        <div className="p-4 bg-[#F0FDF4] border border-[#DCFCE7] rounded-xl text-xs text-[#166534] flex items-center gap-2">
          <Sparkles size={16} className="text-[#15803D] shrink-0" />
          <span>Global trigger active: Any comment across your entire account will trigger this workflow.</span>
        </div>
      )}
    </section>
  );
}
