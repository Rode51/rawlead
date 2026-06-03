#!/usr/bin/env python3
"""Smoke O96 polish-b on prod rawlead.ru."""
from __future__ import annotations

import json
import re
import sys
import urllib.request

BASE = "https://rawlead.ru"


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "rawlead-o96-verify/1.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def main() -> int:
    ok = True
    checks: list[str] = []

    code, html = fetch(f"{BASE}/lenta/")
    if code != 200:
        ok = False
        checks.append(f"FAIL /lenta/ HTTP {code}")
    else:
        if "rl-feed-anon-strip" in html and "Это под твой стек?" in html:
            checks.append("OK anon strip markup")
        else:
            ok = False
            checks.append("FAIL anon strip")
        if "Зарегистрируйтесь, чтобы настроить" in html:
            ok = False
            checks.append("FAIL old card CTA still in page HTML")
        else:
            checks.append("OK no old CTA in page shell")
        if "1.17.2" in html or "ver=1.17.2" in html:
            checks.append("OK theme 1.17.2 enqueued")
        else:
            m = re.search(r"ver=([\d.]+)", html)
            checks.append(f"WARN theme version {m.group(1) if m else '?'} (cache?)")

    code, html = fetch(BASE + "/")
    if "Один поток вместо десяти вкладок" in html:
        checks.append("OK features H2 canon (Z1)")
    else:
        ok = False
        checks.append("FAIL features H2 not canon")

    code, html = fetch(f"{BASE}/cabinet/")
    if "Показать ещё" in html:
        checks.append("OK cabinet load-more copy (Z2)")
    else:
        ok = False
        checks.append("FAIL cabinet still «Ещё лиды» or missing")

    try:
        code, body = fetch(f"{BASE}/v1/feed?limit=4")
        data = json.loads(body)
        items = data.get("items") or []
        if len(items) >= 4:
            checks.append(f"OK API feed 4+ items for grid smoke ({len(items)})")
        else:
            checks.append(f"WARN API feed items={len(items)} (<4 for grid smoke)")
        if "today_count" in data:
            checks.append(f"OK API today_count={data.get('today_count')}")
    except Exception as exc:
        checks.append(f"WARN API feed: {exc}")

    for line in checks:
        print(line)
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
