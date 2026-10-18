'use client';

import React, { useEffect } from 'react';
import { BrandLogo } from './BrandLogo';

export interface ComlinaLoadingOverlayProps {
  isLoading?: boolean;
  className?: string;
  logoSize?: number;
  preventScroll?: boolean;
  children?: React.ReactNode;
}

/**
 * ComlinaLoadingOverlay
 * 
 * Minimal, high-aesthetic loading overlay matching the canonical Comlina mobile spec.
 * Features:
 * - Softly blurred background overlay (blur 14px)
 * - The official Comlina conversation mark (purple, pink, orange gradient)
 * - Three sequential pulsing dots below the logo (purple -> pink -> orange -> rest)
 * - Zero wordmarks, taglines, or extraneous text
 * - Clean scroll-locking and safe-area inset preservation
 */
export function ComlinaLoadingOverlay({
  isLoading = true,
  className = '',
  logoSize = 84,
  preventScroll = true,
  children,
}: ComlinaLoadingOverlayProps) {
  useEffect(() => {
    if (!isLoading || !preventScroll || typeof document === 'undefined') return;

    const originalOverflow = document.body.style.overflow;
    const originalTouchAction = document.body.style.touchAction;
    document.body.style.overflow = 'hidden';
    document.body.style.touchAction = 'none';

    return () => {
      document.body.style.overflow = originalOverflow;
      document.body.style.touchAction = originalTouchAction;
    };
  }, [isLoading, preventScroll]);

  const overlayElement = isLoading ? (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading Comlina"
      className={`comlina-loading-backdrop ${className}`.trim()}
    >
      <span className="sr-only">Loading Comlina...</span>
      <div className="flex flex-col items-center justify-center">
        <BrandLogo
          variant="mark"
          height={logoSize}
          alt="Comlina"
          className="select-none pointer-events-none drop-shadow-2xs"
        />
        <div className="comlina-loading-dots" aria-hidden="true">
          <span className="comlina-loading-dot" />
          <span className="comlina-loading-dot" />
          <span className="comlina-loading-dot" />
        </div>
      </div>
    </div>
  ) : null;

  if (children) {
    return (
      <>
        {children}
        {overlayElement}
      </>
    );
  }

  return overlayElement;
}

export default ComlinaLoadingOverlay;
