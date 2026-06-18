"""Post-quiz: owner tags + feed keyword_match sample."""
from __future__ import annotations

import json
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
        cur.execute("SELECT COUNT(*) FROM user_tags WHERE user_id=%s::uuid", (OWNER,))
        print('owner_tag_count', cur.fetchone()[0])
        cur.execute(
            "SELECT tag, weight, last_active_at IS NOT NULL, interaction_count "
            "FROM user_tags WHERE user_id=%s::uuid ORDER BY weight DESC LIMIT 20",
            (OWNER,),
        )
        for r in cur.fetchall():
            print('tag', r)
        cur.execute("SELECT plan, is_active FROM subscriptions WHERE user_id=%s::uuid", (OWNER,))
        print('sub', cur.fetchone())
        cur.execute(
            "SELECT feed_prefs FROM users WHERE id=%s::uuid",
            (OWNER,),
        )
        print('feed_prefs', cur.fetchone()[0])
        cur.execute(
            "SELECT id, source, tags, ai_score FROM leads ORDER BY created_at DESC LIMIT 3"
        )
        for r in cur.fetchall():
            print('lead', r[0], r[1], (r[2] or [])[:5], r[3])
PY
curl -fsS -m 8 'http://127.0.0.1:8000/v1/feed?limit=2&sort=time' -H 'X-Rawlead-User-Id: 00000000-0000-0000-0000-000000000001' 2>/dev/null | head -c 1200 || echo feed_fail
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    for line in ((out or "") + (err or "")).splitlines():
        print(line.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
