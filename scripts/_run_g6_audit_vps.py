#!/usr/bin/env python3
"""Run G6 L3 audit on VPS and fetch judge artifact."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead
chown -R rawlead:rawlead data/preprod_ai_prod_audit* 2>/dev/null || true
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python \
  scripts/preprod_ai_prod_audit.py --profile site --judge-l3 --judge-l3-limit 25 2>&1
echo AUDIT_EXIT=$?
head -22 data/preprod_ai_prod_audit_judge.md 2>/dev/null
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("Running G6 L3 audit on VPS (may take several minutes)...")
    code, out, err = ssh.run(REMOTE.strip(), check=False)
    log = (out or "") + ("\n" + err if err else "")
    log_path = _ROOT / "scripts" / "_g6_audit_vps.log"
    log_path.write_text(log.replace("\r\n", "\n"), encoding="utf-8")
    print(log[-12000:] if len(log) > 12000 else log)
    print(f"log: {log_path}")
    # Fetch artifacts
    for name in (
        "data/preprod_ai_prod_audit.json",
        "data/preprod_ai_prod_audit_judge.md",
        "data/preprod_ai_prod_audit_human.md",
    ):
        rcode, rout, _ = ssh.run(f"cat /opt/rawlead/{name} 2>/dev/null", check=False)
        if rout.strip():
            dest = _ROOT / name.replace("/", "\\").replace("data\\", "data\\")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(rout.replace("\r\n", "\n"), encoding="utf-8")
            print(f"fetched {name}")
    return 0 if "AUDIT_EXIT=0" in log else 1


if __name__ == "__main__":
    raise SystemExit(main())
