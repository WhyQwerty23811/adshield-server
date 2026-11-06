"""
High-Performance In-Memory LRU DNS Cache with Automated TTL Eviction.
Accelerates response times for repeated queries down to < 1ms.
"""

import time
import struct
import threading
from collections import OrderedDict
from typing import Optional, Tuple

class DnsCache:
    def __init__(self, max_size: int = 10000, default_ttl: int = 120):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[Tuple[str, int], Tuple[bytes, float]] = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, domain: str, qtype: int, new_tx_id: int) -> Optional[bytes]:
        key = (domain.lower(), qtype)
        now = time.time()
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            payload, expire_time = self.cache[key]
            if now > expire_time:
                del self.cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1

            # Patch the transaction ID in the cached response (bytes 0..2)
            patched = bytearray(payload)
            if len(patched) >= 2:
                struct.pack_into("!H", patched, 0, new_tx_id)
            return bytes(patched)

    def put(self, domain: str, qtype: int, response_payload: bytes, custom_ttl: Optional[int] = None):
        if not response_payload or len(response_payload) < 12:
            return

        ttl = custom_ttl if custom_ttl is not None else self._extract_min_ttl(response_payload)
        # Clamp TTL between 10s and 3600s
        ttl = max(10, min(3600, ttl))
        expire_time = time.time() + ttl

        key = (domain.lower(), qtype)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = (response_payload, expire_time)

            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def _extract_min_ttl(self, packet: bytes) -> int:
        try:
            _, _, qdcount, ancount, _, _ = struct.unpack("!HHHHHH", packet[:12])
            if ancount == 0:
                return self.default_ttl

            # Skip questions
            offset = 12
            for _ in range(qdcount):
                while offset < len(packet):
                    length = packet[offset]
                    if length == 0:
                        offset += 1
                        break
                    elif (length & 0xc0) == 0xc0:
                        offset += 2
                        break
                    else:
                        offset += 1 + length
                offset += 4  # Skip QTYPE and QCLASS

            # Read first Answer TTL
            if offset + 10 <= len(packet):
                # Skip Answer NAME (can be pointer or labels)
                if (packet[offset] & 0xc0) == 0xc0:
                    offset += 2
                else:
                    while offset < len(packet) and packet[offset] != 0:
                        offset += 1 + packet[offset]
                    offset += 1

                # Answer Header: TYPE (2), CLASS (2), TTL (4), RDLENGTH (2)
                if offset + 10 <= len(packet):
                    _, _, ttl, _ = struct.unpack("!HHIH", packet[offset:offset+10])
                    return ttl
        except Exception:
            pass
        return self.default_ttl

    def clear(self):
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> dict:
        with self.lock:
            total = self.hits + self.misses
            hit_rate = round((self.hits / total * 100), 1) if total > 0 else 0.0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_pct": hit_rate
            }
