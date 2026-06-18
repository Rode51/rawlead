"""O271 post-migrate: TG bots + auth diagnostics."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
echo ===DB===
grep -E '^(DATABASE_URL|NEON_DATABASE_URL)=' /opt/rawlead/.env.site 2>/dev/null | sed 's/:\/\/[^:]*:/:\/\/***:/g'
echo ===SERVICES===
systemctl is-active postgresql rawlead-api rawlead-radar rawlead-bot-poll 2>/dev/null
systemctl is-active rawlead-radar-legacy 2>/dev/null || true
echo ===BOT_UNITS===
systemctl list-units 'rawlead*' --no-pager 2>/dev/null | grep -E 'rawlead|UNIT' | head -15
echo ===API_HEALTH===
curl -fsS -m 6 http://127.0.0.1:8000/health 2>&1 || echo fail
echo ===AUTH_LOG_API===
journalctl -u rawlead-api -n 80 --no-pager 2>/dev/null | grep -iE 'auth|bot_|telegram|jwt|error|traceback|psycopg' | tail -25
echo ===AUTH_LOG_RADAR===
grep -iE 'bot_auth|bot_login|auth:|telegram|jwt|fail|err' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -20
echo ===AUTH_BOT_SESSIONS===
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv('/opt/rawlead/.env.site', override=True)
url = os.environ.get('DATABASE_URL','')
print('db=' + ('local' if '127.0.0.1' in url else 'neon/other'))
try:
    import psycopg
    with psycopg.connect(url, connect_timeout=6) as c:
        with c.cursor() as cur:
            for t in ('auth_bot_sessions','users','subscriptions'):
                cur.execute("SELECT to_regclass(%s)", (t,))
                print(t + '=' + str(cur.fetchone()[0]))
            cur.execute("SELECT COUNT(*) FROM auth_bot_sessions")
            print('auth_sessions=' + str(cur.fetchone()[0]))
            cur.execute(
                "SELECT id, tg_user_id, plan, is_active FROM users u "
                "JOIN subscriptions s ON s.user_id=u.id "
                "WHERE u.id='00000000-0000-0000-0000-000000000001'::uuid"
            )
            print('owner=' + str(cur.fetchone()))
except Exception as e:
    print('db_err=' + str(e)[:200])
PY
echo ===BOT_POLL===
journalctl -u rawlead-bot-poll -n 50 --no-pager 2>/dev/null | grep -iE 'error|auth|fail|traceback' | tail -20
echo ===API_AUTH_ERR===
journalctl -u rawlead-api -n 300 --no-pager 2>/dev/null | grep -iE 'authorize_bot|auth_bot_complete' | tail -10
echo ===SCHEMA===
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv('/opt/rawlead/.env.site', override=True)
import psycopg
with psycopg.connect(os.environ['DATABASE_URL']) as c:
    with c.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='auth_bot_sessions' ORDER BY ordinal_position")
        print('auth_cols=' + str([r[0] for r in cur.fetchall()]))
        cur.execute("SELECT to_regclass('match_push_log')")
        print('match_push_log=' + str(cur.fetchone()[0]))
        cur.execute("SELECT token_hash, tg_user_id, authorized_at IS NOT NULL, consumed_at IS NOT NULL FROM auth_bot_sessions ORDER BY created_at DESC LIMIT 3")
        for r in cur.fetchall():
            print('sess=' + str(r))
PY
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    for line in ((out or "") + (err or "")).splitlines():
        print(re.sub(r"postgresql://[^@\s]+@", "postgresql://***@", line).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
