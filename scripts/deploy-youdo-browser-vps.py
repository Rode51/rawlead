#!/usr/bin/env python3
"""Deploy O63 secondary ingest fix: YouDo browser-only + FR.ru/pchyol parsers."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/exchange_proxy.py", "/opt/rawlead/src/exchange_proxy.py"),
    ("src/freelance_ru_parser.py", "/opt/rawlead/src/freelance_ru_parser.py"),
    ("src/pchyol_parser.py", "/opt/rawlead/src/pchyol_parser.py"),
)

CLEAR = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python - <<'PY'\n"
    "from config import load_config\n"
    "from storage import ProjectStorage\n"
    "c = load_config()\n"
    "st = ProjectStorage(c.sqlite_path)\n"
    "import json\n"
    "for key in ('exchange_proxy_bans_v1', 'exchange_proxy_bans_v2'):\n"
    "    raw = st.get_setting(key, '{}') or '{}'\n"
    "    try:\n"
    "        data = json.loads(raw)\n"
    "    except json.JSONDecodeError:\n"
    "        data = {}\n"
    "    kept = {k: v for k, v in data.items() if not str(k).startswith('youdo:')}\n"
    "    st.set_setting(key, json.dumps(kept, ensure_ascii=False))\n"
    "    print(key, 'cleared youdo keys', len(data) - len(kept))\n"
    "PY\n"
)

ENV_PATCH = (
    "ENV=/opt/rawlead/.env.site; "
    "grep -q '^EXCHANGE_LISTING_BROWSER=' \"$ENV\" 2>/dev/null || "
    "echo 'EXCHANGE_LISTING_BROWSER=1' | sudo tee -a \"$ENV\" >/dev/null; "
    "grep -E '^(YOUDO_|EXCHANGE_LISTING_BROWSER|PUBLIC_FEED)' \"$ENV\" 2>/dev/null | head -8"
)


def main() -> int:
    for local_rel, remote in _UPLOADS:
        local = _ROOT / local_rel
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up {local_rel}")
    _, out, _ = ssh.run(CLEAR, check=False)
    print(out or "")
    _, out, _ = ssh.run(
        f"{ENV_PATCH}; systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar",
        check=False,
    )
    print(out or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
