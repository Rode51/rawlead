#!/usr/bin/env python3
"""O82-w2: F2+ rank · tools backfill · Sonnet L2 env."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/rank.py",
    "src/ai_analyze.py",
    "src/pg_storage.py",
    "src/lead_pipeline.py",
    "src/main.py",
    "src/match_push.py",
)


def _ensure_env_line(key: str, value: str) -> str:
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's/^{key}=.*/{key}={value}/' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O82-w2 deploy ===")
    remotes: list[str] = []
    for rel in _SRC_FILES:
        local = _ROOT / rel
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    backfill = _ROOT / "scripts" / "backfill_tools_required.py"
    if backfill.is_file():
        ssh.upload(backfill, "/opt/rawlead/scripts/backfill_tools_required.py")
        print("up scripts/backfill_tools_required.py")
    if remotes:
        ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    env_cmd = " && ".join(
        [
            _ensure_env_line("RANK_MATCH_LEAD_WEIGHT", "0.65"),
            _ensure_env_line("RANK_MATCH_USER_WEIGHT", "0.35"),
            _ensure_env_line("RANK_MATCH_USER_CAP", "6"),
            _ensure_env_line("TOOLS_BACKLOG_DRAIN", "1"),
            _ensure_env_line("TOOLS_BATCH_PER_CYCLE", "8"),
            _ensure_env_line(
                "OPENROUTER_MODEL_PREMIUM", "anthropic/claude-sonnet-4"
            ),
            _ensure_env_line(
                "OPENROUTER_MODEL_SHARED_DRAFT", "anthropic/claude-sonnet-4"
            ),
            "grep -E '^(RANK_MATCH_|TOOLS_|OPENROUTER_MODEL_PREMIUM|OPENROUTER_MODEL_SHARED)' "
            "/opt/rawlead/.env.site",
            "grep 'F2+' /opt/rawlead/src/rank.py | head -1",
            "grep analyze_lead_tools /opt/rawlead/src/ai_analyze.py | head -1",
            "systemctl restart rawlead-radar rawlead-api",
            "sleep 4",
            "systemctl is-active rawlead-radar rawlead-api",
        ]
    )
    ssh.run(env_cmd)
    print("=== done — run backfill on VPS if needed ===")
    print(
        "  cd /opt/rawlead && PYTHONPATH=src python3 scripts/backfill_tools_required.py "
        "--profile site --limit 40"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
