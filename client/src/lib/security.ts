// client/src/lib/security.ts
/**
 * Security utilities for untrusted text and URL sanitization.
 * Protects against XSS, open redirects, JavaScript protocol execution, and tabnabbing.
 */

const ALLOWED_PROTOCOLS = new Set(['https:', 'http:', 'mailto:', 'tel:']);

/**
 * Validates and sanitizes a URL to ensure it cannot execute malicious code (e.g. javascript:).
 * Returns the safe URL, or a fallback (default '#') if unsafe.
 */
export function safeUrl(url: string | null | undefined, fallback: string = '#'): string {
  if (!url || typeof url !== 'string') {
    return fallback;
  }

  const trimmed = url.trim();
  if (!trimmed) {
    return fallback;
  }

  // Relative URLs starting with '/' but not '//' (which is protocol-relative)
  if (trimmed.startsWith('/') && !trimmed.startsWith('//') && !trimmed.startsWith('/\\')) {
    return trimmed;
  }

  // Anchor links
  if (trimmed.startsWith('#')) {
    return trimmed;
  }

  try {
    const parsed = new URL(trimmed);
    const protocol = parsed.protocol.toLowerCase();

    if (ALLOWED_PROTOCOLS.has(protocol)) {
      // Extra safeguard against javascript: or data: pseudo-schemes in hostname
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        if (!parsed.hostname || parsed.hostname.includes('javascript:') || parsed.hostname.includes('data:')) {
          return fallback;
        }
      }
      return trimmed;
    }
  } catch {
    // Malformed URL or non-standard protocol
    return fallback;
  }

  return fallback;
}

/**
 * Checks if a given URL is safe to use in href or src attributes.
 */
export function isSafeUrl(url: string | null | undefined): boolean {
  return safeUrl(url, '') !== '';
}

/**
 * Generates secure link attributes for external targets, preventing reverse tabnabbing.
 */
export function safeExternalLinkProps(url: string | null | undefined) {
  const sanitized = safeUrl(url, '#');
  const isExternal = sanitized.startsWith('http:') || sanitized.startsWith('https:');

  return {
    href: sanitized,
    ...(isExternal ? { target: '_blank', rel: 'noopener noreferrer' } : {}),
  };
}

/**
 * Strips dangerous control characters and trims untrusted text.
 */
export function sanitizeText(text: string | null | undefined, maxLength: number = 2000): string {
  if (!text || typeof text !== 'string') {
    return '';
  }
  // Remove null bytes and invisible control characters except standard whitespace
  const sanitized = text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
  return sanitized.trim().slice(0, maxLength);
}
