#!/usr/bin/env python3
"""Append youdo,freelance_ru to PUBLIC_FEED_SOURCES on VPS if missing."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.deploy_vps_ssh import connect  # noqa: E402

ENV_PATH = "/opt/rawlead/.env"
MARKER = "PUBLIC_FEED_SOURCES="


def main() -> int:
    client = connect()
    try:
        sftp = client.open_sftp()
        with sftp.open(ENV_PATH, "r") as f:
            raw = f.read().decode("utf-8", errors="replace")
        lines = raw.splitlines(keepends=True)
        new_lines: list[str] = []
        changed = False
        for ln in lines:
            if ln.startswith(MARKER):
                value = ln[len(MARKER) :].strip()
                parts = [p.strip() for p in value.split(",") if p.strip()]
                if "youdo" not in parts:
                    parts.insert(min(2, len(parts)), "youdo")
                if "freelance_ru" not in parts:
                    idx = parts.index("youdo") + 1 if "youdo" in parts else min(2, len(parts))
                    parts.insert(idx, "freelance_ru")
                new_ln = MARKER + ",".join(parts) + ("\n" if ln.endswith("\n") else "")
                if new_ln != ln:
                    changed = True
                new_lines.append(new_ln)
            else:
                new_lines.append(ln)
        if not any(l.startswith(MARKER) for l in lines):
            raise SystemExit(f"Missing {MARKER} in {ENV_PATH}")
        if not changed:
            print("ALREADY_OK")
            return 0
        with sftp.open(ENV_PATH, "w") as f:
            f.write("".join(new_lines))
        sftp.close()
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
        for ln in new_lines:
            if ln.startswith(MARKER):
                print("UPDATED:", ln.strip()[:220])
                break
        print("SERVICES:", out)
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
