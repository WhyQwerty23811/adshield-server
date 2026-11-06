# 🛡️ AdShield – Complete Privacy & Ad-Blocking Suite
### Android Application (v2.0.0) & Linux VPS Private DNS Server (DoT / DoH / UDP)

AdShield is a 100% native Java, zero-cost, privacy-first system-wide ad and tracker blocker. It can be run in two flexible ways:
1. **On-Device Android Application**: Powered by Android's `VpnService` API running entirely on-device with zero external servers, no paid APIs, no logins, and zero data collection.
2. **Dedicated Linux VPS Private DNS Server**: Host your own **DNS-over-TLS (DoT, Port 853)** and **DNS-over-HTTPS (DoH, Port 443)** server on any Linux VPS with free automatic Let's Encrypt SSL. Connect your phone via native Android **Private DNS** with **0% extra battery drain**, leaving your phone's VPN slot free for real VPNs!

---

## 📑 Table of Contents
1. [Linux VPS Private DNS Hosting](#-part-1-linux-vps-private-dns-hosting)
   - [How It Works (DoT Port 853)](#how-it-works)
   - [Why Host Your Own Private DNS?](#why-host-your-own-private-dns)
   - [Connecting Directly Using VPS IP (No Domain Needed)](#connecting-directly-using-vps-ip-no-domain-needed)
   - [Getting a 100% Free Domain / Hostname (For Android Private DNS)](#getting-a-100-free-domain--hostname-for-android-private-dns)
   - [1-Click VPS Deployment (`deploy.sh`)](#1-click-vps-deployment)
   - [Docker Deployment](#docker-deployment)
   - [Device Connection Guides (Android, iOS, Windows, Router)](#device-connection-guides)
   - [Cybersecurity Web Management Dashboard](#cybersecurity-web-management-dashboard)
2. [AdShield Android Application Modernization](#-part-2-adshield-android-application-modernization)
   - [100% Native Java Migration (Phase 1)](#1-100-native-java-migration-phase-1)
   - [Modern Material Design 3 Interface (Phase 2 & 3)](#2-modern-material-design-3-interface-phase-2--3)
   - [YouTube & Spotify Ad-Blocking Improvements (Phase 4)](#3-youtube--spotify-ad-blocking-improvements-phase-4)
   - [Architecture & Network Engine (Phase 5 & 6)](#-architecture--network-engine-phase-5--6)
   - [Testing & Verification](#-testing--verification)
   - [Build & Installation Instructions (APK)](#-build--installation-instructions)

---

# 🌐 Part 1: Linux VPS Private DNS Hosting

### How It Works
When you type a hostname like `dns.yourdomain.com` into Android's **Private DNS** setting (Android 9 to 15+):
1. **DNS-over-TLS (DoT, RFC 7858)**: Android establishes an encrypted TLS 1.3 tunnel directly to your Linux VPS on **TCP Port 853**.
2. **Persistent Stream**: All DNS queries from every app, browser, game, and background service stream through this encrypted connection.
3. **Ad & Tracker Sinkholing**:
   - If an app requests a known ad/tracking domain (e.g. `doubleclick.net`, `adservice.google.com`, `applovin.com`):
     - For **A** queries: AdShield immediately returns `0.0.0.0` (TTL 300s).
     - For **AAAA** queries: AdShield immediately returns `::` (IPv6 null address).
4. **Sub-Millisecond In-Memory RAM Cache**: Allowed queries are cached in RAM with TTL auto-eviction. Repeated queries resolve in **< 1ms**, providing faster browsing than standard ISP resolvers.

---

### Why Host Your Own Private DNS?

| Metric / Feature | Local VPN App on Phone | AdShield Private DNS (Linux VPS) |
| :--- | :--- | :--- |
| **Battery Consumption** | Noticeable drain (constant TUN packet rewriting) | **0% extra battery drain** (native OS networking) |
| **Frees Android VPN Slot** | ❌ Occupies the single VPN slot | **✔ Yes** (Run WireGuard / Tailscale at the same time) |
| **Response Latency** | Dependent on phone processor speed | **Blazing fast** (<1ms RAM cache, 10Gbps VPS backbone) |
| **Scope of Protection** | Single Android phone | **All devices** (Android, iPhone, Mac, Windows, Router) |
| **Encryption** | Plaintext local loopback | **TLS 1.3 / HTTPS encryption** (Protects from ISP snooping) |
| **Network Coverage** | Wi-Fi only or requires VPN reconnects | **Works globally** on 4G/5G, Public Wi-Fi, and Home LAN |

---

### Connecting Directly Using VPS IP (No Domain Needed)

Yes! You can connect to your AdShield server **directly via IP address** on several platforms without buying or setting up any domain name:

| Platform / Method | Can Use Raw VPS IP? | Port | How to Connect |
| :--- | :---: | :---: | :--- |
| **AdShield Android App** | **YES** | `53` | Settings → Lookup service → Select **Custom AdShield VPS Server** → Enter VPS IP |
| **Home Wi-Fi Router** | **YES** | `53` | Router Admin (192.168.1.1) → DHCP/DNS Settings → Set Primary DNS to VPS IP |
| **Windows 10 / 11** | **YES** | `53` | Network Adapter Properties → IPv4 → Preferred DNS: enter VPS IP |
| **macOS / Linux** | **YES** | `53` | Network Settings or `/etc/resolv.conf` → `nameserver <YOUR_VPS_IP>` |
| **Android Wi-Fi (Static)** | **YES** | `53` | Wi-Fi Settings → Modify Network → Advanced → IP Settings: Static → DNS 1: VPS IP |
| **Android Native Private DNS** | **NO** | `853` | Android OS requires a hostname for TLS certificates (*use free hostname below*) |

#### 1. In the AdShield Android App:
1. Open the **AdShield app** on your phone.
2. Tap the **Settings** tab.
3. Tap **Lookup service**.
4. Select **Custom AdShield VPS Server**.
5. Enter your VPS IP (e.g. `123.45.67.89`) and tap Save.
6. Return to Dashboard and toggle the Shield ON. All DNS requests are filtered through your VPS on standard UDP port 53.

#### 2. Network-Wide on Your Home Router:
1. Open your browser and go to your router's gateway (usually `192.168.1.1` or `192.168.0.1`).
2. Navigate to **DHCP** or **LAN / WAN DNS Settings**.
3. Set **Primary DNS** to your VPS IPv4 address (Port `53` is used automatically).
4. Save and reboot your router.
*Now every Smart TV, PlayStation/Xbox, iPhone, Android, and PC connected to your home Wi-Fi is automatically protected from ads without installing anything!*

---

### Getting a 100% Free Domain / Hostname (For Android Private DNS)

If you want to use **Android's native "Private DNS"** (Settings → Network & Internet → Private DNS), Android **requires a hostname** because it validates a secure TLS certificate on Port 853.

**You do NOT need to buy a domain!** You can get a free hostname in 60 seconds using any of these methods:

#### Method A: Free DuckDNS (Recommended – 60 Seconds)
1. Go to **[duckdns.org](https://www.duckdns.org)**.
2. Sign in with Google, GitHub, or Reddit (100% free, no credit card required).
3. Under **domains**, choose a subdomain name (e.g., `myadshield`).
4. In the **current ip** box, enter your VPS Public IPv4 Address.
5. Click **add domain**.
6. You now have a permanent free hostname: `myadshield.duckdns.org`
7. When running `sudo bash deploy.sh` on your VPS, enter `myadshield.duckdns.org`. Certbot will automatically issue a genuine Let's Encrypt SSL certificate!
8. In your phone's **Private DNS**, enter `myadshield.duckdns.org`. Done!

#### Method B: Free `sslip.io` (Instant – Zero Registration)
Every IP on the internet automatically has a working hostname via `sslip.io` without signing up anywhere:
* If your VPS IP is `123.45.67.89`, your instant hostname is:
  ```
  123-45-67-89.sslip.io
  ```
* This hostname automatically resolves worldwide to `123.45.67.89`.
* When running `sudo bash deploy.sh`, you can enter `123-45-67-89.sslip.io` as your domain!

---

### 1-Click VPS Deployment

SSH into your Linux VPS as `root` (or with `sudo`):

```bash
git clone https://github.com/WhyQwerty23811/adshield-server.git /opt/adshield-repo
cd /opt/adshield-repo
sudo bash deploy.sh
```

**What the installer does automatically:**
1. Fixes Ubuntu/Debian port 53 stub listener conflicts with `systemd-resolved`.
2. Requests a free, genuine **Let's Encrypt TLS Certificate** via Certbot for your domain.
3. Sets up automated certificate auto-renewal hooks.
4. Configures firewall rules (opening ports 53, 853, 443, 8080).
5. Registers and launches AdShield as a background `systemd` service (`adshield.service`).

---

### Docker Deployment

If you prefer running via Docker Compose:
```bash
cd /opt/adshield-repo/adshield-server
docker compose up -d --build
```

---

### Device Connection Guides

#### 1. Android (Android 9 to 15+) – Native Private DNS
1. Open your Android phone's **Settings**.
2. Tap **Network & Internet** (on Samsung: **Connections** → **More connection settings**).
3. Tap **Private DNS** → select **Private DNS provider hostname**.
4. Enter your domain: `dns.yourdomain.com` (or `myadshield.duckdns.org`).
5. Tap **Save**.

#### 2. Apple iOS / iPadOS / macOS
Use **DNS-over-HTTPS (DoH)**:
* **DoH URL**: `https://dns.yourdomain.com/dns-query`
* In browsers (Safari / Chrome / Firefox / Brave) or via standard mobile configuration profile.

#### 3. Windows 11
1. Open **Settings** → **Network & Internet** → **Wi-Fi** (or **Ethernet**).
2. Click **Hardware properties** → **DNS server assignment** → Click **Edit**.
3. Select **Manual** and turn ON **IPv4**.
4. Enter your VPS IPv4 Address as Preferred DNS.
5. Set DNS encryption to **Encrypted only (DNS over HTTPS)** with template: `https://dns.yourdomain.com/dns-query`

---

### Cybersecurity Web Management Dashboard

Access the real-time Cyber Dashboard in any web browser at:
```
http://<your-vps-ip>:8080/
```
* **Live Query Stream**: Inspect live queries (DoT, DoH, UDP) with search and status chips (`BLOCKED`, `ALLOWED`, `CACHED`).
* **Shield Controls**: Toggle YouTube Shield, Spotify Shield, and JioCinema/Hotstar Shield in 1 click.
* **Custom Rules**: Add custom whitelisted or blacklisted domains.
* **Community Updates**: One-click update for StevenBlack 77,000+ ad/tracker hostnames.

---

# 📱 Part 2: AdShield Android Application Modernization

AdShield is a **100% native Java**, zero-cost, privacy-first Android system-wide ad and tracker blocker powered by the Android `VpnService` API. It executes entirely on-device with **zero external servers, no paid APIs, no logins, and zero data collection**.

---

## 🚀 Key Highlights & Milestone 3 Modernization

### 1. 100% Native Java Migration (Phase 1)
- Converted **100% of Kotlin source files and tests to native Java 17**.
- Removed all Kotlin dependencies and Kotlin compiler plugins from Gradle.
- Replaced Coroutines and Flow with native Java concurrency (`ExecutorService`, `Handler`, `Thread`, `AtomicReference`, `LiveData`).
- Replaced Jetpack Compose with modern Material Design 3 XML layouts and Android ViewBinding for faster compilation and reliable DayNight theming.

### 2. Modern Material Design 3 Interface (Phase 2 & 3)
Built with a sleek **Cybersecurity** theme supporting **Light Mode, Dark Mode, and System Default**:
1. **Dashboard Screen**:
   - Modern AdShield status branding and logo.
   - Large interactive power switch with glowing status halo.
   - Measured metrics: Ads Blocked, Total Queries, Block Rate %, Today's Blocked, Protection Uptime.
   - Dedicated YouTube & Spotify Shield quick-status cards.
   - Real-time recent blocked threats list.
2. **App Protection / Selection Screen**:
   - Lists installed applications with app icon, title, and package name.
   - Highlights essential apps: **YouTube, Spotify, Instagram, Facebook, and Chrome**.
   - Per-app toggle to exclude/bypass apps from VPN filtering (`VpnService.Builder.addDisallowedApplication`).
   - Search bar and filter chips (*All*, *Protected*, *Excluded*).
3. **Live DNS Query Log**:
   - Real-time feed of all incoming DNS queries.
   - Domain name, application name, query type badge (`A`, `AAAA`), status dot (`🔴 Blocked`, `🟢 Allowed`), resolved IP, and timestamp.
   - Live search and filter chips (*All*, *Blocked*, *Allowed*).
   - Clear logs action.
4. **Statistics & Analytics**:
   - Measured actual statistics: Overall Block Rate %, Total queries, Blocked vs Allowed count.
   - Visual proportional ratio bar.
   - Top Blocked Domains list with counts and visual progress indicators.
   - Strictly real data—no simulated or fake numbers.
5. **Filter Management**:
   - Tabbed layout: **Blacklist**, **Whitelist**, and **Built-in Community Lists**.
   - Add custom domain rule dialog with domain validation.
   - Per-rule toggle switch and delete button.
   - Built-in community filter definitions included offline.
6. **Settings Screen**:
   - **Theme Selector**: System Default, Light Mode, Dark Mode (Cybersecurity).
   - **Upstream DNS Provider**: Cloudflare (`1.1.1.1`), Google (`8.8.8.8`), Quad9 (`9.9.9.9`), AdGuard (`94.140.14.14`), and **Custom VPS DNS Server**.
   - **Specialized Shield Toggles**: Dedicated controls for YouTube and Spotify protection.
   - **System Reliability**: Start on device boot (`RECEIVE_BOOT_COMPLETED`), Battery Optimization exemption shortcut.
   - Reset statistics and clear data.

### 3. YouTube & Spotify Ad-Blocking Improvements (Phase 4)
#### Technical Transparency & Engineering Reality:
DNS-based filtering operates at layer 3/4. Ads delivered through the identical media hostnames as actual video/audio streams (e.g. `googlevideo.com`) cannot be separated by domain-name without breaking video playback or causing endless buffering loops.
- **YouTube Strategy**: Intercepts known telemetry, advertising, and companion banner domains (`doubleclick.net`, `googleads.g.doubleclick.net`, `adservice.google.com`, `youtubeads.l.google.com`, `s.youtube.com`).
- **YouTube Media Guarantee**: Strictly preserves `googlevideo.com`, `ytimg.com`, `youtubei.googleapis.com` so video playback and authentication remain 100% smooth.
- **Spotify Strategy**: Intercepts companion banners and audio ad telemetry domains (`spclient.wg.spotify.com/ads`, `adeventtracker.spotify.com`, `adstudio.spotify.com`).
- **Spotify Media Guarantee**: Whitelists `audio-*.spotify.com` and core streaming endpoints to avoid music playback freezes.

---

## 🛠️ Architecture & Network Engine (Phase 5 & 6)

```
                 ┌──────────────────────────────────────────────┐
                 │                Android Device                │
                 └──────────────────────┬───────────────────────┘
                                        │ DNS Query (UDP Port 53)
                                        ▼
                 ┌──────────────────────────────────────────────┐
                 │           VpnService TUN Interface           │
                 │                 (10.0.0.1:53)                │
                 └──────────────────────┬───────────────────────┘
                                        │
                 ┌──────────────────────▼───────────────────────┐
                 │             DnsFilteringEngine               │
                 │  - Parses IPv4 UDP header (RFC 768 / 791)    │
                 │  - Extracts QNAME & QTYPE                    │
                 │  - Checks In-Memory LRU DNS Cache            │
                 └──────────────┬───────────────────────────────┘
                                │
          Domain Blocked? ──────┴──────────────────────┐
          │ Yes                                        │ No (Allowed)
          ▼                                            ▼
┌───────────────────────────────┐            ┌──────────────────────────────┐
│     DnsResponseBuilder        │            │    CloudflareDnsForwarder    │
│  - 0.0.0.0 for IPv4 (A)       │            │  - Protected UDP Socket      │
│  - :: for IPv6 (AAAA)         │            │  - TCP Fallback on Truncation│
│  - TTL = 300s                 │            │  - Cloudflare / Google / Quad9│
└──────────────┬────────────────┘            └──────────────┬───────────────┘
               │                                            │
               └──────────────────────┬─────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   SQLite Logging & Stats│
                         │ (dns_logs, daily_stats) │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   IpPacketUtil Builder  │
                         │  Calculates Checksums   │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  TUN FileDescriptor     │
                         │(Delivered to client app)│
                         └─────────────────────────┘
```

1. **Selective DNS Routing**: `VpnService.Builder` routes *only* `10.0.0.1/32` into the TUN interface. Regular HTTPS traffic bypasses the VPN tunnel entirely and flows at full native hardware speeds.
2. **Loop Prevention**: Forwarder sockets call `VpnService.protect(socket)` to ensure upstream traffic bypasses the VPN interface.
3. **Android 14+ FGS Compliance**: Service declares `android:foregroundServiceType="specialUse"` with `PROPERTY_SPECIAL_USE_FGS_SUBTYPE` metadata.
4. **In-Memory LRU Cache**: Accelerates response times for repeated allowed queries with automated TTL eviction.

---

## 🧪 Testing & Verification

All 20 unit tests are written in pure Java (JUnit 4) and pass with 0 errors:

```bash
JAVA_HOME="<path-to-jdk-17>" ./gradlew testDebugUnitTest
```

### Test Suite Summary:
- `DnsParserTest`: Standard A queries, Subdomain AAAA queries, Cyclic pointer protection, Malformed packets.
- `DnsResponseBuilderTest`: Sinkhole A responses (`0.0.0.0`), AAAA responses (`::`), SERVFAIL responses.
- `DomainBlocklistTest`: Initial test domains (`doubleclick.net`, `googlesyndication.com`, etc.), Hierarchical subdomain matching, Whitelisting precedence, Essential streaming protection.
- `IpPacketUtilTest`: IPv4 header checksum verification (sum folds to `0xFFFF`), UDP checksum calculation (including odd-length payloads).
- `DnsFilteringEngineTest`: End-to-end packet processing pipeline, Sinkholing verification, Non-DNS packet bypassing.
- `ProtectionStateTest`: VpnState transition integrity, service constants, statistics defaults.

---

## 📱 Build & Installation Instructions

### 1. Compile the Debug APK
```bash
JAVA_HOME="<path-to-jdk-17>" ./gradlew clean assembleDebug
```
The APK will be generated at:
```
app/build/outputs/apk/debug/app-debug.apk
```

### 2. Install on Device
With your device connected via USB or Wireless ADB:
```bash
adb install -r "app/build/outputs/apk/debug/app-debug.apk"
```

### 3. Launch AdShield
```bash
adb shell am start -n com.adshield/.MainActivity
```
