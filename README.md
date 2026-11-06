# 🛡️ AdShield: Private DNS & System-Wide Ad-Blocking Suite

**AdShield** is a privacy-first, zero-battery ad and tracker filtering suite that turns any cheap Linux VPS ($2–$5/mo) into a personal **Private DNS server (DNS-over-TLS on Port 853 & DNS-over-HTTPS on Port 443)** with automated Let's Encrypt SSL, an in-memory LRU cache, and a real-time Cybersecurity Web Dashboard.

It also includes the complete **100% native Java Android client application** for devices that prefer local VPN-based filtering.

---

## 📑 Table of Contents
1. [How It Works](#-how-it-works)
2. [Why Host Your Own Private DNS?](#-why-host-your-own-private-dns)
3. [Connecting Directly Using VPS IP (No Domain Needed)](#-connecting-directly-using-vps-ip-no-domain-needed)
4. [Getting a 100% Free Domain / Hostname (For Android Private DNS)](#-getting-a-100-free-domain--hostname-for-android-private-dns)
5. [Architecture Overview](#-architecture-overview)
6. [Prerequisites](#-prerequisites)
7. [How to Run It (1-Click VPS Deployment)](#-how-to-run-it-1-click-vps-deployment)
8. [Alternative: Docker Deployment](#-alternative-docker-deployment)
9. [Device Connection Guides](#-device-connection-guides)
   - [Android (Native Private DNS)](#1-android-9-to-15--native-private-dns)
   - [Apple iOS / iPadOS / macOS](#2-apple-ios--ipados--macos)
   - [Windows 11](#3-windows-11)
   - [Home Routers & Linux Machines](#4-home-routers--linux-machines)
   - [AdShield Android App](#5-adshield-android-app-client)
10. [Cybersecurity Web Management Dashboard](#-cybersecurity-web-management-dashboard)
11. [Verification & Troubleshooting](#-verification--troubleshooting)
12. [Repository Structure](#-repository-structure)

---

## 🧠 How It Works

### The Technology Behind "Private DNS"
When you type a hostname like `dns.yourdomain.com` into Android's **Private DNS** setting (introduced in Android 9 Pie and supported through Android 15+):
1. **DNS-over-TLS (DoT, RFC 7858)**: Android initiates a secure TLS 1.3/1.2 connection to your VPS on **TCP Port 853**.
2. **Certificate Validation**: Android verifies that your VPS certificate is issued by a recognized Certificate Authority (like Let's Encrypt) matching `dns.yourdomain.com`.
3. **Persistent Streaming Tunnel**: Android maintains this persistent, encrypted TLS connection. Every DNS request across all apps, browsers, games, and system services flows through this tunnel framed by a 2-byte length prefix.
4. **Ad & Tracker Sinkholing**:
   - If an app requests a known ad/tracking domain (e.g. `doubleclick.net`, `adservice.google.com`, `applovin.com`):
     - For **A** queries: AdShield immediately returns `0.0.0.0` (TTL 300s).
     - For **AAAA** queries: AdShield immediately returns `::` (IPv6 null address).
     - The ad fails to load instantly, saving your mobile data and preventing tracking.
5. **Specialized App Protections**:
   - **YouTube Shield**: Intercepts ad banners and telemetry while strictly preserving `googlevideo.com`, `ytimg.com`, and `youtubei.googleapis.com` so video playback and authentication remain 100% smooth.
   - **Spotify Shield**: Blocks audio ad telemetry while strictly preserving `audio-*.spotify.com` and core streaming endpoints to avoid music playback freezes.
   - **JioCinema & Hotstar**: Blocks embedded ad injection networks (`jioads.com`, `vserve.mobi`, `imasdk.googleapis.com`).
6. **Sub-Millisecond In-Memory RAM Cache (LRU)**:
   - Allowed queries are cached in RAM with TTL eviction.
   - Repeated requests resolve in **< 1 millisecond**, significantly accelerating your web browsing and app response times.
7. **Resilient Upstream Resolvers**:
   - Cache misses are resolved via asynchronous upstream lookups to Cloudflare (`1.1.1.1`), Google (`8.8.8.8`), Quad9 (`9.9.9.9`), or AdGuard (`94.140.14.14`).

---

## ⚡ Why Host Your Own Private DNS?

| Metric / Feature | Local VPN App on Phone | AdShield Private DNS (Linux VPS) |
| :--- | :--- | :--- |
| **Battery Consumption** | Noticeable drain (constant TUN packet rewriting) | **0% extra battery drain** (native OS networking) |
| **Frees Android VPN Slot** | ❌ Occupies the single VPN slot | **✔ Yes** (Run WireGuard / Tailscale / OpenVPN at the same time) |
| **Response Latency** | Dependent on phone processor speed | **Blazing fast** (<1ms RAM cache, 10Gbps VPS backbone) |
| **Scope of Protection** | Single Android phone | **All devices** (Android, iPhone, Mac, Windows, Router) |
| **Encryption** | Plaintext local loopback | **TLS 1.3 / HTTPS encryption** (Protects from ISP snooping) |
| **Network Coverage** | Wi-Fi only or requires VPN reconnects | **Works globally** on 4G/5G, Public Wi-Fi, and Home LAN |

---

## 🔌 Connecting Directly Using VPS IP (No Domain Needed)

Yes! You can connect to your AdShield server **directly via IP address** on several platforms without buying or setting up any domain name:

| Platform / Method | Can Use Raw VPS IP? | Port | How to Connect |
| :--- | :---: | :---: | :--- |
| **AdShield Android App** | **YES** | `53` | Settings → Lookup service → Select **Custom AdShield VPS Server** → Enter VPS IP |
| **Home Wi-Fi Router** | **YES** | `53` | Router Admin (192.168.1.1) → DHCP/DNS Settings → Set Primary DNS to VPS IP |
| **Windows 10 / 11** | **YES** | `53` | Network Adapter Properties → IPv4 → Preferred DNS: enter VPS IP |
| **macOS / Linux** | **YES** | `53` | Network Settings or `/etc/resolv.conf` → `nameserver <YOUR_VPS_IP>` |
| **Android Wi-Fi (Static)** | **YES** | `53` | Wi-Fi Settings → Modify Network → Advanced → IP Settings: Static → DNS 1: VPS IP |
| **Android Native Private DNS** | **NO** | `853` | Android OS requires a hostname for TLS certificates (*use free hostname below*) |

### 1. In the AdShield Android App:
1. Open the **AdShield app** on your phone.
2. Tap the **Settings** tab.
3. Tap **Lookup service**.
4. Select **Custom AdShield VPS Server**.
5. Enter your VPS IP (e.g. `123.45.67.89`) and tap Save.
6. Return to Dashboard and toggle the Shield ON. All DNS requests are filtered through your VPS on standard UDP port 53.

### 2. Network-Wide on Your Home Router:
1. Open your browser and go to your router's gateway (usually `192.168.1.1` or `192.168.0.1`).
2. Navigate to **DHCP** or **LAN / WAN DNS Settings**.
3. Set **Primary DNS** to your VPS IPv4 address (Port `53` is used automatically).
4. Save and reboot your router.
*Now every Smart TV, PlayStation/Xbox, iPhone, Android, and PC connected to your home Wi-Fi is automatically protected from ads without installing anything!*

---

## 🆓 Getting a 100% Free Domain / Hostname (For Android Private DNS)

If you want to use **Android's native "Private DNS"** (Settings → Network & Internet → Private DNS), Android **requires a hostname** because it validates a secure TLS certificate on Port 853.

**You do NOT need to buy a domain!** You can get a free hostname in 60 seconds using any of these methods:

### Method A: Free DuckDNS (Recommended – 60 Seconds)
1. Go to **[duckdns.org](https://www.duckdns.org)**.
2. Sign in with Google, GitHub, or Reddit (100% free, no credit card required).
3. Under **domains**, choose a subdomain name (e.g., `myadshield`).
4. In the **current ip** box, enter your VPS Public IPv4 Address.
5. Click **add domain**.
6. You now have a permanent free hostname:
   ```
   myadshield.duckdns.org
   ```
7. When running `sudo bash deploy.sh` on your VPS, enter `myadshield.duckdns.org`. Certbot will automatically issue a genuine Let's Encrypt SSL certificate!
8. In your phone's **Private DNS**, enter `myadshield.duckdns.org`. Done!

### Method B: Free `sslip.io` (Instant – Zero Registration)
Every IP on the internet automatically has a working hostname via `sslip.io` without signing up anywhere:
* If your VPS IP is `123.45.67.89`, your instant hostname is:
  ```
  123-45-67-89.sslip.io
  ```
* This hostname automatically resolves worldwide to `123.45.67.89`.
* When running `sudo bash deploy.sh`, you can enter `123-45-67-89.sslip.io` as your domain!

### Method C: Free No-IP
1. Go to **[noip.com](https://www.noip.com)** and create a free account.
2. Create a free hostname (e.g., `myadshield.ddns.net`).
3. Set the target IP to your VPS IP.

---

```
                      ┌──────────────────────────────────────────────┐
                      │    Android Device (Native Private DNS)       │
                      │         (or iOS / Windows 11 / Mac)          │
                      └──────────────────────┬───────────────────────┘
                                             │ DNS-over-TLS (TCP Port 853)
                                             │ or DNS-over-HTTPS (Port 443)
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │             Linux VPS (AdShield)             │
                      │      Let's Encrypt TLS Termination           │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │              AdShield Server                 │
                      │  - RFC 1035 / RFC 7858 Wire Parser           │
                      │  - Subdomain & Wildcard Rule Matching        │
                      └──────────────┬───────────────────────────────┘
                                     │
         Domain Blocked? ────────────┴──────────────────────────────┐
         │ Yes                                                      │ No (Allowed)
         ▼                                                          ▼
┌───────────────────────────────┐                  ┌─────────────────────────────────┐
│     Synthetic Sinkhole        │                  │      In-Memory RAM Cache        │
│  - 0.0.0.0 for IPv4 (A)       │                  │        (<1ms Latency)           │
│  - :: for IPv6 (AAAA)         │                  └────────────────┬────────────────┘
│  - TTL = 300s                 │                                   │ Cache Miss?
└──────────────┬────────────────┘                                   ▼
               │                                   ┌─────────────────────────────────┐
               │                                   │      Fast Upstream Resolver     │
               │                                   │   (Cloudflare / Google / Quad9) │
               │                                   └────────────────┬────────────────┘
               │                                                    │
               └──────────────────────┬─────────────────────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │ Real-Time Query History  │
                         │   Cybersecurity Web UI   │
                         │      (Port 8080)         │
                         └──────────────────────────┘
```

---

## 📋 Prerequisites

1. **A Linux VPS**: Any distribution (Ubuntu 20.04/22.04/24.04, Debian 11/12, CentOS/Rocky 8/9, Arch Linux) with at least 512 MB of RAM.
2. **A Domain or Subdomain**:
   - Android's Private DNS **strictly requires a valid domain name** and cannot use a raw IP.
   - Example: `dns.yourdomain.com` or `adblock.yourdomain.com`.
3. **DNS A-Record Pointing to Your VPS**:
   - In your DNS registrar (Cloudflare, Namecheap, GoDaddy, Porkbun, etc.), add an **A record**:
     - **Name**: `dns` (or your chosen subdomain)
     - **Type**: `A`
     - **Value**: Your VPS Public IPv4 Address
     - **TTL**: Auto / 5 minutes
     - *(If using Cloudflare DNS, set Proxy status to **DNS only / Grey Cloud**, not Proxied)*.

---

## 🚀 How to Run It (1-Click VPS Deployment)

We provide a fully automated script that handles package installation, Let's Encrypt SSL issuance, port 53 conflict resolution, firewall configuration, and systemd service registration in under 60 seconds.

### Step 1: Clone the Repository to Your VPS
SSH into your Linux VPS as `root` (or with `sudo`):

```bash
git clone https://github.com/<your-username>/Ad-Shield.git /opt/adshield-repo
cd /opt/adshield-repo
```

### Step 2: Run the Installer
```bash
sudo bash deploy.sh
```

### Step 3: Enter Your Domain and Email
* When prompted for **Domain / Hostname**, type your domain (e.g. `dns.yourdomain.com`).
* When prompted for **Email**, enter your email (used by Let's Encrypt for renewal notices).

The installer will automatically:
1. Verify public IP and port availability.
2. Disable the default Ubuntu/Debian `systemd-resolved` DNS stub listener on port 53.
3. Automatically obtain a free **Let's Encrypt TLS Certificate** via Certbot.
4. Copy the server engine, rules, and UI to `/opt/adshield`.
5. Open firewall ports: `53` (DNS), `853` (DoT), `443` (DoH), `8080` (Web UI), `80` (ACME challenges).
6. Create an automated renewal hook to reload certificates every 60 days.
7. Start `adshield.service` with automatic restarts on boot.

---

## 🐳 Alternative: Docker Deployment

If you prefer running inside a container:

```bash
cd /opt/adshield-repo/adshield-server
# Build and start in detached mode
docker compose up -d --build
```

The container runs with `network_mode: host` to guarantee zero-overhead packet routing for UDP port 53 and TCP port 853.

---

## 📱 Device Connection Guides

### 1. Android (Android 9 to 15+) – Native Private DNS
1. Open your Android phone's **Settings**.
2. Tap **Network & Internet** (on Samsung: **Connections** → **More connection settings**).
3. Tap **Private DNS**.
4. Select **Private DNS provider hostname**.
5. Enter your domain: `dns.yourdomain.com`
6. Tap **Save**.

> **Verification**: Look at your connection status under Private DNS. It will display `dns.yourdomain.com`. Your phone is now 100% ad-blocked with zero extra battery consumption!

---

### 2. Apple iOS / iPadOS / macOS
Apple platforms natively support **DNS-over-HTTPS (DoH)**:
* **DoH URL**: `https://dns.yourdomain.com/dns-query`
* **In Browsers (Firefox / Chrome / Brave)**: Go to **Settings** → **Privacy & Security** → **Secure DNS** → Select **Custom** and paste `https://dns.yourdomain.com/dns-query`.
* **System-wide Profile**: You can generate a standard `.mobileconfig` file pointing to your DoH server URL.

---

### 3. Windows 11
1. Open **Settings** → **Network & Internet** → **Wi-Fi** (or **Ethernet**).
2. Click **Hardware properties** → **DNS server assignment** → Click **Edit**.
3. Select **Manual** and turn ON **IPv4**.
4. Enter your VPS IPv4 Address as the **Preferred DNS**.
5. Set **DNS encryption** to **Encrypted only (DNS over HTTPS)**.
6. Under **DNS over HTTPS template**, paste:
   ```
   https://dns.yourdomain.com/dns-query
   ```
7. Click **Save**.

---

### 4. Home Routers & Linux Machines
To block ads on every smart TV, game console, and smart home gadget on your home Wi-Fi:
* Access your Home Router admin settings (usually `192.168.1.1` or `192.168.0.1`).
* Under **WAN / LAN / DHCP Settings**, change Primary DNS to your VPS IPv4 Address.

---

### 5. AdShield Android App Client
If you prefer using the on-device AdShield Android application:
1. Open the AdShield app on your phone.
2. Tap the **Settings** tab.
3. Tap **Lookup service**.
4. Select **Custom AdShield VPS Server** and enter your VPS IP or domain.
5. Tap the Power Switch on the Dashboard to connect.

---

## 📊 Cybersecurity Web Management Dashboard

Access the real-time Cyber Dashboard in any web browser at:
```
http://<your-vps-ip>:8080/
```

### Dashboard Features:
* **Live System Metrics**: View Total Queries processed, Blocked Ads, Block Rate %, and LRU Cache Hit Speed.
* **Real-Time DNS Query Log**: Inspect queries as they happen across DoT, DoH, and UDP. Filter by domain, IP, or query status (`BLOCKED`, `ALLOWED`, `CACHED`).
* **Interactive Shield Toggles**: Turn YouTube Shield, Spotify Shield, or JioCinema/Hotstar Shield ON or OFF with a single click.
* **Rule Manager**: Instantly add or remove custom domain rules to your Whitelist or Blacklist.
* **1-Click Community Updater**: Update to the latest 77,000+ domain community blocklist from upstream StevenBlack hosts without restarting the server.
* **Private DNS Connection Assistant**: Built-in modal with quick copy-paste instructions for your configured hostname.

---

## 🛠️ Verification & Troubleshooting

### Test DoT (Port 853)
From any terminal with `kdig` or `knot-dnsutils`:
```bash
kdig -d @dns.yourdomain.com +tls doubleclick.net
```
*Expected result: Status `NOERROR`, Answer `0.0.0.0`.*

### Test Standard UDP (Port 53)
```bash
dig @<your-vps-ip> doubleclick.net
```

### Test DoH (Port 443)
```bash
curl -H 'accept: application/dns-message' 'https://dns.yourdomain.com/dns-query?dns=AAABAAABAAAAAAAAA3d3dwdleGFtcGxlA2NvbQAAAQAB'
```

### Helpful Server Commands:
```bash
# Check if AdShield service is running
sudo systemctl status adshield

# Follow real-time server logs
sudo journalctl -u adshield -f

# Restart the service
sudo systemctl restart adshield

# Check listening ports (should see 53, 853, 443, 8080)
sudo ss -tulpn | grep -E '53|853|443|8080'
```

---

## 📁 Repository Structure

```
Ad-Shield/
├── adshield-server/                     # The Linux VPS Private DNS & DoT/DoH Server
│   ├── adshield_server.py              # Asynchronous DNS (DoT 853 / DoH 443 / UDP 53) daemon
│   ├── filter_engine.py                # AdShield filtering logic (YouTube, Spotify, Hotstar, Community)
│   ├── cache.py                        # In-Memory LRU RAM cache with TTL auto-eviction
│   ├── config.json                     # Server configuration (ports, TLS cert paths, upstreams)
│   ├── setup_vps.sh                    # Automated 1-click Linux VPS installer
│   ├── adshield.service                # Systemd service definition
│   ├── Dockerfile                      # Ultra-lightweight Docker container
│   ├── docker-compose.yml              # Docker Compose deployment file
│   ├── static/                         # Cyberpunk Web Dashboard assets
│   │   ├── index.html                  # Dashboard UI
│   │   ├── style.css                   # Responsive dark theme styling
│   │   └── app.js                      # Real-time polling & REST API interaction
│   └── blocklists/                     # Blocklist store directory
│       ├── blocklist.txt               # Bundled community hosts (77,000+ domains)
│       ├── custom_whitelist.txt        # User custom whitelist rules
│       └── custom_blacklist.txt        # User custom blacklist rules
│
├── app/                                # Android App Source (Java 17, Material Design 3)
│   ├── src/main/java/com/adshield/
│   │   ├── data/PreferencesManager.java # Settings persistence & custom upstream resolver
│   │   ├── ui/settings/SettingsFragment.java # Settings UI & Private DNS helper card
│   │   └── dns/                        # On-device DNS parsing and filtering logic
│   └── src/main/res/                   # Layouts, themes, and drawables
│
├── deploy.sh                           # Root 1-command installer entrypoint
└── README.md                           # This documentation
```

---

## 📜 License
AdShield is open-source under the MIT / Apache 2.0 License. Free for personal and commercial use.
