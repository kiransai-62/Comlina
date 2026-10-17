# Comlina Production Deployment & Architecture Guide

This document describes the complete production deployment architecture for Comlina:
* **Frontend**: Next.js deployed on Vercel or Docker standalone container.
* **Backend**: FastAPI ASGI deployed using Gunicorn with multiple Uvicorn workers on robust cloud infrastructure.
* **Worker**: Dedicated ARQ background automation worker container.
* **Database**: Managed PostgreSQL (Supabase, AWS RDS, GCP Cloud SQL) with SSL and connection pooling.
* **Redis**: Upstash Redis (over TLS) or AWS ElastiCache.
* **Reverse Proxy & SSL**: Nginx with TLS 1.3, HSTS, security headers, rate limiting, and Certbot auto-renewal.
* **Secrets Management**: Secure environment variable handling across cloud providers.

---

## 1. Production Architecture Diagram

```
                                      [ Internet Clients & Meta Webhooks ]
                                                        │
                         ┌──────────────────────────────┴──────────────────────────────┐
                         │                                                             │
                  (HTTPS Port 443)                                              (HTTPS Port 443)
                         ▼                                                             ▼
         ┌───────────────────────────────┐                             ┌───────────────────────────────┐
         │       Vercel Edge CDN         │                             │     Nginx Reverse Proxy       │
         │  (Comlina Next.js Frontend)   │                             │  (TLS 1.3 / HSTS / Rate Limit)│
         │       app.comlina.ai          │                             │        api.comlina.ai         │
         └───────────────┬───────────────┘                             └───────────────┬───────────────┘
                         │                                                             │
                         │ API Requests                                                │ Upstream (Port 8000)
                         └──────────────────────────────┬──────────────────────────────┘
                                                        ▼
                                       ┌───────────────────────────────────┐
                                       │   FastAPI ASGI Server Cluster     │
                                       │   Gunicorn + 4 Uvicorn Workers    │
                                       │       (server/gunicorn.conf.py)   │
                                       └───────────────┬───────────────────┘
                                                       │
                           ┌───────────────────────────┴───────────────────────────┐
                           │ Enqueue Jobs                                          │ SQL Queries (SSL)
                           ▼                                                       ▼
        ┌───────────────────────────────────┐                   ┌───────────────────────────────────┐
        │        Redis Queue & Cache        │                   │     Managed PostgreSQL 16+        │
        │   (Upstash TLS / ElastiCache)     │                   │  (Supabase / AWS RDS / Cloud SQL) │
        └──────────────────┬────────────────┘                   └──────────────────┬────────────────┘
                           │ Pull Jobs                                             │
                           ▼                                                       │
        ┌───────────────────────────────────┐                                      │
        │     ARQ Automation Worker         │◄─────────────────────────────────────┘
        │   (worker/app/main.py)            │
        └───────────────────────────────────┘
```

---

## 2. Dockerization of Application Components

All components are containerized with production-ready multi-stage Dockerfiles:

### A. Next.js Client ([`infra/docker/client.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/client.Dockerfile) & [`client/Dockerfile`](file:///c:/PROJECTS/Comlina/client/Dockerfile))
* **Multi-stage build**: `deps` -> `builder` -> `runner`.
* **Output Standalone**: Bundles only production dependencies and static files (`.next/standalone`), reducing image size to ~150MB.
* **Non-root**: Runs as `nextjs:nodejs` user (UID 1001).
* **Healthcheck**: HTTP check on `http://127.0.0.1:3000/`.

### B. FastAPI Server ([`infra/docker/server.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/server.Dockerfile) & [`server/Dockerfile`](file:///c:/PROJECTS/Comlina/server/Dockerfile))
* **Multi-Worker ASGI**: Runs Gunicorn with `uvicorn.workers.UvicornWorker` managed by [`server/gunicorn.conf.py`](file:///c:/PROJECTS/Comlina/server/gunicorn.conf.py).
* **Dynamic Concurrency**: Defaults to `(2 x vCPU) + 1` or configured `WEB_CONCURRENCY=4`.
* **Process Recycling**: Automatically restarts workers after 2,000 requests (`max_requests`) to prevent memory leaks.
* **Graceful Termination**: 30-second shutdown timeout (`graceful_timeout`) ensuring in-flight requests finish cleanly.
* **Non-root**: Runs as `appuser` (UID 1000).
* **Healthcheck**: Targets `http://127.0.0.1:8000/health`.

### C. ARQ Background Worker ([`infra/docker/worker.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/worker.Dockerfile) & [`worker/Dockerfile`](file:///c:/PROJECTS/Comlina/worker/Dockerfile))
* **Execution**: Runs `arq app.main.WorkerSettings`.
* **Dedicated runtime**: Processes comment events, condition evaluation, and Instagram DM dispatch without blocking HTTP request threads.

### D. Reverse Proxy ([`infra/docker/nginx.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/nginx.Dockerfile) & [`infra/nginx/nginx.conf`](file:///c:/PROJECTS/Comlina/infra/nginx/nginx.conf))
* **TLS 1.3 / HTTP/2 Termination**: Modern cryptographic suites.
* **ACME Webroot & Certbot Integration**: Automatic renewal every 12 hours.
* **Bootstrap Script**: [`infra/nginx/entrypoint.sh`](file:///c:/PROJECTS/Comlina/infra/nginx/entrypoint.sh) generates temporary self-signed certificates on initial boot so Nginx starts without errors while waiting for domain DNS propagation.
* **Rate Limiting**:
  * Webhook burst limit: 100 requests/sec with burst buffer of 200.
  * API limit: 50 requests/sec with burst buffer of 100.
  * Auth brute-force protection: 10 requests/min.

---

## 3. Backend Cloud Deployment Options

You can deploy the backend using any of the following robust cloud services:

### Option 1: AWS ECS / Fargate (Containerized Serverless)
1. Push images to AWS ECR:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
   docker tag comlina-server:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/comlina-server:latest
   docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/comlina-server:latest
   ```
2. Create an ECS Task Definition with 1 vCPU and 2GB RAM.
3. Attach an AWS Application Load Balancer (ALB) with an AWS Certificate Manager (ACM) SSL certificate for `api.comlina.ai`.
4. Point environment variables to AWS Secrets Manager.

### Option 2: Google Cloud Run (Fully Managed Serverless Container)
1. Build and push image via Google Cloud Build:
   ```bash
   gcloud builds submit --tag gcr.io/[PROJECT_ID]/comlina-server ./server
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy comlina-server \
     --image gcr.io/[PROJECT_ID]/comlina-server \
     --platform managed \
     --region us-central1 \
     --concurrency 80 \
     --min-instances 1 \
     --max-instances 10 \
     --set-env-vars ENVIRONMENT=production,WEB_CONCURRENCY=4 \
     --set-secrets DATABASE_URL=comlina-db-url:latest,REDIS_URL=comlina-redis-url:latest
   ```
3. Map custom domain `api.comlina.ai` with Google-managed SSL.

### Option 3: Render / Fly.io / DigitalOcean App Platform
1. Connect repository branch.
2. Set Root Directory to `server`.
3. Build Command: `pip install -r requirements.txt && pip install gunicorn==23.0.0`
4. Start Command: `gunicorn -c gunicorn.conf.py app.main:app`
5. Add production environment variables in the platform dashboard.

### Option 4: Multi-Container Docker Compose on Linux Cloud VM
Deploy the complete stack using [`docker-compose.prod.yml`](file:///c:/PROJECTS/Comlina/docker-compose.prod.yml):
```bash
# 1. Clone repository on VM
git clone https://github.com/your-org/comlina.git /opt/comlina
cd /opt/comlina

# 2. Configure production secrets
cp .env.production.example .env

# 3. Launch stack
docker-compose -f docker-compose.prod.yml up --build -d

# 4. Issue official Let's Encrypt certificates
docker exec comlina-certbot certbot certonly --webroot -w /var/www/certbot \
  -d api.comlina.ai -d app.comlina.ai \
  --email admin@comlina.ai --agree-tos --no-eff-email

# 5. Reload Nginx
docker exec comlina-nginx nginx -s reload
```

---

## 4. Secure Environment Variables & Secrets Management

Comlina enforces strict runtime validation when `ENVIRONMENT=production` in [`server/app/core/config.py`](file:///c:/PROJECTS/Comlina/server/app/core/config.py):
* `TOKEN_ENCRYPTION_KEY`: Must be a valid 32-byte URL-safe base64 string.
* `SUPABASE_JWT_SECRET`: Rejects mock or default keys.
* `META_APP_SECRET`: Rejects placeholder strings.
* `META_WEBHOOK_VERIFY_TOKEN`: Requires high-entropy secret.
* `CORS_ORIGINS`: Prohibits wildcard `*` when credentials are enabled.

### Secret Manager Integration Examples

#### AWS Secrets Manager
Store all environment variables as a JSON secret:
```json
{
  "DATABASE_URL": "postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require",
  "REDIS_URL": "rediss://default:[TOKEN]@[HOST].upstash.io:6379",
  "TOKEN_ENCRYPTION_KEY": "[32-BYTE-BASE64-KEY]",
  "SUPABASE_JWT_SECRET": "[SUPABASE-JWT-SECRET]",
  "META_APP_SECRET": "[META-APP-SECRET]",
  "META_WEBHOOK_VERIFY_TOKEN": "[VERIFY-TOKEN]"
}
```
Inject directly into ECS tasks via `secrets` array in the task definition.

#### Google Cloud Secret Manager
```bash
gcloud secrets create comlina-db-url --data-file=- <<< "postgresql+asyncpg://..."
gcloud secrets add-iam-policy-binding comlina-db-url \
    --member="serviceAccount:comlina-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## 5. Summary of Created Production Assets

| Asset | Location | Purpose |
| :--- | :--- | :--- |
| **Gunicorn ASGI Config** | [`server/gunicorn.conf.py`](file:///c:/PROJECTS/Comlina/server/gunicorn.conf.py) | Multi-worker process manager with UvicornWorker, recycling, timeouts. |
| **Server Entrypoint** | [`server/entrypoint.sh`](file:///c:/PROJECTS/Comlina/server/entrypoint.sh) | Auto-migration runner and multi-worker ASGI startup. |
| **Server Dockerfile** | [`infra/docker/server.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/server.Dockerfile) | Hardened Python 3.11 container with Gunicorn and healthcheck. |
| **Client Dockerfile** | [`infra/docker/client.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/client.Dockerfile) | Multi-stage Next.js standalone container (~150MB). |
| **Worker Dockerfile** | [`infra/docker/worker.Dockerfile`](file:///c:/PROJECTS/Comlina/infra/docker/worker.Dockerfile) | Lean ARQ worker container with signal handling. |
| **Nginx Reverse Proxy** | [`infra/nginx/nginx.conf`](file:///c:/PROJECTS/Comlina/infra/nginx/nginx.conf) | TLS 1.3, HSTS, security headers, rate limiting. |
| **Nginx Bootstrap** | [`infra/nginx/entrypoint.sh`](file:///c:/PROJECTS/Comlina/infra/nginx/entrypoint.sh) | Self-signed certificate bootstrap for initial boot. |
| **Prod Docker Compose** | [`docker-compose.prod.yml`](file:///c:/PROJECTS/Comlina/docker-compose.prod.yml) | Multi-container stack with network isolation and Certbot. |
| **Vercel Frontend Config** | [`client/vercel.json`](file:///c:/PROJECTS/Comlina/client/vercel.json) & [`vercel.json`](file:///c:/PROJECTS/Comlina/vercel.json) | Zero-config Next.js deployment with security headers. |
| **Database Migration Guide** | [`docs/DATABASE_MIGRATION_GUIDE.md`](file:///c:/PROJECTS/Comlina/docs/DATABASE_MIGRATION_GUIDE.md) | Supabase/RDS migration steps, connection pooling, SSL. |
| **Vercel Guide** | [`docs/VERCEL_DEPLOYMENT_GUIDE.md`](file:///c:/PROJECTS/Comlina/docs/VERCEL_DEPLOYMENT_GUIDE.md) | Step-by-step Vercel frontend deployment and OAuth redirect setup. |
| **Production Env Template** | [`.env.production.example`](file:///c:/PROJECTS/Comlina/.env.production.example) | Production environment variable blueprint with security docs. |
