#!/usr/bin/env python3
"""Quick VPS draft error tail."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMD = (
    "journalctl -u rawlead-api --since '2 hours ago' --no-pager 2>/dev/null "
    "| grep -E 'lenta:draft|ai_fail|OpenRouter|rate_limit|ai_unavailable' | tail -50; "
    "echo '--- health ---'; "
    "curl -sS http://127.0.0.1:8000/health 2>/dev/null; echo; "
    "grep -E '^(AI_ENABLED|OPENROUTER_MODEL_SHARED|OPENROUTER_API_KEY)' /opt/rawlead/.env.site 2>/dev/null "
    "| sed 's/OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=***/'"
)


def main() -> int:
    _, out, err = ssh.run(CMD, check=False)
    print(out or err or "(no output)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
