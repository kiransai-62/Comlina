# Comlina Architecture Documentation

## High-Level System Architecture

```text
                         ┌───────────────────┐
                         │      COMLINA      │
                         │      CLIENT       │
                         │ Next.js (App)     │
                         └─────────┬─────────┘
                                   │ HTTPS / REST (X-Workspace-ID)
                                   ▼
                         ┌───────────────────┐
                         │     FASTAPI       │
                         │       API         │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼───────────────────┐
              │                    │                   │
              ▼                    ▼                   ▼
        ┌───────────┐       ┌────────────┐      ┌─────────────┐
        │PostgreSQL │       │   Redis    │      │    Meta     │
        │ /Supabase │       │   Queue    │      │  Graph API  │
        │(Multi-Ten)│       └─────┬──────┘      └─────────────┘
        └───────────┘             │
                                  ▼
                           ┌──────────────┐
                           │  ARQ WORKER  │
                           │              │
                           │ Trigger      │
                           │ Condition    │
                           │ Action       │
                           │ Flow         │
                           └──────┬───────┘
                                  │ Outbound API Calls
                                  ▼
                            Instagram API
```

## Architectural Tenets

1. **Client Never Communicates with Meta Directly**:
   All Meta Graph API credentials and secret tokens are guarded by the backend. The client only calls `api.comlina.ai`.

2. **Durable Webhook Idempotency**:
   The webhook endpoint persists event headers and payloads to `webhook_events` with `UNIQUE(provider_event_id)` before queueing to Redis. Duplicates delivered by Meta are dropped safely at the DB boundary.

3. **Multi-Tenancy at Every Layer**:
   Every database query filters by `workspace_id`. Authentication via Supabase Auth JWT is decoded to verify the user's permitted workspace memberships before any resource is accessed.

4. **Pure Trigger → Condition → Action Automation Engine**:
   The automation engine executes independently of AI. Flow definitions are stored as JSONB with snapshot versioning (`automation_versions`).
