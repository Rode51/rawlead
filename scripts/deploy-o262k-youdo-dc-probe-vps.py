#!/usr/bin/env python3
"""O262k: restore DC-first env on VPS, upload probe, run DC diagnostic."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

from config import normalize_proxy_url  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

_ENV_SITE = "/opt/rawlead/.env.site"
_PROBE_LOCAL = _ROOT / "scripts" / "probe_youdo_dc_page.py"
_PROBE_REMOTE = "/opt/rawlead/scripts/probe_youdo_dc_page.py"
_WORKER_REMOTE = "/opt/rawlead/scripts/youdo_fetch_worker.py"


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
from exchange_proxy import youdo_dc_alive_urls, youdo_dc_pool_size, youdo_realign_to_dc_tier
realign = youdo_realign_to_dc_tier()
dc_alive = youdo_dc_alive_urls()
dc_total = youdo_dc_pool_size()
print(f"youdo_realign={realign}")
print(f"youdo_dc_alive={len(dc_alive)}/{dc_total}")
PY
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return out or ""


def _restore_dc_env() -> int:
    dc = _dc_slots()
    if not dc:
        print("FAIL — set YOUDO_DC_PROXY_URLS or FL_PROXY_URLS in local .env")
        return 1
    dc_val = ",".join(dc)
    slots_n = str(len(dc))
    print(f"O262k restore DC: {len(dc)} slots — {', '.join(_hint(u) for u in dc)}")
    for key, val in (
        ("YOUDO_DC_PROXY_URLS", dc_val),
        ("YOUDO_O191_DC_SLOTS", slots_n),
    ):
        if not _patch_env_key(key, val):
            print(f"FAIL — {key} not written")
            return 1
        print(f"env: {key} ok")
    print(_realign_remote())
    return 0


def _run_probe() -> tuple[int, str]:
    remote = (
        "cd /opt/rawlead && sudo -u rawlead env "
        "PYTHONPATH=/opt/rawlead/src:/opt/rawlead "
        "RADAR_PROFILE=site "
        ".venv/bin/python scripts/probe_youdo_dc_page.py --json 2>&1"
    )
    return ssh.run(remote, check=False)


def main() -> int:
    if _restore_dc_env() != 0:
        return 1

    uploads = (
        (_PROBE_LOCAL, _PROBE_REMOTE),
        (_ROOT / "scripts" / "youdo_fetch_worker.py", _WORKER_REMOTE),
        (_ROOT / "src" / "exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    )
    for local, remote in uploads:
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")

    print("\n=== probe_youdo_dc_page.py (VPS) ===")
    code, out, _ = _run_probe()
    text = (out or "").replace("\r\n", "\n")
    print(text)

    out_path = _ROOT / "data" / "o262k_dc_probe.json"
    try:
        start = text.find("{")
        if start >= 0:
            obj = json.loads(text[start:])
            out_path.write_text(
                json.dumps(obj, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\nsaved: {out_path}")
    except (json.JSONDecodeError, OSError) as exc:
        print(f"WARN — could not save JSON: {exc}")

    _, verify, _ = ssh.run(
        f"grep YOUDO_O191_DC_SLOTS {_ENV_SITE} | tail -1; "
        f"grep YOUDO_DC_PROXY_URLS {_ENV_SITE} | tail -1 | cut -c1-80",
        check=False,
    )
    print(verify or "")

    if code != 0:
        print(f"probe exit {code}")
        return code
    print("O262k DC probe OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
