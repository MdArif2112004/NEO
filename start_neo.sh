#!/usr/bin/env bash
# start_neo.sh — NEO master boot sequence (Linux)
# ===============================================
# Replaces the old start_neo.bat. Launches the alerting / background matrix
# detached, so closing the terminal does not kill them.
#
# Usage:  ./start_neo.sh
# Stop:   python3 -c "from neo.tools.cold_reboot import cold_reboot; cold_reboot()"
#         or: pkill -f reddit_bounty_tracker.py (etc.)

set -u

# Always run from the repo root, no matter where this is called from
cd "$(dirname "$(readlink -f "$0")")" || exit 1

# Keep the launcher itself executable (survives zip/Windows copies)
chmod +x "$0" 2>/dev/null || true

# Load repo-local secrets so the launched scripts inherit them (none of the boot
# scripts call load_dotenv themselves). `set -a` exports everything sourced.
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
    echo "🔐 [start_neo] loaded .env"
fi

[ -n "${NEO_TELEGRAM_TOKEN:-}" ] || echo "⚠️  [start_neo] NEO_TELEGRAM_TOKEN not set — telegram_router will idle"
[ -n "${DISCORD_BOT_TOKEN:-}" ] || echo "⚠️  [start_neo] DISCORD_BOT_TOKEN not set — discord spider will idle"

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Stability delay — mirrors the old `timeout /t 5` in start_neo.bat
sleep 5

launch() {
    local script="$1"
    local name
    name="$(basename "$script" .py)"
    if [ ! -f "$script" ]; then
        echo "⚠️  [start_neo] missing: $script — skipped"
        return 0
    fi
    nohup python3 "$script" >> "$LOG_DIR/${name}.log" 2>&1 &
    echo "🚀 [start_neo] $script started (pid $!) → $LOG_DIR/${name}.log"
}

echo "🟢 [start_neo] Igniting NEO background matrix..."
launch reddit_bounty_tracker.py
launch telegram_router.py
launch voice.py
launch notification_server.py

echo "✅ [start_neo] Boot sequence complete. Logs in $LOG_DIR/"