# server/gunicorn.conf.py
"""
Production Gunicorn Configuration for Comlina FastAPI ASGI Application.
Runs multiple Uvicorn worker processes with dynamic CPU-based concurrency,
connection recycling, graceful shutdown timeouts, and structured logging.
"""

import os
import multiprocessing

# 1. Server Socket Binding
port = os.getenv("PORT", "8000")
host = os.getenv("HOST", "0.0.0.0")
bind = os.getenv("BIND", f"{host}:{port}")
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# 2. Worker Concurrency
# Formula: (2 x cores) + 1 or explicit WEB_CONCURRENCY environment variable
web_concurrency = os.getenv("WEB_CONCURRENCY") or os.getenv("WORKERS")
if web_concurrency:
    workers = int(web_concurrency)
else:
    cores = multiprocessing.cpu_count()
    default_workers = (cores * 2) + 1
    # Cloud container safeguard: minimum 2 workers, maximum 8 by default
    min_workers = int(os.getenv("MIN_WORKERS", "2"))
    max_workers = int(os.getenv("MAX_WORKERS", "8"))
    workers = max(min_workers, min(default_workers, max_workers))

worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))

# 3. Timeouts & Keep-Alive
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# 4. Worker Recycling (Prevents memory accumulation over extended runtimes)
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "2000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "200"))

# 5. Security & Isolation
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 6. Logging
accesslog = os.getenv("ACCESS_LOG", "-")
errorlog = os.getenv("ERROR_LOG", "-")
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s µs'

# 7. Process Naming
proc_name = "comlina-fastapi"

def on_starting(server):
    server.log.info("Starting Comlina FastAPI with %d Uvicorn ASGI workers on %s", workers, bind)

def worker_int(worker):
    worker.log.info("Worker received SIGINT/SIGQUIT — performing graceful shutdown (pid: %d)", worker.pid)

def worker_abort(worker):
    worker.log.error("Worker received SIGABRT — worker aborting (pid: %d)", worker.pid)
