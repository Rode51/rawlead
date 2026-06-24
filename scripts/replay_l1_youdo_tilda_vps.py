#!/usr/bin/env python3
"""One-shot: re-L1 YouDo lead with detail enrich + fallback body (L1-TILDA-TAGS)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)

_UPLOADS = (
    ("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),
    ("scripts/replay_neon_lite_site.py", "/opt/rawlead/scripts/replay_neon_lite_site.py"),
)

REMOTE_PY = r"""
import json
import sys
sys.path.insert(0, '/opt/rawlead/src')
from config import load_radar_env, load_config
from pg_storage import pg_storage_from_config
from ai_analyze import analyze_lite
from youdo_parser import fetch_project_detail

LEAD_ID = 18311
FALLBACK_TZ = (
    "Ищу разработчика Tilda (Online Store + PDF-доставка). "
    "Нужен специалист по Tilda для интернет-магазина цифровых товаров (PDF). "
    "Tilda Commerce, Zero Block, корзина, ЮKassa, автоматическая выдача PDF после оплаты."
)

load_radar_env()
cfg = load_config()
pg = pg_storage_from_config(cfg)
rows = pg.fetch_leads_by_ids([LEAD_ID])
if not rows:
    raise SystemExit(f'no lead {LEAD_ID}')
row = rows[0]
project = row.to_listing()
url = row.url or f'https://youdo.com/t{row.external_id}'
snippet = (row.body or row.title or '').strip()
detail, _html, ok = fetch_project_detail(url, cfg, fallback_snippet=snippet)
if ok and detail and len(detail) > len(snippet):
    snippet = detail.strip()
    print('detail_fetch_ok', len(snippet))
else:
    snippet = f"{row.title.strip()}\n\n{FALLBACK_TZ}"
    print('detail_fetch_fail_using_fallback', len(snippet))

errors = []
lite = analyze_lite(
    cfg,
    title=row.title,
    budget_text=row.budget_text,
    snippet=snippet,
    url=url,
    errors=errors,
    log_prefix=f'{row.source}:id={row.external_id} tilda-replay:',
)
pg.update_after_lite(project, lite=lite, errors=errors, body_snippet=snippet)
tags = pg.fetch_lead_tags_by_ids([LEAD_ID]).get(LEAD_ID) or []
print(json.dumps({
    'lead_id': LEAD_ID,
    'external_id': row.external_id,
    'lead_tags': tags,
    'body_len': len(snippet),
    'detail_ok': ok,
    'errors': errors,
}, ensure_ascii=False))
"""


def _patch_env_key(key: str, value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    env_site = "/opt/rawlead/.env.site"
    cmd = (
        f"grep -q '^{key}=' {env_site} 2>/dev/null && "
        f"sed -i '/^{key}=/d' {env_site}; "
        f"echo '{key}={safe}' >> {env_site} && "
        f"grep -c '^{key}=' {env_site}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def main() -> int:
    _patch_env_key("YOUDO_DETAIL_FETCH", "1")
    ssh.run("systemctl restart rawlead-radar rawlead-api && sleep 3", check=False)

    for local, remote in _UPLOADS:
        ssh.upload(_ROOT / local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"uploaded {local}")

    cmd = (
        "cd /opt/rawlead && sudo -u rawlead env "
        "PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site "
        "YOUDO_DETAIL_FETCH=1 YOUDO_BROWSER_ONLY=1 "
        f".venv/bin/python - <<'PY'\n{REMOTE_PY.strip()}\nPY"
    )
    _, out, err = ssh.run(cmd, check=False)
    text = ((out or "") + (err or "")).replace("\r\n", "\n")
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))

    line = ""
    for raw in text.splitlines():
        if raw.strip().startswith("{"):
            line = raw.strip()
    try:
        data = json.loads(line) if line else {}
    except json.JSONDecodeError:
        data = {}
    tags = data.get("lead_tags") or []
    ok = "tilda_dev" in tags and "wordpress_dev" not in tags
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
