#!/usr/bin/env python3
"""O78 hotfix: SQL %% + ops gate + admin Bearer-only."""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/owner_admin.py", "src/api_server.py")


def _ensure_ops_key() -> str:
    _, out, _ = ssh.run(
        "grep '^RAWLEAD_OPS_KEY=' /opt/rawlead/.env 2>/dev/null | head -1",
        check=False,
    )
    line = (out or "").strip()
    if line.startswith("RAWLEAD_OPS_KEY=") and len(line) > 16:
        return line.split("=", 1)[1].strip()
    key = secrets.token_urlsafe(24)
    ssh.run(
        f"grep -q '^RAWLEAD_OPS_KEY=' /opt/rawlead/.env 2>/dev/null || "
        f"echo 'RAWLEAD_OPS_KEY={key}' >> /opt/rawlead/.env",
        check=False,
    )
    _, out2, _ = ssh.run(
        "grep '^RAWLEAD_OPS_KEY=' /opt/rawlead/.env | tail -1",
        check=False,
    )
    val = (out2 or "").strip().split("=", 1)
    return val[1].strip() if len(val) == 2 else key


def main() -> int:
    print("=== O78 ops hotfix deploy ===")
    ops_key = _ensure_ops_key()
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "curl -sf -o /dev/null -w 'dash_no_auth=%{http_code}\\n' "
        "http://127.0.0.1:8000/v1/admin/dashboard && "
        "curl -sf -o /dev/null -w 'ops_no_key=%{http_code}\\n' "
        "http://127.0.0.1:8000/ops/ && "
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
        "\"import os,sys; sys.path.insert(0,'src'); "
        "from dotenv import load_dotenv; load_dotenv('.env'); "
        "from owner_admin import fetch_dashboard; "
        "d=fetch_dashboard(os.environ['DATABASE_URL']); "
        "print('visits', d['today']['visits'], 'leads', d['feed']['visible_count'])\"",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = (
        "active" in text
        and "dash_no_auth=401" in text
        and "ops_no_key=404" in text
        and "visits" in text
    )
    print(f"OPS_URL=https://rawlead.ru/ops/?key={ops_key}")
    print("O78 OPS HOTFIX OK" if ok else "O78 OPS HOTFIX — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
