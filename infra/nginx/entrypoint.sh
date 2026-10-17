#!/bin/sh
set -e

CERT_DIR="/etc/letsencrypt/live/comlina.ai"

# Ensure certificate directory exists
mkdir -p "$CERT_DIR"

# Generate fallback self-signed certificates if none exist to allow Nginx to start
if [ ! -f "$CERT_DIR/fullchain.pem" ] || [ ! -f "$CERT_DIR/privkey.pem" ]; then
    echo "[INFO] No existing SSL certificate found. Generating self-signed bootstrap certificate for comlina.ai..."
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
        -keyout "$CERT_DIR/privkey.pem" \
        -out "$CERT_DIR/fullchain.pem" \
        -subj "/CN=comlina.ai/O=Comlina/C=US" \
        2>/dev/null || echo "[WARN] OpenSSL bootstrap skipped or already present."
fi

# Ensure certbot webroot exists
mkdir -p /var/www/certbot

echo "[INFO] Testing Nginx configuration..."
nginx -t

echo "[INFO] Starting Nginx reverse proxy..."
exec nginx -g "daemon off;"
