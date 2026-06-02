from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import normalize_proxy_url


def _parse_pool(name_plural: str, name_single: str) -> list[str]:
    raw = os.environ.get(name_plural, "").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()] if raw else []
    if not parts:
        one = os.environ.get(name_single, "").strip()
        if one:
            parts = [one]
    out: list[str] = []
    for p in parts:
        try:
            out.append(normalize_proxy_url(p))
        except ValueError:
            continue
    return out


def _probe_tcp(proxy_url: str, timeout_sec: float) -> bool:
    parsed = urlparse(proxy_url)
    host = parsed.hostname
    if not host:
        return False
    port = parsed.port or 8080
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout_sec)
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def probe_exchange_pools(timeout_sec: float = 5.0) -> dict[str, dict[str, int]]:
    pools = {
        "fl": _parse_pool("FL_PROXY_URLS", "FL_PROXY_URL"),
        "kwork": _parse_pool("KWORK_PROXY_URLS", "KWORK_PROXY_URL"),
    }
    out: dict[str, dict[str, int]] = {}
    for source, urls in pools.items():
        if not urls:
            out[source] = {"alive": 0, "total": 0}
            continue
        alive = sum(1 for u in urls if _probe_tcp(u, timeout_sec))
        out[source] = {"alive": alive, "total": len(urls)}
    return out


if __name__ == "__main__":
    result = probe_exchange_pools()
    print(json.dumps(result, ensure_ascii=False))
