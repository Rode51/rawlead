#!/usr/bin/env python3
"""Smoke: O95 shell + O94-w4 L3 tray on prod."""
from __future__ import annotations

import re
import urllib.request

LENTA = "https://rawlead.ru/lenta/"


def main() -> int:
    ok = True
    with urllib.request.urlopen(LENTA, timeout=25) as r:
        html = r.read().decode("utf-8", errors="replace")
    m = re.search(r"rawlead-feed\.js\?ver=([\d.]+)", html)
    ver = m.group(1) if m else "n/a"
    print("feed js ver:", ver)
    if not m or ver < "1.16.1":
        ok = False
    print("tags-edit btn:", "rl-feed-tags-edit" in html)
    if "rl-feed-tags-edit" not in html:
        ok = False
    print("skills modal:", "rl-feed-skills-modal" in html)
    css = re.search(r"rawlead\.css\?ver=([\d.]+)", html)
    print("css ver:", css.group(1) if css else "n/a")
    with urllib.request.urlopen(
        "https://rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
        timeout=25,
    ) as r:
        css_text = r.read().decode("utf-8", errors="replace")
    with urllib.request.urlopen(
        "https://rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js?ver="
        + (ver if ver != "n/a" else "1.16.1"),
        timeout=25,
    ) as r:
        feed_js = r.read().decode("utf-8", errors="replace")
    print("feed tags sync:", "rawlead_user_tags_rev" in feed_js)
    print("feed dedupe tray:", "data-l3-deduped" in feed_js)
    print("rl-l3-tray in css:", ".rl-l3-tray" in css_text)
    if "rawlead_user_tags_rev" not in feed_js or ".rl-l3-tray" not in css_text:
        ok = False
    print("SMOKE", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
