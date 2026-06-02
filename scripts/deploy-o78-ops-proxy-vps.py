#!/usr/bin/env python3
"""O78: ops dashboard via WP REST (avoid /admin/ URL blockers)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/owner_admin.py",)


def main() -> int:
    print("=== O78 ops proxy deploy ===")
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead /opt/rawlead/src/owner_admin.py")

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

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c '/ops/dashboard' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep 'ops/dashboard' /opt/rawlead/src/owner_admin.py | head -1 && "
        "curl -sf -o /dev/null -w 'wp_ops=%{http_code}\\n' "
        "https://rawlead.ru/wp-json/rawlead/v1/ops/dashboard -k",
        check=False,
    )
    print(out or "")
    ok = "active" in (out or "") and "wp_ops=401" in (out or "")
    print("O78 OPS PROXY OK" if ok else "O78 OPS PROXY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
