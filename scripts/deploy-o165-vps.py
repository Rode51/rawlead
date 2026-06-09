#!/usr/bin/env python3
"""O165: TG test group join (acc1/2/3) + PUBLIC_FEED_SOURCES + radar restart."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_TEST_LINK = "https://t.me/+Z7HcnIAdSw9kY2U6"
_UPLOADS = (
    "docs/ops/TG_JOIN_QUEUE_v2.csv",
    "docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt",
    "src/public_feed.py",
    "scripts/build_public_feed_sources.py",
)
_JOIN_POLL_SEC = 90 * 60
_JOIN_POLL_INTERVAL = 120


def _ensure_env_line(key: str, value: str) -> str:
    safe = value.replace("'", "'\\''")
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={safe}|' /opt/rawlead/.env.site || "
        f"echo '{key}={safe}' >> /opt/rawlead/.env.site"
    )


def _build_feed_sources() -> str:
    proc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "build_public_feed_sources.py")],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        check=True,
    )
    line = (proc.stdout or "").strip()
    if "=" not in line:
        raise RuntimeError("build_public_feed_sources: bad output")
    return line.split("=", 1)[1]


def _upload_all() -> None:
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print("up", rel)


def _join_status() -> str:
    _, out, _ = ssh.run(
        "grep 'test_bots' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv | "
        "awk -F, '{print $2,$3,$6}'",
        check=False,
    )
    return (out or "").strip()


def _pending_test_rows() -> int:
    _, out, _ = ssh.run(
        "grep -c ',pending,test_bots,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv || true",
        check=False,
    )
    try:
        return int((out or "0").strip().split()[-1])
    except ValueError:
        return 99


def _wait_joins() -> bool:
    deadline = time.monotonic() + _JOIN_POLL_SEC
    while time.monotonic() < deadline:
        pending = _pending_test_rows()
        status = _join_status()
        print(f"join poll pending={pending}\n{status}")
        if pending == 0:
            return True
        time.sleep(_JOIN_POLL_INTERVAL)
    return False


def _apply_feed_and_restart(feed: str) -> bool:
    env_cmd = " && ".join(
        [
            _ensure_env_line("PUBLIC_FEED_SOURCES", feed),
            _ensure_env_line("TG_JOIN_IN_TG_MAIN", "1"),
            "grep '^TG_JOIN_IN_TG_MAIN=' /opt/rawlead/.env.site",
            f"grep -F '{_TEST_LINK}' /opt/rawlead/docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt | head -1",
            "grep 'test_bots' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv | tail -3",
        ]
    )
    _, env_out, _ = ssh.run(env_cmd, check=False)
    print(env_out or "")

    tg_peer = ""
    for part in feed.split(","):
        if part.startswith("tg:") and "5177575757" in part:
            tg_peer = part
            break
    if not tg_peer:
        for part in feed.split(","):
            if part.startswith("tg:-1005177575757"):
                tg_peer = part
                break
    print(f"test tg peer in feed: {tg_peer or 'WAIT (join not done yet)'}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 5 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c test_bots /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv && "
        "wc -l /opt/rawlead/data/telethon_chat_ids_acc1.txt "
        "/opt/rawlead/data/telethon_chat_ids_acc2.txt "
        "/opt/rawlead/data/telethon_chat_ids_acc3.txt 2>/dev/null; "
        "tail -6 /opt/rawlead/data/tg_join.log 2>/dev/null || true; "
        "echo o165_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    return "o165_deploy_ok" in text and "active" in text


def main() -> int:
    print("=== O165 deploy: TG test group ===")
    _upload_all()

    feed_pre = _build_feed_sources()
    print(f"feed (pre-join): {len(feed_pre.split(','))} sources")

    if not _apply_feed_and_restart(feed_pre):
        print("DEPLOY CHECK (phase 1)")
        return 1
    print("PHASE 1 OK — radar up, join pending")

    if not _wait_joins():
        print("WARN: join timeout — owner may wait for tg_main join ticks")
        return 2

    feed_post = _build_feed_sources()
    tg_n = sum(1 for s in feed_post.split(",") if s.startswith("tg:"))
    print(f"feed (post-join): tg={tg_n} total={len(feed_post.split(','))}")

    if "tg:-1005177575757" not in feed_post and "5177575757" not in feed_post:
        print("WARN: test chat_id not in PUBLIC_FEED_SOURCES yet — check CSV chat_id")
    if not _apply_feed_and_restart(feed_post):
        print("DEPLOY CHECK (phase 2)")
        return 1

    print("O165 DEPLOY OK — owner: post vacancy in test group")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
