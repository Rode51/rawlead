#!/usr/bin/env python3
"""Deep push diag: visible 27k leads, lead_missing, debug cycle."""
from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

OUT = _ROOT / "scripts" / "_mechanic_push_cycle.out"


def run(cmd: str) -> str:
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip()


def main() -> int:
    lines: list[str] = []

    def add(name: str, text: str) -> None:
        lines.append(f"=== {name} ===")
        lines.append(text)
        lines.append("")

    add("visible_27k", run(
        "cd /opt/rawlead && .venv/bin/python <<'PY'\n"
        "import os\nfrom dotenv import load_dotenv\nimport psycopg\n"
        "load_dotenv('.env'); load_dotenv('.env.site', override=True)\n"
        "with psycopg.connect(os.environ['DATABASE_URL']) as c:\n"
        "    cur = c.cursor()\n"
        "    cur.execute(\"SELECT id, source, external_id, is_visible, left(title,60), created_at FROM leads WHERE id >= 27000 AND is_visible = true ORDER BY id DESC LIMIT 10\")\n"
        "    for r in cur.fetchall(): print(r)\n"
        "PY"
    ))
    add("lead_missing_post_restart", run(
        r"grep '2026-06-15 1[5-9]:\|2026-06-15 2[0-3]:' /opt/rawlead/data/radar_site.log | grep 'push:match:lead_missing' | tail -20 || echo NONE"
    ))
    add("tg185_lead", run(
        "cd /opt/rawlead && .venv/bin/python <<'PY'\n"
        "import os\nfrom dotenv import load_dotenv\nimport psycopg\n"
        "load_dotenv('.env'); load_dotenv('.env.site', override=True)\n"
        "with psycopg.connect(os.environ['DATABASE_URL']) as c:\n"
        "    cur = c.cursor()\n"
        "    cur.execute(\"SELECT id, is_visible, left(title,80), created_at FROM leads WHERE source='tg:-1005177575757' AND external_id='185' ORDER BY id DESC LIMIT 3\")\n"
        "    for r in cur.fetchall(): print(r)\n"
        "PY"
    ))

    # Enable MATCH_PUSH_DEBUG=1, restart radar, wait ~90s, grep
    add("enable_debug", run(
        "grep -q '^MATCH_PUSH_DEBUG=' /opt/rawlead/.env.site && "
        "sed -i 's/^MATCH_PUSH_DEBUG=.*/MATCH_PUSH_DEBUG=1/' /opt/rawlead/.env.site || "
        "echo 'MATCH_PUSH_DEBUG=1' >> /opt/rawlead/.env.site; "
        "grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)=' /opt/rawlead/.env.site"
    ))
    add("restart", run("systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar"))
    add("runtime_after", run(
        r"""PID=$(systemctl show -p MainPID --value rawlead-radar)
tr '\0' '\n' < /proc/$PID/environ | grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)='"""
    ))
    lines.append("=== waiting 120s for radar cycle ===")
    time.sleep(120)
    add("push_after_debug", run(
        r"grep -E 'push:match:(skip|fail|user|err|lead_missing)' /opt/rawlead/data/radar_site.log | tail -40 || echo NONE"
    ))
    add("disable_debug", run(
        "sed -i 's/^MATCH_PUSH_DEBUG=.*/MATCH_PUSH_DEBUG=0/' /opt/rawlead/.env.site || true; "
        "grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)=' /opt/rawlead/.env.site"
    ))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
