#!/usr/bin/env python3
"""Lead 27xxx + post-restart push activity on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    out_path = _ROOT / "scripts" / "_mechanic_push_vps3.out"
    lines: list[str] = []
    cmds = [
        ("leads_27k", (
            "cd /opt/rawlead && .venv/bin/python <<'PY'\n"
            "import os\nfrom dotenv import load_dotenv\nimport psycopg\n"
            "load_dotenv('.env')\nload_dotenv('.env.site', override=True)\n"
            "with psycopg.connect(os.environ['DATABASE_URL']) as c:\n"
            "    cur = c.cursor()\n"
            "    cur.execute('SELECT id, source, external_id, is_visible, left(title,50), created_at FROM leads WHERE id >= 27000 ORDER BY id DESC LIMIT 12')\n"
            "    [print(r) for r in cur.fetchall()]\n"
            "PY"
        )),
        ("post_restart_l1", r"grep '2026-06-15 1[5-9]:\|2026-06-15 2[0-3]:' /opt/rawlead/data/radar_site.log | grep 'pipeline:L1.*visible=1' | tail -20"),
        ("post_restart_push", r"grep '2026-06-15 1[5-9]:\|2026-06-15 2[0-3]:' /opt/rawlead/data/radar_site.log | grep 'push:match' | tail -30 || echo NO_POST_RESTART_PUSH"),
        ("restart_time", "systemctl show rawlead-radar -p ActiveEnterTimestamp --value"),
    ]
    for name, cmd in cmds:
        lines.append(f"=== {name} ===")
        _, out, _ = ssh.run(cmd, check=False)
        lines.append((out or "").strip())
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"written {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
