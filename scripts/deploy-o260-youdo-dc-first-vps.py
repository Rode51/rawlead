#!/usr/bin/env python3
"""O260: YouDo DC-first canon — DC primary slot indexing, RU fallback only when DC exhausted."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

from config import normalize_proxy_url  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

_ENV_SITE = "/opt/rawlead/.env.site"
_UPLOADS = (
    ("src/exchange_proxy.py", "/opt/rawlead/src/exchange_proxy.py"),
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),
)


def _parse_list(raw: str) -> list[str]:
    out: list[str] = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(normalize_proxy_url(part))
        except ValueError:
            out.append(part)
    return out


def _hint(url: str) -> str:
    try:
        u = normalize_proxy_url(url)
    except ValueError:
        u = url if "://" in url else f"http://{url}"
    p = urlparse(u)
    return f"{p.hostname}:{p.port or ''}".rstrip(":")


def _dc_slots() -> list[str]:
    explicit = _parse_list(os.environ.get("YOUDO_DC_PROXY_URLS", ""))
    if explicit:
        return explicit
    fl = _parse_list(os.environ.get("FL_PROXY_URLS", ""))
    ex = _parse_list(os.environ.get("EXCHANGE_PROXY_URLS", ""))
    base = fl or ex
    if not base:
        return []
    try:
        n = max(1, int(os.environ.get("YOUDO_O191_DC_SLOTS", "4")))
    except ValueError:
        n = 4
    return base[:n]


def _patch_env_key(key: str, value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{key}=' {_ENV_SITE} 2>/dev/null && "
        f"sed -i '/^{key}=/d' {_ENV_SITE}; "
        f"echo '{key}={safe}' >> {_ENV_SITE} && "
        f"grep -c '^{key}=' {_ENV_SITE}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def _realign_remote() -> str:
    remote = r"""
cd /opt/rawlead
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
load_dotenv('/opt/rawlead/.env.site', override=True)
load_dotenv('/opt/rawlead/.env', override=False)
from exchange_proxy import (
    youdo_dc_alive_urls,
    youdo_dc_pool_size,
    youdo_realign_to_dc_tier,
    youdo_ru_alive_urls,
    proxy_log_hint,
)
realign = youdo_realign_to_dc_tier()
dc_alive = youdo_dc_alive_urls()
dc_total = youdo_dc_pool_size()
ru_alive = youdo_ru_alive_urls()
print(f"youdo_realign={realign}")
print(f"youdo_dc_alive={len(dc_alive)}/{dc_total}")
print(f"youdo_ru_alive={len(ru_alive)}")
print(f"proxy_hint={proxy_log_hint('youdo')}")
PY
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return out or ""


def _verify_remote() -> str:
    remote = r"""
grep 'fetch:youdo' /opt/rawlead/data/radar_site.log | tail -8
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return out or ""


def main() -> int:
    dc = _dc_slots()
    if not dc:
        print("FAIL — set YOUDO_DC_PROXY_URLS or FL_PROXY_URLS in local .env")
        return 1

    dc_val = ",".join(dc)
    slots_n = str(len(dc))
    print(f"O260 DC pool: {len(dc)} slots — {', '.join(_hint(u) for u in dc)}")

    for key, val in (
        ("YOUDO_DC_PROXY_URLS", dc_val),
        ("YOUDO_O191_DC_SLOTS", slots_n),
        ("YOUDO_RU_RETRY_MAX", "1"),
    ):
        if not _patch_env_key(key, val):
            print(f"FAIL — {key} not written")
            return 1
    print("env: YOUDO DC-first ok")

    for local_rel, remote in _UPLOADS:
        local = _ROOT / local_rel
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up {local_rel}")

    realign = _realign_remote()
    print(realign)

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar",
        check=False,
    )
    print(rst or "")

    verify = _verify_remote()
    print(verify)

    ok = (
        "active" in (rst or "")
        and "tier=dc" in realign
        and "youdo_dc_alive=" in realign
    )
    if not ok:
        print("O260 DEPLOY CHECK FAILED")
        return 1
    print("O260 DEPLOY OK — expect fetch:youdo tier=dc on next cycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
