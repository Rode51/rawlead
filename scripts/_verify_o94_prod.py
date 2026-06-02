#!/usr/bin/env python3
"""Smoke: O94 catalog + lenta modal on prod."""
from __future__ import annotations

import json
import re
import urllib.request

CATALOG = "https://api.rawlead.ru/v1/skills/catalog"
LENTA = "https://rawlead.ru/lenta/"


def main() -> int:
    ok = True
    with urllib.request.urlopen(CATALOG, timeout=20) as r:
        data = json.loads(r.read())
    for g in data.get("groups") or []:
        cat = g.get("category")
        if cat == "dev":
            keys = [s.get("key") for s in (g.get("picker_subheads") or [])]
            print("dev subheads:", keys)
            if keys != ["use_case", "technology"]:
                ok = False
            for s in g.get("skills") or []:
                if s.get("tag") == "python":
                    ch = s.get("children") or []
                    print("python L3:", ch)
                    if "flask" not in ch or "scrapy" not in ch:
                        ok = False
        if cat == "design":
            keys = [s.get("key") for s in (g.get("picker_subheads") or [])]
            print("design subheads:", keys)
            if not keys:
                ok = False

    with urllib.request.urlopen(LENTA, timeout=20) as r:
        html = r.read().decode("utf-8", errors="replace")
    print("modal in HTML:", "rl-feed-skills-modal" in html)
    if "rl-feed-skills-modal" not in html:
        ok = False
    m = re.search(r"rawlead-feed\.js\?ver=([\d.]+)", html)
    print("feed js ver:", m.group(1) if m else "n/a")
    if not m or m.group(1) < "1.14.0":
        ok = False
    print("double caret bug:", "Навыки ▾ ▾" in html)

    print("SMOKE", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
