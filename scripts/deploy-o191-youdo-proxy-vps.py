#!/usr/bin/env python3
"""O191: prepend DC proxy slot(s) to YOUDO_PROXY_URLS on VPS; RU residential stays after.

Order written to VPS: DC (from FL/EXCHANGE pool, copied — not merged with FL/Kwork runtime) →
existing RU node-proxy slots. Rollback: restore RU-only via patch-vps-youdo-proxy-env.py.

Env (local .env, secrets not in git):
  YOUDO_O191_DC_SLOTS=1          # how many FL/EXCHANGE slots to prepend (default 1)
  YOUDO_DC_PROXY_URLS=...        # optional explicit DC list (overrides FL take)
  YOUDO_PROXY_URLS=...           # RU residential tail (25 slots typical)
  FL_PROXY_URLS / EXCHANGE_PROXY_URLS — DC source when YOUDO_DC_PROXY_URLS empty

Does NOT touch YOUDO_FETCH_EVERY_N or FL/Kwork proxy env keys.
"""
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
    "slot_raw = st.get_setting('exchange_proxy_active_slot_v1', '{}') or '{}'\n"
    "try:\n"
    "    slots = json.loads(slot_raw)\n"
    "except json.JSONDecodeError:\n"
    "    slots = {}\n"
    "if not isinstance(slots, dict):\n"
    "    slots = {}\n"
    "old = slots.get('youdo')\n"
    "slots['youdo'] = 0\n"
    "st.set_setting('exchange_proxy_active_slot_v1', json.dumps(slots, ensure_ascii=False))\n"
    "print('youdo_active_slot', old, '->', 0)\n"
    "print('youdo_cooldown_reset')\n"
    "PY\n"
)


def _hint(url: str) -> str:
    try:
        u = normalize_proxy_url(url)
    except ValueError:
        u = url if "://" in url else f"http://{url}"
    p = urlparse(u)
    return f"{p.hostname}:{p.port or ''}".rstrip(":")


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
        n = max(1, int(os.environ.get("YOUDO_O191_DC_SLOTS", "1")))
    except ValueError:
        n = 1
    return base[:n]


def _ru_tail() -> list[str]:
    return _parse_list(os.environ.get(_KEY, ""))


def _merge_dc_ru(dc: list[str], ru: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for url in dc + ru:
        h = _hint(url)
        if h in seen:
            continue
        seen.add(h)
        merged.append(url)
    return merged


def _patch_env(value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{_KEY}=' {_ENV_SITE} 2>/dev/null && "
        f"sed -i '/^{_KEY}=/d' {_ENV_SITE}; "
        f"echo '{_KEY}={safe}' >> {_ENV_SITE} && "
        f"grep -c '^{_KEY}=' {_ENV_SITE}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def _vps_hints() -> tuple[int, list[str]]:
    remote = r"""
python3 - <<'PY'
from urllib.parse import urlparse
path = "/opt/rawlead/.env.site"
val = ""
for line in open(path):
    if line.startswith("YOUDO_PROXY_URLS="):
        val = line.split("=", 1)[1].strip()
        break
slots = [p.strip() for p in val.split(",") if p.strip()]
hints = []
for s in slots:
    u = s if "://" in s else "http://" + s
    p = urlparse(u)
    hints.append(f"{p.hostname}:{p.port or ''}".rstrip(":"))
print(len(slots))
print("|".join(hints[:5]))
print("|".join(hints[-2:]))
PY
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    if not lines:
        return 0, []
    try:
        count = int(lines[0])
    except ValueError:
        return 0, []
    hints = []
    for chunk in lines[1:]:
        hints.extend([h for h in chunk.split("|") if h])
    return count, hints


def main() -> int:
    dc = _dc_slots()
    ru = _ru_tail()
    if not dc:
        print("FAIL — set YOUDO_DC_PROXY_URLS or FL_PROXY_URLS / EXCHANGE_PROXY_URLS in .env")
        return 1
    if not ru:
        print(f"FAIL — set {_KEY} (RU residential tail) in .env")
        return 1

    merged = _merge_dc_ru(dc, ru)
    dc_hints = [_hint(u) for u in dc]
    print(f"O191 merge: {len(dc)} DC + {len(ru)} RU -> {len(merged)} slots")
    print("DC hints:", ", ".join(dc_hints))
    print("RU first hint:", _hint(ru[0]) if ru else "?")

    if not _patch_env(",".join(merged)):
        print("FAIL — YOUDO_PROXY_URLS not written to VPS .env.site")
        return 1
    print("env: YOUDO_PROXY_URLS ok")

    _, out, _ = ssh.run(CLEAR_YOUDO, check=False)
    print(out or "")

    verify_remote = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python - <<'PY'\n"
        "from dotenv import load_dotenv\n"
        "load_dotenv('/opt/rawlead/.env.site', override=True)\n"
        "load_dotenv('/opt/rawlead/.env', override=False)\n"
        "from exchange_proxy import exchange_pool_status\n"
        "print(exchange_pool_status('youdo'))\n"
        "PY"
    )
    _, out, _ = ssh.run(verify_remote.strip(), check=False)
    print(out or "")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && echo o191_deploy_ok",
        check=False,
    )
    text = (rst or "") + "\n" + (out or "")
    print(rst or "")

    count, hints = _vps_hints()
    print(f"VPS verify: {count} slots, head={hints[:3]}, tail={hints[-2:]}")

    ok = (
        "o191_deploy_ok" in text
        and "active" in text
        and count == len(merged)
        and hints
        and hints[0] == dc_hints[0]
    )
    if not ok:
        print("O191 DEPLOY CHECK FAILED")
        return 1
    print("O191 DEPLOY OK — run: python scripts/smoke_youdo_t6c_vps.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
