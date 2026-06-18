"""Check O272 on VPS prod theme."""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
for f in /opt/rawlead/wordpress/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js \
         /var/www/html/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js; do
  if [ -f "$f" ]; then
    echo FILE=$f
    grep -c 'rawlead-tags-imported' "$f" || true
  fi
done
curl -fsS -m 10 https://rawlead.ru/lenta/ 2>/dev/null | grep -oE 'ver=[0-9.]+' | head -3
curl -fsS -m 10 'https://rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js?ver=1.19.20' 2>/dev/null | grep -c 'rawlead-tags-imported' || echo js_fetch_fail
"""


def main() -> int:
    _, out, _ = ssh.run(REMOTE.strip(), check=False)
    print((out or "").encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
