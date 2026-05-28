#!/usr/bin/env bash
# Отдельный poller @rawlead_bot — не гасится при systemctl stop rawlead-radar.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "run-bot-poll: нет $PY" >&2
  exit 1
fi

export RADAR_PROFILE="${RADAR_PROFILE:-site}"
export RAWLEAD_BOT_POLL_EXTERNAL=1

exec "$PY" -u scripts/bot_poll_main.py
