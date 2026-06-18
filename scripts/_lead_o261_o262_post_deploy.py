#!/usr/bin/env python3
"""Lead post-deploy: O262 env, clear YouDo bans, verify logs."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

ENV_PATCH = (
    "grep -q '^YOUDO_LIST_VIEW_CLICK=' /opt/rawlead/.env.site 2>/dev/null && "
    "sed -i '/^YOUDO_LIST_VIEW_CLICK=/d' /opt/rawlead/.env.site; "
    "echo 'YOUDO_LIST_VIEW_CLICK=1' >> /opt/rawlead/.env.site"
)

CLEAR_YOUDO = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site .venv/bin/python - <<'PY'
from config import load_config
from storage import ProjectStorage
from exchange_proxy import clear_youdo_source_bans, youdo_dc_alive_urls
from youdo_parser import youdo_hard_reset

cfg = load_config()
st = ProjectStorage(cfg.sqlite_path)
cleared = clear_youdo_source_bans()
youdo_hard_reset(reason="lead_deploy_o261_o262", storage=st)
print("youdo_bans_cleared", cleared)
print("dc_alive", len(youdo_dc_alive_urls()))
PY
systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar
"""

VERIFY = r"""
echo '--- code ---'
grep -c list_view_click /opt/rawlead/src/exchange_browser_fetch.py
grep -c clear-youdo-bans /opt/rawlead/src/proxy_ops.py
grep YOUDO_LIST_VIEW_CLICK /opt/rawlead/.env.site | tail -1
echo '--- log ---'
grep -E 'list_view|fetch:youdo|youdo:trace' /opt/rawlead/data/radar_site.log | tail -30
"""


def poll_logs() -> None:
    _, out, err = ssh.run(
        "grep -E 'list_view|fetch:youdo|youdo:trace|fetch:fl|listing:fl|health:youdo|health:fl' "
        "/opt/rawlead/data/radar_site.log | tail -40",
        check=False,
    )
    print((out or err or "").replace("\r\n", "\n"))


def grep_success() -> None:
    remote = r"""
echo '--- o262c code ---'
grep -c _youdo_post_goto_list_view_wait /opt/rawlead/src/exchange_browser_fetch.py || true
grep -c _youdo_maybe_list_view_pass2 /opt/rawlead/src/exchange_browser_fetch.py || true
echo '--- list_view ---'
grep 'youdo:trace stage=list_view' /opt/rawlead/data/radar_site.log | tail -15 || true
echo '--- pass2 ---'
grep 'pass=2' /opt/rawlead/data/radar_site.log | tail -8 || true
echo '--- clicked=1 ---'
grep 'stage=list_view clicked=1' /opt/rawlead/data/radar_site.log | tail -5 || true
echo '--- browser big ---'
grep 'html_len=1' /opt/rawlead/data/radar_site.log | tail -6 || true
echo '--- fetch_end ---'
grep 'youdo:trace stage=fetch_end' /opt/rawlead/data/radar_site.log | tail -5 || true
echo '--- youdo ok ---'
grep 'youdo:trace stage=fetch_end' /opt/rawlead/data/radar_site.log | grep 'parsed=[1-9]' | tail -3 || true
echo '--- big html ---'
grep 'html_len=1[0-9][0-9][0-9][0-9][0-9]' /opt/rawlead/data/radar_site.log | tail -8 || true
echo '--- o261 ---'
grep -E 'dc_ban_limit|dc_auto_unban|dead_proxy_rotate' /opt/rawlead/data/radar_site.log | tail -8 || true
echo '--- dc_alive ---'
grep dc_alive /opt/rawlead/data/radar_site.log | tail -5 || true
"""
    _, out, err = ssh.run(remote.strip(), check=False)
    print((out or err or "").replace("\r\n", "\n"))
    remote = r"""
cd /opt/rawlead && f=$(ls -t data/debug_listings/youdo_antibot_*.html 2>/dev/null | head -1) && \
echo "file=$f" && wc -c "$f" && \
grep -c 'data-id' "$f" && \
grep -c 'Показать списком' "$f" || true && \
grep -c 'списком' "$f" || true
"""
    _, out, err = ssh.run(remote.strip(), check=False)
    print((out or err or "").replace("\r\n", "\n"))


def main() -> int:
    for label, cmd in (
        ("env", ENV_PATCH),
        ("clear", CLEAR_YOUDO.strip()),
        ("verify", VERIFY.strip()),
    ):
        _, out, err = ssh.run(cmd, check=False)
        text = (out or err or "").replace("\r\n", "\n")
        print(f"=== {label} ===")
        print(text)
    return 0


if __name__ == "__main__":
    import sys as _sys

    if len(_sys.argv) > 1 and _sys.argv[1] == "poll":
        poll_logs()
        raise SystemExit(0)
    if len(_sys.argv) > 1 and _sys.argv[1] == "grep":
        grep_success()
        raise SystemExit(0)
    if len(_sys.argv) > 1 and _sys.argv[1] == "inspect":
        inspect_antibot_html()
        raise SystemExit(0)
    raise SystemExit(main())
