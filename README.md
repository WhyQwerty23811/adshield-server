# AdShield – Complete Privacy & Ad-Blocking Suite (App & Linux VPS Private DNS)

AdShield provides complete system-wide ad, tracker, and telemetry protection across your entire device ecosystem. It offers two flexible modes:
1. **AdShield Linux VPS Private DNS Server**: Host your own encrypted **DNS-over-TLS (DoT, Port 853)** and **DNS-over-HTTPS (DoH, Port 443)** server on any Linux VPS with free automatic Let's Encrypt TLS. Connect your Android phone via native **Private DNS** with **zero battery drain** and without occupying your device's VPN slot!
2. **AdShield Android Application**: A 100% native Java on-device VPN ad blocker and query monitor, now featuring support for custom VPS DNS upstreams.

---

## ⚡ Hosting AdShield Private DNS on Your Linux VPS (1-Click Setup)

Android 9+ has built-in support for **Private DNS** (DNS-over-TLS). When you host AdShield on a Linux VPS:
- **0% Extra Battery Drain**: Managed directly by the Android OS network stack.
- **VPN Slot Remains Free**: You can run WireGuard, Tailscale, or work VPNs at the same time.
- **Ultra-Fast Speed**: Powered by an in-memory LRU RAM cache with sub-millisecond query responses.
- **Protects All Devices**: Android (Private DNS), iPhone/iPad/macOS (DoH), Windows 11, and home routers.

### 🚀 1-Click VPS Installation:
SSH into your Linux VPS as root and run:
```bash
git clone https://github.com/<your-username>/Ad-Shield.git /opt/adshield-repo
cd /opt/adshield-repo
sudo bash deploy.sh
```
The installer automatically:
1. Acquires a free **Let's Encrypt TLS Certificate** for your domain (e.g., `dns.yourdomain.com`).
2. Cleans up port 53 stub listener conflicts with `systemd-resolved`.
3. Opens firewall ports (53, 853 DoT, 443 DoH, 8080 Web Dashboard).
4. Configures automatic certificate renewal hooks.
5. Launches the AdShield DNS server as a `systemd` service.

### 📱 How to Connect Android Private DNS:
1. Go to **Settings** → **Network & Internet** → **Private DNS**.
2. Select **Private DNS provider hostname**.
3. Enter your domain: `dns.yourdomain.com`
4. Tap **Save**. Your phone is now 100% protected system-wide!

Access your live Cybersecurity Web Dashboard at `http://<your-vps-ip>:8080/`.

---

## 📱 AdShield Android Client Application (v2.0.0)

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
   - **Upstream DNS Provider**: Cloudflare (`1.1.1.1`), Google (`8.8.8.8`), Quad9 (`9.9.9.9`), AdGuard (`94.140.14.14`).
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
