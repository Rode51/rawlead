#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

OUT = _ROOT / "data" / "_diag_youdo_after_ops.txt"

def main() -> int:
    parts = []
    for name, cmd in [
        ("browser_env", "grep EXCHANGE_LISTING_BROWSER /opt/rawlead/.env.site 2>/dev/null || echo MISSING"),
        ("youdo", 'grep -E "fetch:youdo|YouDo" /opt/rawlead/data/radar_site.log 2>/dev/null | tail -8'),
        ("tail_log", "tail -6 /opt/rawlead/data/radar_site.log 2>/dev/null"),
        ("fr", 'grep "Freelance.ru" /opt/rawlead/data/radar_site.log 2>/dev/null | tail -5'),
    ]:
        _, out, _ = ssh.run(cmd, check=False)
        parts.append(f"=== {name} ===\n{out or ''}")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
