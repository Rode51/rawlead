#!/usr/bin/env python3
"""O161 deploy: ops password login, SSE log stream, exchange cards, restart_source."""
from __future__ import annotations

import base64
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)

_API_FILES = (
    "src/owner_admin.py",
    "src/api_server.py",
    "src/ops_log_stream.py",
)
_RADAR_FILES = ("src/main.py",)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def _sync_ops_password_vps() -> bool:
    """RAWLEAD_OPS_KEY on VPS = OPS_PASSWORD (or RAWLEAD_OPS_KEY) from local .env."""
    pwd = (os.environ.get("OPS_PASSWORD") or os.environ.get("RAWLEAD_OPS_KEY") or "").strip()
    if not pwd:
        print("WARN: OPS_PASSWORD / RAWLEAD_OPS_KEY not in local .env — skip password sync")
        return False
    b64 = base64.b64encode(pwd.encode("utf-8")).decode("ascii")
    remote_py = f"""python3 <<'PYEOF'
import base64, re
from pathlib import Path
p = Path("/opt/rawlead/.env")
text = p.read_text(encoding="utf-8")
key = base64.b64decode("{b64}").decode("utf-8")
line = "RAWLEAD_OPS_KEY=" + key
if re.search(r"^RAWLEAD_OPS_KEY=", text, re.M):
    text = re.sub(r"^RAWLEAD_OPS_KEY=.*$", line, text, flags=re.M)
else:
    text = text.rstrip() + "\\n" + line + "\\n"
p.write_text(text, encoding="utf-8")
print("ops_key_synced")
PYEOF"""
    _, out, err = ssh.run(remote_py, check=False)
    text = (out or "") + (err or "")
    ok = "ops_key_synced" in text
    print("ops password sync:", "OK" if ok else "CHECK")
    return ok


def main() -> int:
    print("=== O161 deploy: ops pro panel ===")
    _sync_ops_password_vps()
    api_remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out_api, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c ops_login_html /opt/rawlead/src/owner_admin.py && "
        "grep -c iter_radar_log_sse /opt/rawlead/src/ops_log_stream.py && "
        "grep -c '/ops/login' /opt/rawlead/src/api_server.py && "
        "echo o161_api_ok",
        check=False,
    )
    print(out_api.strip())
    if "o161_api_ok" not in (out_api or "") or "active" not in (out_api or ""):
        print("API DEPLOY CHECK - verify manually")
        return 1
    print("API DEPLOY OK")

    radar_remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))
    _, out_radar, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c restart_source_ /opt/rawlead/src/main.py && "
        "echo o161_radar_ok",
        check=False,
    )
    print(out_radar.strip())
    if "o161_radar_ok" not in (out_radar or "") or "active" not in (out_radar or ""):
        print("RADAR DEPLOY CHECK - verify manually")
        return 1
    print("RADAR DEPLOY OK")
    print("DEPLOY OK - smoke: /ops/ login, logs SSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
