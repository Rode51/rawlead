from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from exchange_proxy import _shared_exchange_pool, _urls_for_source


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
        "fl": _urls_for_source("fl")[1] or _shared_exchange_pool(),
        "kwork": _urls_for_source("kwork")[1] or _shared_exchange_pool(),
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
