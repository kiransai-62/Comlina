# Comlina — Instagram conversations, automated

Comlina is an event-driven SaaS platform that converts Instagram post comments, story replies, and direct messages into qualified leads and sales through automated Trigger → Condition → Action pipelines.

---

## 🏛️ Production Architecture

```text
comlina/
│
├── client/                 # Next.js (App Router) + TypeScript + Tailwind CSS + Zustand
├── server/                 # FastAPI (Python) Asynchronous Backend API
├── worker/                 # ARQ + Redis Background Automation Worker & DAG Engine
├── shared/                 # Shared TypeScript contracts & validation schemas
├── database/               # PostgreSQL schema migrations (001-011) with Supabase RLS
├── infra/                  # Dockerfiles, Docker Compose, and Nginx proxy
├── docs/                   # Technical guides (Architecture, Webhooks, OAuth, Multi-Tenancy)
├── scripts/                # Database migration and dev orchestration scripts
│
├── .env.example            # Environment variables configuration
├── docker-compose.yml      # Local dev stack (Client, Server, Worker, Postgres, Redis)
└── package.json            # Monorepo workspace commands
```

---

## 🔒 Key Architectural Decisions

1. **Client Locked to Next.js**:
   - Built with Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Zustand, and TanStack Query.
   - Segregation of reusable UI (`components/`) from domain-specific queries and mutations (`features/`).

2. **Durable Webhook Idempotency**:
   - Meta sends webhooks to `POST /webhooks/instagram`.
   - HMAC signature (`X-Hub-Signature-256`) is verified using `META_APP_SECRET`.
   - Webhook events are stored in `webhook_events` with `UNIQUE(provider_event_id)` before queueing.
   - Redundant deliveries are dropped cleanly at the database layer.
   - HTTP 200 OK is returned in under 100ms.

3. **Background Queue via Redis + ARQ**:
   - FastAPI enqueues jobs to Redis via ARQ.
   - The ARQ worker process evaluates the workflow DAG without blocking API requests.
   - The frontend client never communicates directly with Meta or background workers.

4. **Multi-Tenancy at Every Layer**:
   - All records are scoped by `workspace_id`.
   - Incoming user requests verify membership against `workspace_members` via Supabase Auth JWT.
   - Database Row-Level Security (RLS) guarantees defense-in-depth data isolation.

5. **4-State Follower Handling**:
   - Follower status is treated as an explicit 4-state machine:
     - `FOLLOWING` → Delivers protected link/resource.
     - `NOT_FOLLOWING` → Triggers follow gate prompt.
     - `UNKNOWN` / `CHECK_UNAVAILABLE` → Executes safe fallback condition.

6. **Workflow Versioning**:
   - Flow definitions are stored as JSONB with snapshot versioning in `automation_versions` to prevent active runs from mutating mid-flight.

---

## 🚀 Local Development

### Architecture Overview

```text
Browser → Next.js (:3000) → NEXT_PUBLIC_API_URL → FastAPI (:8000) → PostgreSQL (:5432) + Redis (:6379)
```

- **Frontend**: Next.js App Router on [http://localhost:3000](http://localhost:3000)
- **Backend API**: FastAPI on [http://localhost:8000](http://localhost:8000) (Interactive Swagger Docs at [http://localhost:8000/docs](http://localhost:8000/docs), Health check at [http://localhost:8000/health](http://localhost:8000/health))
- **Database**: PostgreSQL on `localhost:5432` (`comlina`)
- **Queue/Cache**: Redis on `localhost:6379`

### Prerequisites

- Node.js 18+ & npm
- Python 3.11+
- Docker & Docker Compose (for backing services: PostgreSQL & Redis)

### 1. Start Backing Services (PostgreSQL & Redis)

Start PostgreSQL and Redis in the background using Docker Compose:

```bash
docker-compose up -d postgres redis
```

### 2. Configure Environment

Ensure environment files are set up:

```bash
cp .env.example .env
cp client/.env.example client/.env.local
```

### 3. Run the Full Stack (`npm run dev`)

Running `npm run dev` from the repository root:

1. Performs a pre-flight dependency check verifying that PostgreSQL (`localhost:5432`) and Redis (`localhost:6379`) are reachable.
2. If either dependency is down, it halts with clear instructions on how to start it.
3. Automatically launches **both** the Next.js frontend and the FastAPI backend concurrently in parallel with clearly labeled, color-coded terminal output (`[client]` and `[server]`).

```bash
npm run dev
```

### 4. Running Services Independently

You can also run frontend and backend processes standalone in separate terminals:

- **Frontend only**:

  ```bash
  npm run dev:client
  ```

- **Backend API only** (runs dependency check, then launches Uvicorn on :8000):

  ```bash
  npm run dev:server
  ```

- **Background Worker only** (ARQ):

  ```bash
  npm run dev:worker
  ```

### Full Containerized Development via Docker Compose

To spin up the entire stack including client and server inside Docker:

```bash
docker-compose up --build
```

---

## 📖 Technical Documentation

- [Architecture Overview](file:///d:/Mine/Comlina/docs/architecture.md)
- [Meta Webhook Integration & Deduplication](file:///d:/Mine/Comlina/docs/webhooks.md)
- [Instagram Graph API OAuth](file:///d:/Mine/Comlina/docs/oauth.md)
- [Multi-Tenancy & Security Guidelines](file:///d:/Mine/Comlina/docs/multi_tenancy.md)
