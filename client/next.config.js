const fs = require('fs');
const path = require('path');

// Helper to parse key=value lines from .env files
function parseEnv(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const content = fs.readFileSync(filePath, 'utf-8');
  const result = {};
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx > 0) {
      const key = trimmed.slice(0, eqIdx).trim();
      let val = trimmed.slice(eqIdx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      result[key] = val;
    }
  }
  return result;
}

// Automatically bridge environment variables from root .env, server/.env, and client/.env.local
const rootEnv = parseEnv(path.resolve(__dirname, '..', '.env'));
const serverEnv = parseEnv(path.resolve(__dirname, '..', 'server', '.env'));
const clientEnv = parseEnv(path.resolve(__dirname, '.env.local'));
const mergedEnv = { ...rootEnv, ...serverEnv, ...clientEnv, ...process.env };

const supabaseUrl = mergedEnv.NEXT_PUBLIC_SUPABASE_URL || mergedEnv.SUPABASE_URL || '';
const supabasePublishableKey = mergedEnv.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || mergedEnv.SUPABASE_PUBLISHABLE_KEY || '';
const supabaseAnonKey = supabasePublishableKey || mergedEnv.NEXT_PUBLIC_SUPABASE_ANON_KEY || mergedEnv.SUPABASE_ANON_KEY || '';
const apiUrl = mergedEnv.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standard default .next build directory
  distDir: process.env.NEXT_DIST_DIR || undefined,
  output: process.env.DOCKER_BUILD === '1' || process.env.OUTPUT_STANDALONE === '1' ? 'standalone' : undefined,
  reactStrictMode: false,
  env: {
    NEXT_PUBLIC_SUPABASE_URL: supabaseUrl,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: supabaseAnonKey,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: supabasePublishableKey,
    NEXT_PUBLIC_API_URL: apiUrl,
  },
  onDemandEntries: {
    maxInactiveAge: 60 * 60 * 1000,
    pagesBufferLength: 30,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'graph.facebook.com',
      },
      {
        protocol: 'https',
        hostname: '**.cdninstagram.com',
      },
      {
        protocol: 'https',
        hostname: 'api.dicebear.com',
      },
    ],
  },
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), usb=(), payment=()',
          },
        ],
      },
    ];
  },
  async redirects() {
    return [
      {
        source: '/data-deletion',
        destination: '/data-deletion-status',
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
