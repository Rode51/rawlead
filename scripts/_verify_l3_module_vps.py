#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMD = (
    "systemctl is-active rawlead-api && "
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python -c 'import l3_human_style; print(\"import_ok\", l3_human_style.__file__)'"
)


def main() -> int:
    _, out, err = ssh.run(CMD, check=False)
    print(out or err)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
