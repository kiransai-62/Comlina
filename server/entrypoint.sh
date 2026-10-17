#!/bin/sh
set -e

# Run database migrations if RUN_MIGRATIONS is set to true
if [ "$RUN_MIGRATIONS" = "true" ] || [ "$RUN_MIGRATIONS" = "1" ]; then
    echo "[INFO] Running database migrations before server startup..."
    python ../scripts/migrate.py || python scripts/migrate.py || echo "[WARN] Migration script returned non-zero code."
fi

# Multi-worker ASGI startup
# If Gunicorn is available and USE_GUNICORN is not explicitly false, use Gunicorn with UvicornWorker
if [ "$USE_GUNICORN" != "false" ] && command -v gunicorn >/dev/null 2>&1; then
    echo "[INFO] Starting FastAPI with Gunicorn (multiple Uvicorn ASGI workers)..."
    exec gunicorn -c gunicorn.conf.py app.main:app
else
    WORKERS=${WEB_CONCURRENCY:-${WORKERS:-4}}
    PORT=${PORT:-8000}
    echo "[INFO] Starting FastAPI with Uvicorn ($WORKERS workers on port $PORT)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
fi
