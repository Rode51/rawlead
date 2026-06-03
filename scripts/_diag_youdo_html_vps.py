#!/usr/bin/env python3
"""Inspect latest youdo debug HTML on VPS + test fetch."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site EXCHANGE_LISTING_BROWSER=1 .venv/bin/python - <<'PY'
import glob
from config import load_config
from youdo_parser import fetch_listing_projects, _looks_like_antibot, parse_listing_html

files = sorted(glob.glob("/opt/rawlead/data/debug_listings/youdo_antibot_*.html"))
if files:
    h = open(files[-1], encoding="utf-8").read()
    print("last_debug len", len(h), "data-id", h.count("data-id"), "antibot", _looks_like_antibot(h))

# clear stale browser profiles for youdo
import shutil
from pathlib import Path
root = Path("/opt/rawlead/data/browser_profiles")
if root.is_dir():
    removed = 0
    for p in root.iterdir():
        if p.is_dir() and p.name.startswith("youdo_"):
            shutil.rmtree(p, ignore_errors=True)
            removed += 1
    print("cleared_profiles", removed)

cfg = load_config()
from exchange_proxy import exchange_alive_proxy_urls
from exchange_browser_fetch import _fetch_youdo_ephemeral

url = "https://youdo.com/tasks-all-opened-all"
slots = exchange_alive_proxy_urls("youdo")
print("slots", len(slots))
for i, proxy_url in enumerate(slots[:1]):
    try:
        html = _fetch_youdo_ephemeral(
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=90.0,
            proxy_url=proxy_url,
        )
        print("ephemeral len", len(html), "data-id", html.count("data-id"), "antibot", _looks_like_antibot(html))
    except Exception as e:
        print("ephemeral FAIL", type(e).__name__, str(e)[:200])

try:
    projects = fetch_listing_projects(cfg, timeout_sec=90.0)
    print("OK count=", len(projects))
    if projects:
        print("sample", projects[0].project_id, projects[0].title[:70])
except Exception as e:
    print("FAIL", type(e).__name__, str(e)[:400])
PY
"""

OUT = Path(__file__).resolve().parents[1] / "data" / "_diag_youdo_html_vps.txt"


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    text = (out or err or "").replace("\r\n", "\n")
    OUT.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
