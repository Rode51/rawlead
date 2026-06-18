#!/usr/bin/env python3
"""Reset YouDo cycle/cooldown and restart rawlead-radar (O190 t0i gate)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from config import load_config
from storage import storage_from_config
from exchange_proxy import clear_youdo_source_bans
from youdo_parser import _reset_youdo_fail_streak, YOUDO_COOLDOWN_KEY, YOUDO_FETCH_CYCLE_KEY

st = storage_from_config(load_config())
_reset_youdo_fail_streak(st)
st.set_setting(YOUDO_COOLDOWN_KEY, "0")
st.set_setting(YOUDO_FETCH_CYCLE_KEY, "0")
cleared = clear_youdo_source_bans()
print("reset_ok cycle=0 cooldown=0 bans_cleared=", cleared)
try:
    from exchange_browser_fetch import youdo_browser_teardown
    killed = youdo_browser_teardown()
    print("teardown_ok killed=", killed)
except Exception as exc:
    print("teardown_warn", exc)
PY
systemctl stop rawlead-radar 2>/dev/null || true
sleep 2
systemctl reset-failed rawlead-radar 2>/dev/null || true
systemctl start rawlead-radar
sleep 8
systemctl is-active rawlead-radar
echo restart_ok
grep fetch_end /opt/rawlead/data/radar_site.log | tail -3
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    text = (out or err or "").encode("ascii", errors="replace").decode("ascii")
    print(text)
    return 0 if "restart_ok" in text and "active" in text else 1


if __name__ == "__main__":
    raise SystemExit(main())
