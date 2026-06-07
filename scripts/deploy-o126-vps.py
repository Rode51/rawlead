#!/usr/bin/env python3
"""O126: category filter = resolve_lead_category + dev niche icon escape (theme)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/lead_category.py",
    "src/api_server.py",
)


def main() -> int:
    print("=== O126 deploy: category filter API ===")
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-radar && systemctl is-active rawlead-api && "
        "grep -c _passes_category_filter /opt/rawlead/src/api_server.py && "
        "grep -c resolve_lead_category /opt/rawlead/src/lead_category.py && "
        "echo o126_api_ok",
        check=False,
    )
    print(out.strip())
    if "o126_api_ok" not in (out or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("API DEPLOY OK")

    print("\n=== O126 backfill (reconcile visible) ===")
    backfill = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "backfill_lead_category.py"), "--reconcile-visible"],
        cwd=str(_ROOT),
        check=False,
    )
    if backfill.returncode != 0:
        print("BACKFILL FAILED — run manually: python scripts/backfill_lead_category.py --reconcile-visible")
        return 1
    print("BACKFILL OK")

    print("\n=== O126-wp: theme 1.18.20 (dev icon escapeHtml) ===")
    theme_rc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
        cwd=str(_ROOT),
        check=False,
    )
    if theme_rc.returncode != 0:
        print("THEME DEPLOY FAILED")
        return 1

    print("\n=== smoke category=dev ===")
    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json,urllib.request; "
            "d=json.loads(urllib.request.urlopen('https://api.rawlead.ru/v1/feed?limit=20&category=dev',timeout=45).read()); "
            "cats={}; "
            "[cats.__setitem__(i.get('category','?'), cats.get(i.get('category','?'),0)+1) for i in d.get('items',[])]; "
            "print('cats', cats); "
            "bad=[c for c in cats if c!='dev']; "
            "raise SystemExit(0 if not bad else 1)",
        ],
        cwd=str(_ROOT),
        check=False,
    )
    if smoke.returncode != 0:
        print("SMOKE WARN — category=dev still mixed; check API cache or backfill")
    else:
        print("SMOKE OK — only dev in feed")

    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
