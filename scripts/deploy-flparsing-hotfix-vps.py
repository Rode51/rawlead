#!/usr/bin/env python3
"""Hotfix: legacy poll logging + /ops/ radar restart includes legacy + TG proxy .env.legacy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/neon_legacy_consumer.py",
    "src/owner_admin.py",
)


def main() -> int:
    print("=== deploy: FLPARSING legacy hotfix ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    print("\n=== patch .env.legacy TG proxy if dead acc1 ===")
    import fix_tg_proxy_acc2_vps as fix  # noqa: E402

    code, body, _ = ssh.run("cat /opt/rawlead/.env", check=False)
    acc2 = fix._parse_env(body).get(fix.SOURCE_KEY, "").strip()
    if acc2 and fix.DEAD_HOST not in acc2:
        fix.patch_file("/opt/rawlead/.env.legacy", acc2)

    print("\n=== restart services (legacy recovery if queued /stop) ===")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar rawlead-radar-legacy && sleep 8 && "
        "systemctl is-active rawlead-radar-legacy >/dev/null || "
        "( systemctl start rawlead-radar-legacy && sleep 4 ) && "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy && "
        "tail -5 /opt/rawlead/data/radar_legacy.log 2>&1 && "
        "echo flparsing_hotfix_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = (
        "flparsing_hotfix_ok" in text
        and text.count("active") >= 3
        and "legacy_radar_status" not in text  # grep count line should be number
    )
    # grep -c outputs numbers on separate logic
    lines = text.splitlines()
    has_grep = any(l.strip() in ("1", "2", "3", "4", "5") for l in lines if l.strip().isdigit())
    if "flparsing_hotfix_ok" in text and "active" in text:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
