FROM python:3.12-alpine

LABEL maintainer="AdShield Project"
LABEL description="AdShield High-Performance Private DNS Server (DoT/DoH/UDP)"

WORKDIR /opt/adshield

# Install runtime tools
RUN apk add --no-cache ca-certificates tzdata

# Copy application files
COPY adshield_server.py filter_engine.py cache.py ./
COPY static/ ./static/
COPY blocklists/ ./blocklists/
COPY config.json ./

# Ports:
# 53/udp & 53/tcp: Standard DNS
# 853/tcp: DNS-over-TLS (Android Private DNS)
# 443/tcp: DNS-over-HTTPS (DoH)
# 8080/tcp: Web Dashboard & Management API
EXPOSE 53/udp 53/tcp 853/tcp 443/tcp 8080/tcp

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD nc -z 127.0.0.1 8080 || exit 1

ENTRYPOINT ["python3", "adshield_server.py"]

