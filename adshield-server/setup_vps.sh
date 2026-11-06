#!/usr/bin/env bash
# ==============================================================================
# AdShield VPS Installer & Private DNS Host Setup
# Sets up DNS-over-TLS (DoT, Port 853) with free Let's Encrypt SSL
# Compatible with Android Private DNS, iOS, Windows, and Linux
# ==============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "================================================================="
echo "        🛡️  AdShield High-Performance Private DNS Server         "
echo "              1-Click Linux VPS Deployment Installer             "
echo "================================================================="
echo -e "${NC}"

# 1. Root check
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] This installer must be run as root (or with sudo).${NC}"
   exit 1
fi

INSTALL_DIR="/opt/adshield"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect public IP
DETECTED_IP=$(curl -4 -s --max-time 5 https://api.ipify.org || curl -4 -s --max-time 5 https://ifconfig.me || echo "unknown")
echo -e "${GREEN}[INFO] Detected Server Public IPv4:${NC} ${BOLD}${DETECTED_IP}${NC}\n"

# 2. Prompt for Domain Name
echo -e "${YELLOW}${BOLD}Android 'Private DNS' requires a domain name with a valid TLS certificate.${NC}"
echo -e "Example: ${CYAN}dns.yourdomain.com${NC} or ${CYAN}adblock.example.org${NC}"
echo -e "Make sure you added an DNS 'A' record pointing your domain to this VPS IP: ${BOLD}${DETECTED_IP}${NC}\n"

read -rp "Enter your Domain / Hostname for Private DNS: " DOMAIN_NAME
DOMAIN_NAME=$(echo "$DOMAIN_NAME" | tr -d '[:space:]' | tr '[:upper:]' | tr '[:lower:]')

if [[ -z "$DOMAIN_NAME" ]]; then
    echo -e "${RED}[ERROR] Domain name cannot be empty.${NC}"
    exit 1
fi

read -rp "Enter your Email (for Let's Encrypt certificate renewal alerts): " USER_EMAIL
if [[ -z "$USER_EMAIL" ]]; then
    USER_EMAIL="admin@${DOMAIN_NAME}"
fi

echo -e "\n${CYAN}[1/6] Installing necessary packages...${NC}"

# Detect Package Manager
if command -v apt-get &>/dev/null; then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-pip certbot curl ufw git
elif command -v dnf &>/dev/null; then
    dnf install -y -q python3 python3-pip certbot curl firewalld git
elif command -v yum &>/dev/null; then
    yum install -y -q epel-release || true
    yum install -y -q python3 python3-pip certbot curl firewalld git
elif command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm python certbot curl ufw git
else
    echo -e "${YELLOW}[WARN] Unknown package manager. Ensure python3 and certbot are installed.${NC}"
fi

# 3. Resolve port 53 conflict on Ubuntu/Debian (systemd-resolved)
echo -e "\n${CYAN}[2/6] Configuring port 53 DNS stub listener...${NC}"
if systemctl is-active --quiet systemd-resolved; then
    if grep -q "^#\?DNSStubListener=yes" /etc/systemd/resolved.conf || ! grep -q "DNSStubListener=no" /etc/systemd/resolved.conf; then
        echo -e "${YELLOW}[INFO] Disabling systemd-resolved DNSStubListener to free port 53...${NC}"
        sed -i 's/^#\?DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf || echo "DNSStubListener=no" >> /etc/systemd/resolved.conf
        systemctl restart systemd-resolved || true
    fi
fi

# 4. Obtain Let's Encrypt SSL/TLS Certificate
echo -e "\n${CYAN}[3/6] Obtaining free TLS Certificate from Let's Encrypt for ${DOMAIN_NAME}...${NC}"

CERT_PATH="/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem"

# Stop anything temporarily on port 80 for standalone verification
systemctl stop nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true

certbot certonly --standalone \
    -d "${DOMAIN_NAME}" \
    --non-interactive \
    --agree-tos \
    -m "${USER_EMAIL}" \
    --preferred-challenges http || {
    echo -e "\n${YELLOW}[WARN] Certbot automatic issuance failed! Check that your DNS A record points to ${DETECTED_IP}.${NC}"
    echo -e "${YELLOW}Falling back to generating a self-signed TLS certificate for testing...${NC}"
    mkdir -p "/etc/letsencrypt/live/${DOMAIN_NAME}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${KEY_PATH}" \
        -out "${CERT_PATH}" \
        -subj "/CN=${DOMAIN_NAME}"
}

# 5. Copy files to /opt/adshield
echo -e "\n${CYAN}[4/6] Installing AdShield files to ${INSTALL_DIR}...${NC}"
mkdir -p "${INSTALL_DIR}/blocklists" "${INSTALL_DIR}/static"

cp -r "${SOURCE_DIR}/adshield_server.py" "${INSTALL_DIR}/"
cp -r "${SOURCE_DIR}/filter_engine.py" "${INSTALL_DIR}/"
cp -r "${SOURCE_DIR}/cache.py" "${INSTALL_DIR}/"
cp -r "${SOURCE_DIR}/static/"* "${INSTALL_DIR}/static/"
cp -r "${SOURCE_DIR}/blocklists/"* "${INSTALL_DIR}/blocklists/" 2>/dev/null || true

# Generate Config
cat > "${INSTALL_DIR}/config.json" <<EOF
{
  "server_hostname": "${DOMAIN_NAME}",
  "upstream_provider": "cloudflare",
  "custom_upstream": [],
  "udp_port": 53,
  "tcp_port": 53,
  "dot_port": 853,
  "doh_port": 443,
  "web_port": 8080,
  "tls_cert_file": "${CERT_PATH}",
  "tls_key_file": "${KEY_PATH}",
  "enable_tls": true,
  "log_history_limit": 500,
  "ad_blocking": true,
  "youtube_shield": true,
  "spotify_shield": true,
  "hotstar_shield": true
}
EOF

# Setup Auto-Renewal Hook for Let's Encrypt
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/adshield-reload.sh <<'EOF'
#!/bin/sh
systemctl restart adshield.service
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/adshield-reload.sh

# 6. Configure Firewall
echo -e "\n${CYAN}[5/6] Configuring Firewall (Ports 53, 853, 443, 8080, 80)...${NC}"
if command -v ufw &>/dev/null && ufw status | grep -q "Status: active"; then
    ufw allow 53/udp comment 'AdShield DNS UDP' >/dev/null
    ufw allow 53/tcp comment 'AdShield DNS TCP' >/dev/null
    ufw allow 853/tcp comment 'AdShield DoT Private DNS' >/dev/null
    ufw allow 443/tcp comment 'AdShield DoH' >/dev/null
    ufw allow 8080/tcp comment 'AdShield Dashboard' >/dev/null
    ufw allow 80/tcp comment 'Certbot ACME challenge' >/dev/null
elif command -v firewall-cmd &>/dev/null && systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-port=53/udp >/dev/null
    firewall-cmd --permanent --add-port=53/tcp >/dev/null
    firewall-cmd --permanent --add-port=853/tcp >/dev/null
    firewall-cmd --permanent --add-port=443/tcp >/dev/null
    firewall-cmd --permanent --add-port=8080/tcp >/dev/null
    firewall-cmd --permanent --add-port=80/tcp >/dev/null
    firewall-cmd --reload >/dev/null
fi

# 7. Install and start Systemd Service
echo -e "\n${CYAN}[6/6] Registering and launching AdShield systemd service...${NC}"
cp "${SOURCE_DIR}/adshield.service" /etc/systemd/system/adshield.service
systemctl daemon-reload
systemctl enable adshield.service
systemctl restart adshield.service

sleep 2

# Verify running
if systemctl is-active --quiet adshield.service; then
    echo -e "${GREEN}${BOLD}✔ AdShield service is RUNNING!${NC}\n"
else
    echo -e "${RED}[ERROR] AdShield service failed to start. View logs with: journalctl -u adshield -e${NC}"
fi

echo -e "${GREEN}${BOLD}=================================================================${NC}"
echo -e "${GREEN}${BOLD}         🎉 AdShield Private DNS Installation Complete!          ${NC}"
echo -e "${GREEN}${BOLD}=================================================================${NC}\n"

echo -e "${BOLD}Your Private DNS Hostname:${NC} ${CYAN}${BOLD}${DOMAIN_NAME}${NC}"
echo -e "${BOLD}Web Management Dashboard:${NC}  ${CYAN}http://${DETECTED_IP}:8080/${NC} (or http://${DOMAIN_NAME}:8080/)"
echo -e "${BOLD}DNS-over-HTTPS (DoH) URL:${NC}  ${CYAN}https://${DOMAIN_NAME}/dns-query${NC}\n"

echo -e "${YELLOW}${BOLD}📱 HOW TO CONNECT ON ANDROID (NATIVE PRIVATE DNS):${NC}"
echo -e "  1. On your Android phone, go to: ${BOLD}Settings → Network & Internet → Private DNS${NC}"
echo -e "  2. Select: ${BOLD}Private DNS provider hostname${NC}"
echo -e "  3. Enter: ${CYAN}${BOLD}${DOMAIN_NAME}${NC}"
echo -e "  4. Tap ${BOLD}Save${NC}."
echo -e "  ${GREEN}✔ Zero battery drain! Encrypted over TLS (Port 853) with system-wide adblocking!${NC}\n"

echo -e "${YELLOW}${BOLD}💻 HOW TO CONNECT ON WINDOWS 11 / LINUX / ROUTER:${NC}"
echo -e "  - Windows 11: Set DNS to ${DETECTED_IP} and enable DoH template https://${DOMAIN_NAME}/dns-query"
echo -e "  - Router / Local LAN: Point primary DNS server IP to ${DETECTED_IP}\n"

echo -e "Service Commands:"
echo -e "  - Check status: ${CYAN}systemctl status adshield${NC}"
echo -e "  - View live logs: ${CYAN}journalctl -u adshield -f${NC}"
echo -e "  - Restart: ${CYAN}systemctl restart adshield${NC}\n"

