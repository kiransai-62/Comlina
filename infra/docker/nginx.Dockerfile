# ==========================================
# Nginx Reverse Proxy Production Dockerfile
# With OpenSSL SSL bootstrap and Certbot support
# ==========================================

FROM nginx:1.25.5-alpine

RUN apk add --no-cache openssl inotify-tools

COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
COPY infra/nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
