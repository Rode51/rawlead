#!/usr/bin/env python3
"""O170: TG L1 filter deploy + delist tail on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/tg_spam_filter.py",
    "src/ai_analyze.py",
    "src/listing.py",
    "src/public_feed.py",
    "scripts/_tmp_o170_delist_tg_ads.py",
)

_DELIST_PY = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src \
  .venv/bin/python scripts/_tmp_o170_delist_tg_ads.py --apply --days=7
"""

_EXTRA_DELIST_PY = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python scripts/_tmp_o170_delist_tg_ads.py --apply --days=7 --extra-book-ads"
)


def main() -> int:
    print("=== O170 deploy: TG filter + delist ===")
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print("up", rel)

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c seller-voice /opt/rawlead/src/tg_spam_filter.py && "
        "grep -c _LITE_TG_APPEND /opt/rawlead/src/ai_analyze.py && "
        "echo o170_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o170_deploy_ok" not in text or "active" not in text:
        print("DEPLOY CHECK FAILED (phase 1)")
        return 1

    _, d1, _ = ssh.run(_DELIST_PY.strip(), check=False)
    print(d1 or "")

    _, d2, _ = ssh.run(_EXTRA_DELIST_PY.strip(), check=False)
    print(d2 or "")

    print("O170 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
