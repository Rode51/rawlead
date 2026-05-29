#!/usr/bin/env python3
"""Apply /ops/ nginx proxy on VPS (O45)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

SNIPPET = """
    location /ops/ {
        proxy_pass http://127.0.0.1:8000/ops/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /v1/admin/ {
        proxy_pass http://127.0.0.1:8000/v1/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
"""

PATCH = r"""
set -e
CONF=""
for f in /etc/nginx/sites-enabled/rawlead.ru /etc/nginx/sites-available/rawlead.ru; do
  [ -f "$f" ] && CONF="$f" && break
done
[ -n "$CONF" ] || { echo "no nginx conf"; exit 1; }
grep -q 'location /ops/' "$CONF" && { echo "already has /ops/"; exit 0; }
cp "$CONF" "${CONF}.bak-pre-stress"
python3 << 'PY'
from pathlib import Path
import os
conf = os.environ["CONF"]
text = Path(conf).read_text(encoding="utf-8")
snippet = """ + repr(SNIPPET.strip()) + r"""
marker = "    location / {"
if marker not in text:
    raise SystemExit("marker not found")
text = text.replace(marker, snippet + "\n\n" + marker, 1)
Path(conf).write_text(text, encoding="utf-8")
print("patched", conf)
PY
nginx -t && systemctl reload nginx && echo NGINX_OK
"""


def main() -> int:
    _, out, err = ssh.run(
        "CONF=$(ls /etc/nginx/sites-enabled/rawlead.ru /etc/nginx/sites-available/rawlead.ru 2>/dev/null | head -1); "
        "export CONF; "
        + PATCH.replace("\n", " "),
        check=False,
    )
    sys.stdout.buffer.write((out or err or "").encode("utf-8", errors="replace"))
    _, o2, _ = ssh.run(
        "grep -n 'location /ops' /etc/nginx/sites-enabled/rawlead.ru "
        "/etc/nginx/sites-available/rawlead.ru 2>/dev/null | head -3",
        check=False,
    )
    print("--- after ---")
    print((o2 or "").strip())
    return 0 if o2 and "/ops" in o2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
