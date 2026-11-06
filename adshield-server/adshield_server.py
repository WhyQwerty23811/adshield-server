"""
AdShield Private DNS Server for Linux VPS
Supports:
- DNS-over-TLS (DoT, RFC 7858) on TCP 853 (Native Android Private DNS)
- DNS-over-HTTPS (DoH, RFC 8484) on TCP 443
- Standard DNS on UDP & TCP 53
- Cybersecurity Web Dashboard & Management API on HTTP 8080
"""

import asyncio
import os
import sys
import time
import json
import ssl
import struct
import socket
import base64
import urllib.parse
from datetime import datetime
from collections import deque
from typing import Optional, Tuple, Dict, Any, List

from filter_engine import FilterEngine, normalize_domain
from cache import DnsCache

# Constants
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_BLOCKLIST_DIR = os.path.join(os.path.dirname(__file__), "blocklists")
DEFAULT_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

UPSTREAM_PROVIDERS = {
    "cloudflare": ["1.1.1.1", "1.0.0.1"],
    "google": ["8.8.8.8", "8.8.4.4"],
    "quad9": ["9.9.9.9", "149.112.112.112"],
    "adguard": ["94.140.14.14", "94.140.15.15"]
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "server_hostname": "dns.example.com",
    "upstream_provider": "cloudflare",
    "custom_upstream": [],
    "udp_port": 53,
    "tcp_port": 53,
    "dot_port": 853,
    "doh_port": 443,
    "web_port": 8080,
    "tls_cert_file": "/etc/letsencrypt/live/dns.example.com/fullchain.pem",
    "tls_key_file": "/etc/letsencrypt/live/dns.example.com/privkey.pem",
    "enable_tls": False,
    "log_history_limit": 500,
    "ad_blocking": True,
    "youtube_shield": True,
    "spotify_shield": True,
    "hotstar_shield": True
}


def parse_dns_question(data: bytes) -> Optional[Tuple[int, str, int, int, int]]:
    """
    Parses a DNS query.
    Returns: (tx_id, domain, qtype, qclass, question_end_offset) or None.
    """
    if len(data) < 12:
        return None
    tx_id, flags, qdcount, _, _, _ = struct.unpack("!HHHHHH", data[:12])
    if qdcount < 1:
        return None

    offset = 12
    labels = []
    while offset < len(data):
        length = data[offset]
        if length == 0:
            offset += 1
            break
        elif (length & 0xc0) == 0xc0:
            # Compression pointer in query question is invalid RFC 1035 for question, but handle safely
            offset += 2
            break
        else:
            offset += 1
            if offset + length > len(data):
                return None
            labels.append(data[offset:offset+length].decode("utf-8", errors="ignore"))
            offset += length

    if offset + 4 > len(data):
        return None

    qtype, qclass = struct.unpack("!HH", data[offset:offset+4])
    domain = ".".join(labels).lower()
    return tx_id, domain, qtype, qclass, offset + 4


def build_sinkhole_response(query_data: bytes, question_end: int, qtype: int) -> bytes:
    """Builds RFC 1035 synthetic sinkhole response (0.0.0.0 or ::)."""
    tx_id, flags, _, _, _, _ = struct.unpack("!HHHHHH", query_data[:12])
    # Response flags: QR=1, AA=1, RD preserved, RA=1, RCODE=0 (NOERROR)
    resp_flags = 0x8180 | (flags & 0x0100)
    question_part = query_data[12:question_end]

    if qtype == 1:  # A record -> 0.0.0.0
        # Name pointer 0xc00c, TYPE 1, CLASS 1, TTL 300, RDLENGTH 4, RDATA 0.0.0.0
        answer = struct.pack("!HHHIHBBBB", 0xc00c, 1, 1, 300, 4, 0, 0, 0, 0)
        ancount = 1
    elif qtype == 28:  # AAAA record -> ::
        # Name pointer 0xc00c, TYPE 28, CLASS 1, TTL 300, RDLENGTH 16, RDATA 16 zeros
        answer = struct.pack("!HHHIH", 0xc00c, 28, 1, 300, 16) + (b"\x00" * 16)
        ancount = 1
    else:  # Return NOERROR with 0 answers
        answer = b""
        ancount = 0

    header = struct.pack("!HHHHHH", tx_id, resp_flags, 1, ancount, 0, 0)
    return header + question_part + answer


def build_servfail_response(query_data: bytes) -> bytes:
    """Builds SERVFAIL response when upstream cannot be contacted."""
    if len(query_data) < 12:
        return b""
    tx_id, flags, qdcount, _, _, _ = struct.unpack("!HHHHHH", query_data[:12])
    resp_flags = 0x8182 | (flags & 0x0100)  # RCODE 2 = SERVFAIL
    return struct.pack("!HHHHHH", tx_id, resp_flags, qdcount, 0, 0, 0) + query_data[12:]


class AdShieldServer:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()
        self.start_time = time.time()

        os.makedirs(DEFAULT_BLOCKLIST_DIR, exist_ok=True)
        self.filter_engine = FilterEngine(DEFAULT_BLOCKLIST_DIR)
        self.cache = DnsCache(max_size=15000, default_ttl=180)

        # Apply initial shield settings
        self.filter_engine.ad_blocking_enabled = self.config.get("ad_blocking", True)
        self.filter_engine.youtube_shield_enabled = self.config.get("youtube_shield", True)
        self.filter_engine.spotify_shield_enabled = self.config.get("spotify_shield", True)
        self.filter_engine.hotstar_shield_enabled = self.config.get("hotstar_shield", True)

        # Recent query logs (in-memory circular buffer)
        self.log_history = deque(maxlen=self.config.get("log_history_limit", 500))
        self.log_lock = asyncio.Lock()

    def _load_config(self) -> Dict[str, Any]:
        config = dict(DEFAULT_CONFIG)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    config.update(user_cfg)
            except Exception as e:
                print(f"[Config] Error loading {self.config_path}: {e}")
        else:
            self._save_config(config)
        return config

    def _save_config(self, config: Dict[str, Any]):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"[Config] Error saving {self.config_path}: {e}")

    def get_upstream_servers(self) -> List[str]:
        custom = self.config.get("custom_upstream", [])
        if custom:
            return custom
        provider = self.config.get("upstream_provider", "cloudflare").lower()
        return UPSTREAM_PROVIDERS.get(provider, UPSTREAM_PROVIDERS["cloudflare"])

    async def forward_upstream(self, query_data: bytes) -> Optional[bytes]:
        """Async forward query to upstream DNS resolvers via UDP with fast fallback."""
        servers = self.get_upstream_servers()
        loop = asyncio.get_running_loop()

        for srv in servers:
            try:
                # Use loop.sock_sendto / recvfrom or asyncio UDP datagram
                future_response = loop.create_future()

                class UpstreamProtocol(asyncio.DatagramProtocol):
                    def datagram_received(self, data, addr):
                        if not future_response.done():
                            future_response.set_result(data)

                    def error_received(self, exc):
                        if not future_response.done():
                            future_response.set_exception(exc)

                transport, _ = await loop.create_datagram_endpoint(
                    lambda: UpstreamProtocol(),
                    remote_addr=(srv, 53)
                )
                try:
                    transport.sendto(query_data)
                    response = await asyncio.wait_for(future_response, timeout=1.8)
                    return response
                finally:
                    transport.close()
            except Exception:
                continue

        return None

    async def process_dns_query(self, query_data: bytes, client_ip: str, protocol: str) -> bytes:
        start_t = time.time()
        parsed = parse_dns_question(query_data)
        if not parsed:
            return b""

        tx_id, domain, qtype, qclass, question_end = parsed
        is_blocked, reason = self.filter_engine.check_domain(domain)

        status_label = "allowed"
        answer_payload = b""

        if is_blocked:
            status_label = "blocked"
            with self.filter_engine.lock:
                self.filter_engine.stats["total_queries"] += 1
                self.filter_engine.stats["blocked_queries"] += 1
            answer_payload = build_sinkhole_response(query_data, question_end, qtype)
        else:
            # Check Cache
            cached = self.cache.get(domain, qtype, tx_id)
            if cached:
                status_label = "cached"
                with self.filter_engine.lock:
                    self.filter_engine.stats["total_queries"] += 1
                    self.filter_engine.stats["allowed_queries"] += 1
                    self.filter_engine.stats["cache_hits"] += 1
                answer_payload = cached
            else:
                # Forward to Upstream
                upstream_resp = await self.forward_upstream(query_data)
                with self.filter_engine.lock:
                    self.filter_engine.stats["total_queries"] += 1
                    self.filter_engine.stats["allowed_queries"] += 1

                if upstream_resp:
                    status_label = "forwarded"
                    self.cache.put(domain, qtype, upstream_resp)
                    answer_payload = upstream_resp
                else:
                    status_label = "servfail"
                    answer_payload = build_servfail_response(query_data)

        elapsed_ms = round((time.time() - start_t) * 1000, 2)

        # Log query
        qtype_str = {1: "A", 28: "AAAA", 5: "CNAME", 15: "MX", 16: "TXT", 65: "HTTPS"}.get(qtype, str(qtype))
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "client_ip": client_ip,
            "protocol": protocol,
            "domain": domain,
            "qtype": qtype_str,
            "status": status_label,
            "reason": reason,
            "latency_ms": elapsed_ms
        }
        async with self.log_lock:
            self.log_history.append(log_entry)

        return answer_payload

    # -------------------------------------------------------------------------
    # Server Protocols
    # -------------------------------------------------------------------------

    async def start_udp_dns(self):
        """Starts UDP DNS on port 53."""
        port = self.config.get("udp_port", 53)
        loop = asyncio.get_running_loop()

        class UdpDnsProtocol(asyncio.DatagramProtocol):
            def __init__(self, server_instance):
                self.server = server_instance
                self.transport = None

            def connection_made(self, transport):
                self.transport = transport

            def datagram_received(self, data, addr):
                asyncio.create_task(self.handle_query(data, addr))

            async def handle_query(self, data, addr):
                try:
                    resp = await self.server.process_dns_query(data, addr[0], "UDP")
                    if resp and self.transport and not self.transport.is_closing():
                        self.transport.sendto(resp, addr)
                except Exception as e:
                    pass

        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda: UdpDnsProtocol(self),
                local_addr=("0.0.0.0", port)
            )
            print(f"[AdShield] UDP DNS listening on 0.0.0.0:{port}")
        except Exception as e:
            print(f"[AdShield] Could not bind UDP port {port}: {e}")

    async def start_tcp_dns(self):
        """Starts TCP DNS on port 53."""
        port = self.config.get("tcp_port", 53)

        async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            client_ip = writer.get_extra_info("peername")[0]
            try:
                while True:
                    length_bytes = await reader.readexactly(2)
                    length = struct.unpack("!H", length_bytes)[0]
                    query_data = await reader.readexactly(length)
                    resp = await self.process_dns_query(query_data, client_ip, "TCP")
                    if resp:
                        writer.write(struct.pack("!H", len(resp)) + resp)
                        await writer.drain()
            except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError):
                pass
            finally:
                writer.close()
                await writer.wait_closed()

        try:
            server = await asyncio.start_server(handle_tcp_client, "0.0.0.0", port)
            print(f"[AdShield] TCP DNS listening on 0.0.0.0:{port}")
        except Exception as e:
            print(f"[AdShield] Could not bind TCP port {port}: {e}")

    async def start_dot_server(self):
        """
        Starts DNS-over-TLS (DoT, RFC 7858) on port 853.
        This powers native Android 'Private DNS' and encrypted system resolvers.
        """
        port = self.config.get("dot_port", 853)
        ssl_ctx = self._create_ssl_context()
        if not ssl_ctx:
            print("[AdShield] TLS certificates not found or invalid. DoT server disabled.")
            print("           Run ./setup_vps.sh to obtain Let's Encrypt certificates.")
            return

        async def handle_dot_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            peer = writer.get_extra_info("peername")
            client_ip = peer[0] if peer else "unknown"
            try:
                # Android keeps TLS connections open persistently for Private DNS
                while True:
                    length_bytes = await reader.readexactly(2)
                    length = struct.unpack("!H", length_bytes)[0]
                    query_data = await reader.readexactly(length)
                    resp = await self.process_dns_query(query_data, client_ip, "DoT")
                    if resp:
                        writer.write(struct.pack("!H", len(resp)) + resp)
                        await writer.drain()
            except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError, ssl.SSLError):
                pass
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        try:
            server = await asyncio.start_server(handle_dot_client, "0.0.0.0", port, ssl=ssl_ctx)
            print(f"[AdShield] DNS-over-TLS (DoT / Private DNS) active on 0.0.0.0:{port}")
        except Exception as e:
            print(f"[AdShield] Could not bind DoT port {port}: {e}")

    async def start_doh_and_web_server(self):
        """
        Starts HTTP/HTTPS server handling:
        1. /dns-query (RFC 8484 DNS over HTTPS)
        2. Web Dashboard UI
        3. REST Management API
        """
        web_port = self.config.get("web_port", 8080)
        doh_port = self.config.get("doh_port", 443)
        ssl_ctx = self._create_ssl_context()

        # Start Plain HTTP Web Dashboard (port 8080)
        try:
            server_web = await asyncio.start_server(
                lambda r, w: self._handle_http_connection(r, w, is_ssl=False),
                "0.0.0.0", web_port
            )
            print(f"[AdShield] Web Dashboard & API active at http://0.0.0.0:{web_port}")
        except Exception as e:
            print(f"[AdShield] Could not bind Web port {web_port}: {e}")

        # Start HTTPS DoH + Admin on port 443 if SSL is available
        if ssl_ctx:
            try:
                server_doh = await asyncio.start_server(
                    lambda r, w: self._handle_http_connection(r, w, is_ssl=True),
                    "0.0.0.0", doh_port, ssl=ssl_ctx
                )
                print(f"[AdShield] DNS-over-HTTPS (DoH) active at https://0.0.0.0:{doh_port}/dns-query")
            except Exception as e:
                print(f"[AdShield] Could not bind DoH HTTPS port {doh_port}: {e}")

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        cert = self.config.get("tls_cert_file")
        key = self.config.get("tls_key_file")
        if not cert or not key or not os.path.exists(cert) or not os.path.exists(key):
            return None
        try:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=cert, keyfile=key)
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            return ctx
        except Exception as e:
            print(f"[AdShield] SSL Context creation failed: {e}")
            return None

    async def _handle_http_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, is_ssl: bool):
        peer = writer.get_extra_info("peername")
        client_ip = peer[0] if peer else "127.0.0.1"

        try:
            # Read HTTP request header
            line = await reader.readline()
            if not line:
                return

            req_line = line.decode("utf-8", errors="ignore").strip()
            parts = req_line.split()
            if len(parts) < 2:
                return

            method = parts[0].upper()
            raw_path = parts[1]

            # Read headers
            headers = {}
            content_length = 0
            while True:
                h_line = await reader.readline()
                if not h_line or h_line == b"\r\n" or h_line == b"\n":
                    break
                decoded = h_line.decode("utf-8", errors="ignore").strip()
                if ":" in decoded:
                    k, v = decoded.split(":", 1)
                    headers[k.strip().lower()] = v.strip()
                    if k.strip().lower() == "content-length":
                        content_length = int(v.strip())

            body = b""
            if content_length > 0:
                body = await reader.readexactly(content_length)

            parsed_url = urllib.parse.urlparse(raw_path)
            path = parsed_url.path

            # -------------------------------------------------------------
            # Route 1: RFC 8484 DNS over HTTPS (/dns-query)
            # -------------------------------------------------------------
            if path == "/dns-query":
                dns_wire = b""
                if method == "POST":
                    dns_wire = body
                elif method == "GET":
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    dns_b64 = query_params.get("dns", [""])[0]
                    if dns_b64:
                        # Base64url padding fix
                        dns_b64 += "=" * ((4 - len(dns_b64) % 4) % 4)
                        dns_wire = base64.urlsafe_b64decode(dns_b64)

                if dns_wire:
                    resp = await self.process_dns_query(dns_wire, client_ip, "DoH")
                    headers_out = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/dns-message\r\n"
                        f"Content-Length: {len(resp)}\r\n"
                        "Cache-Control: max-age=60\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        "\r\n"
                    )
                    writer.write(headers_out.encode("utf-8") + resp)
                    await writer.drain()
                    return
                else:
                    self._send_http_response(writer, 400, "Bad Request", "Missing DNS message")
                    return

            # -------------------------------------------------------------
            # Route 2: REST APIs
            # -------------------------------------------------------------
            if path == "/api/stats":
                data = self._get_full_stats()
                self._send_json_response(writer, 200, data)
                return

            if path == "/api/logs":
                async with self.log_lock:
                    logs = list(reversed(self.log_history))
                self._send_json_response(writer, 200, {"logs": logs})
                return

            if path == "/api/settings" and method == "POST":
                try:
                    payload = json.loads(body.decode("utf-8"))
                    if "ad_blocking" in payload:
                        self.filter_engine.ad_blocking_enabled = bool(payload["ad_blocking"])
                        self.config["ad_blocking"] = bool(payload["ad_blocking"])
                    if "youtube_shield" in payload:
                        self.filter_engine.youtube_shield_enabled = bool(payload["youtube_shield"])
                        self.config["youtube_shield"] = bool(payload["youtube_shield"])
                    if "spotify_shield" in payload:
                        self.filter_engine.spotify_shield_enabled = bool(payload["spotify_shield"])
                        self.config["spotify_shield"] = bool(payload["spotify_shield"])
                    if "hotstar_shield" in payload:
                        self.filter_engine.hotstar_shield_enabled = bool(payload["hotstar_shield"])
                        self.config["hotstar_shield"] = bool(payload["hotstar_shield"])
                    if "upstream_provider" in payload:
                        self.config["upstream_provider"] = str(payload["upstream_provider"])
                    self._save_config(self.config)
                    self._send_json_response(writer, 200, {"status": "ok", "config": self.config})
                except Exception as e:
                    self._send_json_response(writer, 400, {"error": str(e)})
                return

            if path == "/api/rules" and method == "GET":
                data = {
                    "whitelist": sorted(list(self.filter_engine.custom_whitelist)),
                    "blacklist": sorted(list(self.filter_engine.custom_blacklist)),
                    "community_count": len(self.filter_engine.community_blocklist)
                }
                self._send_json_response(writer, 200, data)
                return

            if path == "/api/rules/add" and method == "POST":
                payload = json.loads(body.decode("utf-8"))
                rule_type = payload.get("type", "whitelist")
                domain = normalize_domain(payload.get("domain", ""))
                if domain:
                    with self.filter_engine.lock:
                        if rule_type == "whitelist":
                            self.filter_engine.custom_whitelist.add(domain)
                        else:
                            self.filter_engine.custom_blacklist.add(domain)
                        self.filter_engine.save_custom_rules()
                    self._send_json_response(writer, 200, {"status": "ok", "domain": domain})
                else:
                    self._send_json_response(writer, 400, {"error": "Invalid domain"})
                return

            if path == "/api/rules/remove" and method == "POST":
                payload = json.loads(body.decode("utf-8"))
                rule_type = payload.get("type", "whitelist")
                domain = normalize_domain(payload.get("domain", ""))
                if domain:
                    with self.filter_engine.lock:
                        if rule_type == "whitelist":
                            self.filter_engine.custom_whitelist.discard(domain)
                        else:
                            self.filter_engine.custom_blacklist.discard(domain)
                        self.filter_engine.save_custom_rules()
                    self._send_json_response(writer, 200, {"status": "ok"})
                else:
                    self._send_json_response(writer, 400, {"error": "Invalid domain"})
                return

            if path == "/api/update-blocklists" and method == "POST":
                success, msg = self.filter_engine.update_community_list_from_url()
                self._send_json_response(writer, 200 if success else 500, {"status": success, "message": msg})
                return

            # -------------------------------------------------------------
            # Route 3: Static Dashboard UI
            # -------------------------------------------------------------
            file_path = os.path.join(DEFAULT_STATIC_DIR, "index.html" if path in ("/", "") else path.lstrip("/"))
            if os.path.exists(file_path) and not os.path.isdir(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime = {
                    ".html": "text/html; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".js": "application/javascript; charset=utf-8",
                    ".json": "application/json",
                    ".svg": "image/svg+xml",
                    ".png": "image/png"
                }.get(ext, "application/octet-stream")

                with open(file_path, "rb") as f:
                    content = f.read()

                headers_out = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {mime}\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "\r\n"
                )
                writer.write(headers_out.encode("utf-8") + content)
                await writer.drain()
                return

            self._send_http_response(writer, 404, "Not Found", "Page Not Found")
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    def _send_json_response(self, writer: asyncio.StreamWriter, status: int, data: Any):
        body = json.dumps(data).encode("utf-8")
        headers = (
            f"HTTP/1.1 {status} OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "\r\n"
        )
        writer.write(headers.encode("utf-8") + body)

    def _send_http_response(self, writer: asyncio.StreamWriter, status: int, title: str, body_text: str):
        content = f"<h1>{status} {title}</h1><p>{body_text}</p>".encode("utf-8")
        headers = (
            f"HTTP/1.1 {status} {title}\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(content)}\r\n"
            "\r\n"
        )
        writer.write(headers.encode("utf-8") + content)

    def _get_full_stats(self) -> Dict[str, Any]:
        uptime_sec = int(time.time() - self.start_time)
        hrs = uptime_sec // 3600
        mins = (uptime_sec % 3600) // 60
        secs = uptime_sec % 60
        uptime_fmt = f"{hrs}h {mins}m {secs}s"

        with self.filter_engine.lock:
            total = self.filter_engine.stats["total_queries"]
            blocked = self.filter_engine.stats["blocked_queries"]
            allowed = self.filter_engine.stats["allowed_queries"]
            block_rate = round((blocked / total * 100), 1) if total > 0 else 0.0

            stats_copy = dict(self.filter_engine.stats)
            stats_copy["block_rate_pct"] = block_rate
            stats_copy["community_rules_count"] = len(self.filter_engine.community_blocklist)
            stats_copy["whitelist_count"] = len(self.filter_engine.custom_whitelist)
            stats_copy["blacklist_count"] = len(self.filter_engine.custom_blacklist)

        cache_stats = self.cache.get_stats()

        return {
            "server_hostname": self.config.get("server_hostname", "dns.example.com"),
            "upstream_provider": self.config.get("upstream_provider", "cloudflare"),
            "uptime": uptime_fmt,
            "stats": stats_copy,
            "cache": cache_stats,
            "shields": {
                "ad_blocking": self.filter_engine.ad_blocking_enabled,
                "youtube_shield": self.filter_engine.youtube_shield_enabled,
                "spotify_shield": self.filter_engine.spotify_shield_enabled,
                "hotstar_shield": self.filter_engine.hotstar_shield_enabled,
            }
        }

    async def run(self):
        print("=" * 64)
        print("          AdShield High-Performance Private DNS Server        ")
        print("          Native DoT (Port 853) & DoH (Port 443) Active       ")
        print("=" * 64)

        await self.start_udp_dns()
        await self.start_tcp_dns()
        await self.start_dot_server()
        await self.start_doh_and_web_server()

        print("[AdShield] System successfully initialized and running.")

        # Keep server running indefinitely
        while True:
            await asyncio.sleep(3600)


def main():
    server = AdShieldServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n[AdShield] Shutting down gracefully...")


if __name__ == "__main__":
    main()
