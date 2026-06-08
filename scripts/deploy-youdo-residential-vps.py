#!/usr/bin/env python3
"""YouDo: socks5 config + HC pulse + YOUDO_PROXY_URLS from local .env + clear bans."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

_UPLOADS = (
    "src/config.py",
    "src/healthchecks.py",
    "src/main.py",
    "src/lead_pipeline.py",
    "src/exchange_browser_fetch.py",
    "src/youdo_parser.py",
    "src/exchange_proxy.py",
)

_ENV_SITE = "/opt/rawlead/.env.site"
_KEY = "YOUDO_PROXY_URLS"

CLEAR_YOUDO = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python - <<'PY'\n"
    "import json\n"
    "from config import load_config\n"
    "from storage import ProjectStorage\n"
    "st = ProjectStorage(load_config().sqlite_path)\n"
    "for key in ('exchange_proxy_bans_v1', 'exchange_proxy_bans_v2'):\n"
    "    raw = st.get_setting(key, '{}') or '{}'\n"
    "    try:\n"
    "        data = json.loads(raw)\n"
    "    except json.JSONDecodeError:\n"
    "        data = {}\n"
    "    kept = {k: v for k, v in data.items() if not str(k).startswith('youdo:')}\n"
    "    st.set_setting(key, json.dumps(kept, ensure_ascii=False))\n"
    "    print(key, 'youdo_cleared', len(data) - len(kept))\n"
    "st.set_setting('youdo_cooldown_until', '0')\n"
    "print('youdo_cooldown_reset')\n"
    "PY\n"
)


def _patch_youdo_env(value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{_KEY}=' {_ENV_SITE} 2>/dev/null && "
        f"sed -i '/^{_KEY}=/d' {_ENV_SITE}; "
        f"echo '{_KEY}={safe}' >> {_ENV_SITE} && "
        f"grep -c '^{_KEY}=' {_ENV_SITE}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def main() -> int:
    value = (__import__("os").environ.get(_KEY) or "").strip()
    if not value:
        print(f"Set {_KEY} in .env")
        return 1
    slots = [p for p in value.split(",") if p.strip()]
    print(f"YOUDO pool: {len(slots)} slots")

    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    if not _patch_youdo_env(value):
        print("FAIL — YOUDO_PROXY_URLS not written to VPS .env.site")
        return 1
    print("env: YOUDO_PROXY_URLS ok")

    _, out, _ = ssh.run(CLEAR_YOUDO, check=False)
    print(out or "")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python - <<'PY'\n"
        "from dotenv import load_dotenv\n"
        "load_dotenv('/opt/rawlead/.env.site', override=True)\n"
        "load_dotenv('/opt/rawlead/.env', override=False)\n"
        "from exchange_proxy import exchange_pool_status\n"
        "print(exchange_pool_status('youdo'))\n"
        "PY\n"
        "echo deploy_youdo_ok",
        check=False,
    )
    print(out or "")
    ok = "deploy_youdo_ok" in (out or "") and "active" in (out or "")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
