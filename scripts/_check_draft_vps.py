#!/usr/bin/env python3
"""Quick VPS draft/AI diagnostic."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    cmds = [
        "curl -sf http://127.0.0.1:8000/health",
        "journalctl -u rawlead-api -n 50 --no-pager 2>/dev/null | tail -25",
        "python3 -c \"import sys; sys.path.insert(0,'/opt/rawlead/src'); from tools_catalog import normalize_tools_required; print(normalize_tools_required(['neon','telethon']))\"",
    ]
    out_lines: list[str] = []
    for cmd in cmds:
        out_lines.append(f"=== {cmd[:70]} ===")
        _, o, e = ssh.run(cmd, check=False)
        out_lines.append(o or e or "(empty)")
    path = _ROOT / "data" / "o80_vps_check.txt"
    path.write_text("\n".join(out_lines), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
