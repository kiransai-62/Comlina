# Comlina Frontend Deployment Guide (Vercel)

This guide walks through deploying the Comlina Next.js web application on **Vercel**, configuring monorepo settings, setting environment variables, custom domains with HTTPS, and synchronizing Meta OAuth redirect URIs.

---

## 1. Prerequisites

Before deploying to Vercel, ensure you have:

1. A [Vercel](https://vercel.com) account.
2. The GitHub / GitLab repository linked to Vercel.
3. Your production backend URL (e.g., `https://api.comlina.ai/api`).
4. Your Supabase Project URL and Anon Public Key.

---

## 2. Monorepo Project Settings on Vercel

When importing the repository into Vercel:

| Setting | Value | Explanation |
| :--- | :--- | :--- |
| **Framework Preset** | `Next.js` | Automatically recognized. |
| **Root Directory** | `client` | Points Vercel to the Next.js frontend within the monorepo. |
| **Build Command** | `npm run build` | Builds the optimized production bundle. |
| **Output Directory** | Default (`.next`) | Comlina's `next.config.js` defaults to `.next` when `VERCEL=1`. |
| **Install Command** | `npm install` | Installs frontend dependencies. |
| **Node.js Version** | `18.x` or `20.x` | Modern LTS version. |

> [!NOTE]
> The repository includes both [`client/vercel.json`](file:///c:/PROJECTS/Comlina/client/vercel.json) and root [`vercel.json`](file:///c:/PROJECTS/Comlina/vercel.json), so Vercel can detect and configure these settings automatically.

---

## 3. Required Environment Variables

In your Vercel Project Dashboard under **Settings -> Environment Variables**, add the following:

| Variable Name | Environments | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Production, Preview | `https://api.comlina.ai/api` | URL of your deployed FastAPI backend. |
| `NEXT_PUBLIC_SUPABASE_URL` | Production, Preview | `https://vrfwgoigtmixkkunvrnw.supabase.co` | Supabase API URL for auth & sessions. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Production, Preview | `eyJhbGciOiJIUzI1Ni...` | Supabase Public Anonymous API Key. |

---

## 4. Custom Domain & HTTPS

1. Navigate to **Project Settings -> Domains**.
2. Add your custom domain (e.g., `app.comlina.ai`).
3. Add the DNS records provided by Vercel in your DNS registrar (Cloudflare, GoDaddy, AWS Route 53):
   * **Type**: `CNAME`
   * **Name**: `app`
   * **Value**: `cname.vercel-dns.com`
4. Vercel automatically issues and renews an SSL/TLS certificate via Let's Encrypt with HTTP/2 and HTTP/3 support.

---

## 5. Meta Developer OAuth Redirect URI Update

After your Vercel production domain is live (e.g., `https://app.comlina.ai`):

1. Go to the [Meta Developer Portal](https://developers.facebook.com/apps/964103992653470/).
2. Navigate to **Instagram Platform / Facebook Login -> Settings**.
3. Under **Valid OAuth Redirect URIs**, add:

   ```text
   https://app.comlina.ai/connect/instagram
   ```

4. In your backend environment (or `.env.production`), update:

   ```env
   META_REDIRECT_URI=https://app.comlina.ai/connect/instagram
   CORS_ORIGINS=https://app.comlina.ai,https://comlina.ai
   ```

---

## 6. Verification Steps

1. Trigger a deployment by pushing to your main branch or via Vercel CLI:

   ```bash
   vercel --prod
   ```

2. Open `https://app.comlina.ai` in your browser.
3. Verify that:
   * Landing page, login, and dashboard load cleanly.
   * Supabase session restores and user state is preserved.
   * Network requests to `NEXT_PUBLIC_API_URL` succeed with HTTP 200/201 and valid CORS headers.
   * Connecting an Instagram account redirects to Meta and returns to `/connect/instagram` without error.
