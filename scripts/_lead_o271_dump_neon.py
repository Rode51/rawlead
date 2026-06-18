"""O271 one-shot: Neon dump + VPS Postgres install (remote). No secrets in stdout."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
set -euo pipefail
echo STEP0_services
systemctl is-active rawlead-radar rawlead-api 2>/dev/null || true
echo STEP1_stop
systemctl stop rawlead-radar rawlead-api || true
sleep 2
echo STEP2_install_client
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq postgresql-client >/dev/null
which pg_dump
echo STEP3_dump
sudo -u rawlead bash -lc 'set -a; source /opt/rawlead/.env.site; set +a; pg_dump "$DATABASE_URL" -Fc -f /opt/rawlead/data/neon_pre_migration.dump 2>/tmp/o271_dump.err; echo DUMP_EXIT=$?; ls -lh /opt/rawlead/data/neon_pre_migration.dump 2>/dev/null || true; tail -5 /tmp/o271_dump.err 2>/dev/null'
"""


def redact(s: str) -> str:
    return re.sub(r"postgresql://[^@\s]+@", "postgresql://***@", s)


def main() -> int:
    _, out, err = ssh.run(REMOTE, False)
    text = (out or "") + (err or "")
    for line in text.splitlines():
        print(redact(line).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
