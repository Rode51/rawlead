#!/usr/bin/env python3
"""O255: YouDo hard reset fail@1 + rate cap — youdo_parser + .env.site."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = ("src/youdo_parser.py",)

_ENV_LINES = (
    ("YOUDO_HARD_RESET_FAILS", "1"),
    ("YOUDO_HARD_RESET_MIN_SEC", "120"),
    ("YOUDO_HARD_RESET_MAX_PER_HOUR", "8"),
    ("YOUDO_SHORT_COOLDOWN_MIN", "5"),
)


def _ensure_env_line(key: str, value: str) -> str:
    esc = "'" + value.replace("'", "'\"'\"'") + "'"
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={esc}|' /opt/rawlead/.env.site || "
        f"echo '{key}={esc}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O255 deploy: YouDo hard reset fail@1 + rate cap ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    env_cmds = " && ".join(_ensure_env_line(k, v) for k, v in _ENV_LINES)
    _, out, _ = ssh.run(
        f"{env_cmds} && "
        "grep -E '^YOUDO_HARD_RESET_(FAILS|MIN_SEC|MAX_PER_HOUR)=' /opt/rawlead/.env.site && "
        "grep '^YOUDO_SHORT_COOLDOWN_MIN=' /opt/rawlead/.env.site && "
        "grep -c hard_reset_rate_limited /opt/rawlead/src/youdo_parser.py && "
        "grep -c hard_reset_hourly_cap /opt/rawlead/src/youdo_parser.py && "
        "systemctl restart rawlead-radar && sleep 6 && "
        "systemctl is-active rawlead-radar && "
        "echo o255_deploy_ok",
        check=False,
    )
    text = (out or "").strip()
    print(text)
    ok = "o255_deploy_ok" in text and "active" in text
    if ok:
        print("DEPLOY OK — tail radar log for fetch:youdo hard_reset")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
