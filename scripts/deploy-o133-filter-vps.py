#!/usr/bin/env python3
"""O133-FILTER-KW deploy: FL + Kwork legal attachment filter on radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = ("src/tz_attachments.py",)


def main() -> int:
    print("=== O133-FILTER deploy: tz_attachments legal filters ===")
    remotes: list[str] = []
    for rel in _RADAR_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-radar && "
        "grep -c _FL_LEGAL_PATH_RE /opt/rawlead/src/tz_attachments.py && "
        "grep -c _KWORK_LEGAL_PATH_RE /opt/rawlead/src/tz_attachments.py && "
        "echo o133_filter_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    if "o133_filter_ok" not in text or "active" not in text:
        print("DEPLOY CHECK — verify grep _FL_LEGAL_PATH_RE / _KWORK_LEGAL_PATH_RE")
        return 1
    print("RADAR DEPLOY OK — new FL/Kwork ingest skips site legal PDFs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
