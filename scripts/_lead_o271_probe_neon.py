"""O271 probe: can Neon accept pg_dump (read-only, no service stop)."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
which pg_dump || apt-get install -y -qq postgresql-client
cd /opt/rawlead
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src /opt/rawlead/.venv/bin/python - <<'PY'
import os, subprocess, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/opt/rawlead/.env.site", override=True)
url = os.environ.get("DATABASE_URL", "")
if not url:
    print("NO_DATABASE_URL"); sys.exit(2)
host = "neon" if "neon" in url else "other"
print("DB_HOST_KIND=" + host)
r = subprocess.run(
    ["pg_dump", url, "--schema-only"],
    capture_output=True, text=True, timeout=120,
)
print("PROBE_EXIT=" + str(r.returncode))
if r.stdout:
    print("SCHEMA_HEAD:")
    print("\n".join(r.stdout.splitlines()[:8]))
if r.stderr:
    print("ERR_TAIL:")
    for line in r.stderr.strip().splitlines()[-5:]:
        print(line.replace(url.split("@")[0].split("//")[1] if "@" in url else "", "***"))
PY
"""


def redact(s: str) -> str:
    return re.sub(r"postgresql://[^@\s]+@", "postgresql://***@", s)


def main() -> int:
    _, out, err = ssh.run(REMOTE, False)
    for line in ((out or "") + (err or "")).splitlines():
        print(redact(line).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
