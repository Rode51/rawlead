#!/usr/bin/env python3
"""O168: Neon pooler on VPS + deploy ai_analyze (g1c false-truncation)."""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402
from check_neon_pooler import db_connection_mode, to_pooler_url  # noqa: E402

_UPLOADS = (
    "src/ai_analyze.py",
    "src/api_server.py",
    "src/pg_storage.py",
)
_ENV_FILES = ("/opt/rawlead/.env.site", "/opt/rawlead/.env")


def _patch_pooler_on_vps() -> bool:
    for env_path in _ENV_FILES:
        _, raw, _ = ssh.run(
            f"grep '^DATABASE_URL=' {env_path} 2>/dev/null | head -1 | cut -d= -f2-",
            check=False,
        )
        current = (raw or "").strip()
        if not current:
            print(f"skip {env_path}: DATABASE_URL unset")
            continue
        mode = db_connection_mode(current)
        if mode == "pooler":
            print(f"OK {env_path}: already pooler")
            continue
        pooled = to_pooler_url(current)
        if db_connection_mode(pooled) != "pooler":
            print(f"FAIL {env_path}: cannot derive pooler URL", file=sys.stderr)
            return False
        safe = shlex.quote(pooled)
        ssh.run(
            f"grep -q '^DATABASE_URL=' {env_path} && "
            f"sed -i 's|^DATABASE_URL=.*|DATABASE_URL={safe}|' {env_path} || "
            f"echo 'DATABASE_URL={safe}' >> {env_path}",
            check=True,
        )
        print(f"patched {env_path}: direct → pooler")
    return True


def main() -> int:
    print("=== O168 deploy: pooler + ai_analyze (g1c) ===")
    if not _patch_pooler_on_vps():
        return 1

    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    ssh.upload(_ROOT / "requirements.txt", "/opt/rawlead/requirements.txt")
    ssh.run(
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/pip install -q psycopg-pool 2>/dev/null || "
        "sudo -u rawlead .venv/bin/pip install -q -r requirements.txt",
        check=False,
    )

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c false_truncation_claim /opt/rawlead/src/ai_analyze.py && "
        "grep -c _shared_snippet_for_l2 /opt/rawlead/src/ai_analyze.py && "
        "grep -c _feed_today_count_cached /opt/rawlead/src/api_server.py && "
        "grep -c _skills_catalog_popular_cached /opt/rawlead/src/api_server.py && "
        "grep -c app_pool /opt/rawlead/src/api_server.py && "
        "/opt/rawlead/.venv/bin/python -c \"import psycopg_pool\" && "
        "journalctl -u rawlead-api -n 40 --no-pager | grep -E 'db: (pooler|direct)' | tail -1 && "
        "echo o168_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o168_deploy_ok" not in text or "active" not in text:
        print("O168 DEPLOY CHECK FAILED")
        return 1
    if "db: pooler" not in text:
        print("WARN: API log does not show db: pooler — verify DATABASE_URL on VPS")
    print("O168 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
