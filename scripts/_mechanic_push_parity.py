#!/usr/bin/env python3
"""Feed vs push km parity on tg185 + prompt-test visible leads."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

OUT = _ROOT / "scripts" / "_mechanic_push_parity.out"


def run(cmd: str) -> str:
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip()


def main() -> int:
    py = r"""
import os, sys
from dotenv import load_dotenv
import psycopg
sys.path.insert(0, 'src')
load_dotenv('.env'); load_dotenv('.env.site', override=True)
from lead_category import resolve_lead_category
from rank import compatibility_match, effective_user_tag_weights, parse_lead_tags, user_quiz_niches_from_tags, keyword_match
from match_push import _fetch_lead_row, _push_km_for_lead_row, _load_user_tags
MONICA_TG = 8688264540

def km_feed(cur, uid, lead_row):
    tags = parse_lead_tags(lead_row[8] or [])
    title = lead_row[2] or ''
    cat = resolve_lead_category(lead_row[11], title, '', tags)
    cur.execute('SELECT tag, COALESCE(weight,1.0), last_active_at FROM user_tags WHERE user_id=%s::uuid', (uid,))
    ut = effective_user_tag_weights(cur.fetchall())
    return compatibility_match(tags, ut, lead_category=cat, user_quiz_niches=user_quiz_niches_from_tags(ut))

with psycopg.connect(os.environ['DATABASE_URL']) as c:
    cur = c.cursor()
    cur.execute('SELECT id::text, tg_user_id, push_min_match FROM users WHERE tg_user_id=%s', (MONICA_TG,))
    mu = cur.fetchone()
    print('monica', mu)
    if not mu: raise SystemExit(0)
    uid, tg, thr = mu
    # tg test posts visible
    cur.execute(
        "SELECT id, source, external_id, left(title,60), is_visible, created_at "
        "FROM leads WHERE source LIKE 'tg:%5177575757%' OR source='tg:-1005177575757' "
        "ORDER BY id DESC LIMIT 8"
    )    print('\n=== tg prompt-test leads ===')
    tg_leads = cur.fetchall()
    for r in tg_leads: print(r)
    ids = [r[0] for r in tg_leads if r[4]]
    for lid in ids:
        lead_row = _fetch_lead_row(cur, lid)
        if not lead_row:
            print(f'lead={lid} fetch_lead_row MISSING')
            continue
        utags = _load_user_tags(cur, uid)
        push_km = _push_km_for_lead_row(lead_row, utags)
        feed_km = km_feed(cur, uid, lead_row)
        kw = keyword_match(parse_lead_tags(lead_row[8] or []), utags)
        print(f'lead={lid} push_km={push_km} feed_km={feed_km} keyword_km={kw} thr={thr} pass={push_km and push_km>=int(thr)} title={lead_row[2][:50]!r}')
    # grep push lines for these ids
"""
    lines = [
        "=== parity ===",
        run(f"cd /opt/rawlead && .venv/bin/python <<'PY'\n{py}\nPY"),
        "=== push_lines_tg ===",
        run(r"grep -E 'push:match.*lead=269[0-9]{2}|push:match.*lead=270[0-9]{2}' /opt/rawlead/data/radar_site.log | tail -30 || echo NONE"),
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
