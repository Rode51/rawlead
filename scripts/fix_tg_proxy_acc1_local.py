#!/usr/bin/env python3
"""Point acc1 / TG_PROXY to working spare (TELETHON_PROXY_ACC2) in local .env files."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = (_ROOT / ".env", _ROOT / ".env.site")
KEYS_TO_SWAP = ("TG_PROXY_URL", "TELETHON_PROXY_URL", "TELETHON_PROXY_ACC1")
SOURCE_KEY = "TELETHON_PROXY_ACC2"
DEAD_HOST = "45.152.197.25"


def _parse_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _host(url: str) -> str:
    m = re.search(r"@([^:/]+)", url)
    if m:
        return m.group(1)
    m2 = re.search(r"//([^:/]+)", url)
    return m2.group(1) if m2 else "?"


def _set_env_key(text: str, key: str, value: str) -> str:
    pat = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pat.search(text):
        return pat.sub(line, text, count=1)
    return text.rstrip("\n") + "\n" + line + "\n"


def main() -> int:
    env_path = _ROOT / ".env"
    if not env_path.is_file():
        print("skip: no .env")
        return 0

    spare = _parse_env(env_path.read_text(encoding="utf-8")).get(SOURCE_KEY, "").strip()
    if not spare or DEAD_HOST in spare:
        print("FAIL: set TELETHON_PROXY_ACC2 in .env first")
        return 1

    spare_host = _host(spare)
    any_change = False
    for path in ENV_FILES:
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        env = _parse_env(body)
        new_body = body
        changed = False
        for key in KEYS_TO_SWAP:
            old = env.get(key, "").strip()
            if not old or DEAD_HOST not in old:
                continue
            new_body = _set_env_key(new_body, key, spare)
            changed = True
            print(f"{path.name}: {key} {DEAD_HOST} -> {spare_host}")
        if changed:
            path.write_text(new_body, encoding="utf-8")
            any_change = True
        else:
            print(f"{path.name}: already ok (no {DEAD_HOST})")

    if not any_change:
        print("nothing to patch")
    else:
        print(f"OK: acc1/TG proxy -> spare host {spare_host}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
