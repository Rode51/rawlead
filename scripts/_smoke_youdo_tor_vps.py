#!/usr/bin/env python3
"""One-shot YouDo fetch smoke via local Tor on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
set -e
if ! command -v tor >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq tor
fi
systemctl enable tor >/dev/null 2>&1 || true
systemctl restart tor
sleep 2
echo TOR_STATUS=$(systemctl is-active tor)

cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import re, time
from playwright.sync_api import sync_playwright
from youdo_parser import _looks_like_antibot, parse_listing_html

url = "https://youdo.com/tasks-all-opened-all"
ua = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
tor = {"server": "socks5://127.0.0.1:9050"}


def fetch_via_tor(wait_until="domcontentloaded", extra_wait_ms=1500):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=tor)
        try:
            ctx = browser.new_context(user_agent=ua, locale="ru-RU")
            page = ctx.new_page()
            page.goto(url, wait_until=wait_until, timeout=90000)
            page.wait_for_timeout(extra_wait_ms)
            return page.content()
        finally:
            browser.close()


print("=== tor playwright domcontentloaded ===")
try:
    html = fetch_via_tor()
    ids = set(re.findall(r"/t(\d+)", html))
    print("len", len(html), "ids", len(ids), "data-id", html.count("data-id"))
    print("antibot", _looks_like_antibot(html))
    if not _looks_like_antibot(html):
        p = parse_listing_html(html, url)
        print("projects", len(p))
except Exception as e:
    print("pw_FAIL", type(e).__name__, str(e)[:500])

print("=== tor playwright networkidle ===")
try:
    html = fetch_via_tor(wait_until="networkidle", extra_wait_ms=5000)
    ids = set(re.findall(r"/t(\d+)", html))
    print("len", len(html), "ids", len(ids), "data-id", html.count("data-id"))
    print("antibot", _looks_like_antibot(html))
    if not _looks_like_antibot(html):
        p = parse_listing_html(html, url)
        print("projects", len(p))
except Exception as e:
    print("pw_idle_FAIL", type(e).__name__, str(e)[:500])
PY
"""

OUT = Path(__file__).resolve().parents[1] / "data" / "_smoke_youdo_tor_vps.txt"


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    text = (out or err or "").replace("\r\n", "\n")
    OUT.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
