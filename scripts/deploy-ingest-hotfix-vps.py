#!/usr/bin/env python3
"""Sync L1 ingest bundle to VPS + restart radar/API (fixes AiLiteAnalysis verdict drift)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== ingest coupled deploy (radar + API) ===")
    names = ssh.deploy_ingest_coupled_src()
    print("uploaded:", ", ".join(names))

    _, out, _ = ssh.run(
        "grep -n 'feed_visible=True' /opt/rawlead/src/lead_pipeline.py | head -1 && "
        "! grep -n 'AiLiteAnalysis(' /opt/rawlead/src/lead_pipeline.py | grep -q 'verdict=' && "
        "echo lead_pipeline_contract_ok",
        check=False,
    )
    print(out.strip())
    if "lead_pipeline_contract_ok" not in (out or ""):
        print("FAIL: lead_pipeline still has verdict= in AiLiteAnalysis()")
        return 1

    print("restart rawlead-api rawlead-radar rawlead-radar-legacy...")
    _, out2, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar rawlead-radar-legacy && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy",
        check=False,
    )
    print(out2.strip())
    if out2 and "active" not in out2:
        print("FAIL: services not active")
        return 1

    print("wait one cycle (~90s) and check log...")
    _, log_out, _ = ssh.run(
        "sleep 95 && tail -25 /opt/rawlead/data/radar_site.log",
        check=False,
    )
    sys.stdout.buffer.write((log_out or "").encode("utf-8", errors="replace"))

    _, err_cnt, _ = ssh.run(
        "tail -80 /opt/rawlead/data/radar_site.log | "
        "grep -cE 'TypeError: AiLiteAnalysis|AttributeError.*by_source' || echo 0",
        check=False,
    )
    try:
        n_err = int((err_cnt or "0").strip().split()[0])
    except ValueError:
        n_err = -1
    if n_err > 0:
        print(f"WARN: last 80 log lines still have {n_err} ingest error(s) — check full cycle")
        return 1

    print("DEPLOY OK — no ingest contract errors in last 80 lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
