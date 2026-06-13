#!/usr/bin/env python3
"""One-shot YouDo fetch smoke — alive proxy slot failover (O190 t0d)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead env \
  PYTHONPATH=/opt/rawlead/src \
  RADAR_PROFILE=site \
  EXCHANGE_LISTING_BROWSER=1 \
  YOUDO_BROWSER_ONLY=1 \
  xvfb-run -a --server-args="-screen 0 1366x768x24" \
  .venv/bin/python - <<'PY'
import os
from config import load_config
from exchange_proxy import exchange_alive_proxy_urls
from exchange_browser_fetch import fetch_listing_html_browser_slots

cfg = load_config()
print("headless", os.getenv("YOUDO_HEADLESS", "?"))
print("browser", os.getenv("YOUDO_BROWSER", "patchright"))
print("wait_until", os.getenv("YOUDO_GOTO_WAIT_UNTIL", "?"))
print("goto_timeout", os.getenv("YOUDO_GOTO_TIMEOUT_SEC", "?"))
print("slot_retry_max", os.getenv("YOUDO_SLOT_RETRY_ON_TIMEOUT", "3"))
url = "https://youdo.com/tasks-all-opened-all"
slots = exchange_alive_proxy_urls("youdo")
print("slots", len(slots))
if not slots:
    raise SystemExit("no proxy slots")
try:
    html = fetch_listing_html_browser_slots(
        "youdo",
        url,
        user_agent=cfg.http_user_agent,
        timeout_sec=float(os.getenv("YOUDO_GOTO_TIMEOUT_SEC", "150")),
    )
    print("OK html_len", len(html), "data-id", html.count("data-id"))
except Exception as exc:
    print("FAIL", type(exc).__name__, str(exc)[:300])
PY
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    text = (out or err or "").replace("\r\n", "\n")
    out_path = _ROOT / "data" / "smoke_youdo_t6c_vps.txt"
    out_path.write_text(text, encoding="utf-8")
    print(text.encode("ascii", errors="replace").decode("ascii"))
    return 0 if "OK html_len" in text and "data-id" in text else 1


if __name__ == "__main__":
    raise SystemExit(main())
