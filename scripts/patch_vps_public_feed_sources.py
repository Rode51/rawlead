#!/usr/bin/env python3
"""Rebuild PUBLIC_FEED_SOURCES on VPS (O63 secondary + tg). Prefer deploy-o169-restore-secondary-vps.py."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.deploy_vps_ssh import connect  # noqa: E402

_SECONDARY = ("youdo", "freelance_ru", "freelancejob", "pchyol")


def _build_feed() -> str:
    from scripts.build_public_feed_sources import feed_sources_csv

    return feed_sources_csv()


def main() -> int:
    feed = _build_feed()
    missing = [s for s in _SECONDARY if s not in feed.split(",")]
    if missing:
        raise SystemExit(f"build missing secondary: {missing}")
    client = connect()
    try:
        for env_path in ("/opt/rawlead/.env.site", "/opt/rawlead/.env"):
            sftp = client.open_sftp()
            with sftp.open(env_path, "r") as f:
                raw = f.read().decode("utf-8", errors="replace")
            marker = "PUBLIC_FEED_SOURCES="
            lines = raw.splitlines(keepends=True)
            new_lines: list[str] = []
            found = False
            for ln in lines:
                if ln.startswith(marker):
                    found = True
                    new_ln = marker + feed + ("\n" if ln.endswith("\n") else "")
                    new_lines.append(new_ln)
                else:
                    new_lines.append(ln)
            if not found:
                new_lines.append(marker + feed + "\n")
            with sftp.open(env_path, "w") as f:
                f.write("".join(new_lines))
            sftp.close()
            print("UPDATED", env_path, "len", len(feed))
        stdin, stdout, stderr = client.exec_command(
            "systemctl restart rawlead-radar rawlead-api && sleep 2 && "
            "systemctl is-active rawlead-radar rawlead-api",
            get_pty=True,
        )
        del stdin
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        code = stdout.channel.recv_exit_status()
        if code != 0:
            raise RuntimeError(f"restart failed {code}: {out}\n{err}")
        print("SERVICES:", out)
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
