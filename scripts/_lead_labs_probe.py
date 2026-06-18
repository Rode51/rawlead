"""Diagnose labs.rawlead.ru deploy."""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
echo ===FILES===
ls -la /var/www/labs.rawlead.ru/ | head -8
echo ===NGINX===
nginx -t 2>&1
ls -la /etc/nginx/sites-enabled/labs.rawlead.ru.conf 2>/dev/null || echo no_symlink
echo ===LOCAL===
curl -fsSI -H 'Host: labs.rawlead.ru' http://127.0.0.1/ 2>&1 | head -8
curl -fsS -H 'Host: labs.rawlead.ru' http://127.0.0.1/ 2>/dev/null | head -c 300
echo
echo ===EXT_HTTP===
curl -fsSI -m 10 http://labs.rawlead.ru/ 2>&1 | head -8
echo ===EXT_HTTPS===
curl -fsSI -m 10 https://labs.rawlead.ru/ 2>&1 | head -8
echo ===DNS===
getent hosts labs.rawlead.ru 2>/dev/null || host labs.rawlead.ru 2>/dev/null | head -3
echo ===CERT===
test -f /etc/letsencrypt/live/labs.rawlead.ru/fullchain.pem && echo HAS_CERT || echo NO_CERT
"""


def main() -> int:
    _, out, _ = ssh.run(REMOTE.strip(), check=False)
    print((out or "").encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
