#!/usr/bin/env bash
# Legacy dogfood 24/7 на VPS: Neon → FILTERS_LEGACY → @FLPARSINGBOT. Без main/tg_main.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "run-radar-legacy: нет $PY" >&2
  exit 1
fi

export RADAR_PROFILE="${RADAR_PROFILE:-legacy}"

exec "$PY" -u src/neon_legacy_consumer.py --profile legacy
