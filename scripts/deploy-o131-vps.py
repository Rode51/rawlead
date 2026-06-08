#!/usr/bin/env python3
"""O131-PERF: feed scan + today_count inline + L2 hot path + WP JS poll 120s."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/match_push.py",
    "src/ai_analyze.py",
)


def main() -> int:
    print("=== O131 deploy: API perf + L2 hot path ===")
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c _feed_scan_limit /opt/rawlead/src/api_server.py && "
        "grep -c fast_shared /opt/rawlead/src/match_push.py && "
        "journalctl -u rawlead-api -n 30 --no-pager | grep -E 'db: (pooler|direct)' | tail -1 && "
        "echo o131_api_ok",
        check=False,
    )
    print(out.strip())
    if "o131_api_ok" not in (out or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("API DEPLOY OK")

    print("\n=== O131-wp: theme 1.18.35 (feed boot parallel + draft poll 120s) ===")
    theme_rc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
        cwd=str(_ROOT),
        check=False,
    )
    if theme_rc.returncode != 0:
        print("THEME DEPLOY FAILED")
        return 1

    print("\n=== smoke feed latency ===")
    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            "import time,json,urllib.request; "
            "t0=time.perf_counter(); "
            "d=json.loads(urllib.request.urlopen('https://api.rawlead.ru/v1/feed?limit=20',timeout=45).read()); "
            "ms=int((time.perf_counter()-t0)*1000); "
            "print('feed_ms', ms, 'items', len(d.get('items',[])), 'today', d.get('today_count')); "
            "raise SystemExit(0 if d.get('items') else 1)",
        ],
        cwd=str(_ROOT),
        check=False,
    )
    if smoke.returncode != 0:
        print("SMOKE WARN — feed empty or slow")
    else:
        print("SMOKE OK")

    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
