#!/usr/bin/env python3
"""L1-TILDA-TAGS follow-up: YOUDO_DETAIL_FETCH=1 + re-L1 lead 18311 on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

_ENV_SITE = "/opt/rawlead/.env.site"
PY_ENV = "PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site"
_UPLOADS = (("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),)
PY = f"cd /opt/rawlead && sudo -u rawlead env {PY_ENV} /opt/rawlead/.venv/bin/python"


def _patch_env_key(key: str, value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{key}=' {_ENV_SITE} 2>/dev/null && "
        f"sed -i '/^{key}=/d' {_ENV_SITE}; "
        f"echo '{key}={safe}' >> {_ENV_SITE} && "
        f"grep -c '^{key}=' {_ENV_SITE}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def main() -> int:
    for local, remote in _UPLOADS:
        ssh.upload(_ROOT / local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"uploaded {local}")

    if not _patch_env_key("YOUDO_DETAIL_FETCH", "1"):
        print("FAIL — YOUDO_DETAIL_FETCH not written")
        return 1
    print("env: YOUDO_DETAIL_FETCH=1 ok")

    _, env_line, _ = ssh.run(
        f"grep -E 'YOUDO_DETAIL_FETCH=|YOUDO_BROWSER_ONLY=' {_ENV_SITE} | tail -5",
        check=False,
    )
    print((env_line or "").strip())

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-radar rawlead-api",
        check=False,
    )
    print(rst or "")
    if "active" not in (rst or ""):
        print("FAIL — services not active")
        return 1

    print("\n=== re-L1 lead 18311 ===")
    _, replay_out, replay_err = ssh.run(
        f"{PY} /opt/rawlead/scripts/replay_neon_lite_site.py "
        "--profile site --lead-ids 18311 --limit 1",
        check=False,
    )
    combined = (replay_out or "") + (replay_err or "")
    sys.stdout.buffer.write(combined.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")

    print("\n=== verify lead 18311 tags ===")
    verify_py = (
        f"{PY} -c \"import sys,json;sys.path.insert(0,'/opt/rawlead/src');"
        "from config import load_radar_env,load_config;"
        "from pg_storage import pg_storage_from_config;"
        "load_radar_env();pg=pg_storage_from_config(load_config());"
        "tags=pg.fetch_lead_tags_by_ids([18311]);"
        "rows=pg.fetch_leads_by_ids([18311]);r=rows[0] if rows else None;"
        "body=(r.body if r else '');"
        "print(json.dumps({"
        "'lead_id':(r.lead_id if r else None),"
        "'external_id':(r.external_id if r else None),"
        "'lead_tags':tags.get(18311),"
        "'body_len':len(body),"
        "'has_tilda':('tilda' in body.casefold() or 'тильда' in body.casefold())"
        "}, ensure_ascii=False))\""
    )
    _, verify_out, _ = ssh.run(verify_py, check=False)
    sys.stdout.buffer.write(((verify_out or "").strip() + "\n").encode("utf-8", errors="replace"))

    import json

    verify_line = (verify_out or "").strip().splitlines()[-1] if verify_out else "{}"
    try:
        vdata = json.loads(verify_line)
    except json.JSONDecodeError:
        vdata = {}
    db_tags = vdata.get("lead_tags") or []
    ok_tags = "tilda_dev" in db_tags and "wordpress_dev" not in db_tags
    if ok_tags:
        print("\nOK — lead 18311 has tilda_dev, no wordpress_dev")
        return 0

    print("\nWARN — tags not fixed yet; trying YOUDO_BROWSER_ONLY=1 if HTTP blocked")
    _patch_env_key("YOUDO_BROWSER_ONLY", "1")
    ssh.run("systemctl restart rawlead-radar rawlead-api && sleep 4", check=False)
    _, replay2, _ = ssh.run(
        f"{PY} /opt/rawlead/scripts/replay_neon_lite_site.py "
        "--profile site --lead-ids 18311 --limit 1",
        check=False,
    )
    sys.stdout.buffer.write(((replay2 or "").strip() + "\n").encode("utf-8", errors="replace"))
    _, verify2, _ = ssh.run(verify_py, check=False)
    print((verify2 or "").strip())
    verify_line2 = (verify2 or "").strip().splitlines()[-1] if verify2 else "{}"
    try:
        vdata2 = json.loads(verify_line2)
    except json.JSONDecodeError:
        vdata2 = {}
    db_tags2 = vdata2.get("lead_tags") or []
    ok2 = "tilda_dev" in db_tags2 and "wordpress_dev" not in db_tags2
    if ok2:
        print("\nOK — lead 18311 fixed with browser-only path")
        return 0
    print("\nFAIL — lead 18311 still missing tilda_dev")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
