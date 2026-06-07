#!/usr/bin/env python3
"""O121-w1: /ops/ proxies — VPS API + WP route."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/proxy_ops.py",
    "src/tg_proxy_pool.py",
    "src/exchange_proxy.py",
    "src/owner_admin.py",
    "src/api_server.py",
    "scripts/probe_all_proxies.py",
    "wordpress/rawlead-kadence-child/inc/rawlead-api.php",
)


def main() -> int:
    print("=== O121-w1 deploy: /ops/ proxies ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'rl-ops-mini-nav' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'ops-proxies' /opt/rawlead/src/owner_admin.py && "
        "grep -c '/v1/admin/proxies' /opt/rawlead/src/api_server.py && "
        "grep -c '/ops/proxies' /opt/rawlead/wordpress/rawlead-kadence-child/inc/rawlead-api.php && "
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
        "\"import sys; sys.path.insert(0,'src'); "
        "from proxy_ops import collect_proxies_payload, strip_internal_urls; "
        "p=strip_internal_urls(collect_proxies_payload()); "
        "print('groups', len(p.get('groups') or []))\" && "
        "echo o121_w1_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "o121_w1_ok" in text and "groups" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
