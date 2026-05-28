#!/usr/bin/env python3
"""VPS: rawlead-landing plugin + marketing pages (how/pricing/faq/contact/home).

Checklist (l2-2):
  1. python scripts/wp-vps-skeleton-pages.py
  2. python scripts/deploy-wp-theme-vps.py   # theme v1.7.7+
  3. curl -sI http://rawlead.ru/how/ | head -1
  4. curl -sI http://rawlead.ru/pricing/ | head -1
  5. curl -sI http://rawlead.ru/ | head -1   # front page 200

Ops владельца (L1): BotFather → @rawlead_bot → /setdomain → rawlead.ru
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PLUGIN = _ROOT / "wordpress" / "rawlead-landing"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE_PLUGIN = "/var/www/rawlead.ru/wp-content/plugins/rawlead-landing"
REMOTE_WP = "/var/www/rawlead.ru"


def main() -> int:
    if not _PLUGIN.is_dir():
        print("missing plugin:", _PLUGIN)
        return 1

    print("=== VPS skeleton pages (L2) ===")
    n = ssh.sync_project(local_root=_PLUGIN, remote_root=REMOTE_PLUGIN)
    print(f"uploaded {n} files -> {REMOTE_PLUGIN}")

    ssh.run(f"chown -R www-data:www-data {REMOTE_PLUGIN}")

    cmd = rf"""
set -e
cd {REMOTE_WP}
wp plugin is-active rawlead-landing --allow-root 2>/dev/null || wp plugin activate rawlead-landing --allow-root
wp plugin list --name=rawlead-landing --allow-root --format=table
for slug in home how pricing faq contact lenta cabinet; do
  pid=$(wp post list --post_type=page --name=$slug --field=ID --allow-root 2>/dev/null | head -1)
  if [ -z "$pid" ]; then
    echo "MISSING page: $slug"
  else
    echo "OK page $slug id=$pid"
  fi
done
for slug in lenta cabinet; do
  pid=$(wp post list --post_type=page --name=$slug --field=ID --allow-root 2>/dev/null | head -1)
  [ -n "$pid" ] && wp post meta update "$pid" _wp_page_template "page-$slug.php" --allow-root 2>/dev/null || true
done
front=$(wp option get page_on_front --allow-root 2>/dev/null || echo 0)
echo "page_on_front=$front show_on_front=$(wp option get show_on_front --allow-root 2>/dev/null)"
wp rewrite flush --allow-root 2>/dev/null || true
"""
    _, out, err = ssh.run(cmd, check=False)
    print(out or err or "")

    checks = """
for path in / /how/ /pricing/ /faq/ /contact/ /lenta/ /cabinet/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1$path" || echo 000)
  echo "$path -> $code"
done
"""
    _, curl_out, _ = ssh.run(checks, check=False)
    print(curl_out or "")

    ok = curl_out and " / -> 200" in curl_out.replace("\r", "")
    if ok:
        print("SKELETON PAGES OK")
        return 0
    print("SKELETON CHECK — verify manually (nginx/wp may need theme deploy first)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
