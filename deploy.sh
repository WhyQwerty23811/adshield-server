#!/usr/bin/env bash
# Root deployment helper for AdShield Private DNS
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/adshield-server/setup_vps.sh" "$@"

