#!/usr/bin/env python3
"""Retry L2 draft for lead on VPS — debug only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

LID = 7019
REMOTE = rf"""
cd /opt/rawlead && sudo -u rawlead .venv/bin/python << 'PY'
import os, json, sys
sys.path.insert(0, "src")
import psycopg
from dotenv import load_dotenv
from config import load_config
from ai_analyze import analyze_premium, AiLiteAnalysis
from skills_catalog import normalize_tags

load_dotenv("/opt/rawlead/.env.site")
lid = {LID}
errors = []
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT title, body, budget_text, url, ai_verdict, task_summary, lead_tags, ai_reasons FROM leads WHERE id=%s",
            (lid,),
        )
        row = cur.fetchone()
if not row:
    print("not found")
    raise SystemExit(1)
title, body, budget, url, verdict, summary, tags, reasons = row
tags = normalize_tags(list(tags or []))
lite = AiLiteAnalysis(
    feed_visible=(verdict or "OK").strip().casefold() not in ("мимо", "пропустить"),
    task_summary=(summary or body or "")[:400],
    lead_tags=tuple(tags),
    ai_reasons=tuple(reasons or []),
)
cfg = load_config()
premium = analyze_premium(
    cfg,
    title=title or "",
    budget_text=budget or "",
    description=body or "",
    url=url or "",
    lite=lite,
    profile_excerpt="Python, WordPress, API integrations",
    log_prefix="debug:draft:" + str(lid) + ":",
    errors=errors,
)
print("ERRORS", errors)
if premium:
    print("OK draft", (premium.reply_draft or "")[:200])
    print("tools", premium.tools_required)
else:
    print("FAIL premium=None")
PY
"""

if __name__ == "__main__":
    _, o, e = ssh.run(REMOTE.strip(), check=False)
    sys.stdout.buffer.write((o or e or "").encode("utf-8", errors="replace"))
