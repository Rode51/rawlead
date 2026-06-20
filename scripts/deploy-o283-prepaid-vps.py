#!/usr/bin/env python3
"""O283: prepaid subscription during trial + billing API deploy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/trial_subscription.py",
    "src/yookassa_billing.py",
    "src/api_server.py",
    "sql/025_prepaid_subscription.sql",
    "scripts/set_subscription_state.py",
)


def main() -> int:
    print("=== O283 prepaid subscription deploy ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "cd /opt/rawlead && sudo -u postgres psql rawlead -f /opt/rawlead/sql/025_prepaid_subscription.sql && "
        "grep -c paid_active_until /opt/rawlead/src/trial_subscription.py && "
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "echo o283_prepaid_ok",
        check=False,
    )
    print((out or "").strip())
    ok = "o283_prepaid_ok" in (out or "")
    print("DEPLOY OK" if ok else "DEPLOY CHECK — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
