#!/usr/bin/env python3
"""O262j smoke: tail YouDo fetch/ingest on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    remote = r"""
grep YOUDO_O191_DC_SLOTS /opt/rawlead/.env.site | tail -1
grep YOUDO_DC_PROXY_URLS /opt/rawlead/.env.site || echo YOUDO_DC_PROXY_URLS=unset
tail -8000 /opt/rawlead/data/radar_site.log | grep fetch:youdo | tail -5
tail -8000 /opt/rawlead/data/radar_site.log | grep youdo:trace | tail -5
tail -8000 /opt/rawlead/data/radar_site.log | grep youdo:ingest | tail -5
tail -8000 /opt/rawlead/data/radar_site.log | grep 'YouDo ' | tail -3
systemctl is-active rawlead-radar
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    text = (out or "").replace("\r\n", "\n")
    out_path = _ROOT / "data" / "o262j_smoke_tail.txt"
    out_path.write_text(text, encoding="utf-8")
    print(text)
    has_ru = "tier=ru" in text
    has_ingest50 = "youdo:ingest done=50" in text
    print(f"\nSMOKE: tier=ru={has_ru} ingest50={has_ingest50}")
    return 0 if has_ru and has_ingest50 else 2


if __name__ == "__main__":
    raise SystemExit(main())
