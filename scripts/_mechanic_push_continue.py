#!/usr/bin/env python3
"""Continue P0 push diag — state + grep + Monica km on visible lead."""
from __future__ import annotations

import sys
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

    add("env_now", run(r"grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)=' /opt/rawlead/.env.site"))
    add("runtime_now", run(
        r"""PID=$(systemctl show -p MainPID --value rawlead-radar)
echo PID=$PID
tr '\0' '\n' < /proc/$PID/environ 2>/dev/null | grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG|RADAR_PROFILE)=' || echo NO_PROC"""
    ))
    add("radar_active", run("systemctl is-active rawlead-radar"))
    add("push_all_recent", run(
        r"grep -E 'push:match:(skip|fail|user|err|lead_missing)' /opt/rawlead/data/radar_site.log | tail -50 || echo NONE"
    ))
    add("push_today", run(
        r"grep '2026-06-15' /opt/rawlead/data/radar_site.log | grep -E 'push:match' | tail -30 || echo NONE_TODAY"
    ))
    add("visible_27k", run(
        "cd /opt/rawlead && .venv/bin/python <<'PY'\n"
        "import os\nfrom dotenv import load_dotenv\nimport psycopg\n"
        "load_dotenv('.env'); load_dotenv('.env.site', override=True)\n"
        "with psycopg.connect(os.environ['DATABASE_URL']) as c:\n"
        "    cur = c.cursor()\n"
        "    cur.execute(\"SELECT id, source, external_id, left(title,70), created_at FROM leads WHERE is_visible=true AND created_at > now()-interval '12 hours' ORDER BY id DESC LIMIT 15\")\n"
        "    rows = cur.fetchall()\n"
        "    print('visible_12h', len(rows))\n"
        "    for r in rows: print(r)\n"
        "    cur.execute(\"SELECT count(*) FROM match_push_log\")\n"
        "    print('match_push_log_total', cur.fetchone()[0])\n"
        "PY"
    ))
    add("monica_km_tg185", run(
        "cd /opt/rawlead && .venv/bin/python <<'PY'\n"
        "import os, sys\nfrom dotenv import load_dotenv\nimport psycopg\n"
        "sys.path.insert(0, 'src')\n"
        "load_dotenv('.env'); load_dotenv('.env.site', override=True)\n"
        "from lead_category import resolve_lead_category\n"
        "from rank import compatibility_match, effective_user_tag_weights, parse_lead_tags, user_quiz_niches_from_tags\n"
        "from match_push import _fetch_lead_row, _push_km_for_lead_row, _load_user_tags\n"
        "from config import load_config\n"
        "cfg = load_config()\n"
        "MONICA_TG = 8688264540\n"
        "OWNER_TG = 5177575757\n"
        "with psycopg.connect(os.environ['DATABASE_URL']) as c:\n"
        "    cur = c.cursor()\n"
        "    cur.execute(\"SELECT id FROM leads WHERE source='tg:-1005177575757' AND external_id='185' ORDER BY id DESC LIMIT 1\")\n"
        "    row = cur.fetchone()\n"
        "    print('tg185_lead_id', row[0] if row else None)\n"
        "    if not row: raise SystemExit(0)\n"
        "    lid = row[0]\n"
        "    lead_row = _fetch_lead_row(cur, lid)\n"
        "    print('fetch_lead_row', 'OK' if lead_row else 'MISSING')\n"
        "    for label, tg in [('monica', MONICA_TG), ('owner', OWNER_TG)]:\n"
        "        cur.execute('SELECT id::text, push_min_match FROM users WHERE tg_user_id=%s', (tg,))\n"
        "        u = cur.fetchone()\n"
        "        if not u: print(label, 'NO_USER'); continue\n"
        "        uid, thr = u\n"
        "        tags = _load_user_tags(cur, uid)\n"
        "        km = _push_km_for_lead_row(lead_row, tags) if lead_row else None\n"
        "        print(f'{label} uid={uid[:8]} thr={thr} tags={len(tags)} km={km} pass={km is not None and km>=int(thr)}')\n"
        "PY"
    ))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
