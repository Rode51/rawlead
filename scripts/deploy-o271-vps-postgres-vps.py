#!/usr/bin/env python3
"""O271 deploy: upload sql + migrate script, fresh VPS Postgres, restart API/radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_REMOTE_ROOT = "/opt/rawlead"
_MIGRATE = f"{_REMOTE_ROOT}/scripts/migrate_neon_to_vps_postgres.py"


def _upload_tree() -> None:
    sql_dir = _ROOT / "sql"
    for path in sorted(sql_dir.glob("*.sql")):
        remote = f"{_REMOTE_ROOT}/sql/{path.name}"
        ssh.upload(path, remote)
    ssh.upload(_ROOT / "scripts" / "migrate_neon_to_vps_postgres.py", _MIGRATE)


def main() -> int:
    print("O271: stop radar/api (brief)")
    ssh.run("systemctl stop rawlead-radar rawlead-api || true", check=False)

    print("O271: upload sql + migrate script")
    _upload_tree()

    remote = f"""
set -euo pipefail
cd {_REMOTE_ROOT}
chown rawlead:rawlead scripts/migrate_neon_to_vps_postgres.py sql/*.sql 2>/dev/null || true
{_REMOTE_ROOT}/.venv/bin/python {_MIGRATE} --apply --backfill-leads --backfill-limit 800
systemctl start rawlead-api rawlead-radar
sleep 3
systemctl is-active rawlead-api rawlead-radar postgresql
curl -fsS http://127.0.0.1:8000/health || curl -fsS http://127.0.0.1:8000/api/health || true
"""
    _, out, err = ssh.run(remote.strip(), check=False)
    text = (out or "") + (err or "")
    for line in text.splitlines():
        safe = line
        if "postgresql://" in safe:
            import re

            safe = re.sub(r"postgresql://[^@\s]+@", "postgresql://***@", safe)
        print(safe.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
