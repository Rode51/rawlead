#!/usr/bin/env python3
"""O185 t6c P2: YouDo — networkidle, headless=0+Xvfb, timeout 150s, stealth."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/youdo_parser.py",
    "src/exchange_browser_fetch.py",
    "src/main.py",
    "deploy/run-radar-site.sh",
)

_ENV_LINES = (
    "YOUDO_GOTO_WAIT_UNTIL=load",
    "YOUDO_RETRY_GOTO_WAIT_UNTIL=domcontentloaded",
    "YOUDO_GOTO_TIMEOUT_SEC=150",
    "YOUDO_POST_GOTO_JITTER_MS=1500,3500",
    "YOUDO_HEADLESS=1",
    "YOUDO_STEALTH=1",
    "YOUDO_LEAN_PERSISTENT=0",
)


def _ensure_env_line(key: str, value: str) -> str:
    esc = "'" + value.replace("'", "'\"'\"'") + "'"
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={esc}|' /opt/rawlead/.env.site || "
        f"echo '{key}={esc}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O185 t6c deploy: load 150s + selector wait + stealth ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run(
        "chown rawlead:rawlead " + " ".join(remotes) + " && "
        "sed -i 's/\\r$//' /opt/rawlead/deploy/run-radar-site.sh && "
        "chmod +x /opt/rawlead/deploy/run-radar-site.sh"
    )
    env_cmds = " && ".join(_ensure_env_line(k, v) for k, v in (line.split("=", 1) for line in _ENV_LINES))
    reset_guard = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python -c \"from config import load_config; "
        "from storage import storage_from_config; "
        "from youdo_parser import _reset_youdo_fail_streak, YOUDO_COOLDOWN_KEY; "
        "st = storage_from_config(load_config()); "
        "_reset_youdo_fail_streak(st); "
        "st.set_setting(YOUDO_COOLDOWN_KEY, '0'); "
        "print('guard_reset_ok')\""
    )
    _, out, _ = ssh.run(
        f"{env_cmds} && "
        "command -v Xvfb >/dev/null && echo xvfb_ok || echo xvfb_missing && "
        "grep YOUDO_GOTO_WAIT_UNTIL=load /opt/rawlead/.env.site && "
        "grep YOUDO_HEADLESS=1 /opt/rawlead/.env.site && "
        f"{reset_guard} && "
        "systemctl stop rawlead-radar 2>/dev/null || true; sleep 3; "
        "systemctl reset-failed rawlead-radar 2>/dev/null || true; "
        "systemctl start rawlead-radar && sleep 6 && systemctl is-active rawlead-radar && "
        "echo o185_t6_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o185_t6_deploy_ok" not in text or "active" not in text:
        print("O185 t6 DEPLOY CHECK FAILED")
        return 1
    print("O185 t6 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
