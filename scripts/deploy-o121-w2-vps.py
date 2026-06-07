#!/usr/bin/env python3
"""O121-w2: /ops/ proxies — clear-bans, status_label, UX."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/api_server.py",
    "src/owner_admin.py",
    "src/proxy_ops.py",
    "src/tg_proxy_pool.py",
    "tests/test_o121_ops_proxies.py",
)


def main() -> int:
    print("=== O121-w2 deploy: /ops/ proxies UX ===")
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
        "grep -c 'rl-proxy-clear-bans' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'clear-bans' /opt/rawlead/src/proxy_ops.py && "
        "grep -c 'status_label' /opt/rawlead/src/tg_proxy_pool.py && "
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
        "\"import sys; sys.path.insert(0,'src'); "
        "from proxy_ops import slot_status_label, run_proxy_control; "
        "from tg_proxy_pool import clear_all_bans; "
        "from exchange_proxy import clear_all_bans as cex; "
        "print('w2_imports_ok')\" && "
        "echo o121_w2_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "o121_w2_ok" in text and "w2_imports_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
