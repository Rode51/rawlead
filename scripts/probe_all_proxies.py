#!/usr/bin/env python3
"""Probe all VPS proxies: TCP + HTTPS to relevant targets. Masks credentials."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)

import os  # noqa: E402

import requests  # noqa: E402

from config import normalize_proxy_url  # noqa: E402
from proxy_ops import https_probe, mask, tcp_ok  # noqa: E402

ENV_KEYS = [
    "TG_PROXY_URL",
    "TELETHON_PROXY_URL",
    "TELETHON_PROXY_ACC1",
    "TELETHON_PROXY_ACC2",
    "TELETHON_PROXY_ACC3",
    "EXCHANGE_PROXY_URLS",
    "EXCHANGE_PROXY_URLS_SECONDARY",
    "FL_PROXY_URLS",
    "KWORK_PROXY_URLS",
    "YOUDO_PROXY_URLS",
    "FREELANCE_RU_PROXY_URLS",
    "FREELANCEJOB_PROXY_URLS",
    "PCHYOL_PROXY_URLS",
]

TARGETS = {
    "telegram": "https://api.telegram.org/",
    "fl": "https://www.fl.ru/projects/",
    "kwork": "https://kwork.ru/projects",
    "youdo": "https://youdo.com/",
    "generic": "https://httpbin.org/ip",
}


def parse_list(raw: str) -> list[str]:
    out: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(normalize_proxy_url(part))
        except ValueError:
            out.append(part)
    return out


def main() -> int:
    print("=== RawLead proxy probe ===\n")

    # collect unique proxies with labels
    labeled: list[tuple[str, str, str]] = []  # label, raw_key, url
    seen_urls: set[str] = set()

    for key in ENV_KEYS:
        raw = os.getenv(key, "").strip()
        if not raw:
            continue
        items = parse_list(raw) if "," in raw else [raw]
        for i, u in enumerate(items):
            try:
                norm = normalize_proxy_url(u)
            except ValueError:
                norm = u
            label = key if len(items) == 1 else f"{key}[{i}]"
            if norm not in seen_urls:
                seen_urls.add(norm)
                labeled.append((label, key, norm))

    if not labeled:
        print("No proxy env vars set.")
        return 1

    print(f"Found {len(labeled)} unique proxy endpoint(s)\n")

    # assign HTTPS target per label
    def target_for(label: str) -> str:
        lu = label.upper()
        if "TG_" in lu or "TELETHON" in lu:
            return TARGETS["telegram"]
        if "KWORK" in lu:
            return TARGETS["kwork"]
        if "FL_" in lu or "EXCHANGE" in lu:
            return TARGETS["fl"]
        if "YOUDO" in lu:
            return TARGETS["youdo"]
        return TARGETS["generic"]

    results: list[tuple[str, str, bool, str, bool, str]] = []
    for label, _key, url in labeled:
        m = mask(url)
        tcp, tcp_msg = tcp_ok(url)
        tgt = target_for(label)
        https, https_msg = https_probe(url, tgt)
        results.append((label, m, tcp, tcp_msg, https, https_msg))

    # table
    w_label = max(len(r[0]) for r in results)
    print(f"{'LABEL'.ljust(w_label)}  {'ENDPOINT'.ljust(36)}  TCP       HTTPS → target")
    print("-" * (w_label + 70))
    for label, m, tcp, tcp_msg, https, https_msg in results:
        tcp_s = "OK" if tcp else "FAIL"
        https_s = "OK" if https else "FAIL"
        tgt_short = target_for(label).split("/")[2]
        print(f"{label.ljust(w_label)}  {m[:36].ljust(36)}  {tcp_s:4}      {https_s:4}  {https_msg[:60]}")

    print()
    ok_https = sum(1 for r in results if r[4])
    ok_tcp = sum(1 for r in results if r[2])
    print(f"Summary: TCP {ok_tcp}/{len(results)} · HTTPS {ok_https}/{len(results)}")

    # direct baseline
    print("\n=== Direct (no proxy) baseline ===")
    for name, url in [("telegram", TARGETS["telegram"]), ("fl", TARGETS["fl"]), ("kwork", TARGETS["kwork"])]:
        try:
            r = requests.get(url, timeout=10, proxies={"http": None, "https": None})
            print(f"  {name}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  {name}: FAIL {type(e).__name__}: {str(e)[:80]}")

    return 0 if ok_https else 1


if __name__ == "__main__":
    raise SystemExit(main())
