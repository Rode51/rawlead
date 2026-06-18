#!/usr/bin/env python3
"""Mechanic P0: MATCH_PUSH runtime + push:match log grep on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def run(name: str, cmd: str) -> str:
    print(f"=== {name} ===")
    code, out, err = ssh.run(cmd, check=False)
    text = (out or err or "").strip()
    print(text)
    if code != 0:
        print(f"(exit {code})")
    print()
    return text


def main() -> int:
    run("status", "systemctl is-active rawlead-radar rawlead-api rawlead-bot-poll")
    run("env_site", r"grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)=' /opt/rawlead/.env.site || echo NO_MATCH_PUSH_IN_ENV_SITE")
    run(
        "runtime_env",
        r"""PID=$(systemctl show -p MainPID --value rawlead-radar)
echo PID=$PID
if [ -n "$PID" ] && [ "$PID" != "0" ]; then
  tr '\0' '\n' < /proc/$PID/environ | grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG|RADAR_PROFILE)=' || echo NO_MATCH_PUSH_IN_RUNTIME
else
  echo NO_PID
fi""",
    )
    run("proc_start", "systemctl show rawlead-radar -p ActiveEnterTimestamp --value")
    run(
        "o250c_code",
        "grep -c tg_http_request /opt/rawlead/src/match_push.py; "
        "grep -c _push_km_for_lead_row /opt/rawlead/src/match_push.py; "
        "grep -c 'push:match:skip' /opt/rawlead/src/match_push.py",
    )
    run(
        "push_log_recent",
        r"grep -E 'push:match' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -30 || echo NO_PUSH_MATCH_LINES",
    )
    run(
        "lead_27k",
        r"""cd /opt/rawlead && .venv/bin/python <<'PY'
import os
from dotenv import load_dotenv
import psycopg
load_dotenv('.env')
load_dotenv('.env.site', override=True)
with psycopg.connect(os.environ['DATABASE_URL']) as c:
    cur = c.cursor()
    cur.execute('SELECT count(*) FROM match_push_log')
    print('match_push_log_total', cur.fetchone()[0])
    cur.execute("SELECT count(*) FROM match_push_log WHERE created_at > now() - interval '24 hours'")
    print('match_push_log_24h', cur.fetchone()[0])
    cur.execute("SELECT id, source, is_visible, left(title,40), created_at FROM leads WHERE id >= 27000 ORDER BY id DESC LIMIT 8")
    print('recent_leads_27k:')
    for r in cur.fetchall():
        print(' ', r)
    cur.execute("SELECT u.tg_user_id, u.push_min_match, u.push_enabled, u.tg_chat_id IS NOT NULL AS has_chat FROM users u WHERE u.tg_user_id IN (5177575757, 8688264540)")
    print('owner_monica:')
    for r in cur.fetchall():
        print(' ', r)
PY""",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
