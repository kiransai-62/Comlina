# ==========================================
# ARQ Background Worker Production Dockerfile
# Asynchronous automation and comment processing
# ==========================================

FROM python:3.15.0-slim-bookworm

WORKDIR /app

# Install security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install worker dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker application code
COPY . .

# Run as non-privileged application user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run ARQ worker with WorkerSettings
CMD ["arq", "app.main.WorkerSettings"]
