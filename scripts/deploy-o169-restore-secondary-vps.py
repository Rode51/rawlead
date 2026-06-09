#!/usr/bin/env python3
"""O169: restore O63 secondary in PUBLIC_FEED_SOURCES on VPS (.env + .env.site)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "docs/ops/PUBLIC_FEED_WEB_SOURCES.txt",
    "scripts/build_public_feed_sources.py",
)
_SECONDARY = ("youdo", "freelance_ru", "freelancejob", "pchyol")


def _ensure_env_line(key: str, value: str) -> str:
    safe = value.replace("'", "'\\''")
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={safe}|' /opt/rawlead/.env.site || "
        f"echo '{key}={safe}' >> /opt/rawlead/.env.site"
    )


def _ensure_env_line_shared(key: str, value: str) -> str:
    safe = value.replace("'", "'\\''")
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env && "
        f"sed -i 's|^{key}=.*|{key}={safe}|' /opt/rawlead/.env || "
        f"echo '{key}={safe}' >> /opt/rawlead/.env"
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


def main() -> int:
    print("=== O169: restore secondary PUBLIC_FEED_SOURCES ===")
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print("up", rel)

    feed = _build_feed_sources()
    web_n = sum(1 for s in feed.split(",") if not s.startswith("tg:"))
    tg_n = sum(1 for s in feed.split(",") if s.startswith("tg:"))
    print(f"feed: web={web_n} tg={tg_n} total={len(feed.split(','))}")

    missing = [s for s in _SECONDARY if s not in feed.split(",")]
    if missing:
        print("FAIL: secondary missing in build:", ",".join(missing))
        return 1

    env_cmd = " && ".join(
        [
            _ensure_env_line("PUBLIC_FEED_SOURCES", feed),
            _ensure_env_line_shared("PUBLIC_FEED_SOURCES", feed),
            "grep '^PUBLIC_FEED_SOURCES=' /opt/rawlead/.env.site | head -c 200",
            "systemctl restart rawlead-api rawlead-radar",
            "sleep 4",
            "systemctl is-active rawlead-api rawlead-radar",
            "echo o169_restore_ok",
        ]
    )
    _, out, _ = ssh.run(env_cmd, check=False)
    text = out or ""
    print(text)
    if "o169_restore_ok" not in text or "active" not in text:
        print("DEPLOY CHECK FAILED")
        return 1

    for sid in _SECONDARY:
        if sid not in text:
            print(f"WARN: {sid} not visible in env grep (truncated?)")
    print("O169 OK — secondary restored; /ops/ should show YouDo + Freelance.ru + …")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
