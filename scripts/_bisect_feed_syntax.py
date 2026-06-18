#!/usr/bin/env python3
"""Bisect which line range in rawlead-feed.js introduces syntax error."""
from __future__ import annotations

import subprocess
from pathlib import Path

HEAD = subprocess.check_output(
    ["git", "show", "HEAD:wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js"],
    text=True,
    encoding="utf-8",
).splitlines()
CUR = Path("wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js").read_text(encoding="utf-8").splitlines()
OUT = Path("data/_feed_bisect.js")


def ok(lines: list[str]) -> bool:
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run(["node", "--check", str(OUT)], capture_output=True, text=True)
    return r.returncode == 0


assert ok(HEAD), "HEAD must parse"
assert not ok(CUR), "CUR must fail"

lo, hi = 0, len(CUR)
while lo < hi:
    mid = (lo + hi) // 2
    hybrid = HEAD[:mid] + CUR[mid:]
    if ok(hybrid):
        lo = mid + 1
    else:
        hi = mid

print("first bad line from CUR:", lo + 1)
for j in range(max(1, lo - 2), min(len(CUR), lo + 5)):
    print(f"{j:5} CUR: {CUR[j-1][:120]}")
    if j - 1 < len(HEAD):
        print(f"      OLD: {HEAD[j-1][:120]}")
