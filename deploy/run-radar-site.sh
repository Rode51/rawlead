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

XVFB_PID=""
if [[ "${YOUDO_HEADLESS:-1}" == "0" ]]; then
  export DISPLAY="${YOUDO_DISPLAY:-:99}"
  if command -v Xvfb >/dev/null 2>&1; then
    Xvfb "$DISPLAY" -screen 0 1366x768x24 -nolisten tcp >/dev/null 2>&1 &
    XVFB_PID=$!
    sleep 1
  else
    echo "run-radar-site: YOUDO_HEADLESS=0 but Xvfb missing" >&2
  fi
fi

"$PY" -u src/main.py --profile site &
MAIN_PID=$!
"$PY" -u scripts/tg_main.py --profile site &
TG_PID=$!

cleanup() {
  kill "$MAIN_PID" "$TG_PID" 2>/dev/null || true
  wait "$MAIN_PID" "$TG_PID" 2>/dev/null || true
  if [[ -n "${XVFB_PID:-}" ]]; then
    kill "$XVFB_PID" 2>/dev/null || true
  fi
}
trap cleanup TERM INT

# Перезапуск unit, если упал любой воркер
wait -n
EXIT=$?
cleanup
exit "$EXIT"
