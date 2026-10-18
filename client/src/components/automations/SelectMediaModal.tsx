'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  X,
  Search,
  Check,
  Video,
  Copy,
  Image as ImageIcon,
  Heart,
  MessageCircle,
  RefreshCw,
  AlertCircle,
  ChevronDown
} from 'lucide-react';
import { instagramApi, type NormalizedInstagramMedia } from '@/features/instagram/api';

export interface SelectMediaModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedMediaId: string;
  onSelectMedia: (media: NormalizedInstagramMedia) => void;
  accountId?: string;
  accountUsername?: string;
  onReconnect?: () => void;
}

type FilterType = 'ALL' | 'POST' | 'REEL';
type SortType = 'newest' | 'oldest' | 'likes' | 'comments';

export function SelectMediaModal({
  isOpen,
  onClose,
  selectedMediaId,
  onSelectMedia,
  accountId,
  accountUsername,
  onReconnect,
}: SelectMediaModalProps) {
  const [items, setItems] = useState<NormalizedInstagramMedia[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [is409, setIs409] = useState(false);

  // Active UI filters & search
  const [activeFilter, setActiveFilter] = useState<FilterType>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<SortType>('newest');

  // Currently highlighted selection inside modal
  const [tempSelectedId, setTempSelectedId] = useState<string>(selectedMediaId);

  // Keep tempSelectedId synchronized whenever modal opens
  useEffect(() => {
    if (isOpen) {
      setTempSelectedId(selectedMediaId);
    }
  }, [isOpen, selectedMediaId]);

  // Initial fetch when opened or accountId changes
  const fetchInitialMedia = useCallback(async () => {
    if (!accountId) {
      setItems([]);
      setNextCursor(null);
      setError('Please connect an Instagram account first.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setIs409(false);

    try {
      const res = await instagramApi.listMedia(accountId, 25);
      const fetchedData = res?.data || [];
      // Deduplicate by media ID
      const seen = new Set<string>();
      const deduped: NormalizedInstagramMedia[] = [];
      for (const item of fetchedData) {
        if (item.id && !seen.has(item.id)) {
          seen.add(item.id);
          deduped.push(item);
        }
      }
      setItems(deduped);
      setNextCursor(res?.next_cursor || null);
    } catch (err: any) {
      const msg = err?.message || 'Failed to load Instagram media.';
      setError(msg);
      if (msg.includes('409') || msg.toLowerCase().includes('expired') || msg.toLowerCase().includes('reconnect')) {
        setIs409(true);
      }
    } finally {
      setIsLoading(false);
    }
  }, [accountId]);

  useEffect(() => {
    if (isOpen) {
      fetchInitialMedia();
    }
  }, [isOpen, fetchInitialMedia]);

  // Load more with pagination cursor
  const handleLoadMore = async () => {
    if (!accountId || !nextCursor || isLoadingMore) return;
    setIsLoadingMore(true);

    try {
      const res = await instagramApi.listMedia(accountId, 25, nextCursor);
      const newItems = res?.data || [];
      setItems((prev) => {
        const existingIds = new Set(prev.map((p) => p.id));
        const uniqueNew = newItems.filter((p) => !existingIds.has(p.id));
        return [...prev, ...uniqueNew];
      });
      setNextCursor(res?.next_cursor || null);
    } catch (err: any) {
      console.warn('Could not load additional Instagram media:', err);
    } finally {
      setIsLoadingMore(false);
    }
  };

  // Filter and sort returned real media
  const filteredAndSortedItems = useMemo(() => {
    let result = [...items];

    // 1. Filter by media type
    if (activeFilter === 'POST') {
      result = result.filter((item) => item.type === 'POST');
    } else if (activeFilter === 'REEL') {
      result = result.filter((item) => item.type === 'REEL');
    }

    // 2. Search query by caption or ID
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter(
        (item) =>
          item.caption?.toLowerCase().includes(q) ||
          item.id.toLowerCase().includes(q)
      );
    }

    // 3. Sorting
    result.sort((a, b) => {
      if (sortOrder === 'newest') {
        const dateA = a.publishedDate ? new Date(a.publishedDate).getTime() : 0;
        const dateB = b.publishedDate ? new Date(b.publishedDate).getTime() : 0;
        return dateB - dateA;
      }
      if (sortOrder === 'oldest') {
        const dateA = a.publishedDate ? new Date(a.publishedDate).getTime() : 0;
        const dateB = b.publishedDate ? new Date(b.publishedDate).getTime() : 0;
        return dateA - dateB;
      }
      if (sortOrder === 'likes') {
        const likesA = a.likesCount ?? -1;
        const likesB = b.likesCount ?? -1;
        return likesB - likesA;
      }
      if (sortOrder === 'comments') {
        const commA = a.commentsCount ?? -1;
        const commB = b.commentsCount ?? -1;
        return commB - commA;
      }
      return 0;
    });

    return result;
  }, [items, activeFilter, searchQuery, sortOrder]);

  const currentlyChosenItem = useMemo(() => {
    return items.find((p) => p.id === tempSelectedId) || null;
  }, [items, tempSelectedId]);

  const handleConfirmSelection = () => {
    if (currentlyChosenItem) {
      onSelectMedia(currentlyChosenItem);
      onClose();
    }
  };

  // Format date helper (e.g. 2026-10-16 19:29)
  const formatPublishedDate = (isoStr?: string) => {
    if (!isoStr) return null;
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      const yr = d.getFullYear();
      const mo = String(d.getMonth() + 1).padStart(2, '0');
      const da = String(d.getDate()).padStart(2, '0');
      const hr = String(d.getHours()).padStart(2, '0');
      const mi = String(d.getMinutes()).padStart(2, '0');
      return `${yr}-${mo}-${da} ${hr}:${mi}`;
    } catch {
      return isoStr;
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="select-media-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div className="w-full max-w-5xl max-h-[92vh] bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-[#ECECE8]">
        {/* Header */}
        <div className="px-6 py-4.5 border-b border-[#ECECE8] flex items-center justify-between shrink-0 bg-white">
          <div>
            <h2 id="select-media-modal-title" className="text-lg sm:text-xl font-bold text-[#111110] tracking-tight">
              Select a Post or Reel
            </h2>
            <p className="text-xs text-[#70706B] mt-0.5">
              Choose a post or reel to set up the automation.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] rounded-full transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Filters, Search, and Sort Row */}
        <div className="px-6 py-3.5 border-b border-[#F4F4F0] flex flex-wrap items-center justify-between gap-3 bg-white shrink-0">
          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 bg-[#F4F4F0] p-1 rounded-2xl">
            <button
              type="button"
              onClick={() => setActiveFilter('ALL')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                activeFilter === 'ALL'
                  ? 'bg-[#062E1A] text-white shadow-2xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('POST')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                activeFilter === 'POST'
                  ? 'bg-[#062E1A] text-white shadow-2xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
            >
              Posts
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('REEL')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                activeFilter === 'REEL'
                  ? 'bg-[#062E1A] text-white shadow-2xs'
                  : 'text-[#70706B] hover:text-[#111110]'
              }`}
            >
              Reels
            </button>
          </div>

          {/* Search & Sort */}
          <div className="flex items-center gap-2.5 flex-1 sm:flex-initial justify-end">
            {/* Search Box */}
            <div className="relative w-full sm:w-64">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9E9E96]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search posts or reels..."
                className="w-full pl-8.5 pr-8 py-1.5 text-xs bg-white border border-[#ECECE8] rounded-xl placeholder-[#9E9E96] text-[#111110] focus:outline-none focus:border-[#15803D] focus:ring-1 focus:ring-[#15803D] transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#9E9E96] hover:text-[#111110]"
                  title="Clear search"
                >
                  <X size={12} />
                </button>
              )}
            </div>

            {/* Sort Dropdown */}
            <div className="relative">
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as SortType)}
                aria-label="Sort posts"
                className="appearance-none pl-3 pr-7 py-1.5 text-xs bg-white border border-[#ECECE8] rounded-xl text-[#111110] font-medium focus:outline-none focus:border-[#15803D] cursor-pointer"
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="likes">Most likes</option>
                <option value="comments">Most comments</option>
              </select>
              <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#70706B] pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Modal Body: Scrollable Grid */}
        <div className="px-6 py-5 overflow-y-auto flex-1 min-h-[360px] bg-[#FAFAF8]/50">
          {isLoading ? (
            /* Loading Skeleton Grid */
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3.5">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="rounded-2xl border border-[#ECECE8] bg-white p-2.5 space-y-2.5 animate-pulse">
                  <div className="aspect-square w-full bg-[#EFEFEA] rounded-xl" />
                  <div className="space-y-1.5 pt-1">
                    <div className="h-3 bg-[#EFEFEA] rounded w-3/4" />
                    <div className="h-2.5 bg-[#EFEFEA] rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            /* API Error State */
            <div className="max-w-md mx-auto my-12 p-6 rounded-3xl bg-white border border-[#FDE68A] shadow-xs text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-[#FEF3C7] flex items-center justify-center text-[#D97706] mx-auto">
                <AlertCircle size={24} />
              </div>
              <div className="text-sm font-bold text-[#111110]">
                Unable to load Instagram media
              </div>
              <p className="text-xs text-[#70706B]">{error}</p>
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={fetchInitialMedia}
                  className="px-4 py-2 bg-white border border-[#ECECE8] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] rounded-xl transition-all cursor-pointer"
                >
                  Retry
                </button>
                {is409 && onReconnect && (
                  <button
                    type="button"
                    onClick={onReconnect}
                    className="px-4 py-2 bg-[#15803D] hover:bg-[#166534] text-xs font-semibold text-white rounded-xl shadow-2xs transition-all cursor-pointer"
                  >
                    Reconnect Account
                  </button>
                )}
              </div>
            </div>
          ) : filteredAndSortedItems.length === 0 ? (
            /* Empty State */
            <div className="max-w-md mx-auto my-12 p-8 rounded-3xl bg-white border border-dashed border-[#ECECE8] text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-[#F4F4F0] flex items-center justify-center text-[#9E9E96] mx-auto">
                <ImageIcon size={24} />
              </div>
              <div className="text-sm font-bold text-[#111110]">
                {searchQuery ? 'No matching posts or Reels' : 'No posts or Reels available'}
              </div>
              <p className="text-xs text-[#70706B] leading-relaxed">
                {searchQuery
                  ? `No media matches your search "${searchQuery}". Try a different keyword.`
                  : `No media was found published on @${accountUsername || 'this Instagram account'}. Publish a post or Reel on Instagram, then refresh.`}
              </p>
              {searchQuery ? (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="px-4 py-1.5 bg-[#F4F4F0] hover:bg-[#ECECE8] text-xs font-semibold text-[#111110] rounded-xl transition-all cursor-pointer"
                >
                  Clear search
                </button>
              ) : (
                <button
                  type="button"
                  onClick={fetchInitialMedia}
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white border border-[#ECECE8] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] rounded-xl shadow-2xs transition-all cursor-pointer"
                >
                  <RefreshCw size={13} />
                  <span>Refresh Media</span>
                </button>
              )}
            </div>
          ) : (
            /* Media Cards Grid */
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3.5">
              {filteredAndSortedItems.map((post) => {
                const isSelected = post.id === tempSelectedId;
                const formattedDate = formatPublishedDate(post.publishedDate);
                const hasLikes = post.likesCount !== null && post.likesCount !== undefined;
                const hasComments = post.commentsCount !== null && post.commentsCount !== undefined;

                return (
                  <div
                    key={post.id}
                    onClick={() => setTempSelectedId(post.id)}
                    className={`group relative rounded-2xl border transition-all duration-150 overflow-hidden bg-white cursor-pointer text-left flex flex-col ${
                      isSelected
                        ? 'border-2 border-[#15803D] ring-2 ring-[#15803D]/20 shadow-md'
                        : 'border-[#ECECE8] hover:border-gray-400 hover:shadow-2xs'
                    }`}
                  >
                    {/* Thumbnail */}
                    <div className="aspect-square w-full relative bg-[#F4F4F0] overflow-hidden">
                      {post.imageUrl ? (
                        <img
                          src={post.imageUrl}
                          alt={post.caption || 'Instagram Media'}
                          className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-200"
                          onError={(e) => {
                            // Neutral fallback if image load fails
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-[#9E9E96]">
                          <ImageIcon size={28} />
                        </div>
                      )}

                      {/* Top-Left Media Type Badge */}
                      <div className="absolute top-2 left-2 p-1 rounded-md bg-black/60 text-white shadow-xs">
                        {post.type === 'REEL' ? (
                          <Video size={12} />
                        ) : post.rawMediaType === 'CAROUSEL_ALBUM' ? (
                          <Copy size={12} />
                        ) : (
                          <ImageIcon size={12} />
                        )}
                      </div>

                      {/* Top-Right Checkmark Badge when Selected */}
                      {isSelected && (
                        <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#15803D] text-white flex items-center justify-center shadow-xs">
                          <Check size={12} strokeWidth={3} />
                        </div>
                      )}
                    </div>

                    {/* Metadata details under thumbnail */}
                    <div className="p-2.5 space-y-1 flex-1 flex flex-col justify-between">
                      <div>
                        {/* Caption or (No caption) */}
                        {post.caption && post.caption.trim() ? (
                          <p
                            className="text-xs font-semibold text-[#111110] line-clamp-1 truncate"
                            title={post.caption}
                          >
                            {post.caption}
                          </p>
                        ) : (
                          <p className="text-xs text-[#70706B] italic font-medium">
                            (No caption)
                          </p>
                        )}

                        {/* Timestamp */}
                        {formattedDate && (
                          <p className="text-[11px] text-[#70706B] mt-0.5">
                            {formattedDate}
                          </p>
                        )}
                      </div>

                      {/* Genuine Engagement Metrics: hidden if null/unavailable */}
                      {(hasLikes || hasComments) && (
                        <div className="flex items-center gap-3 text-[11px] text-[#70706B] pt-0.5 border-t border-[#F4F4F0]/80">
                          {hasLikes && (
                            <span className="inline-flex items-center gap-1 font-medium">
                              <Heart size={11} className="text-[#9E9E96]" />
                              <span>{post.likesCount} {post.likesCount === 1 ? 'like' : 'likes'}</span>
                            </span>
                          )}
                          {hasComments && (
                            <span className="inline-flex items-center gap-1 font-medium">
                              <MessageCircle size={11} className="text-[#9E9E96]" />
                              <span>{post.commentsCount} {post.commentsCount === 1 ? 'comment' : 'comments'}</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-[#ECECE8] flex flex-wrap items-center justify-between gap-3 bg-white shrink-0">
          {/* Item count & pagination action */}
          <div className="flex items-center gap-3">
            <div>
              <div className="text-xs font-bold text-[#111110]">
                {items.length} {items.length === 1 ? 'post or reel' : 'posts and reels'}
              </div>
              <div className="text-[11px] text-[#70706B]">
                Showing all available posts and reels from your Instagram account.
              </div>
            </div>

            {nextCursor && (
              <button
                type="button"
                onClick={handleLoadMore}
                disabled={isLoadingMore}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#ECECE8] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] rounded-xl shadow-2xs transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoadingMore ? (
                  <>
                    <RefreshCw size={12} className="animate-spin text-[#15803D]" />
                    <span>Loading more...</span>
                  </>
                ) : (
                  <span>Load more posts</span>
                )}
              </button>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmSelection}
              disabled={!tempSelectedId}
              className="px-5 py-2 text-xs font-bold text-white bg-[#062E1A] hover:bg-[#0A482A] rounded-xl shadow-2xs transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Select Post
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
