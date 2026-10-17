# Comlina Production Database Migration Guide

This guide details how to migrate the Comlina database from local development (SQLite / local Docker PostgreSQL) to a production-grade managed database service, configure SSL/TLS encryption, connection pooling, and verify table schema integrity.

---

## 1. Supported Managed Database Services

Comlina uses SQLAlchemy 2.0 with asynchronous `asyncpg` drivers and dialect-agnostic models. Any modern PostgreSQL 14+ managed service is supported:

| Managed Service | Recommended Tier | SSL Mode | Notes |
| :--- | :--- | :--- | :--- |
| **Supabase** | Pro ($25/mo) | `require` | **Recommended**. Built-in pairing with Comlina's Supabase Auth & Storage. |
| **AWS RDS PostgreSQL** | `db.t4g.small` or higher | `require` | Ideal for AWS ECS / EKS backend deployments. Multi-AZ supported. |
| **GCP Cloud SQL** | 2 vCPU, 4GB RAM+ | `require` | Ideal for GCP Cloud Run or GKE deployments. |
| **Neon** | Launch / Scale | `require` | Serverless Postgres with instant branching. |

---

## 2. Connection String Formatting

Comlina uses the asynchronous driver prefix `postgresql+asyncpg://`.

### A. Supabase
Supabase provides two connection types in **Project Settings -> Database**:
1. **Transaction Connection Pooler (Port 6543) — Recommended for High Concurrency**:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres.vrfwgoigtmixkkunvrnw:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
   ```
2. **Session / Direct Connection (Port 5432)**:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.vrfwgoigtmixkkunvrnw.supabase.co:5432/postgres?sslmode=require
   ```

> [!IMPORTANT]
> Comlina's database engine in `server/app/core/database.py` automatically handles SSL parameters and query parameter sanitization for `asyncpg`. You can safely include `?sslmode=require`.

### B. AWS RDS PostgreSQL
```env
DATABASE_URL=postgresql+asyncpg://comlina_admin:[YOUR-PASSWORD]@comlina-prod.c3x9y8z.us-east-1.rds.amazonaws.com:5432/comlina?sslmode=require
```

### C. GCP Cloud SQL
```env
DATABASE_URL=postgresql+asyncpg://comlina_user:[YOUR-PASSWORD]@10.0.0.3:5432/comlina?sslmode=require
```

---

## 3. Applying Migrations to Managed Database

Comlina includes an automated, idempotent migration runner in [`scripts/migrate.py`](file:///c:/PROJECTS/Comlina/scripts/migrate.py). It applies all 11 migration files in order and tracks applied versions in the `schema_migrations` table.

### Method 1: Using the Migration CLI
Run the migration runner against your managed database:

```bash
# Using npm with explicit database URL
npm run migrate -- --url="postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require"

# Or using Python directly
node scripts/run-python.js scripts/migrate.py --url="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require"
```

### Method 2: Setting DATABASE_URL in Environment
Set `DATABASE_URL` in your production environment (or `.env`):
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require"
npm run migrate
```

### Method 3: Automated Migration on Container Startup
In [`docker-compose.prod.yml`](file:///c:/PROJECTS/Comlina/docker-compose.prod.yml) or your container entrypoint, set:
```env
RUN_MIGRATIONS=true
```
When `server/entrypoint.sh` starts, it automatically executes pending migrations before binding the ASGI workers.

---

## 4. Applied Schema Inventory

The migration runner applies the following 11 database migration files:

| Order | Migration File | Description | Core Tables / Features |
| :---: | :--- | :--- | :--- |
| **001** | `001_users.sql` | User accounts & credentials | `users` table, password hashing |
| **002** | `002_workspaces.sql` | Multi-tenant organization | `workspaces`, `workspace_members` |
| **003** | `003_instagram_accounts.sql` | Meta Graph API tokens | `instagram_accounts`, AES encryption |
| **004** | `004_automations.sql` | Visual flow builder storage | `automations` table, status, triggers |
| **005** | `005_automation_versions.sql` | Flow versioning & rollback | `automation_versions`, JSON graph |
| **006** | `006_contacts.sql` | Customer CRM & followers | `contacts`, Instagram usernames |
| **007** | `007_conversations.sql` | Direct message thread state | `conversations`, participant IDs |
| **008** | `008_messages.sql` | Message exchange history | `messages`, delivery statuses |
| **009** | `009_webhook_events.sql` | Meta webhook idempotency | `webhook_events`, event deduplication |
| **010** | `010_analytics.sql` | Real-time conversion metrics | `analytics_events`, KPI rollups |
| **011** | `011_row_level_security.sql` | Multi-tenant security | PostgreSQL Row Level Security (RLS) |

---

## 5. Production Connection Pooling Configuration

When running multiple backend workers and background task runners, configure connection pooling parameters in `.env`:

```env
# Permanent pool size per worker process
DB_POOL_SIZE=10

# Max burst overflow connections
DB_MAX_OVERFLOW=20

# Connection timeout in seconds
DB_POOL_TIMEOUT=30

# Recycle connections every 30 minutes (prevents cloud NAT / firewall drops)
DB_POOL_RECYCLE=1800

# Force SSL encryption in transit
DB_SSL=true
```

With 4 Gunicorn workers (`WEB_CONCURRENCY=4`), total active database connections will stay capped at `4 x (10 + 20) = 120` connections, well within Supabase and RDS limits.

---

## 6. Verification Checklist

After running migrations, verify that the managed database is healthy:

1. **Table Count**: Check that 11 application tables and 1 migration table (`schema_migrations`) exist:
   ```sql
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
   ```
2. **Migration History**: Verify that all 11 migrations are marked as applied:
   ```sql
   SELECT version, applied_at FROM schema_migrations ORDER BY applied_at ASC;
   ```
3. **Backend Health Check**:
   Query the FastAPI backend:
   ```bash
   curl -s https://api.comlina.ai/health
   # Expected: {"status":"healthy","service":"comlina-api","version":"1.0.0"}
   ```
