import React from 'react';

export type BrandLogoVariant = 'horizontal' | 'horizontal-tagline' | 'mark' | 'dark-mark' | 'wordmark' | 'full';

interface BrandLogoProps {
  variant?: BrandLogoVariant;
  height?: number;
  className?: string;
  style?: React.CSSProperties;
  alt?: string;
}

/**
 * Authentic Comlina Brand Logo Component
 * Uses the exact canonical brand assets derived from the official logo artwork.
 */
export function BrandLogo({
  variant = 'horizontal',
  height = 32,
  className = '',
  style = {},
  alt = 'Comlina — Turn Conversations into Growth'
}: BrandLogoProps) {
  const assetMap: Record<BrandLogoVariant, string> = {
    'horizontal': '/comlina-horizontal.png',
    'horizontal-tagline': '/comlina-horizontal-tagline.png',
    'mark': '/comlina-mark.png',
    'dark-mark': '/comlina-mark-dark.png',
    'wordmark': '/comlina-wordmark.png',
    'full': '/comlina-full.png'
  };

  const src = assetMap[variant] || assetMap.horizontal;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      height={height}
      className={`comlina-brand-logo ${className}`.trim()}
      style={{
        height: `${height}px`,
        width: 'auto',
        display: 'inline-block',
        verticalAlign: 'middle',
        objectFit: 'contain',
        ...style
      }}
    />
  );
}

export default BrandLogo;
