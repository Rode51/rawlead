#!/usr/bin/env python3
"""L2 prod stack: tools-tune + on-demand draft (O125). Upload + restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/ai_analyze.py",
    "src/l3_human_style.py",
    "src/tools_catalog.py",
    "src/match_push.py",
    "src/main.py",
)


def main() -> int:
    print("=== L2 stack deploy (tools-tune + on-demand) ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c _TOOLS_ONLY_SYSTEM /opt/rawlead/src/ai_analyze.py && "
        "grep -c _ondemand_lead_tools /opt/rawlead/src/match_push.py && "
        "grep -c finalize_tools_for_lead /opt/rawlead/src/tools_catalog.py && "
        "grep -c _REPLY_AI_SMELL_RE /opt/rawlead/src/l3_human_style.py && "
        "systemctl restart rawlead-radar rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-radar rawlead-api && "
        "grep -E '^(TOOLS_BACKLOG_DRAIN|OPENROUTER_MODEL_PREMIUM|OPENROUTER_MODEL_SHARED_DRAFT)=' "
        "/opt/rawlead/.env.site && "
        "echo l2_stack_ok",
        check=False,
    )
    print(out.strip())
    ok = "l2_stack_ok" in (out or "") and "active" in (out or "")
    print("DEPLOY OK" if ok else "DEPLOY CHECK — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
