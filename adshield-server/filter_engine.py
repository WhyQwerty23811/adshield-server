"""
AdShield Filter Engine
Ported and enhanced from Android AdShield (v2.0.0) Java implementation.
Provides multi-layered ad, tracker, and telemetry filtering with strict
streaming guarantees for YouTube, Spotify, and JioHotstar.
"""

import os
import re
import urllib.request
import threading
from typing import Set, Tuple, Optional

# Major mobile & web advertising / tracking networks (RFC / AdShield DomainBlocklist.java)
BUILT_IN_BLOCKED_DOMAINS: Set[str] = {
    # Core Ad Networks
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "adservice.google.com",
    "adnxs.com",
    "advertising.com",
    "adcolony.com",
    "applovin.com",
    "unityads.unity3d.com",
    "vungle.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
    "scorecardresearch.com",
    "quantserve.com",
    "amazon-adsystem.com",
    "popads.net",
    "admob.com",
    "mopub.com",
    "inmobi.com",
    "chartboost.com",
    "ironsrc.com",
    "adjust.com",
    "appsflyer.com",
    "appsflyersdk.com",
    "branch.io",
    "jioads.com",
    "vserve.mobi",
    "imasdk.googleapis.com",
    # Additional mobile analytics & tracker domains
    "telemetry.adcolony.com",
    "ads.unity3d.com",
    "api.vungle.com",
    "pixel.advertising.com",
    "ib.adnxs.com",
    "rtb.unityads.unity3d.com",
    "s.amazon-adsystem.com",
    "aax.amazon-adsystem.com",
    "analytics.google.com",
    "stats.wp.com",
    "track.ironsrc.com"
}

# YouTube Filter (YouTubeFilter.java)
YOUTUBE_AD_DOMAINS: Set[str] = {
    # Only true YouTube endpoints count toward the "YouTube Shield" stat.
    "ad.youtube.com",
    "ads.youtube.com",
    "youtubeads.l.google.com",
    "s.youtube.com",
    "video-stats.l.google.com",
    "partnerad.l.google.com",
}

# Generic Google / DoubleClick ad infrastructure. Still blocked, but counted as a
# normal ad-network block: Play Services, Chrome and most Android apps query these
# constantly, so attributing them to "YouTube" made the dashboard misleading.
GENERIC_GOOGLE_AD_DOMAINS: Set[str] = {
    "googleads.g.doubleclick.net",
    "pubads.g.doubleclick.net",
    "securepubads.g.doubleclick.net",
    "static.doubleclick.net",
    "pagead2.googlesyndication.com",
    "pagead.l.google.com",
    "ade.googlesyndication.com",
    "adclick.g.doubleclick.net",
    "stats.g.doubleclick.net",
    "adservice.google.com",
}

BUILT_IN_BLOCKED_DOMAINS |= GENERIC_GOOGLE_AD_DOMAINS

# Essential YouTube domains that must NEVER be blocked (guarantees video streaming & auth)
ESSENTIAL_YOUTUBE_DOMAINS: Set[str] = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "googlevideo.com",
    "ytimg.com",
    "i.ytimg.com",
    "youtubei.googleapis.com",
}

# Spotify Filter (SpotifyFilter.java)
SPOTIFY_AD_DOMAINS: Set[str] = {
    "aet.spotify.com",
    "adeventtracker.spotify.com",
    "ads-fa.spotify.com",
    "crashdump.spotify.com",
    "adstudio.spotify.com",
    "video-fa.scdn.co",
    "gated.spotify.com",
}

# Essential Spotify domains that must NEVER be blocked (guarantees audio streaming & login)
ESSENTIAL_SPOTIFY_DOMAINS: Set[str] = {
    "spotify.com",
    "www.spotify.com",
    "api.spotify.com",
    "spclient.wg.spotify.com",
    "dealer.spotify.com",
    "ap.spotify.com",
    "login5.spotify.com",
    "i.scdn.co",
    "audio-fa.spotify.com",
    "audio-ak.spotify.com",
    "audio4-ak-spotify-com.akamaized.net",
}

# JioCinema & Hotstar Filter (JioHotstarFilter.java)
HOTSTAR_AD_DOMAINS: Set[str] = {
    "jioads.com",
    "vserve.mobi",
    "imasdk.googleapis.com",
    "ads.hotstar.com",
    "ad.hotstar.com",
    "telemetry.hotstar.com"
}

ESSENTIAL_HOTSTAR_DOMAINS: Set[str] = {
    "hotstar.com",
    "www.hotstar.com",
    "jiocinema.com",
    "www.jiocinema.com",
    "akamaized.net"
}


def normalize_domain(domain: str) -> str:
    if not domain:
        return ""
    d = domain.strip().lower()
    while d.endswith("."):
        d = d[:-1]
    return d


class FilterEngine:
    def __init__(self, blocklists_dir: str):
        self.blocklists_dir = blocklists_dir
        self.lock = threading.RLock()

        # Configurable Shields
        self.ad_blocking_enabled: bool = True
        self.youtube_shield_enabled: bool = True
        self.spotify_shield_enabled: bool = True
        self.hotstar_shield_enabled: bool = True

        # In-memory rule sets
        self.builtin_blocklist: Set[str] = set(BUILT_IN_BLOCKED_DOMAINS)
        self.community_blocklist: Set[str] = set()
        self.custom_whitelist: Set[str] = set()
        self.custom_blacklist: Set[str] = set()

        # Stats counters
        self.stats = {
            "total_queries": 0,
            "blocked_queries": 0,
            "allowed_queries": 0,
            "youtube_blocked": 0,
            "spotify_blocked": 0,
            "hotstar_blocked": 0,
            "cache_hits": 0,
        }

        self.load_all_lists()

    def load_all_lists(self):
        with self.lock:
            self._load_community_blocklist()
            self._load_custom_rules()

    def _load_community_blocklist(self):
        primary_file = os.path.join(self.blocklists_dir, "blocklist.txt")
        downloaded_file = os.path.join(self.blocklists_dir, "blocklist_downloaded.txt")

        target_file = downloaded_file if os.path.exists(downloaded_file) else primary_file
        if not os.path.exists(target_file):
            return

        loaded_set = set()
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Format can be '0.0.0.0 domain.com' or '127.0.0.1 domain.com' or just 'domain.com'
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                        domain = normalize_domain(parts[1])
                    else:
                        domain = normalize_domain(parts[0])

                    if domain and domain not in ("localhost", "broadcasthost", "local"):
                        loaded_set.add(domain)

            self.community_blocklist = loaded_set
            print(f"[FilterEngine] Loaded {len(self.community_blocklist)} community blocklist rules.")
        except Exception as e:
            print(f"[FilterEngine] Error loading blocklist: {e}")

    def _load_custom_rules(self):
        whitelist_path = os.path.join(self.blocklists_dir, "custom_whitelist.txt")
        blacklist_path = os.path.join(self.blocklists_dir, "custom_blacklist.txt")

        if os.path.exists(whitelist_path):
            with open(whitelist_path, "r", encoding="utf-8", errors="ignore") as f:
                self.custom_whitelist = {
                    normalize_domain(line) for line in f if line.strip() and not line.strip().startswith("#")
                }
        else:
            self.custom_whitelist = set()

        if os.path.exists(blacklist_path):
            with open(blacklist_path, "r", encoding="utf-8", errors="ignore") as f:
                self.custom_blacklist = {
                    normalize_domain(line) for line in f if line.strip() and not line.strip().startswith("#")
                }
        else:
            self.custom_blacklist = set()

    def save_custom_rules(self):
        with self.lock:
            whitelist_path = os.path.join(self.blocklists_dir, "custom_whitelist.txt")
            blacklist_path = os.path.join(self.blocklists_dir, "custom_blacklist.txt")

            with open(whitelist_path, "w", encoding="utf-8") as f:
                for d in sorted(self.custom_whitelist):
                    f.write(f"{d}\n")

            with open(blacklist_path, "w", encoding="utf-8") as f:
                for d in sorted(self.custom_blacklist):
                    f.write(f"{d}\n")

    def update_community_list_from_url(self, url: str = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts") -> Tuple[bool, str]:
        downloaded_file = os.path.join(self.blocklists_dir, "blocklist_downloaded.txt")
        temp_file = downloaded_file + ".tmp"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AdShield-Server/2.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_file, "wb") as out:
                out.write(resp.read())

            # Validate before moving
            count = 0
            with open(temp_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        count += 1

            if count < 1000:
                os.remove(temp_file)
                return False, f"Downloaded list has only {count} rules. Minimum required is 1000."

            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            os.rename(temp_file, downloaded_file)

            with self.lock:
                self._load_community_blocklist()
            return True, f"Successfully updated blocklist! Now active: {len(self.community_blocklist)} domains."
        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return False, f"Failed to download blocklist: {e}"

    def is_essential_streaming(self, domain: str) -> bool:
        """Never block essential media infrastructure for audio/video playback."""
        # YouTube
        if domain in ESSENTIAL_YOUTUBE_DOMAINS:
            return True
        if domain.endswith(".googlevideo.com") or domain.endswith(".ytimg.com"):
            return True

        # Spotify
        if domain in ESSENTIAL_SPOTIFY_DOMAINS:
            return True
        if domain.endswith(".scdn.co") and not domain.startswith("video-fa."):
            return True

        # JioCinema / Hotstar
        if domain in ESSENTIAL_HOTSTAR_DOMAINS:
            return True
        if domain.endswith(".hotstar.com") or domain.endswith(".jiocinema.com"):
            # Ensure we only whitelist non-ad hotstar subdomains
            if not any(ad in domain for ad in HOTSTAR_AD_DOMAINS):
                return True

        return False

    def check_domain(self, domain: str) -> Tuple[bool, str]:
        """
        Returns (is_blocked, reason_string).
        Evaluates rules with the exact precedence order as AdShield Android.
        """
        clean = normalize_domain(domain)
        if not clean:
            return False, "allowed:empty"

        if not self.ad_blocking_enabled:
            return False, "allowed:protection_disabled"

        # 1. Whitelist has TOP precedence: if whitelisted, never block
        if self._matches_set_or_parent(clean, self.custom_whitelist):
            return False, "allowed:custom_whitelist"

        # 2. Custom Blacklist check
        if self._matches_set_or_parent(clean, self.custom_blacklist):
            return True, "blocked:custom_blacklist"

        # 3. YouTube specific filtering check
        if self.youtube_shield_enabled:
            if self._is_youtube_ad(clean):
                with self.lock:
                    self.stats["youtube_blocked"] += 1
                return True, "blocked:youtube_shield"

        # 4. Spotify specific filtering check
        if self.spotify_shield_enabled:
            if self._is_spotify_ad(clean):
                with self.lock:
                    self.stats["spotify_blocked"] += 1
                return True, "blocked:spotify_shield"

        # 5. JioCinema & Hotstar specific filtering check
        if self.hotstar_shield_enabled:
            if self._is_hotstar_ad(clean):
                with self.lock:
                    self.stats["hotstar_blocked"] += 1
                return True, "blocked:hotstar_shield"

        # 6. Essential streaming playback check
        if self.is_essential_streaming(clean):
            return False, "allowed:essential_streaming"

        # 7. Built-in ad networks list
        if self._matches_set_or_parent(clean, self.builtin_blocklist):
            return True, "blocked:builtin_ad_network"

        # 8. Large Community Blocklist
        if self._matches_set_or_parent(clean, self.community_blocklist):
            return True, "blocked:community_blocklist"

        return False, "allowed:clean"

    def _matches_set_or_parent(self, domain: str, rule_set: Set[str]) -> bool:
        if not rule_set:
            return False
        if domain in rule_set:
            return True
        # Parent domain match (e.g. ad.doubleclick.net matches doubleclick.net)
        parts = domain.split(".")
        for i in range(1, len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in rule_set:
                return True
        return False

    def _is_youtube_ad(self, domain: str) -> bool:
        if self.is_essential_streaming(domain):
            return False
        if domain in YOUTUBE_AD_DOMAINS:
            return True
        for ad_domain in YOUTUBE_AD_DOMAINS:
            if domain.endswith("." + ad_domain):
                return True
        return False

    def _is_spotify_ad(self, domain: str) -> bool:
        if self.is_essential_streaming(domain):
            return False
        if domain in SPOTIFY_AD_DOMAINS:
            return True
        for ad_domain in SPOTIFY_AD_DOMAINS:
            if domain.endswith("." + ad_domain):
                return True
        return False

    def _is_hotstar_ad(self, domain: str) -> bool:
        if self.is_essential_streaming(domain):
            return False
        if domain in HOTSTAR_AD_DOMAINS:
            return True
        for ad_domain in HOTSTAR_AD_DOMAINS:
            if domain.endswith("." + ad_domain):
                return True
        return False
