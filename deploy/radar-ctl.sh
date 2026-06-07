#!/usr/bin/env bash
# Безопасный wrapper: только stop/start/status для rawlead-radar[*].
# Вызывать: sudo /opt/rawlead/deploy/radar-ctl.sh <cmd> <site|legacy>
set -euo pipefail

CMD="${1:-}"
PROFILE="${2:-}"

case "$CMD" in
  stop | start | restart | status) ;;
  *)
    echo "usage: radar-ctl.sh {stop|start|restart|status} {site|legacy}" >&2
    exit 2
    ;;
esac

case "$PROFILE" in
  site) UNIT=rawlead-radar ;;
  legacy) UNIT=rawlead-radar-legacy ;;
  *)
    echo "unknown profile: $PROFILE" >&2
    exit 2
    ;;
esac

case "$CMD" in
  stop) systemctl stop "$UNIT" ;;
  start) systemctl start "$UNIT" ;;
  restart) systemctl restart "$UNIT" ;;
  status) systemctl is-active "$UNIT" ;;
esac
