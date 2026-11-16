# Comlina Web (Frontend)

Production Next.js 14 App Router frontend for **Comlina** — the automated Instagram comment-to-DM conversion and audience growth platform.

## Architecture & Tech Stack

- **Framework**: Next.js 14.2.35 (App Router)
- **Language**: TypeScript 5.5
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Server State & Data Fetching**: TanStack React Query v5
- **Authentication**: Dual Auth Context (FastAPI JWT Session + Supabase Auth)
- **Deployment**: Cloudflare Pages / Vercel

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Required variables:
```env
NEXT_PUBLIC_API_URL=https://api.comlina.ai/api
NEXT_PUBLIC_APP_URL=https://app.comlina.ai
NEXT_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

### 3. Run Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

## Quality & Verification Commands

- `npm run lint`: Next.js core web vitals and ESLint verification.
- `npm run typecheck`: Strict TypeScript compile check (`tsc --noEmit`).
- `npm run build`: Production Next.js build.
