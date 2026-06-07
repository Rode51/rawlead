#!/usr/bin/env bash
# Безопасный wrapper: только stop/start/restart/status для rawlead-bot-poll.
# Вызывать: sudo /opt/rawlead/deploy/bot-ctl.sh <cmd>
set -euo pipefail

CMD="${1:-}"
UNIT=rawlead-bot-poll

case "$CMD" in
  stop | start | restart | status) ;;
  *)
    echo "usage: bot-ctl.sh {stop|start|restart|status}" >&2
    exit 2
    ;;
esac

case "$CMD" in
  stop) systemctl stop "$UNIT" ;;
  start) systemctl start "$UNIT" ;;
  restart) systemctl restart "$UNIT" ;;
  status) systemctl is-active "$UNIT" ;;
esac
