# ==========================================
# FastAPI Production Dockerfile
# Multi-worker ASGI deployment (Gunicorn + Uvicorn)
# ==========================================

FROM python:3.11.9-slim-bookworm

WORKDIR /app

# Install security updates and minimal build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies + gunicorn for multi-worker process management
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

# Copy application source
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x entrypoint.sh 2>/dev/null || true

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').getcode() == 200 else 1)"

ENTRYPOINT ["./entrypoint.sh"]
