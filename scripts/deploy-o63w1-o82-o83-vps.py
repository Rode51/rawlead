#!/usr/bin/env python3
"""O63-w1 parsers + O82-w1/O83 theme + api · VPS env PUBLIC_FEED_SOURCES."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/youdo_parser.py",
    "src/freelance_ru_parser.py",
    "src/listing.py",
    "src/listing_dedup.py",
    "src/main.py",
    "src/exchange_proxy.py",
    "src/fl_parser.py",
    "src/kwork_parser.py",
    "src/public_feed.py",
    "src/api_server.py",
)

_FEED_SOURCES = "fl,kwork,youdo,freelance_ru"


def _upload_src() -> list[str]:
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
    return remotes


def _ensure_env_line(key: str, value: str) -> str:
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's/^{key}=.*/{key}={value}/' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O63-w1 + O82/O83 deploy ===")
    remotes = _upload_src()
    if remotes:
        ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    theme = _ROOT / "wordpress" / "rawlead-kadence-child"
    if theme.is_dir():
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

    env_cmd = " && ".join(
        [
            _ensure_env_line("PUBLIC_FEED_SOURCES", _FEED_SOURCES),
            "grep '^PUBLIC_FEED_SOURCES=' /opt/rawlead/.env.site",
            "systemctl restart rawlead-api rawlead-radar",
            "sleep 3",
            "systemctl is-active rawlead-api rawlead-radar",
            "test -f /opt/rawlead/src/youdo_parser.py && echo youdo_parser=OK",
            "grep -c rl-match-breakdown "
            "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
            "grep -c _strip_tools_for_anon /opt/rawlead/src/api_server.py",
            "curl -sf http://127.0.0.1:8000/health | head -c 300; echo",
        ]
    )
    _, out, _ = ssh.run(env_cmd, check=False)
    print(out or "")
    ok = (
        "active" in (out or "")
        and "youdo_parser=OK" in (out or "")
        and _FEED_SOURCES in (out or "")
    )
    if ok:
        print("O63-w1 + O82/O83 DEPLOY OK")
        return 0
    print("DEPLOY — verify services manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
