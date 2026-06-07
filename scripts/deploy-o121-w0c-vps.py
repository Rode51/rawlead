#!/usr/bin/env python3
"""O121-w0c: /ops/ restart HTTP 400 — JS detail, sudo ctl wrappers, legacy TG drain."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/owner_admin.py",
    "deploy/radar-ctl.sh",
    "deploy/bot-ctl.sh",
    "deploy/sudoers.d/rawlead-radar-ctl",
)


def main() -> int:
    print("=== O121-w0c deploy: ops restart 400 fix ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chmod +x /opt/rawlead/deploy/radar-ctl.sh /opt/rawlead/deploy/bot-ctl.sh")
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    ssh.run(
        "sed -i 's/\\r$//' /opt/rawlead/deploy/radar-ctl.sh "
        "/opt/rawlead/deploy/bot-ctl.sh "
        "/opt/rawlead/deploy/sudoers.d/rawlead-radar-ctl && "
        "cp /opt/rawlead/deploy/sudoers.d/rawlead-radar-ctl /etc/sudoers.d/rawlead-radar-ctl && "
        "chmod 440 /etc/sudoers.d/rawlead-radar-ctl && visudo -c"
    )

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'ctlFetchErr' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'restart' /opt/rawlead/deploy/radar-ctl.sh && "
        "test -x /opt/rawlead/deploy/bot-ctl.sh && "
        "grep -c 'bot-ctl.sh' /etc/sudoers.d/rawlead-radar-ctl && "
        "sudo -u rawlead sudo -n /opt/rawlead/deploy/bot-ctl.sh status && "
        "sudo -u rawlead sudo -n /opt/rawlead/deploy/radar-ctl.sh status legacy && "
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
        "\"import sys; sys.path.insert(0,'src'); "
        "from owner_admin import _bot_poll_status, _legacy_radar_status; "
        "print('poll', _bot_poll_status(), 'legacy', _legacy_radar_status())\" && "
        "echo o121_w0c_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "o121_w0c_ok" in text and "poll" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
