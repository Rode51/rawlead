#!/usr/bin/env python3
"""One-off: pull VPS radar lines for secondary ingest sources."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

OUT = _ROOT / "data" / "_diag_secondary_logs.txt"

BLOCKS = [
    ("env", 'grep -E "^(PUBLIC_FEED_SOURCES|YOUDO_|EXCHANGE_LISTING_BROWSER|EXCHANGE_PROXY_URLS_SECONDARY)" /opt/rawlead/.env.site 2>/dev/null | head -15'),
    ("youdo_fetch", 'grep -E "fetch:youdo|youdo_listing|youdo:" /opt/rawlead/data/radar_site.log 2>/dev/null | tail -50'),
    ("freelance_ru", 'grep -E "fetch:freelance_ru|freelance_ru:" /opt/rawlead/data/radar_site.log 2>/dev/null | tail -30'),
    ("pchyol_job", 'grep -E "fetch:pchyol|fetch:freelancejob|pchyol:|freelancejob:" /opt/rawlead/data/radar_site.log 2>/dev/null | tail -30'),
    ("youdo_funnel", 'grep "youdo" /opt/rawlead/data/radar_site.log 2>/dev/null | grep -E "воронка|downloaded|new_ids|skip|fetch:" | tail -25'),
    ("fr_funnel", 'grep "freelance_ru" /opt/rawlead/data/radar_site.log 2>/dev/null | grep -E "воронка|downloaded|new_ids|skip|fetch:" | tail -15'),
    ("youdo_pw", 'grep -E "youdo_listing|Playwright browser failed|antibot|TasksList|YoudoListing" /opt/rawlead/data/radar_site.log 2>/dev/null | tail -30'),
    ("dl_counts", 'grep "скачано" /opt/rawlead/data/radar_site.log 2>/dev/null | grep -E "YouDo|Freelance|Пчел|freelancejob" | tail -40'),
    ("pchyol_dl", 'grep "Пчёл" /opt/rawlead/data/radar_site.log 2>/dev/null | grep "скачано" | tail -12'),
    ("neon_counts", r"""cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv('/opt/rawlead/.env.site', override=True)
import psycopg
url = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')
if not url:
    print('no DATABASE_URL')
else:
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            for src in ('youdo','freelance_ru','freelancejob','pchyol','fl','kwork','tg'):
                cur.execute("SELECT COUNT(*) FROM leads WHERE source=%s", (src,))
                nall = cur.fetchone()[0]
                cur.execute("SELECT MAX(created_at)::text FROM leads WHERE source=%s", (src,))
                last = cur.fetchone()[0]
                print(f'{src}: all={nall} last={last}')
PY"""),
]


def main() -> int:
    lines: list[str] = []
    for name, cmd in BLOCKS:
        lines.append(f"\n=== {name} ===\n")
        try:
            _, out, err = ssh.run(cmd, check=False)
            lines.append(out or "")
            if err.strip():
                lines.append(f"[stderr] {err}")
        except Exception as exc:
            lines.append(f"ERROR: {exc}")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
