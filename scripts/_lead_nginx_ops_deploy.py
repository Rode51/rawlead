#!/usr/bin/env python3
"""Upload nginx rawlead.ru.conf with /ops/ proxy."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CONF = Path(__file__).resolve().parents[1] / "data" / "vps-staging" / "rawlead.ru.conf"
REMOTE = "/etc/nginx/sites-available/rawlead.ru.conf"


def main() -> int:
    if not CONF.is_file():
        print("missing", CONF)
        return 1
    ssh.upload(CONF, "/tmp/rawlead.ru.conf.new")
    _, out, err = ssh.run(
        f"cp {REMOTE} {REMOTE}.bak-pre-stress && "
        "cp /tmp/rawlead.ru.conf.new " + REMOTE + " && "
        "nginx -t && systemctl reload nginx && echo NGINX_RELOAD_OK",
        check=False,
    )
    print(out or err)
    _, o2, _ = ssh.run(
        "grep -c 'location /ops/' /etc/nginx/sites-available/rawlead.ru.conf",
        check=False,
    )
    print("ops blocks:", (o2 or "").strip())
    _, o3, _ = ssh.run(
        "curl -s -o /dev/null -w 'https_ops:%{http_code}' 'https://rawlead.ru/ops/' -k",
        check=False,
    )
    print((o3 or "").strip())
    return 0 if "NGINX_RELOAD_OK" in (out or "") and "https_ops:200" in (o3 or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
