#!/usr/bin/env python3
"""Check VPS match_push.py + lead 27xxx push lines."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    for name, cmd in [
        ("uid8_on_vps", "grep -n '_uid8\\|def _uid8' /opt/rawlead/src/match_push.py | head -10"),
        ("raw_subscript", r"grep -n 'user_id\[:8\]' /opt/rawlead/src/match_push.py || echo NONE"),
        ("push_27k", r"grep -E 'push:match.*lead=27[0-9]{3}' /opt/rawlead/data/radar_site.log | tail -20 || echo NO_27K_PUSH"),
        ("l1_27k", r"grep -E 'pipeline:L1.*27[0-9]{3}|lead=27[0-9]{3}' /opt/rawlead/data/radar_site.log | tail -15"),
        ("recent_err", r"grep 'push:match:err' /opt/rawlead/data/radar_site.log | tail -5"),
        ("recent_ok", r"grep -E 'push:match:(user|skip|fail)' /opt/rawlead/data/radar_site.log | tail -10 || echo NO_SKIP_FAIL_USER"),
    ]:
        print(f"=== {name} ===")
        _, out, _ = ssh.run(cmd, check=False)
        print((out or "").strip())
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
