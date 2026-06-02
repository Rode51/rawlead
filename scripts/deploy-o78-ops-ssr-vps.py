#!/usr/bin/env python3
"""O78: SSR ops dashboard + rl_access cookie."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/owner_admin.py", "src/api_server.py")


def main() -> int:
    print("=== O78 ops SSR deploy ===")
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(f"/opt/rawlead/{f}" for f in _FILES))

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
        "grep -c login-box /opt/rawlead/src/owner_admin.py && "
        "curl -sf 'https://rawlead.ru/ops/?key=ZDZFL74ChSIFpm732mzbqhLEj3_U0xEo' -k | grep -c login-box && "
        "curl -sf 'https://rawlead.ru/ops/?key=ZDZFL74ChSIFpm732mzbqhLEj3_U0xEo' -k | grep -c 'Сегодня на сайте' || true",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "active" in text and text.count("1") >= 1
    print("O78 OPS SSR OK" if ok else "O78 OPS SSR — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
