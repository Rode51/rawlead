#!/usr/bin/env python3
"""Deploy O34 src to VPS + restart radar + clear L1 backlog."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O34 deploy: sync src + restart radar ===")
    n = ssh.sync_project()
    print(f"synced {n} files -> /opt/rawlead")
    ssh.run(
        r"find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\r$//' {} \; && "
        "chmod +x /opt/rawlead/deploy/*.sh"
    )
    ssh.run("chown -R rawlead:rawlead /opt/rawlead/src /opt/rawlead/scripts /opt/rawlead/tests")
    ssh.run(
        "test -f /opt/rawlead/src/l1_pool.py && echo l1_pool.py OK || (echo MISSING l1_pool.py && exit 1)"
    )
    print("restart services...")
    ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar"
    )
    print("clear L1 backlog (apply)...")
    _, out, _ = ssh.run(
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python scripts/clear_l1_backlog.py "
        "--profile site --dry-run",
        check=False,
    )
    print(out)
    _, out2, _ = ssh.run(
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python scripts/clear_l1_backlog.py "
        "--profile site --apply",
        check=False,
    )
    print(out2)
    print("verify (after 2 min cycle)...")
    _, log_out, _ = ssh.run(
        "sleep 130 && tail -30 /opt/rawlead/data/radar_site.log && "
        "echo '---' && grep pipeline:L1 /opt/rawlead/data/radar_site.log | tail -3 || "
        "echo 'pipeline:L1 not yet'",
        check=False,
    )
    print(log_out or "")
    smoke_rc = _post_deploy_smoke()
    return smoke_rc


def _post_deploy_smoke() -> int:
    """O39: radar active · l1_pool · no backlog drain · feed 200."""
    print("=== post-deploy smoke (O39) ===")
    rc = 0

    _, out, _ = ssh.run("systemctl is-active rawlead-radar", check=False)
    if "active" not in (out or ""):
        print("FAIL: rawlead-radar not active")
        rc = 1
    else:
        print("rawlead-radar: active")

    _, out, _ = ssh.run(
        "test -f /opt/rawlead/src/l1_pool.py && echo OK || echo MISSING",
        check=False,
    )
    if "OK" not in (out or ""):
        print("FAIL: l1_pool.py missing")
        rc = 1

    _, backlog_out, _ = ssh.run(
        "tail -400 /opt/rawlead/data/radar_site.log 2>/dev/null | "
        "grep -c 'конвейер:backlog=' || echo 0",
        check=False,
    )
    try:
        backlog_hits = int((backlog_out or "0").strip().splitlines()[-1])
    except ValueError:
        backlog_hits = -1
    if backlog_hits > 0:
        print(f"FAIL: конвейер:backlog= in last ~3 cycles ({backlog_hits} hits)")
        rc = 1
    else:
        print("no конвейер:backlog= in recent log")

    _, feed_code, _ = ssh.run(
        "curl -s -o /dev/null -w '%{http_code}' "
        "'http://127.0.0.1:8000/v1/feed?limit=1'",
        check=False,
    )
    code = (feed_code or "").strip()
    if code != "200":
        print(f"FAIL: feed API HTTP {code or 'empty'}")
        rc = 1
    else:
        print("feed API: 200")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
