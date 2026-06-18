"""O271: owner tags/skills/quiz state after fresh PG."""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv('/opt/rawlead/.env.site', override=True)
import psycopg
OWNER = '00000000-0000-0000-0000-000000000001'
with psycopg.connect(os.environ['DATABASE_URL']) as c:
    with c.cursor() as cur:
        cur.execute("SELECT tg_user_id, email FROM users WHERE id=%s::uuid", (OWNER,))
        print('owner_user', cur.fetchone())
        cur.execute("SELECT plan, is_active FROM subscriptions WHERE user_id=%s::uuid", (OWNER,))
        print('owner_sub', cur.fetchone())
        cur.execute("SELECT COUNT(*) FROM user_tags WHERE user_id=%s::uuid", (OWNER,))
        print('owner_tag_count', cur.fetchone()[0])
        cur.execute("SELECT tag, weight FROM user_tags WHERE user_id=%s::uuid ORDER BY weight DESC LIMIT 15", (OWNER,))
        for r in cur.fetchall():
            print('tag', r)
        cur.execute("SELECT COUNT(*) FROM users")
        print('users_total', cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM user_tags")
        print('tags_total', cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM leads WHERE ai_score IS NOT NULL")
        print('leads_scored', cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM leads")
        print('leads_total', cur.fetchone()[0])
        for t in ('pending_tags', 'user_feed_prefs'):
            cur.execute("SELECT to_regclass(%s)", (t,))
            print(t, cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM pending_tags WHERE user_id=%s::uuid", (OWNER,))
        print('owner_pending_tags', cur.fetchone()[0])
PY
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    for line in ((out or "") + (err or "")).splitlines():
        print(line.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
