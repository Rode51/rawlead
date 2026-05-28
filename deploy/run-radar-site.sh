#!/usr/bin/env bash
# Site-контур 24/7 на VPS: биржи (main) + TG (tg_main). Без radar_control / пульта.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "run-radar-site: нет $PY" >&2
  exit 1
fi

export RADAR_PROFILE="${RADAR_PROFILE:-site}"

"$PY" -u src/main.py --profile site &
MAIN_PID=$!
"$PY" -u scripts/tg_main.py --profile site &
TG_PID=$!

cleanup() {
  kill "$MAIN_PID" "$TG_PID" 2>/dev/null || true
  wait "$MAIN_PID" "$TG_PID" 2>/dev/null || true
}
trap cleanup TERM INT

# Перезапуск unit, если упал любой воркер
wait -n
EXIT=$?
cleanup
exit "$EXIT"
