#!/usr/bin/env python3
"""Quick VPS verify for O190 t0f ingest."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMD = (
    "grep -E '^L1_MAX_WORKERS=' /opt/rawlead/.env.site; "
    "echo '--- fetch_end ---'; "
    "grep fetch_end /opt/rawlead/data/radar_site.log | tail -8; "
    "echo '--- asyncio/health ---'; "
    "grep asyncio /opt/rawlead/data/radar_site.log | tail -3; "
    "grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -3"
)


def main() -> int:
    _, out, err = ssh.run(CMD, check=False)
    text = (out or "") + (err or "")
    print(text.encode("ascii", errors="replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
