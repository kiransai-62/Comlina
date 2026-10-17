# Meta Instagram Webhook Integration

## 1. Webhook Handshake (GET /webhooks/instagram)

Meta validates your webhook endpoint by sending a GET request with query parameters:

- `hub.mode`: `"subscribe"`
- `hub.challenge`: A random challenge integer/string.
- `hub.verify_token`: Must match `META_WEBHOOK_VERIFY_TOKEN`.

Comlina verifies `hub.verify_token` against configuration and echoes back `hub.challenge` with `Content-Type: text/plain` and HTTP 200 OK.

## 2. Ingestion & HMAC Verification (POST /webhooks/instagram)

Meta signs every webhook request using HMAC-SHA256 with your `META_APP_SECRET`:

```http
X-Hub-Signature-256: sha256=<computed_hash>
```

The FastAPI endpoint executes:

1. `hmac.compare_digest(expected_hash, computed_hash)`.
2. Validates JSON payload.
3. Performs atomic insert into `webhook_events`:

   ```sql
   INSERT INTO webhook_events (provider_event_id, event_type, payload, status)
   VALUES (:provider_event_id, :event_type, :payload, 'PENDING')
   ON CONFLICT (provider_event_id) DO NOTHING;
   ```

4. If inserted, enqueues the job into Redis via ARQ:

   ```python
   await arq_redis.enqueue_job("process_webhook_event", event_id, event_data)
   ```

5. Returns HTTP 200 OK immediately (< 100ms).

## 3. Worker Processing (ARQ Worker)

The worker process receives the job and dispatches it through `FlowEngine`:

- **Comment Trigger**: Reads comment text, checks keyword matches.
- **Follower Gate**: Evaluates `FollowerStatus` (`FOLLOWING`, `NOT_FOLLOWING`, `UNKNOWN`, `CHECK_UNAVAILABLE`).
- **Actions**: Calls Meta Graph API (`POST /{comment-id}/replies` or `POST /me/messages`).
