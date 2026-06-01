#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_, o, _ = ssh.run(
    "journalctl -u rawlead-api --since '2026-06-01 05:15:00' --no-pager 2>/dev/null | "
    "grep -E 'ai:|OpenRouter|draft generation|AiAnalyze|Traceback' | tail -40",
    check=False,
)
(_ROOT / "data" / "o80_ai_errors.txt").write_text(o or "empty", encoding="utf-8")
print("written", len(o or ""))
