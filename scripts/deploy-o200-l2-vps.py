#!/usr/bin/env python3
"""O200-L2-CATEGORY-WAVE: deploy category playbooks + primary_category in L2 user payload."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/ai_analyze.py",
    "src/l3_human_style.py",
    "src/match_push.py",
    "scripts/regen_shared_reply_drafts.py",
)


def main() -> int:
    print("=== O200 L2 category wave deploy ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c 'Category playbooks' /opt/rawlead/src/l3_human_style.py && "
        "grep -c 'primary_category:' /opt/rawlead/src/ai_analyze.py && "
        "grep -c 'primary_category=primary_category' /opt/rawlead/src/match_push.py && "
        "systemctl restart rawlead-radar rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-radar rawlead-api && "
        "echo o200_l2_ok",
        check=False,
    )
    print(out.strip())
    ok = "o200_l2_ok" in (out or "") and "active" in (out or "")
    print("DEPLOY OK" if ok else "DEPLOY CHECK — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
