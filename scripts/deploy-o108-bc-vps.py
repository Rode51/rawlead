#!/usr/bin/env python3
"""O108-BC: TZ attachments v1.1 + theme 1.18.5 + PUBLIC_FEED_SOURCES with TG."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_EXTRA_SRC = (
    "tz_attachments.py",
    "l3_human_style.py",
    "api_server.py",
    "ai_analyze.py",
    "fl_parser.py",
    "kwork_parser.py",
    "lead_pipeline.py",
    "pg_storage.py",
    "ai_reasons.py",
)

_SECONDARY = ("youdo", "freelance_ru", "freelancejob", "pchyol")


def _ensure_env_line(key: str, value: str) -> str:
    safe = value.replace("'", "'\\''")
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={safe}|' /opt/rawlead/.env.site || "
        f"echo '{key}={safe}' >> /opt/rawlead/.env.site"
    )


def _build_feed_sources() -> str:
    proc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "build_public_feed_sources.py")],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        check=True,
    )
    line = (proc.stdout or "").strip()
    if "=" not in line:
        raise RuntimeError("build_public_feed_sources: bad output")
    parts = line.split("=", 1)[1].split(",")
    seen = set(parts)
    insert_at = 2
    for src in _SECONDARY:
        if src not in seen:
            parts.insert(insert_at, src)
            insert_at += 1
            seen.add(src)
    return ",".join(parts)


def main() -> int:
    print("=== O108-BC deploy (1.18.5 + TZ attachments + TG feed) ===")
    feed = _build_feed_sources()
    tg_n = sum(1 for s in feed.split(",") if s.startswith("tg:"))
    print(f"PUBLIC_FEED_SOURCES: web+secondary+tg={tg_n} ({len(feed.split(','))} total)")

    uploaded = ssh.deploy_ingest_coupled_src()
    print(f"ingest coupled: {len(uploaded)} files")
    remote_src = "/opt/rawlead/src"
    for name in _EXTRA_SRC:
        local = _ROOT / "src" / name
        remote = f"{remote_src}/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    ssh.run(
        "/opt/rawlead/.venv/bin/pip install -q python-docx pypdf 2>/dev/null || "
        "pip install -q python-docx pypdf",
        check=False,
    )

    n = ssh.sync_project(
        local_root=_THEME,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"WP uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )

    env_cmds = " && ".join(
        [
            _ensure_env_line("PUBLIC_FEED_SOURCES", feed),
            _ensure_env_line("TZ_ATTACHMENTS_ENABLED", "1"),
            _ensure_env_line("TZ_ATTACHMENT_MAX_TEXT_MB", "8"),
            _ensure_env_line("TZ_ATTACHMENT_MAX_ARCHIVE_MB", "2"),
            "grep '^PUBLIC_FEED_SOURCES=' /opt/rawlead/.env.site | head -c 120",
            "grep '^TZ_ATTACHMENT' /opt/rawlead/.env.site",
        ]
    )
    _, env_out, _ = ssh.run(env_cmd := env_cmds, check=False)
    print(env_out or "")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "test -f /opt/rawlead/src/tz_attachments.py && echo tz_attachments_ok && "
        "/opt/rawlead/.venv/bin/python -c \"import docx, pypdf; print('deps_ok')\" 2>/dev/null || "
        "python3 -c \"import docx, pypdf; print('deps_ok')\" && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c rl-feed-card__tz-warn "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -o '1\\.18\\.5' | head -1",
        check=False,
    )
    print(out or "")
    text = (out or "") + (env_out or "")
    ok = (
        "active" in text
        and "tz_attachments_ok" in text
        and "1.18.5" in text
        and "tg:-" in (env_out or feed)
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
