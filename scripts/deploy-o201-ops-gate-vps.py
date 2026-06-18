#!/usr/bin/env python3
"""O201: ops password-only gate + header «Админка» — API + theme deploy."""
from __future__ import annotations

import base64
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=False)

_API_FILES = ("src/owner_admin.py", "src/api_server.py")
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
_ENV_SITE = "/opt/rawlead/.env.site"


def _upload_api() -> list[str]:
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def _sync_ops_password_vps() -> bool:
    pwd = (os.environ.get("OPS_PASSWORD") or os.environ.get("RAWLEAD_OPS_KEY") or "").strip()
    if not pwd:
        print("WARN: OPS_PASSWORD / RAWLEAD_OPS_KEY not in local env — skip password sync")
        return False
    b64 = base64.b64encode(pwd.encode("utf-8")).decode("ascii")
    remote_py = f"""python3 <<'PYEOF'
import base64, re
from pathlib import Path
p = Path("{_ENV_SITE}")
text = p.read_text(encoding="utf-8") if p.exists() else ""
key = base64.b64decode("{b64}").decode("utf-8")
line = "RAWLEAD_OPS_KEY=" + key
if re.search(r"^RAWLEAD_OPS_KEY=", text, re.M):
    text = re.sub(r"^RAWLEAD_OPS_KEY=.*$", line, text, flags=re.M)
else:
    text = text.rstrip() + "\\n" + line + "\\n"
p.write_text(text, encoding="utf-8")
print("ops_key_synced_site")
PYEOF"""
    _, out, err = ssh.run(remote_py, check=False)
    text = (out or "") + (err or "")
    ok = "ops_key_synced_site" in text
    print("ops password sync (.env.site):", "OK" if ok else "CHECK")
    return ok


def _deploy_theme() -> bool:
    if not _THEME.is_dir():
        print("missing theme:", _THEME)
        return False
    n = ssh.sync_project(
        local_root=_THEME,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"theme uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    print("theme version:", (ver or "").strip())
    return "1.18.77" in (ver or "")


def main() -> int:
    print("=== O201 ops gate deploy ===")
    _sync_ops_password_vps()
    api_remotes = _upload_api()
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out_api, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "grep -c ops_setup_html /opt/rawlead/src/owner_admin.py && "
        "grep -c _ops_gate_configured /opt/rawlead/src/api_server.py && "
        "grep '^RAWLEAD_OPS_KEY=' /opt/rawlead/.env.site | wc -l && "
        "curl -sf -o /tmp/ops_o201.html -w 'ops_local=%{http_code}\\n' http://127.0.0.1:8000/ops/ && "
        "grep -c 'type=\"password\"' /tmp/ops_o201.html && "
        "grep -c Telegram /tmp/ops_o201.html || true && "
        "grep -n 'location /ops' /etc/nginx/sites-enabled/rawlead.ru "
        "/etc/nginx/sites-available/rawlead.ru 2>/dev/null | head -2 && "
        "echo o201_api_ok",
        check=False,
    )
    print(out_api.strip())
    api_ok = "o201_api_ok" in (out_api or "") and "active" in (out_api or "")

    theme_ok = _deploy_theme()
    _, out_hdr, _ = ssh.run(
        "grep -c 'Админка' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/template-parts/rawlead/header.php",
        check=False,
    )
    hdr_ok = (out_hdr or "").strip() not in {"", "0"}

    _, out_pub, _ = ssh.run(
        "curl -sf -o /tmp/ops_pub.html -w 'ops_pub=%{http_code}\\n' https://rawlead.ru/ops/ && "
        "grep -c 'type=\"password\"' /tmp/ops_pub.html && "
        "(grep -c Telegram /tmp/ops_pub.html || true)",
        check=False,
    )
    print(out_pub.strip())
    pub_ok = "ops_pub=200" in (out_pub or "") and "\n1\n" in (out_pub or "") + "\n"

    ok = api_ok and theme_ok and hdr_ok and pub_ok
    print("O201 OPS GATE OK" if ok else "O201 OPS GATE — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
