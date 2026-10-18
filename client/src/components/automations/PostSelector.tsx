'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Film, Image as ImageIcon, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { instagramApi, type InstagramMediaApiItem } from '@/features/instagram/api';

export interface InstagramMediaItem {
  id: string;
  type: 'POST' | 'REEL';
  caption: string;
  imageUrl: string;
  commentsCount?: number | null;
  likesCount?: number | null;
  publishedDate?: string;
  permalink?: string;
  rawMediaType?: string;
  mediaProductType?: string;
}

export function mapApiMedia(m: InstagramMediaApiItem): InstagramMediaItem {
  const published = m.timestamp ? new Date(m.timestamp) : null;
  return {
    id: m.id,
    type: m.media_type === 'VIDEO' ? 'REEL' : 'POST',
    caption: m.caption || '',
    imageUrl: m.thumbnail_url || m.media_url || '',
    commentsCount: m.comments_count ?? null,
    likesCount: m.like_count ?? null,
    publishedDate: published && !isNaN(published.getTime()) ? published.toLocaleDateString() : '',
  };
}

interface PostSelectorProps {
  selectedPostId: string;
  onSelectPost: (post: InstagramMediaItem) => void;
  posts?: InstagramMediaItem[];
  isLoading?: boolean;
  error?: string | null;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoadingMore?: boolean;
}

export function PostSelector({
  selectedPostId,
  onSelectPost,
  posts: externalPosts = [],
  isLoading: externalLoading = false,
  error = null,
  onLoadMore,
  hasMore = false,
  isLoadingMore = false,
}: PostSelectorProps) {
  const [internalPosts, setInternalPosts] = useState<InstagramMediaItem[]>([]);
  const [internalLoading, setInternalLoading] = useState(false);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (externalPosts && externalPosts.length > 0) return;
    let mounted = true;
    setInternalLoading(true);
    instagramApi.getMedia()
      .then((data) => {
        if (!mounted) return;
        if (data && data.length > 0) {
          setInternalPosts(data as InstagramMediaItem[]);
        } else {
          setInternalPosts([]);
        }
      })
      .catch(() => {
        if (mounted) setInternalPosts([]);
      })
      .finally(() => {
        if (mounted) setInternalLoading(false);
      });
    return () => { mounted = false; };
  }, [externalPosts]);

  const posts = (externalPosts && externalPosts.length > 0)
    ? externalPosts
    : internalPosts;
  const isLoading = externalLoading || (internalLoading && (!externalPosts || externalPosts.length === 0));

  // Skeletons in the exact same grid
  if (isLoading) {
    return (
      <div className="w-full space-y-3">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="rounded-xl border border-[#ECECE8] overflow-hidden bg-white animate-pulse">
              <div className="aspect-square w-full bg-[#EFEFEA]" />
              <div className="p-2.5 space-y-2">
                <div className="h-3 bg-[#EFEFEA] rounded w-full" />
                <div className="h-2.5 bg-[#EFEFEA] rounded w-2/3" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error handling with 409 check
  if (error) {
    const is409 = error.includes('409') || error.toLowerCase().includes('reconnect') || error.toLowerCase().includes('conflict');
    return (
      <div className="text-xs text-red-600 py-6 text-center bg-red-50/60 border border-red-200 rounded-2xl space-y-2 p-4">
        <p>Could not load your posts: {error}</p>
        {is409 && (
          <div>
            <Link
              href="/dashboard/instagram-accounts"
              className="inline-flex items-center gap-1 text-xs font-semibold text-[#15803D] hover:underline"
            >
              Reconnect account →
            </Link>
          </div>
        )}
      </div>
    );
  }

  // Empty state with link to instagram accounts
  if (posts.length === 0) {
    return (
      <div className="text-xs text-[#70706B] py-8 text-center bg-[#FAFAF8] border border-dashed border-[#ECECE8] rounded-2xl space-y-2">
        <p>No posts found on the connected account yet.</p>
        <Link
          href="/dashboard/instagram-accounts"
          className="inline-flex items-center gap-1 text-xs font-semibold text-[#15803D] hover:underline"
        >
          Manage connected accounts →
        </Link>
      </div>
    );
  }

  const displayedPosts = showAll ? posts : posts.slice(0, 4);

  return (
    <div className="w-full space-y-3">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {displayedPosts.map((post) => {
          const isSelected = post.id === selectedPostId;
          return (
            <button
              type="button"
              key={post.id}
              aria-pressed={isSelected}
              onClick={() => onSelectPost(post)}
              className={`group relative rounded-xl border-2 overflow-hidden cursor-pointer transition-all duration-200 bg-white text-left w-full ${
                isSelected
                  ? 'border-[#15803D] ring-2 ring-[#15803D]/20 shadow-md transform -translate-y-0.5'
                  : 'border-[#ECECE8] hover:border-[#D3D3CE] hover:shadow-sm'
              }`}
            >
              {/* Thumbnail Container */}
              <div className="relative aspect-square w-full bg-[#1A1A19] overflow-hidden">
                <img
                  src={post.imageUrl}
                  alt={post.caption}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />

                {/* Media Type Badge */}
                <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded-md bg-black/60 backdrop-blur-md text-[10px] font-semibold text-white flex items-center gap-1 shadow-sm">
                  {post.type === 'REEL' ? <Film size={11} /> : <ImageIcon size={11} />}
                  <span>{post.type === 'REEL' ? 'Reel' : 'Post'}</span>
                </div>

                {/* Selection Checkmark */}
                {isSelected && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#15803D] text-white flex items-center justify-center shadow-md animate-in zoom-in-75 duration-150">
                    <Check size={12} strokeWidth={3} />
                  </div>
                )}

                {/* Gradient overlay for stats if genuinely available */}
                {(post.commentsCount !== null && post.commentsCount !== undefined || post.likesCount !== null && post.likesCount !== undefined) && (
                  <div className="absolute inset-x-0 bottom-0 p-2 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex items-center justify-between text-xs text-white font-medium">
                    {post.commentsCount !== null && post.commentsCount !== undefined && <span>💬 {post.commentsCount}</span>}
                    {post.likesCount !== null && post.likesCount !== undefined && (
                      <span>❤️ {post.likesCount > 999 ? `${(post.likesCount / 1000).toFixed(1)}k` : post.likesCount}</span>
                    )}
                  </div>
                )}
              </div>

              {/* Caption snippet */}
              <div className="p-2.5">
                <p className="text-xs text-[#111110] font-medium line-clamp-2 leading-tight">
                  {post.caption && post.caption.trim() ? post.caption : <span className="italic text-[#70706B] font-normal">(No caption)</span>}
                </p>
                <div className="text-xs text-[#70706B] mt-1.5 flex items-center justify-between">
                  <span>{post.publishedDate}</span>
                  {isSelected && (
                    <span className="text-[#15803D] font-bold text-xs">Selected</span>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Load More Button (when cursor pagination is available) */}
      {hasMore && onLoadMore && (
        <div className="flex justify-center pt-1">
          <button
            type="button"
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-[#062E1A] bg-[#EAF6EE] hover:bg-[#DCFCE7] rounded-xl transition-colors cursor-pointer disabled:opacity-50"
          >
            {isLoadingMore ? <span>Loading more posts...</span> : <span>Load more</span>}
          </button>
        </div>
      )}

      {/* Show all toggle if local list exceeds 4 and hasMore is not active */}
      {!hasMore && posts.length > 4 && (
        <div className="flex justify-center pt-1">
          <button
            type="button"
            onClick={() => setShowAll(!showAll)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[#15803D] hover:text-[#062E1A] hover:bg-[#F0FDF4] rounded-lg transition-colors cursor-pointer"
          >
            <span>{showAll ? 'Show Fewer Posts' : `Show All (${posts.length} Posts)`}</span>
            {showAll ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      )}
    </div>
  );
}
