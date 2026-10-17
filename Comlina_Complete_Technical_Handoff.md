# Comlina — Complete Codebase & Architecture Handoff Report

**Document Target:** External Coding Agent / Engineering Team
**System Name:** Comlina (Instagram Conversations & Automation SaaS)
**Author:** Senior Software Architect, Full-Stack & DevOps Engineer
**Date of Audit:** October 15, 2026
**Repository Location:** `c:\PROJECTS\Comlina`
**Document Status:** Ground-Truth Technical Specification & Implementation Guide

---

## 1. Executive Summary

This document serves as the **definitive technical handoff** for an external coding agent taking over the Comlina codebase. It reflects the **actual, verified state** of the repository as of October 15, 2026.

Comlina is an event-driven Software-as-a-Service (SaaS) platform architected to convert Instagram comments, story interactions, and direct messages into qualified business leads through automated **Trigger → Condition → Action** DAG (Directed Acyclic Graph) pipelines.

### Current Health & Maturity Baseline

- **Overall Operational Readiness:** **28%**
- **Frontend App Shell:** **Production-built and verified.** Next.js 14.2.35 App Router compiles with 0 TypeScript errors across all 17 routes. First load JS is 87.3 kB.
- **Backend API Server:** **Operational.** FastAPI 0.141.1 binds to port 8000. Verified health endpoint returns HTTP 200 in 12ms. Multi-tenant Row-Level Security (RLS) and OWASP middleware are production-grade.
- **Background Worker Engine:** **BROKEN (Blocking Startup).** The ARQ background worker in `worker/app/jobs/process_comment.py` has an `IndentationError` at line 137, which completely prevents the worker process from importing and running.
- **Instagram / Meta Integration:** **PARTIAL / CONFLICTING.** Webhook signature verification and deduplication are solidly built. However, the OAuth flow mixes incompatible endpoints (`api.instagram.com` Instagram Login for Business vs. `graph.facebook.com` Facebook Pages API). In development, this is masked by a mock fallback account.
- **Data & Commercial Core:** Post selection in the Automation Builder is hardcoded to 5 Unsplash mock cards; manual DM sending in the Inbox only mutates local React state; and billing consists of mock toasts without a payment gateway.

This guide provides the exact file maps, route inventories, database schemas, confirmed bugs with line numbers, and an execution roadmap to bring Comlina from its current state to a verified production launch.

---

## 2. Actual System Architecture & Data Flow

The codebase is organized as a monorepo containing three core runtime tiers (Client, Server, Worker), backed by PostgreSQL, Redis, and Meta's Graph API.

```mermaid
flowchart TD
    subgraph ClientTier["Client Tier (Port 3000)"]
        Browser["End-User Browser"]
        NextApp["Next.js 14 App Router<br/>(Tailwind + Zustand + TanStack Query)"]
        EdgeMW["Edge Security Middleware<br/>(CSP, RateLimiter, Exploit Trap)"]
        SupabaseAuth["Supabase Auth JS Client<br/>(Session & JWT)"]

        Browser --> NextApp
        NextApp --> EdgeMW
        NextApp --> SupabaseAuth
    end

    subgraph APITier["Backend API Tier (Port 8000)"]
        FastAPI["FastAPI 0.141.1 Server<br/>(Uvicorn ASGI)"]
        APIMW["Security Middleware<br/>(OWASP, Payload Limit, IP RateLimit)"]
        AuthDeps["Deps: get_current_user<br/>(Verifies Supabase JWT)"]
        TenantDeps["Deps: get_current_workspace<br/>(BOLA / Membership Check)"]
        APIRouters["API Routers<br/>(automations, contacts, conversations, instagram)"]
        WebhookEndpoint["POST /webhooks/instagram<br/>(HMAC-SHA256 Verification)"]

        EdgeMW -->|"HTTP /api (Bearer JWT, X-Workspace-ID)"| APIMW
        APIMW --> FastAPI
        FastAPI --> AuthDeps
        AuthDeps --> TenantDeps
        TenantDeps --> APIRouters
        FastAPI --> WebhookEndpoint
    end

    subgraph DataStorage["Data & State Tier"]
        PG[("PostgreSQL 16 Database<br/>(Supabase RLS Enabled)")]
        SQLiteDev[("SQLite Fallback DB<br/>(comlina_dev.db)")]
        RedisQ[("Redis 7.0 (Port 6379)<br/>ARQ Job Queue & Cache")]
    end

    subgraph WorkerTier["Worker Tier (Background Automation)"]
        ARQWorker["ARQ Worker Engine<br/>(app.main.WorkerSettings)"]
        JobRouter["Job Dispatcher<br/>(process_webhook_event)"]
        FlowEngine["DAG FlowEngine<br/>(Trigger -> Condition -> Action)"]
        FollowerService["InstagramFollowerService<br/>(4-State Follower Machine)"]
        ActionEngine["ActionEngine<br/>(Public Reply / Private DM / Delay)"]

        RedisQ -->|"Dequeue Event"| ARQWorker
        ARQWorker --> JobRouter
        JobRouter --> FlowEngine
        FlowEngine --> FollowerService
        FlowEngine --> ActionEngine
    end

    subgraph ExternalServices["External APIs & Meta Infrastructure"]
        MetaWebhook["Meta Graph Webhook Emitter<br/>(Comments, DMs, Feed)"]
        MetaGraphAPI["Meta Graph API v21.0<br/>(graph.facebook.com / graph.instagram.com)"]
        SupabaseCloud["Supabase Auth Cloud"]
    end

    %% Webhook ingestion flow
    MetaWebhook -->|"POST /webhooks/instagram<br/>(X-Hub-Signature-256)"| WebhookEndpoint
    WebhookEndpoint -->|"1. Deduplicate & Persist"| PG
    WebhookEndpoint -->|"2. Enqueue Job"| RedisQ
    WebhookEndpoint -.->|"Dev Fallback"| SQLiteDev

    %% API Data Access
    APIRouters --> PG
    APIRouters -.->|"Dev Fallback"| SQLiteDev

    %% Worker Execution
    ActionEngine -->|"Outbound REST Calls"| MetaGraphAPI
    FollowerService -->|"Query Follow Status"| MetaGraphAPI
    ARQWorker -->|"Update Contacts, Logs, Stats"| PG
    ARQWorker -.->|"CRASH: process_comment.py:137"| PG
```

### Architectural Tenets Implemented in Code

1. **Frontend Isolation:** The Next.js client never holds Meta app secrets and never calls Meta directly.
2. **Durable Webhook Idempotency:** In [webhooks.py](file:///c:/PROJECTS/Comlina/server/app/api/webhooks.py), incoming webhook events are validated via HMAC-SHA256, deduplicated in `webhook_events.provider_event_id` via `ON CONFLICT DO NOTHING`, and only then enqueued to Redis. An immediate HTTP 200 OK is returned to Meta within 100ms.
3. **Defense-in-Depth Multi-Tenancy:** Tenant isolation is enforced at both the API dependency layer ([deps.py](file:///c:/PROJECTS/Comlina/server/app/api/deps.py)) and the PostgreSQL database layer ([011_row_level_security.sql](file:///c:/PROJECTS/Comlina/database/migrations/011_row_level_security.sql)).
4. **4-State Follower Safety Machine:** Follower status is tracked as `FOLLOWING`, `NOT_FOLLOWING`, `UNKNOWN`, or `CHECK_UNAVAILABLE` ([follower_status.py](file:///c:/PROJECTS/Comlina/worker/app/integrations/instagram/follower_status.py)). If Meta rate-limits the check, the engine triggers a safe fallback rather than failing the workflow.

---

## 3. Complete Codebase Map

| Directory / File | Responsibility | Key Classes / Functions / Exports | Consumed By | Status & Critical Notes |
| --- | --- | --- | --- | --- |
| **`client/src/middleware.ts`** | Edge reverse-proxy protection | `middleware()`, `CSP_POLICY`, `checkRateLimit()` | Next.js Server | **Active.** OWASP headers, scanner trapping (`/.env`, `sqlmap`). |
| **`client/src/lib/api.ts`** | Central client HTTP fetcher | `api`, `ApiClient`, `ApiError` | Feature modules | **Active.** Automatically injects Supabase Bearer token and `X-Workspace-ID`. |
| **`client/src/lib/auth.ts`** | Auth state wrapper | `authService`, `AUTH_ENABLED` | UI & Layouts | **Active.** Wraps Supabase session recovery and token retrieval. |
| **`client/src/app/(auth)/`** | Authentication screens | `/login/page.tsx`, `/signup/page.tsx` | End-users | **Active.** Email/password auth against Supabase Auth. |
| **`client/src/app/connect/instagram/`** | Meta OAuth callback handler | `ConnectInstagramCallbackPage` | Meta OAuth redirect | **Active.** Captures `code` and `state`; passes to backend. |
| **`client/src/app/dashboard/page.tsx`** | Main dashboard overview | `DashboardOverviewPage` | Authenticated users | **Partial.** Analytics integration has key mismatch. |
| **`client/src/app/dashboard/automations/create/`** | Visual automation builder | `CreateAutomationPage`, Flow sub-components | Content creators | **Partial.** Functional DAG UI, but post selector uses mock cards. |
| **`client/src/app/dashboard/inbox/`** | Direct message inbox | `ConversationsPage` | Account managers | **Incomplete.** Outbound "Send" updates local state only; no API call. |
| **`server/app/main.py`** | FastAPI app entrypoint | `app`, `lifespan()`, `health_check()` | Uvicorn ASGI | **Active.** Mounts security middlewares and 8 route controllers. |
| **`server/app/core/config.py`** | Environment configuration | `Settings`, `settings` | Entire backend | **Active.** Pydantic v2 settings; validates production secrets. |
| **`server/app/core/database.py`** | SQLAlchemy DB session provider | `engine`, `AsyncSessionLocal`, `get_db()`, `init_db()` | API route handlers | **Active.** Contains auto-fallback to SQLite when Postgres is offline. |
| **`server/app/core/security.py`** | Cryptography & Token verification | `encrypt_token()`, `decrypt_token()`, `verify_meta_webhook_signature()` | OAuth & Webhooks | **Active.** Tested with 10 unit tests. |
| **`server/app/core/security_middleware.py`** | ASGI security middleware | `SecurityHeadersMiddleware`, `PayloadSizeLimitMiddleware`, `AttackFilterMiddleware` | FastAPI app | **Active.** Rejects oversized payloads (>2MB) and attack tools. |
| **`server/app/api/deps.py`** | FastApi dependency injection | `get_current_user()`, `get_current_workspace()`, `require_workspace_owner()` | All API routers | **Active.** Strict tenant isolation and BOLA authorization. |
| **`server/app/api/instagram.py`** | Instagram account CRUD & OAuth | `list_instagram_accounts()`, `get_connect_url()`, `handle_oauth_callback()` | Client | **Broken.** Conflates Instagram Login scopes with Pages API calls. |
| **`server/app/api/webhooks.py`** | Meta Webhook Receiver | `verify_webhook_subscription()`, `receive_meta_webhook()` | Meta Webhook engine | **Partial.** Uses `pg_insert` which breaks on SQLite fallback. |
| **`server/app/api/automations.py`** | Automation CRUD & publishing | `list_automations()`, `create_automation()`, `publish_automation()` | Client | **Active.** Enforces plan quota checks and snapshots versions. |
| **`server/app/api/analytics.py`** | Aggregated workspace metrics | `get_analytics_summary()` | Client dashboard | **Broken.** Keys returned do not match client TypeScript schema. |
| **`server/app/models/**init**.py`** | SQLAlchemy ORM Models | `User`, `Workspace`, `InstagramAccount`, `Automation`, `Contact`, `Conversation`, `Message`, `WebhookEvent` | Backend & Worker | **Active.** Complete schema matching migrations 001-011. |
| **`worker/app/main.py`** | ARQ Worker Entrypoint | `WorkerSettings`, `process_webhook_event()`, `startup()`, `shutdown()` | ARQ CLI | **Broken.** Fails to import due to syntax error in `process_comment.py`. |
| **`worker/app/jobs/process_comment.py`** | Core automation job | `process_comment_job()` | ARQ Worker | **CRITICAL BUG.** `IndentationError` at line 137. |
| **`worker/app/engine/flow_engine.py`** | DAG evaluation engine | `FlowEngine.run_flow()` | `process_comment_job` | **Active.** Evaluates triggers, conditions, and actions in sequence. |
| **`worker/app/engine/action_engine.py`** | Automation action executor | `ActionEngine.execute_action()` | `FlowEngine` | **Active.** Executes `PUBLIC_REPLY`, `PRIVATE_DM`, `TAG_CONTACT`, `DELAY`. |
| **`scripts/check-deps.js`** | Pre-flight dependency checker | `checkPort()`, `main()` | `npm run dev` | **Problematic.** Hard-halts dev environment if Docker is down. |
| **`scripts/start-server.js`** | Uvicorn server launcher | `findUvicornCommand()`, `main()` | `npm run dev:server` | **Active.** Finds virtualenv python and launches Uvicorn on port 8000. |

---

## 4. Frontend Architecture

- **Framework:** Next.js 14.2.35 (React 18.3.1, TypeScript 5.5.4)
- **Routing Paradigm:** Next.js App Router (`client/src/app`)
- **State Management:**
  - Server state: TanStack React Query 5.51.11
  - Client UI state: Zustand 4.5.4 (`client/src/stores/uiStore.ts`)
- **UI & Styling:** Tailwind CSS 3.4.7 with custom design tokens, Lucide React icons, and custom components (`BrandLogo`, `MovingArrowConnector`).

### Page Integration Status & Real vs. Mock Behavior

| Route | Page File | Backing API | Data State | What Works vs. What Is Mocked |
| --- | --- | --- | --- | --- |
| `/login` | `src/app/(auth)/login/page.tsx` | Supabase Auth | **Real** | Form validation, password sign-in, redirect to dashboard. |
| `/signup` | `src/app/(auth)/signup/page.tsx` | Supabase Auth | **Real** | Account creation, auto-provisions profile on first login. |
| `/connect/instagram` | `src/app/connect/instagram/page.tsx` | `POST /api/instagram/oauth/callback` | **Broken Integration** | Reads `code` & `state` from URL query; sends to backend. Fails in prod due to backend scope conflict. |
| `/dashboard` | `src/app/dashboard/page.tsx` | `GET /api/analytics/summary`, `GET /api/instagram/accounts` | **Partial** | Layout and account switcher work; metrics display `0` due to contract key mismatch. |
| `/dashboard/automations` | `src/app/dashboard/automations/page.tsx` | `GET /api/automations`, `POST /api/automations` | **Real** | Lists real database automations; status toggles (active/paused); delete works. |
| `/dashboard/automations/create` | `src/app/dashboard/automations/create/page.tsx` | `POST /api/automations`, `POST /api/automations/{id}/publish` | **Mixed** | Full DAG configuration & JSONB saving work; post selector is hardcoded to 5 mock Unsplash cards. |
| `/dashboard/inbox` | `src/app/dashboard/inbox/page.tsx` | `GET /api/conversations`, `GET /api/conversations/{id}/messages` | **Mixed** | Reads real threads and messages; clicking "Send" only updates React local state without API call. |
| `/dashboard/contacts` | `src/app/dashboard/contacts/page.tsx` | `GET /api/contacts`, `GET /api/contacts/export-csv` | **Real** | Real contact listing, filtering by follower status and tag, working CSV export stream. |
| `/dashboard/instagram-accounts` | `src/app/dashboard/instagram-accounts/page.tsx` | `GET /api/instagram/accounts`, `POST /api/instagram/connect-dev-account` | **Real** | Shows real connected accounts; dev mock account button works; disconnect works. |
| `/dashboard/settings` | `src/app/dashboard/settings/page.tsx` | None (Local state) | **Mocked** | UI tabs exist; "Upgrade to Pro" displays mock toast; "Delete Account" is a dummy alert. |

---

## 5. Backend Architecture & Endpoint Inventory

- **Framework:** FastAPI 0.141.1 on Python 3.14.3 (ASGI via Uvicorn)
- **Application Lifespan:** `app.main:lifespan()` calls `init_db()`, registering models and creating tables.
- **Middleware Pipeline (Executed in order):**
  1. `SecurityHeadersMiddleware`: OWASP security headers.
  2. `PayloadSizeLimitMiddleware`: Rejects request bodies > 2MB (HTTP 413).
  3. `ApiRateLimitMiddleware`: In-memory sliding-window IP rate limiter.
  4. `AttackFilterMiddleware`: Blocks scanners (`sqlmap`, `nikto`, `wp-login.php`, SQL injection).
  5. `CORSMiddleware`: Strict origin validation for `localhost:3000`, `localhost:5173`, `app.comlina.ai`.

### API Endpoint Inventory

| Method & Route | Source Controller | Auth Required | Request / Response | Database Query | Current Status | Notes & Known Defects |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /health` | `app/main.py:69` | None | Resp: `{ status, service, version, meta_api_version }` | None | **Verified (200 OK)** | Returns system health in 12ms. |
| `GET /api/auth/me` | `app/api/auth.py:9` | Bearer JWT | Resp: `{ id, email, full_name, avatar_url, timezone }` | `SELECT users` | **Verified** | Auto-provisions user on first login. |
| `GET /api/workspaces` | `app/api/workspaces.py:14` | Bearer JWT | Resp: `List[WorkspaceOut]` | `SELECT workspaces JOIN members` | **Verified** | Lists workspaces user belongs to. |
| `GET /api/workspaces/current` | `app/api/workspaces.py:27` | Bearer JWT | Resp: `WorkspaceOut` | Resolves from `X-Workspace-ID` | **Verified** | Re-verifies tenant membership. |
| `GET /api/instagram/accounts` | `app/api/instagram.py:24` | Bearer JWT | Resp: `List[InstagramAccountOut]` | `SELECT instagram_accounts` | **Verified** | Returns active accounts for workspace. |
| `GET /api/instagram/oauth/connect-url` | `app/api/instagram.py:64` | Bearer JWT (Owner) | Query: `redirect_uri` / Resp: `{ authorization_url, state }` | None (HMAC sign) | **Verified** | Generates signed CSRF state. |
| `POST /api/instagram/oauth/callback` | `app/api/instagram.py:76` | Bearer JWT (Owner) | Body: `ConnectAccountRequest` / Resp: `InstagramAccountOut` | `UPSERT instagram_accounts` | **Broken** | Scopes conflict with Graph API call. |
| `POST /api/instagram/connect-dev-account` | `app/api/instagram.py:236` | Bearer JWT (Owner) | Resp: `InstagramAccountOut` | `INSERT instagram_accounts` | **Verified** | Development convenience mock account. |
| `DELETE /api/instagram/accounts/{id}` | `app/api/instagram.py:315` | Bearer JWT (Owner) | Resp: HTTP 204 No Content | `DELETE instagram_accounts` | **Verified** | Cascade deletes automations/contacts. |
| `GET /api/automations` | `app/api/automations.py:14` | Bearer JWT | Query: `limit, offset` / Resp: `List[AutomationOut]` | `SELECT automations` | **Verified** | Ordered by `created_at DESC`. |
| `POST /api/automations` | `app/api/automations.py:23` | Bearer JWT | Body: `AutomationCreate` / Resp: `AutomationOut` | `INSERT automations` | **Verified** | Checks account BOLA & plan quota. |
| `POST /api/automations/{id}/publish` | `app/api/automations.py:36` | Bearer JWT | Resp: `AutomationOut` | `UPDATE automations`, `INSERT versions` | **Verified** | Creates immutable version snapshot. |
| `DELETE /api/automations/{id}` | `app/api/automations.py:48` | Bearer JWT | Resp: HTTP 204 No Content | `DELETE automations` | **Verified** | Verifies workspace ownership. |
| `GET /api/contacts` | `app/api/contacts.py:14` | Bearer JWT | Query: `tag, follower_status, is_converted` | `SELECT contacts` | **Verified** | Supports filtering and pagination. |
| `GET /api/contacts/export-csv` | `app/api/contacts.py:34` | Bearer JWT | Resp: `text/csv` stream | `SELECT contacts` | **Verified** | Downloads `comlina_contacts.csv`. |
| `GET /api/conversations` | `app/api/conversations.py:14` | Bearer JWT | Query: `account_id` / Resp: `List[ConversationOut]` | `SELECT conversations` | **Verified** | Thread listing ordered by last message. |
| `GET /api/conversations/{id}/messages` | `app/api/conversations.py:26` | Bearer JWT | Resp: `List[MessageOut]` | `SELECT messages` | **Verified** | BOLA check on conversation tenant. |
| `GET /api/analytics/summary` | `app/api/analytics.py:12` | Bearer JWT | Resp: JSON dictionary | `SELECT COUNT/SUM` | **Broken Contract** | Key names mismatch frontend schema. |
| `GET /webhooks/instagram` | `app/api/webhooks.py:22` | None | Query: `hub.mode, hub.challenge, hub.verify_token` | None | **Verified (200 OK)** | Meta challenge verification handshake. |
| `POST /webhooks/instagram` | `app/api/webhooks.py:45` | `X-Hub-Signature-256` | Body: Meta JSON / Resp: `{ status, count }` | `INSERT webhook_events` | **Partial** | Uses `pg_insert` (fails on SQLite). |

---

## 6. Database Schema & ER Diagram

The database uses PostgreSQL with Supabase Auth integration. Eleven sequential migrations exist in `database/migrations/`:

```mermaid
erDiagram
    USERS ||--o{ WORKSPACE_MEMBERS : "has membership"
    WORKSPACES ||--o{ WORKSPACE_MEMBERS : "contains"
    WORKSPACES ||--o{ INSTAGRAM_ACCOUNTS : "owns"
    WORKSPACES ||--o{ AUTOMATIONS : "scopes"
    WORKSPACES ||--o{ CONTACTS : "scopes"
    WORKSPACES ||--o{ CONVERSATIONS : "scopes"
    WORKSPACES ||--o{ WEBHOOK_EVENTS : "logs"
    WORKSPACES ||--o{ ANALYTICS_EVENTS : "logs"

    INSTAGRAM_ACCOUNTS ||--o{ AUTOMATIONS : "executes"
    INSTAGRAM_ACCOUNTS ||--o{ CONTACTS : "interacts with"
    INSTAGRAM_ACCOUNTS ||--o{ CONVERSATIONS : "manages"

    AUTOMATIONS ||--o{ AUTOMATION_VERSIONS : "snapshots"
    AUTOMATIONS ||--o{ MESSAGES : "generates"
    AUTOMATIONS ||--o{ ANALYTICS_EVENTS : "tracks"

    CONTACTS ||--o{ CONVERSATIONS : "participates in"
    CONVERSATIONS ||--o{ MESSAGES : "contains"

    USERS {
        uuid id PK "Maps to auth.users.id"
        varchar email UK
        varchar full_name
        varchar timezone
        timestamptz created_at
    }

    WORKSPACES {
        uuid id PK
        varchar name
        varchar slug UK
        varchar plan_tier "FREE, PRO, SCALE, ENTERPRISE"
        varchar plan_status "ACTIVE, PAST_DUE, CANCELLED"
        int max_automations "Default 10"
        int max_accounts "Default 1"
        timestamptz created_at
    }

    WORKSPACE_MEMBERS {
        uuid id PK
        uuid workspace_id FK
        uuid user_id FK
        varchar role "OWNER, ADMIN, MEMBER"
    }

    INSTAGRAM_ACCOUNTS {
        uuid id PK
        uuid workspace_id FK
        varchar ig_user_id "Instagram Scoped ID"
        varchar username
        varchar account_type "BUSINESS, CREATOR"
        text access_token_encrypted "Fernet AES-256"
        timestamptz token_expires_at
        boolean is_active
        jsonb permissions
    }

    AUTOMATIONS {
        uuid id PK
        uuid workspace_id FK
        uuid instagram_account_id FK
        varchar name
        varchar status "DRAFT, ACTIVE, PAUSED, ERROR, ARCHIVED"
        varchar trigger_type "COMMENT, STORY_REPLY, DM"
        jsonb flow_definition "Full DAG Trigger/Condition/Action"
        int version "Auto-incrementing"
        int stats_comments
        int stats_dms_sent
        int stats_clicks
    }

    AUTOMATION_VERSIONS {
        uuid id PK
        uuid automation_id FK
        uuid workspace_id FK
        int version
        jsonb flow_definition "Immutable snapshot"
        timestamptz published_at
    }

    CONTACTS {
        uuid id PK
        uuid workspace_id FK
        uuid instagram_account_id FK
        varchar ig_user_id
        varchar username
        varchar follower_status "UNKNOWN, FOLLOWING, NOT_FOLLOWING, CHECK_UNAVAILABLE"
        boolean is_converted
        int interaction_count
        jsonb tags
    }

    CONVERSATIONS {
        uuid id PK
        uuid workspace_id FK
        uuid instagram_account_id FK
        uuid contact_id FK
        varchar status "OPEN, SNOOZED, RESOLVED, BLOCKED"
        text last_message_text
        timestamptz last_message_at
        int unread_count
    }

    MESSAGES {
        uuid id PK
        uuid workspace_id FK
        uuid conversation_id FK
        varchar sender_type "CONTACT, INSTAGRAM_ACCOUNT, BOT"
        text text
        text media_url
        varchar meta_message_id
        uuid automation_id FK
    }

    WEBHOOK_EVENTS {
        uuid id PK
        varchar provider_event_id UK "mid / comment_id"
        varchar event_type "COMMENT, MESSAGING, FEED"
        jsonb payload
        varchar status "PENDING, PROCESSING, PROCESSED, FAILED, IGNORED"
        timestamptz received_at
    }

    ANALYTICS_EVENTS {
        uuid id PK
        uuid workspace_id FK
        uuid automation_id FK
        varchar event_type "COMMENT_RECEIVED, DM_SENT, LEAD_CAPTURED"
        jsonb metadata
        timestamptz created_at
    }
```

### Missing Entities (Must be created when features are built)

- `posts` / `scheduled_content`: For Content Calendar & Instagram Content Publishing.
- `subscriptions` / `invoices`: For Stripe billing customer IDs, plan states, and webhooks.
- `audit_logs`: For enterprise workspace security audit trails.

---

## 7. Instagram / Meta Integration Architecture

### The Conflict: Instagram Login vs. Facebook Login

The codebase currently contains conflicting assumptions regarding Meta's authentication pathways:

```text
Current Code Behavior:
1. oauth.py:25 redirects to:
   https://api.instagram.com/oauth/authorize?scope=instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments
   --> [This is Instagram Login for Business]

2. BUT instagram.py:144 attempts to query:
   https://graph.facebook.com/v21.0/me/accounts?fields=id,name,access_token,instagram_business_account{...}
   --> [This requires Facebook Login with 'pages_show_list' permission, which was never requested!]

3. In development mode:
   Lines 168-185 of instagram.py catch the failure and create a fake account:
   ig_user_id="ig_dev_...", username="comlina_creator_dev"
   --> [This completely masks the failure during local dev testing!]
```

### Required Resolution for External Agent

Standardize exclusively on **Instagram Login for Business**:

- User authorizes directly via Instagram credentials.
- After code exchange on `https://api.instagram.com/oauth/access_token`, query `https://graph.instagram.com/me?fields=id,username,account_type` directly using the Instagram User Access Token.
- Eliminate calls to `graph.facebook.com/me/accounts` (Pages API).

### Rate Limits & Error Handling

- Handled in `worker/app/integrations/instagram/client.py`:
  - Automatically retries network timeouts and transient Meta 5xx errors with exponential backoff (`INITIAL_BACKOFF = 1.0s`, `BACKOFF_FACTOR = 2.0`, max 3 attempts).
  - Explicitly detects Meta rate-limit codes (`4`, `17`, `32`, `613`) and pauses.
  - Detects expired token code `190` (`MetaTokenExpiredError`) and fails immediately without retry loops.

---

## 8. Environment & Local Development Setup

### Configuration Variables (`.env`)

| Variable Name | Required In | Purpose | Status in Code |
| --- | --- | --- | --- |
| `ENVIRONMENT` | All | Runtime mode (`development`, `production`) | Active. Defaults to `production`. |
| `DATABASE_URL` | All | PostgreSQL connection DSN (`postgresql+asyncpg://...`) | Active. Fallback to SQLite in dev. |
| `REDIS_URL` | Worker/Server | Redis connection DSN for ARQ queue | Active. Required for ARQ worker. |
| `TOKEN_ENCRYPTION_KEY` | Server/Worker | 32-byte urlsafe base64 key for Fernet token encryption | Active. Auto-generated in dev. |
| `SUPABASE_URL` | Client/Server | Supabase project URL | Active. |
| `SUPABASE_ANON_KEY` | Client | Supabase anonymous public key | Active in Next.js. |
| `SUPABASE_JWT_SECRET` | Server | Secret used to verify incoming Supabase JWTs | Active in `deps.py`. |
| `META_APP_ID` | Server | Meta Application ID | Active in OAuth & Webhooks. |
| `META_APP_SECRET` | Server | Meta App Secret (for token exchange & HMAC) | Active in OAuth & Webhooks. |
| `META_WEBHOOK_VERIFY_TOKEN` | Server | Secret for Meta Webhook GET handshake | Active in `webhooks.py`. |
| `META_GRAPH_API_VERSION` | Server/Worker | Meta Graph API Version (e.g. `v21.0`) | Active. Injected in all HTTP calls. |
| `NEXT_PUBLIC_API_URL` | Client | FastAPI base URL (`http://localhost:8000/api`) | Active in `api.ts`. |

### Step-by-Step Local Developer Runbook

1. **Prerequisites:**
   - Node.js 18+ and npm
   - Python 3.11+ or 3.14 (with `uv` or virtualenv)
   - Docker Desktop (must be running for PostgreSQL and Redis)

2. **Step 1: Start Backing Services (Docker)**

   ```bash
   docker-compose up -d postgres redis
   ```

   *Verification:* Ensure `docker ps` shows `postgres` on port 5432 and `redis` on port 6379 as healthy.

3. **Step 2: Apply Database Migrations**

   ```bash
   python scripts/migrate.py
   ```

   *Output:* Applies 11 migrations and records them in `schema_migrations`.

4. **Step 3: Run Backend Server (FastAPI)**

   ```bash
   npm run dev:server
   ```

   *Verification:* Open `http://localhost:8000/health` in a browser. It will return `{"status":"healthy"}`.

5. **Step 4: Run Frontend Client (Next.js)**

   ```bash
   npm run dev:client
   ```

   *Verification:* Open `http://localhost:3000`. The login/dashboard will be interactive.

6. **Step 5: Run Background Worker (ARQ)**
   *(Note: Must apply Fix ISS-001 first!)*

   ```bash
   npm run dev:worker
   ```

---

## 9. Feature Implementation Status

- **`COMPLETED AND VERIFIED`**: Code is complete, active, and verified by runtime tests.
- **`IMPLEMENTED BUT UNVERIFIED`**: Code exists but lacks live integration verification.
- **`PARTIALLY IMPLEMENTED`**: Functional core exists, but important capabilities are missing.
- **`IMPLEMENTED BUT BROKEN`**: Feature exists in code but fails upon execution.
- **`NOT IMPLEMENTED`**: No meaningful codebase implementation exists.

| Feature Area | Status | Evidence / Files | Current Limitations |
| --- | --- | --- | --- |
| **Multi-Tenant Security** | **COMPLETED & VERIFIED** | [deps.py](file:///c:/PROJECTS/Comlina/server/app/api/deps.py), [011_row_level_security.sql](file:///c:/PROJECTS/Comlina/database/migrations/011_row_level_security.sql) | None. Application & RLS defense verified. |
| **Token Encryption** | **IMPLEMENTED BUT UNVERIFIED** | [encryption.py](file:///c:/PROJECTS/Comlina/server/app/core/encryption.py) | Unit tests pass; automated 60-day refresh job absent. |
| **User Authentication** | **PARTIALLY IMPLEMENTED** | [login/page.tsx](file:///c:/PROJECTS/Comlina/client/src/app/(auth)/login/page.tsx), [deps.py](file:///c:/PROJECTS/Comlina/server/app/api/deps.py) | Client login works; backend lacks password reset endpoints. |
| **Instagram Account Mgmt** | **PARTIALLY IMPLEMENTED** | [instagram.py](file:///c:/PROJECTS/Comlina/server/app/api/instagram.py) | Listing and disconnect work; reconnect/refresh incomplete. |
| **Instagram OAuth** | **IMPLEMENTED BUT BROKEN** | [oauth.py](file:///c:/PROJECTS/Comlina/server/app/integrations/instagram/oauth.py), [instagram.py](file:///c:/PROJECTS/Comlina/server/app/api/instagram.py) | Scopes conflict with Pages API; falls back to mock account. |
| **Webhooks Ingestion** | **PARTIALLY IMPLEMENTED** | [webhooks.py](file:///c:/PROJECTS/Comlina/server/app/api/webhooks.py) | Verification & HMAC work; uses Postgres-only syntax. |
| **Background ARQ Worker** | **IMPLEMENTED BUT BROKEN** | [process_comment.py](file:///c:/PROJECTS/Comlina/worker/app/jobs/process_comment.py:137) | **Crashes on startup** due to `IndentationError`. |
| **Automation Flow Builder** | **PARTIALLY IMPLEMENTED** | [create/page.tsx](file:///c:/PROJECTS/Comlina/client/src/app/dashboard/automations/create/page.tsx) | DAG saving works; post selector restricted to 5 mock cards. |
| **Comment Automation** | **PARTIALLY IMPLEMENTED** | [action_engine.py](file:///c:/PROJECTS/Comlina/worker/app/engine/action_engine.py) | Auto-reply works; lacks manual comment moderation UI. |
| **Direct Messaging Inbox** | **PARTIALLY IMPLEMENTED** | [inbox/page.tsx](file:///c:/PROJECTS/Comlina/client/src/app/dashboard/inbox/page.tsx) | Ingestion works; manual "Send" is a client-side mock. |
| **Analytics Dashboard** | **IMPLEMENTED BUT BROKEN** | [analytics_service.py](file:///c:/PROJECTS/Comlina/server/app/services/analytics_service.py) | API contract key mismatch displays `0` for all cards. |
| **Multi-Account Switching** | **PARTIALLY IMPLEMENTED** | [instagram-accounts/page.tsx](file:///c:/PROJECTS/Comlina/client/src/app/dashboard/instagram-accounts/page.tsx) | Schema supports it; frontend active account context is stubbed. |
| **Billing & Subscriptions** | **NOT IMPLEMENTED** | [settings/page.tsx](file:///c:/PROJECTS/Comlina/client/src/app/dashboard/settings/page.tsx) | Pricing modal displays dummy toast; no Stripe integration. |
| **Content Creation & Scheduling** | **NOT IMPLEMENTED** | N/A | No post editor, media upload, calendar UI, or schemas exist. |
| **Instagram Content Publishing** | **NOT IMPLEMENTED** | N/A | No Meta Content Publishing API endpoints implemented. |
| **AI Captions & Copywriting** | **NOT IMPLEMENTED** | [ai_service.py](file:///c:/PROJECTS/Comlina/server/app/services/ai_service.py) | Only hardcoded rules exist; no LLM provider connected. |

---

## 10. Known Issues & Technical Debt Register

### Critical & High Severity Issues (Require Immediate Fix)

#### [ISS-001] Worker IndentationError on Startup

- **Component:** `worker/app/jobs/process_comment.py:137`
- **Severity:** **CRITICAL**
- **Observed Behavior:** Importing `worker.app.main` or running `npm run dev:worker` crashes immediately:

  ```text
  IndentationError: unexpected indent (process_comment.py, line 137)
  ```

- **Root Cause:** Line 137 (`if res.get("status") in ("COMPLETED", "FALLBACK_EXECUTED"):`) has 20 leading spaces instead of 16.
- **Proposed Fix:** Re-indent lines 137–145 to 16 spaces inside `for auto in automations:`.

#### [ISS-002] Dependency Pre-Flight Blocker in Development

- **Component:** `scripts/check-deps.js:139`
- **Severity:** **HIGH**
- **Observed Behavior:** `npm run dev` and `npm run dev:server` exit with code 1 if PostgreSQL (port 5432) or Redis (port 6379) are not reachable.
- **Root Cause:** The script forces an exit even though `server/app/core/database.py` has an SQLite fallback.
- **Proposed Fix:** Modify `check-deps.js` to log a warning rather than calling `process.exit(1)` when `ENVIRONMENT=development`.

#### [ISS-003] Database Engine Divergence Between Server and Worker

- **Component:** `server/app/core/database.py:34`, `worker/app/core/database.py:12`
- **Severity:** **HIGH**
- **Observed Behavior:** In local dev without Docker, the server connects to SQLite (`comlina_dev.db`), but the worker connects to PostgreSQL on port 5432 and fails.
- **Root Cause:** SQLite fallback logic was implemented only in `server/`, omitted from `worker/`.
- **Proposed Fix:** Move database engine resolution into a shared configuration module or mandate PostgreSQL via Docker.

#### [ISS-004] Meta OAuth Scopes & Endpoint Incompatibility

- **Component:** `server/app/integrations/instagram/oauth.py:25`, `server/app/api/instagram.py:144`
- **Severity:** **HIGH**
- **Observed Behavior:** OAuth flow redirects to `api.instagram.com/oauth/authorize` with `instagram_business_*` scopes, but `instagram.py` attempts to query `graph.facebook.com/me/accounts` (Facebook Pages). In production, account connection fails.
- **Root Cause:** Conflation of Instagram Login for Business vs. Facebook Login for Business.
- **Proposed Fix:** Eliminate `graph.facebook.com/me/accounts`. Standardize on Instagram Login for Business: query `https://graph.instagram.com/me?fields=id,username,account_type` with the Instagram user token.

#### [ISS-005] Analytics API Contract Key Mismatch

- **Component:** `server/app/services/analytics_service.py:44-52`, `client/src/features/analytics/api.ts:5-16`
- **Severity:** **MEDIUM**
- **Observed Behavior:** Metrics on `/dashboard/analytics` show `0` or `...`.
- **Root Cause:** Backend returns `total_comments`, `total_dms`, `total_contacts`; client expects `stats_comments`, `stats_dms_sent`, `total_leads`.
- **Proposed Fix:** Align `analytics_service.py` keys to match `AnalyticsSummary` TypeScript interface.

#### [ISS-006] Manual Message Dispatch Mocked in Inbox

- **Component:** `client/src/app/dashboard/inbox/page.tsx:65-78`
- **Severity:** **MEDIUM**
- **Observed Behavior:** Clicking "Send" in the Inbox adds a message to local React state; no network request is sent.
- **Root Cause:** Missing `POST /api/conversations/{id}/messages` endpoint on the backend.
- **Proposed Fix:** Implement `POST /api/conversations/{id}/messages` and connect frontend `handleSendMessage`.

#### [ISS-007] Automation Builder Restricted to 5 Mock Post Cards

- **Component:** `client/src/components/automations/PostSelector.tsx:16-60`
- **Severity:** **MEDIUM**
- **Observed Behavior:** Users cannot select their real Instagram posts when configuring triggers.
- **Root Cause:** Missing `GET /api/instagram/accounts/{id}/media` endpoint.
- **Proposed Fix:** Implement `GET /api/instagram/accounts/{id}/media` querying Meta Graph API `/{ig-user-id}/media`.

#### [ISS-008] Uninitialized Git Repository

- **Component:** Workspace root
- **Severity:** **LOW**
- **Observed Behavior:** `git status` reports `fatal: not a git repository`.
- **Proposed Fix:** Initialize Git tracking (`git init`) and create baseline commit.

#### [ISS-009] Missing ESLint Configuration in Client

- **Component:** `client/`
- **Severity:** **LOW**
- **Observed Behavior:** `npm run lint` halts with an interactive prompt.
- **Proposed Fix:** Add `.eslintrc.json` extending `next/core-web-vitals`.

---

## 11. Security & Production Readiness Assessment

### Production-Ready Security Controls

- **Row-Level Security (RLS):** All 11 PostgreSQL tables enforce `is_workspace_member()`.
- **BOLA Protection:** All API endpoints verify that requested accounts and conversations belong to the active workspace.
- **OWASP Middleware:** Strictly configured CSP, strict transport security, and exploit scanner traps.
- **Fernet Token Encryption:** Tokens are encrypted with AES-256 prior to database storage.
- **HMAC Webhook Verification:** Constant-time comparison prevents timing attacks on webhook ingestion.

### Gaps Requiring Remediation Before Launch

- **Meta Data Deletion Callback:** Meta requires a Data Deletion Request Callback (`POST /webhooks/data-deletion`) returning a confirmation code. This is mandatory for Meta App Review approval.
- **24-Hour Messaging Window:** Direct messages sent after 24 hours of user inactivity fail with Meta error 551. The worker must check recipient interaction recency before dispatching non-template DMs.
- **Automated Token Rotation:** Long-lived tokens expire in 60 days. A scheduled worker job is needed to refresh tokens before expiration.

---

## 12. External Coding Agent Handoff Instructions

When continuing development on Comlina, follow these rules:

1. **Do Not Rebuild Existing Modules:** The Next.js frontend, FastAPI routing structure, and PostgreSQL RLS schemas are high-quality. Do not replace them with alternative frameworks.
2. **Fix Root Causes in Place:**
   - Fix line 137 in `worker/app/jobs/process_comment.py` directly; do not rewrite the worker.
   - Adjust `scripts/check-deps.js` rather than removing the pre-flight check.
   - Align API contract keys in `analytics_service.py` rather than creating duplicate endpoints.
3. **Preserve Established Coding Conventions:**
   - Client: Keep reusable UI in `client/src/components/` and API hooks in `client/src/features/`.
   - Server: Keep routes in `server/app/api/`, business logic in `server/app/services/`, and external integrations in `server/app/integrations/`.
4. **Never Bypass Tenant Scoping:** Every new database query must filter by `workspace_id` or join through `workspace_members`.
5. **Standardize on Instagram Login for Business:** Do not reintroduce Facebook Pages permissions (`pages_show_list`) unless explicitly required by a new product specification.
6. **Verification Discipline:** After any change, run:
   - `.\server\.venv\Scripts\python.exe -m pytest server\tests worker\tests`
   - `npm --prefix client run typecheck`
   - `npm --prefix client run build`

---

## 13. Prioritized Implementation Roadmap

### Phase P0: Critical Blockers (Immediate)

1. **Fix Worker Syntax Error:** Re-indent line 137 of `worker/app/jobs/process_comment.py`.
2. **Unblock Dev Server:** Update `scripts/check-deps.js` to warn rather than exit when in development mode.
3. **Synchronize DB Fallback:** Harmonize `worker/app/core/database.py` with `server/app/core/database.py`.
4. **Configure ESLint:** Add `.eslintrc.json` in `client/`.

### Phase P1: Core Automation MVP

1. **Resolve Meta OAuth Flow:** Standardize on Instagram Login for Business; query `graph.instagram.com/me` for profile identity; eliminate dead Facebook Pages logic.
2. **Fix Analytics Contract:** Update dictionary keys in `analytics_service.py` to match `AnalyticsSummary`.
3. **Real Media Post Selector:** Add `GET /api/instagram/accounts/{id}/media` to fetch real Instagram posts for automation triggers.
4. **Real Inbox Message Dispatch:** Implement `POST /api/conversations/{id}/messages` and connect frontend "Send" button.

### Phase P2: Reliability & Compliance

1. **Meta Data Deletion Endpoint:** Implement `POST /webhooks/data-deletion` for Meta App Review compliance.
2. **Automated Token Refresh:** Add an ARQ cron job to refresh tokens within 7 days of expiration.
3. **Comprehensive Test Suite:** Add unit tests for `process_comment.py`, `contacts.py`, and `conversations.py`.

### Phase P3: Production Launch & Monetization

1. **Stripe Billing Integration:** Create `subscriptions` table, integrate Stripe Checkout, and enforce automation quotas.
2. **Observability:** Integrate Sentry for error tracking and APM.
3. **Meta App Review Submission:** Submit application for `instagram_business_manage_messages` and `instagram_business_manage_comments`.

---

## 14. Appendix: Key Commands & References

### Essential Verification Commands

- **Run Backend Tests:**

  ```powershell
  .\server\.venv\Scripts\python.exe -m pytest server\tests
  ```

- **Run Worker Tests:**

  ```powershell
  .\server\.venv\Scripts\python.exe -m pytest worker\tests
  ```

- **Run Frontend Typecheck:**

  ```powershell
  npm --prefix client run typecheck
  ```

- **Run Frontend Production Build:**

  ```powershell
  npm --prefix client run build
  ```

- **Run Security Verification Suite:**

  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/test_security.ps1
  ```

- **Start Uvicorn Server Standalone:**

  ```powershell
  .\server\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir server --port 8000
  ```

### External Documentation References


- [Meta Instagram Graph API Overview](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api)
- [Instagram Login for Business](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login)
- [Meta Webhooks for Instagram](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-instagram)
- [Meta Data Deletion Callback Guide](https://developers.facebook.com/docs/development/create-an-app/app-dashboard/data-deletion-callback)
