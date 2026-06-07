#!/usr/bin/env python3
"""O125: L2 on-demand only — TOOLS_BACKLOG_DRAIN=0, match_push tools+shared on click."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/match_push.py", "src/main.py")


def _ensure_env_line(key: str, value: str) -> str:
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={value}|' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O125 deploy: L2 on-demand (no radar tools drain) ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    env_cmd = " && ".join(
        [
            _ensure_env_line("TOOLS_BACKLOG_DRAIN", "0"),
            "grep -E '^(TOOLS_BACKLOG_DRAIN|OPENROUTER_MODEL_PREMIUM)=' /opt/rawlead/.env.site",
            "grep -c _ondemand_lead_tools /opt/rawlead/src/match_push.py",
            "systemctl restart rawlead-radar rawlead-api",
            "sleep 3",
            "systemctl is-active rawlead-radar rawlead-api",
            "echo o125_ok",
        ]
    )
    _, out, _ = ssh.run(env_cmd, check=False)
    print(out.strip())
    ok = "o125_ok" in (out or "") and "active" in (out or "")
    print("DEPLOY OK" if ok else "DEPLOY CHECK — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
