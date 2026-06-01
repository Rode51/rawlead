#!/usr/bin/env python3
"""O81-w1c + match_push order URL + pchyol new-only hotfix."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/match_push.py",
    "src/pchyol_parser.py",
    "src/storage.py",
    "src/main.py",
)

_BOOTSTRAP_FLOOR = r"""
cd /opt/rawlead && PYTHONPATH=src python3 - <<'PY'
import os
from pathlib import Path
from config import load_radar_env, Config
from storage import ProjectStorage
from pchyol_parser import fetch_listing_projects, pchyol_ingest_floor

load_radar_env()
cfg = Config()
storage = ProjectStorage(Path(cfg.sqlite_path))
floor = pchyol_ingest_floor(storage)
if floor <= 0:
    batch = fetch_listing_projects(cfg)
    if batch:
        floor = max(p.project_id for p in batch)
if floor > 0:
    print(floor)
PY
"""


def _ensure_env_line(key: str, value: str) -> str:
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's/^{key}=.*/{key}={value}/' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O81-w1c hotfix deploy ===")
    remotes: list[str] = []
    for rel in _SRC_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print("SKIP missing", rel)
            continue
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    if remotes:
        ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    theme = _ROOT / "wordpress" / "rawlead-kadence-child"
    n = ssh.sync_project(
        local_root=theme,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"theme uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )

    _, floor_out, _ = ssh.run(_BOOTSTRAP_FLOOR.strip(), check=False)
    floor = (floor_out or "").strip().splitlines()[-1] if floor_out else ""
    env_steps = []
    if floor.isdigit() and int(floor) > 0:
        env_steps.append(_ensure_env_line("PCHYOL_MIN_PROJECT_ID", floor))
        print("PCHYOL_MIN_PROJECT_ID=", floor)
    env_cmd = " && ".join(
        env_steps
        + [
            "grep '^PCHYOL_MIN_PROJECT_ID=' /opt/rawlead/.env.site || true",
            "systemctl restart rawlead-radar rawlead-api",
            "sleep 3",
            "systemctl is-active rawlead-radar",
            "systemctl is-active rawlead-api",
            "grep \"RAWLEAD_CHILD_VERSION\" "
            "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        ]
    )
    ssh.run(env_cmd)
    print("=== done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
