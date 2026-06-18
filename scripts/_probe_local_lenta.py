#!/usr/bin/env python3
"""Probe local lenta page + feed REST."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

URLS = [
    "http://radarzakaz.local/wp-json/rawlead/v1/feed?limit=3",
    "http://localhost:3011/wp-json/rawlead/v1/feed?limit=3",
    "https://api.rawlead.ru/v1/feed?limit=3",
]
PAGES = [
    "http://radarzakaz.local/lenta/",
    "http://localhost:3011/lenta/",
]


def fetch(url: str, timeout: int = 30) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


def main() -> int:
    print("=== REST ===")
    for url in URLS:
        try:
            code, body = fetch(url)
            data = json.loads(body)
            n = len(data.get("items", []))
            print(f"OK  {url}  status={code}  items={n}")
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:300]
            print(f"HTTP {e.code}  {url}\n  {err}")
        except Exception as e:
            print(f"FAIL {url}  {type(e).__name__}: {e}")

    print("\n=== PAGES ===")
    for url in PAGES:
        try:
            code, html = fetch(url, timeout=20)
            print(f"OK  {url}  status={code}")
            print(f"  rawleadFeed: {'rawleadFeed' in html}")
            print(f"  rawlead-feed.js: {'rawlead-feed.js' in html}")
            print(f"  rl-feed-list: {'rl-feed-list' in html}")
            m = re.search(r"rawlead-feed\.js\?ver=([\d.]+)", html)
            print(f"  feed ver: {m.group(1) if m else 'n/a'}")
            if "rawleadFeed" not in html:
                print("  WARN: feed JS not enqueued — WP page slug may not be 'lenta'")
        except Exception as e:
            print(f"FAIL {url}  {type(e).__name__}: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
