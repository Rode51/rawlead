#!/usr/bin/env python3
"""O190: TG join→listen chain + allowlist expand — deploy to VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/public_feed.py", "/opt/rawlead/src/public_feed.py"),
    ("src/tg_monitor.py", "/opt/rawlead/src/tg_monitor.py"),
    ("src/tg_join_runner.py", "/opt/rawlead/src/tg_join_runner.py"),
    ("src/radar_status.py", "/opt/rawlead/src/radar_status.py"),
    ("src/ops_funnel.py", "/opt/rawlead/src/ops_funnel.py"),
    ("src/owner_admin.py", "/opt/rawlead/src/owner_admin.py"),
    ("src/api_server.py", "/opt/rawlead/src/api_server.py"),
    ("src/tg_spam_corpus.py", "/opt/rawlead/src/tg_spam_corpus.py"),
    ("docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt", "/opt/rawlead/docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt"),
    ("scripts/tg_expand_allowlist.py", "/opt/rawlead/scripts/tg_expand_allowlist.py"),
    ("scripts/tg_sync_chat_ids.py", "/opt/rawlead/scripts/tg_sync_chat_ids.py"),
)


def main() -> int:
    print("=== O190 deploy: TG join→listen chain + allowlist ===")
    remotes: list[str] = []
    for rel, remote in _UPLOADS:
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    backfill = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python scripts/tg_expand_allowlist.py && "
        ".venv/bin/python scripts/tg_sync_chat_ids.py --account all"
    )
    verify = (
        "grep -c 'тг:цепочка' /opt/rawlead/src/tg_monitor.py && "
        "grep -c 'record_tg_listen_stats' /opt/rawlead/src/radar_status.py && "
        "grep -c 'expand_allowlist_from_done_queues' /opt/rawlead/src/public_feed.py && "
        "grep -c 'admin_mark_tg_spam' /opt/rawlead/src/api_server.py && "
        "test -f /opt/rawlead/src/tg_spam_corpus.py"
    )
    _, out, _ = ssh.run(
        f"{verify} && {backfill} && "
        "systemctl restart rawlead-api 2>/dev/null || true; "
        "systemctl stop rawlead-radar 2>/dev/null || true; sleep 3; "
        "systemctl reset-failed rawlead-radar 2>/dev/null || true; "
        "systemctl start rawlead-radar && sleep 6 && systemctl is-active rawlead-radar && "
        "echo o190_tg_join_listen_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    if "o190_tg_join_listen_deploy_ok" not in text or "active" not in text:
        print("O190 TG DEPLOY CHECK FAILED")
        return 1
    print("O190 TG DEPLOY OK — grep 'тг:цепочка\\|тг:сводка' /opt/rawlead/logs/radar_site.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
