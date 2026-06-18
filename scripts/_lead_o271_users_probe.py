"""Check all users and tags; test /v1/me/tags path."""
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
with psycopg.connect(os.environ['DATABASE_URL']) as c:
    with c.cursor() as cur:
        cur.execute(
            "SELECT u.id, u.tg_user_id, u.tg_username, s.plan, "
            "(SELECT COUNT(*) FROM user_tags t WHERE t.user_id=u.id) AS ntags "
            "FROM users u LEFT JOIN subscriptions s ON s.user_id=u.id ORDER BY ntags DESC"
        )
        for r in cur.fetchall():
            print('user', r)
PY
grep -E 'restTags|restFeed|apiBase' /opt/rawlead/wordpress/wp-content/themes/rawlead-kadence-child/functions.php 2>/dev/null | head -5
journalctl -u rawlead-api -n 100 --no-pager 2>/dev/null | grep -iE '/v1/me/tags|me/tags' | tail -10
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    for line in ((out or "") + (err or "")).splitlines():
        print(line.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
