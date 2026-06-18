"""O271: quick VPS state after migration attempt."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
echo ===SERVICES===
systemctl is-active postgresql rawlead-api rawlead-radar 2>/dev/null || true
echo ===PG_DB===
sudo -u postgres psql -tAc "SELECT datname FROM pg_database WHERE datname='rawlead'" 2>/dev/null || echo no-db
echo ===ENV===
grep -E '^(DATABASE_URL|NEON_DATABASE_URL)=' /opt/rawlead/.env.site 2>/dev/null | sed 's/:\/\/[^:]*:/:\/\/***:/g' | head -2
echo ===FILES===
test -f /opt/rawlead/data/.pg_local_credentials && echo cred_ok || echo no_cred
test -f /opt/rawlead/scripts/migrate_neon_to_vps_postgres.py && echo script_ok || echo no_script
cd /opt/rawlead
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv('/opt/rawlead/.env.site', override=True)
url = os.environ.get('DATABASE_URL', '')
if '127.0.0.1' in url or 'localhost' in url:
    kind = 'local'
elif 'neon' in url:
    kind = 'neon'
else:
    kind = 'other'
print('db_kind=' + kind)
try:
    import psycopg
    with psycopg.connect(url, connect_timeout=8) as c:
        with c.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM leads')
            print('leads=' + str(cur.fetchone()[0]))
            cur.execute(
                "SELECT plan, is_active, tg_user_id FROM users u "
                "JOIN subscriptions s ON s.user_id=u.id "
                "WHERE u.id='00000000-0000-0000-0000-000000000001'::uuid"
            )
            print('owner=' + str(cur.fetchone()))
except Exception as e:
    print('db_err=' + str(e)[:160])
PY
echo ===HEALTH===
curl -fsS -m 5 http://127.0.0.1:8000/health 2>/dev/null || echo health_fail
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    for line in ((out or "") + (err or "")).splitlines():
        print(re.sub(r"postgresql://[^@\s]+@", "postgresql://***@", line).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
