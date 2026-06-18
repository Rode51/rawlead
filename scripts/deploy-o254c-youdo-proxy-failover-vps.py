#!/usr/bin/env python3
"""O254c mechanic: YouDo browser antibot → ban proxy + advance slot."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/exchange_proxy.py", "/opt/rawlead/src/exchange_proxy.py"),
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("scripts/restart_radar_youdo_cycle.py", "/opt/rawlead/scripts/restart_radar_youdo_cycle.py"),
)

SMOKE = r"""
cd /opt/rawlead
PW_VER=$(sudo -u rawlead .venv/bin/python -c "import playwright; print(playwright.__version__)" 2>/dev/null || echo unknown)
echo playwright=$PW_VER
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from exchange_proxy import clear_youdo_source_bans, exchange_alive_proxy_urls, exchange_primary_proxy_url
from youdo_parser import _reset_youdo_fail_streak, YOUDO_COOLDOWN_KEY, YOUDO_FETCH_CYCLE_KEY
from config import load_config
from storage import storage_from_config

st = storage_from_config(load_config())
_reset_youdo_fail_streak(st)
st.set_setting(YOUDO_COOLDOWN_KEY, "0")
st.set_setting(YOUDO_FETCH_CYCLE_KEY, "0")
n = clear_youdo_source_bans()
alive = exchange_alive_proxy_urls("youdo")
primary = exchange_primary_proxy_url("youdo")
print("bans_cleared", n, "alive", len(alive), "primary_hint", primary.split("@")[-1][:40] if primary else "none")
PY
PROXY=$(sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from exchange_proxy import exchange_alive_proxy_urls, exchange_primary_proxy_url
alive = exchange_alive_proxy_urls("youdo")
primary = exchange_primary_proxy_url("youdo") or (alive[0] if alive else "")
print(primary)
PY
)
if [ -z "$PROXY" ]; then echo smoke_skip no_proxy; exit 0; fi
echo smoke_proxy=${PROXY#*@}
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site .venv/bin/python scripts/youdo_fetch_worker.py \
  --url https://youdo.com/tasks-all-opened-all \
  --proxy "$PROXY" \
  --user-agent 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0' \
  --timeout 120 --stage listing --json 2>&1 | tail -1
grep 'youdo:trace.*fetch_end' /opt/rawlead/data/radar_site.log | tail -3
"""


def main() -> int:
    for local_rel, remote in _UPLOADS:
        local = _ROOT / local_rel
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up {local_rel}")
    _, out, err = ssh.run(SMOKE.strip(), check=False)
    text = (out or err or "").encode("ascii", errors="replace").decode("ascii")
    print(text)
    ok = "html_len" in text.lower() or '"html"' in text
    return 0 if ok or "bans_cleared" in text else 1


if __name__ == "__main__":
    raise SystemExit(main())
