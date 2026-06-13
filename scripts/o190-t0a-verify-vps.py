#!/usr/bin/env python3
"""O190 t0a: lean env + wipe YouDo profiles + one patchright smoke (stop if DoD met)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_ENV_LINES = (
    "YOUDO_LEAN_PERSISTENT=0",
    "YOUDO_LEAN_ON_RETRY=0",
    "YOUDO_EPHEMERAL=0",
    "YOUDO_BROWSER=patchright",
)


def _ensure_env_line(key: str, value: str) -> str:
    esc = "'" + value.replace("'", "'\"'\"'") + "'"
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={esc}|' /opt/rawlead/.env.site || "
        f"echo '{key}={esc}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O190 t0a verify: env + wipe profiles + stop radar ===")
    env_cmds = " && ".join(
        _ensure_env_line(k, v) for k, v in (line.split("=", 1) for line in _ENV_LINES)
    )
    prep = (
        f"{env_cmds} && "
        "grep -E 'YOUDO_LEAN|YOUDO_EPHEMERAL|YOUDO_BROWSER' /opt/rawlead/.env.site && "
        "rm -rf /opt/rawlead/data/youdo_* 2>/dev/null || true && "
        "echo wiped_profiles_ok && "
        "pkill -f smoke_youdo 2>/dev/null || true && "
        "systemctl stop rawlead-radar && sleep 3 && "
        "(systemctl is-active rawlead-radar && echo radar_still_running || echo radar_stopped)"
    )
    _, prep_out, _ = ssh.run(prep, check=False)
    print(prep_out or "")

    print("=== O190 t0a smoke (single slot, ~10 min) ===")
    smoke = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "smoke_youdo_t6c_vps.py")],
        cwd=str(_ROOT),
        check=False,
    )
    smoke_path = _ROOT / "data" / "smoke_youdo_t6c_vps.txt"
    text = smoke_path.read_text(encoding="utf-8") if smoke_path.is_file() else ""
    print(text)

    _, restart_out, _ = ssh.run(
        "systemctl start rawlead-radar && sleep 4 && systemctl is-active rawlead-radar",
        check=False,
    )
    print(restart_out or "")

    dod = "OK html_len" in text and "data-id" in text
    if dod:
        print("O190 t0a DoD MET — root was stale profile/lean env; skip t0b camoufox")
        return 0
    print("O190 t0a DoD NOT MET — proceed to t0b: python scripts/deploy-o190-youdo-camoufox-vps.py")
    return smoke.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
