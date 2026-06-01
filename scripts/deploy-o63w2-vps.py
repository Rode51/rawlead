#!/usr/bin/env python3
"""O63-w2: FreelanceJob + Пчёл parsers · VPS PUBLIC_FEED_SOURCES."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/freelancejob_parser.py",
    "src/pchyol_parser.py",
    "src/listing.py",
    "src/listing_dedup.py",
    "src/main.py",
    "src/exchange_proxy.py",
    "src/radar_cycle_log.py",
    "src/public_feed.py",
)

_FEED_SOURCES = "fl,kwork,youdo,freelance_ru,freelancejob,pchyol"


def _ensure_env_line(key: str, value: str) -> str:
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's/^{key}=.*/{key}={value}/' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O63-w2 deploy ===")
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
            "systemctl restart rawlead-radar",
            "sleep 3",
            "systemctl is-active rawlead-radar",
            "test -f /opt/rawlead/src/freelancejob_parser.py && echo freelancejob_parser=OK",
            "test -f /opt/rawlead/src/pchyol_parser.py && echo pchyol_parser=OK",
            "grep -c freelancejob "
            "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
        ]
    )
    ssh.run(env_cmd)
    print("=== done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
