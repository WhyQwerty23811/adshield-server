# AdShield Private DNS Server for Linux VPS

High-performance, privacy-first **Private DNS & Ad-Blocking Server** designed to run on any Linux VPS.

Enables system-wide, zero-battery ad and tracker filtering across **Android (Native Private DNS / DoT)**, **iOS / macOS**, and **Windows 11 (DoH)** without requiring any local VPN apps.

---

## ⚡ Why Host Your Own Private DNS?

| Feature | Local Android VPN App | AdShield Private DNS VPS |
| :--- | :--- | :--- |
| **Battery Consumption** | Moderate (constant TUN processing) | **Zero** (handled by Android OS natively) |
| **Frees Device VPN Slot** | ❌ Occupies the single VPN slot | **✔ Yes** (You can run WireGuard / Tailscale simultaneously!) |
| **Connection Speed** | Dependent on phone CPU | **Instant** (<1ms RAM cache, 10Gbps VPS uplink) |
| **All Devices Protected** | Android device only | **Android, iPhone, Mac, Windows, Router** |
| **Encryption** | Local plaintext loopback | **DNS-over-TLS (DoT, Port 853)** & **DoH (Port 443)** |
| **YouTube & Spotify Filtering** | Yes | **Yes** (Built-in dedicated shields) |

---

## 🚀 1-Minute Quick Start (Automated VPS Setup)

### Prerequisites:
1. A Linux VPS (Ubuntu 20.04/22.04/24.04, Debian 11/12, CentOS/Rocky 8/9).
2. A Domain or Subdomain pointing to your VPS IPv4 address (e.g. `dns.yourdomain.com`).
   * *Note: Android's Private DNS strictly requires a valid domain name and TLS certificate.*

### Installation Command:
SSH into your VPS as `root` and run:

```bash
git clone https://github.com/<your-username>/Ad-Shield.git /opt/adshield-repo
cd /opt/adshield-repo
sudo bash deploy.sh
```

The script will:
1. Check your public IP and domain resolution.
2. Automatically obtain a free **Let's Encrypt SSL/TLS Certificate** via Certbot.
3. Fix port 53 conflicts with `systemd-resolved` (on Ubuntu/Debian).
4. Configure firewall rules (opening ports 53, 853, 443, 8080).
5. Set up auto-renewal hooks for SSL certificates.
6. Start the **AdShield Server** as a background `systemd` service.

---

## 📱 How to Connect Your Devices

### 1. Android (Android 9 to 15+) – Native Private DNS
1. Open **Settings** on your phone.
2. Go to **Network & Internet** (or **Connections** → **More connection settings**).
3. Tap **Private DNS**.
4. Select **Private DNS provider hostname**.
5. Type your domain: `dns.yourdomain.com`
6. Tap **Save**.

> Android will now route 100% of its DNS traffic through your VPS over encrypted **DNS-over-TLS (Port 853)** with zero battery drain.

### 2. Apple iOS / iPadOS / macOS
Use **DNS-over-HTTPS (DoH)**:
* DoH URL: `https://dns.yourdomain.com/dns-query`
* Or configure in browsers like Safari/Chrome/Firefox or via an iOS `.mobileconfig` profile.

### 3. Windows 11
1. Open **Settings** → **Network & Internet** → **Wi-Fi** (or **Ethernet**).
2. Click **Hardware properties** → **DNS server assignment** → **Edit**.
3. Select **Manual** → Turn ON **IPv4**.
4. Enter your VPS IP as Preferred DNS.
5. Set DNS encryption to **Encrypted only (DNS over HTTPS)** with template:
   `https://dns.yourdomain.com/dns-query`

---

## 📊 Cybersecurity Web Dashboard

Access the real-time Cyber Dashboard at:
```
http://<your-vps-ip>:8080/
```
* **Real-time Metrics**: Total Queries, Blocked Ads, Block Rate %, In-Memory Cache Hit Speed.
* **Live Query Stream**: Inspect live queries (DoT, DoH, UDP) with search and status chips.
* **Shield Controls**: Toggle YouTube Shield, Spotify Shield, and JioCinema/Hotstar Shield in 1 click.
* **Custom Rules**: Add custom whitelisted or blacklisted domains.
* **Community Updates**: One-click update for StevenBlack 77,000+ ad/tracker hostnames.

---

## 🛠️ Verification & Troubleshooting

Test your DoT server from any terminal:
```bash
# Test DoT (port 853) using kdig
kdig -d @dns.yourdomain.com +tls doubleclick.net

# Test standard UDP query
dig @<vps-ip> doubleclick.net

# Test DoH query
curl -H 'accept: application/dns-message' 'https://dns.yourdomain.com/dns-query?dns=AAABAAABAAAAAAAAA3d3dwdleGFtcGxlA2NvbQAAAQAB'
```

### Useful Server Commands:
```bash
# Check status
systemctl status adshield

# Follow live server logs
journalctl -u adshield -f

# Restart service
systemctl restart adshield
```

