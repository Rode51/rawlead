#!/usr/bin/env python3
"""O268: YouDo recovery — ephemeral-first, profile wipe, 4 DC pool, RU burst cap."""
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
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/exchange_proxy.py", "/opt/rawlead/src/exchange_proxy.py"),
    ("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),
    ("scripts/youdo_sticky_worker.py", "/opt/rawlead/scripts/youdo_sticky_worker.py"),
    ("scripts/youdo_fetch_worker.py", "/opt/rawlead/scripts/youdo_fetch_worker.py"),
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


def _wipe_youdo_profiles_remote() -> str:
    cmd = (
        "rm -rf /opt/rawlead/data/youdo_* 2>/dev/null; "
        "ls -d /opt/rawlead/data/youdo_* 2>/dev/null | wc -l"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip()


def _verify_remote() -> str:
    remote = r"""
grep 'youdo:ingest done' /opt/rawlead/data/radar_site.log | tail -3
grep 'fetch:youdo' /opt/rawlead/data/radar_site.log | tail -8
grep 'profile_wiped=sp\|ru_burst=' /opt/rawlead/data/radar_site.log | tail -5
cd /opt/rawlead
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
load_dotenv('/opt/rawlead/.env.site', override=True)
load_dotenv('/opt/rawlead/.env', override=False)
from exchange_proxy import youdo_dc_alive_urls, youdo_dc_pool_size
print(f"youdo_dc_alive={len(youdo_dc_alive_urls())}/{youdo_dc_pool_size()}")
PY
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return (out or "").replace("\r\n", "\n")


def main() -> int:
    dc = _dc_slots()
    if not dc:
        print("FAIL — set YOUDO_DC_PROXY_URLS or FL_PROXY_URLS in local .env")
        return 1

    dc_val = ",".join(dc)
    print(f"O268 DC pool: {len(dc)} slots — {', '.join(_hint(u) for u in dc)}")

    env_pairs = (
        ("YOUDO_STICKY_SESSION", "1"),
        ("YOUDO_PERSISTENT_PROFILE", "1"),
        ("YOUDO_STICKY_AFTER_OK", "1"),
        ("YOUDO_GOTO_WAIT_UNTIL", "domcontentloaded"),
        ("YOUDO_SERVICEPIPE_WAIT_SEC", "90"),
        ("YOUDO_SOFT_SERVICEPIPE_BAN", "1"),
        ("YOUDO_STICKY_RELOAD_SP_ABORT_SEC", "15"),
        ("YOUDO_O191_DC_SLOTS", str(len(dc))),
        ("YOUDO_DC_PROXY_URLS", dc_val),
        ("YOUDO_RU_RETRY_MAX", "1"),
        ("YOUDO_RU_BURST_MAX_PER_DAY", "2"),
        ("YOUDO_SERVICEPIPE_EARLY_RU", "0"),
        ("YOUDO_PROFILE_GENERATION", "2"),
        ("YOUDO_MAX_DC_BANS_PER_FETCH", "1"),
    )
    for key, val in env_pairs:
        if not _patch_env_key(key, val):
            print(f"FAIL — {key} not written")
            return 1
    print("env: O268 recovery vars ok")

    left = _wipe_youdo_profiles_remote()
    print(f"wipe youdo_* profiles remaining={left}")

    for local, remote in _UPLOADS:
        ssh.upload(_ROOT / local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"uploaded {local}")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-radar rawlead-api",
        check=False,
    )
    print(rst or "")
    print(_verify_remote())

    ok = "active" in (rst or "")
    if not ok:
        print("FAIL — services not active")
        return 1
    print("OK — O268 YouDo recovery deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
