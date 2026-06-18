#!/usr/bin/env python3
"""O223: YouDo physical-service guard + short detail gate — radar+api."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/vacancy_filter.py",
    "src/lead_pipeline.py",
    "src/ai_analyze.py",
)

_DELIST_PY = r"""
import os
from dotenv import load_dotenv
load_dotenv("/opt/rawlead/.env.site", override=True)
load_dotenv("/opt/rawlead/.env", override=False)
os.environ.setdefault("RADAR_PROFILE", "site")

from config import apply_profile_argv, load_config
apply_profile_argv()
cfg = load_config()
from pg_storage import NeonLeadStorage

pg = NeonLeadStorage(cfg.database_url)
lead_id = 25128
with pg.connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, external_id, is_visible, delist_reason FROM leads WHERE id=%s",
            (lead_id,),
        )
        print("before=", cur.fetchone())
ok = pg.delist_lead(lead_id, reason="o223_non_digital")
print("delist_applied=", ok)
with pg.connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, external_id, is_visible, delist_reason FROM leads WHERE id=%s",
            (lead_id,),
        )
        print("after=", cur.fetchone())
"""


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O223 deploy: YouDo L1 guard ===")
    remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 6 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c is_physical_service_job /opt/rawlead/src/vacancy_filter.py && "
        "grep -c 'detail:short' /opt/rawlead/src/lead_pipeline.py && "
        "echo o223_deploy_ok",
        check=False,
    )
    print(out.strip())
    ok = "o223_deploy_ok" in (out or "") and (out or "").count("active") >= 2
    if not ok:
        print("DEPLOY CHECK — verify manually")
        return 1

    print("=== O223 delist lead #25128 ===")
    _, delist_out, _ = ssh.run(
        "cd /opt/rawlead && sudo -u rawlead env RADAR_PROFILE=site "
        "PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'\n"
        + _DELIST_PY
        + "\nPY",
        check=False,
    )
    print((delist_out or "").strip())
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
