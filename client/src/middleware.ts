// client/src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// ============================================================================
// 1. IN-MEMORY SLIDING-WINDOW RATE LIMITER
// ============================================================================
interface RateLimitRecord {
  count: number;
  windowStart: number;
}

const rateLimitMap = new Map<string, RateLimitRecord>();

// Clean up stale IP records every 60 seconds to avoid memory leaks
setInterval(() => {
  const now = Date.now();
  rateLimitMap.forEach((record, key) => {
    if (now - record.windowStart > 120000) {
      rateLimitMap.delete(key);
    }
  });
}, 60000);

function checkRateLimit(
  ip: string,
  limit: number,
  windowMs: number
): { allowed: boolean; remaining: number; resetSec: number } {
  const now = Date.now();
  const record = rateLimitMap.get(ip);

  if (!record || now - record.windowStart > windowMs) {
    rateLimitMap.set(ip, { count: 1, windowStart: now });
    return { allowed: true, remaining: limit - 1, resetSec: Math.ceil(windowMs / 1000) };
  }

  record.count += 1;
  const elapsed = now - record.windowStart;
  const resetSec = Math.max(1, Math.ceil((windowMs - elapsed) / 1000));

  if (record.count > limit) {
    return { allowed: false, remaining: 0, resetSec };
  }

  return { allowed: true, remaining: limit - record.count, resetSec };
}

// ============================================================================
// 2. THREAT SIGNATURES & RECONNAISSANCE PROBE TRAPS
// ============================================================================
// Proactively block automated exploit scanners looking for vulnerable files
const BLOCKED_PATH_PATTERNS = [
  /^\/\.env(\..*)?$/i,
  /^\/\.git(\/.*)?$/i,
  /^\/\.aws(\/.*)?$/i,
  /^\/\.vscode(\/.*)?$/i,
  /^\/\.DS_Store$/i,
  /\bwp-(login|admin|content|includes)\b/i,
  /\b(xmlrpc|phpmyadmin|pma|eval-stdin|cgis?|autodiscover)\b/i,
  /\.(php|asp|aspx|jsp|cgi|pl|sh|bash|sql|bak|yaml|yml|orig|conf)$/i,
];

// Block automated vulnerability attack tools by User-Agent
const BLOCKED_USER_AGENTS = [
  /sqlmap/i,
  /nikto/i,
  /dirbuster/i,
  /gobuster/i,
  /wpscan/i,
  /masscan/i,
  /zgrab/i,
  /nmap/i,
  /burpsuite/i,
  /acunetix/i,
  /havij/i,
];

// Detect path traversal and dangerous injection keywords in query string
const INJECTION_PATTERNS = [
  /(\.\.[\/\\]|%2e%2e[\/\\])/i, // Path traversal ../ or ..\
  /<script\b[^>]*>/i, // Cross-site scripting tags
  /\b(javascript:|vbscript:|data:text\/html)/i, // Malicious protocol schemes
  /(union(\s+|%20|\+)(all(\s+|%20|\+))?select|select(\s+|%20|\+).+(\s+|%20|\+)from|insert(\s+|%20|\+)into|waitfor(\s+|%20|\+)delay|benchmark\s*\(|drop(\s+|%20|\+)table)/i, // SQL injection
  /\b(eval|alert|prompt|confirm)\s*\(/i, // Obvious JS execution payloads in query
  /%00/i, // Null-byte poisoning
];

// ============================================================================
// 3. SECURITY HEADERS POLICY (OWASP Top 10 Recommended)
// ============================================================================
const CSP_POLICY = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.supabase.co https://*.facebook.com https://*.instagram.com https://accounts.google.com https://pagead2.googlesyndication.com https://*.googlesyndication.com https://adservice.google.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "img-src 'self' data: blob: https://images.unsplash.com https://*.facebook.com https://*.instagram.com https://*.cdninstagram.com https://*.fbcdn.net https://api.dicebear.com https://*.googleusercontent.com https://pagead2.googlesyndication.com",
  "font-src 'self' https://fonts.gstatic.com data:",
  "connect-src 'self' https://api.comlina.ai wss://api.comlina.ai https://*.onrender.com wss://*.onrender.com http://localhost:8000 http://127.0.0.1:8000 https://*.supabase.co wss://*.supabase.co https://*.instagram.com https://graph.facebook.com https://accounts.google.com https://*.googleapis.com https://pagead2.googlesyndication.com https://*.googlesyndication.com",
  "frame-src 'self' https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self' https://accounts.google.com https://*.facebook.com https://*.instagram.com https://api.instagram.com",
].join('; ');

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const userAgent = request.headers.get('user-agent') || '';
  const clientIp = 
    request.headers.get('x-real-ip')?.trim() ||
    request.headers.get('cf-connecting-ip')?.trim() ||
    request.headers.get('x-forwarded-for')?.split(',').pop()?.trim() ||
    '127.0.0.1';

  // Generate unique request ID for correlation and security auditing
  const requestId = crypto.randomUUID();

  // --------------------------------------------------------------------------
  // CHECK 1: Malicious Scanner & Exploit Trapping (Immediate 403)
  // --------------------------------------------------------------------------
  for (const pattern of BLOCKED_PATH_PATTERNS) {
    if (pattern.test(pathname)) {
      console.warn(`[SECURITY BLOCKED: EXPLOIT_PROBE] IP=${clientIp} Path=${pathname} RequestId=${requestId}`);
      return new NextResponse(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Access denied: Security violation detected.',
          requestId,
        }),
        {
          status: 403,
          headers: {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'x-request-id': requestId,
          },
        }
      );
    }
  }

  // --------------------------------------------------------------------------
  // CHECK 2: Malicious Attack Tooling User-Agent (Immediate 403)
  // --------------------------------------------------------------------------
  for (const agentPattern of BLOCKED_USER_AGENTS) {
    if (agentPattern.test(userAgent)) {
      console.warn(`[SECURITY BLOCKED: ATTACK_TOOL] IP=${clientIp} UA=${userAgent} RequestId=${requestId}`);
      return new NextResponse(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Access denied: Automated attack tool blocked.',
          requestId,
        }),
        {
          status: 403,
          headers: {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'x-request-id': requestId,
          },
        }
      );
    }
  }

  // --------------------------------------------------------------------------
  // CHECK 3: Injection Attack Pattern Detection (Immediate 400)
  // --------------------------------------------------------------------------
  if (search) {
    let decodedQuery = search;
    try {
      decodedQuery = decodeURIComponent(search.replace(/\+/g, ' '));
    } catch {
      // Keep raw search if malformed
    }
    const queryCandidates = [search, decodedQuery, search.replace(/%20/g, ' ')];

    for (const injectionPattern of INJECTION_PATTERNS) {
      const isMatched = queryCandidates.some((candidate) => injectionPattern.test(candidate));
      if (isMatched) {
        console.warn(`[SECURITY BLOCKED: INJECTION_ATTEMPT] IP=${clientIp} Query=${search} RequestId=${requestId}`);
        return new NextResponse(
          JSON.stringify({
            error: 'Bad Request',
            message: 'Malicious payload signature detected in request query.',
            requestId,
          }),
          {
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              'X-Content-Type-Options': 'nosniff',
              'x-request-id': requestId,
            },
          }
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // CHECK 4: Edge Rate Limiting
  // --------------------------------------------------------------------------
  // Tiered thresholds:
  // - Sensitive auth endpoints: max 12 requests per 60 seconds (brute-force defense)
  // - General traffic: max 120 requests per 10 seconds (DoS defense)
  const isAuthRoute = pathname.startsWith('/login') || pathname.startsWith('/signup') || pathname.startsWith('/auth');
  const isDev = process.env.NODE_ENV !== 'production';
  const rateLimitConfig = isDev
    ? { limit: 500, windowMs: 60000 }
    : (isAuthRoute
        ? { limit: 20, windowMs: 60000 }
        : { limit: 120, windowMs: 10000 });

  const rateCheck = checkRateLimit(`${clientIp}:${isAuthRoute ? 'auth' : 'gen'}`, rateLimitConfig.limit, rateLimitConfig.windowMs);

  if (!rateCheck.allowed) {
    console.warn(`[SECURITY BLOCKED: RATE_LIMIT_EXCEEDED] IP=${clientIp} Path=${pathname} RequestId=${requestId}`);
    return new NextResponse(
      JSON.stringify({
        error: 'Too Many Requests',
        message: 'Rate limit exceeded. Please wait before retrying.',
        retryAfter: rateCheck.resetSec,
        requestId,
      }),
      {
        status: 429,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': String(rateCheck.resetSec),
          'X-RateLimit-Limit': String(rateLimitConfig.limit),
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': String(rateCheck.resetSec),
          'x-request-id': requestId,
        },
      }
    );
  }

  // --------------------------------------------------------------------------
  // CHECK 5: Forward Request with Injected Security Headers & Request Correlation
  // --------------------------------------------------------------------------
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-request-id', requestId);

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  // Apply OWASP Security Headers to the response
  response.headers.set('x-request-id', requestId);
  response.headers.set('Content-Security-Policy', CSP_POLICY);
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), usb=(), payment=()');
  response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
  response.headers.set('X-DNS-Prefetch-Control', 'on');
  response.headers.set('X-XSS-Protection', '1; mode=block');

  // Add rate limit telemetry headers
  response.headers.set('X-RateLimit-Limit', String(rateLimitConfig.limit));
  response.headers.set('X-RateLimit-Remaining', String(rateCheck.remaining));

  return response;
}

// Match all routes except static Next.js assets, public images, and favicons
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, logo.svg, images, fonts
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|woff2?|ico|css|js|txt|html|xml)).*)',
  ],
};
