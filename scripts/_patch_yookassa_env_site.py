#!/usr/bin/env python3
"""Patch /opt/rawlead/.env.site with keys from /tmp/rawlead_yookassa.env."""
from __future__ import annotations

import pathlib

patch = pathlib.Path("/tmp/rawlead_yookassa.env").read_text(encoding="utf-8")
updates: dict[str, str] = {}
for line in patch.splitlines():
    if not line.strip() or line.strip().startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    updates[k.strip()] = v.strip()

path = pathlib.Path("/opt/rawlead/.env.site")
lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
out: list[str] = []
seen: set[str] = set()
for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        k = line.split("=", 1)[0].strip()
        if k in updates:
            out.append(f"{k}={updates[k]}")
            seen.add(k)
            continue
    out.append(line)
for k, v in updates.items():
    if k not in seen:
        out.append(f"{k}={v}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
print("patched:", ",".join(sorted(updates)))
