#!/usr/bin/env python3
"""O105-w1 r2: pay deep links + change method + theme 1.18.7."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "config.py",
    "premium_pay.py",
    "telegram_control.py",
    "stars_billing.py",
    "health_check.py",
)

_THEME_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/inc/rawlead-api.php",
    "wordpress/rawlead-kadence-child/inc/marketing.php",
    "wordpress/rawlead-kadence-child/page-cabinet.php",
    "wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-card.php",
)


def _sync_pay_env_site() -> None:
    _, out, _ = ssh.run(
        "for f in /opt/rawlead/.env /opt/rawlead/.env.site; do "
        "[ -f \"$f\" ] && grep -v '^STARS_PRICE_XTR=' \"$f\" > \"$f.tmp\" && mv \"$f.tmp\" \"$f\"; "
        "done; "
        "echo 'STARS_PRICE_XTR=600' >> /opt/rawlead/.env; "
        "echo 'STARS_PRICE_XTR=600' >> /opt/rawlead/.env.site; "
        "grep '^PAY_' /opt/rawlead/.env >> /opt/rawlead/.env.site 2>/dev/null || true; "
        "awk -F= '!seen[$1]++' /opt/rawlead/.env.site > /opt/rawlead/.env.site.tmp && "
        "mv /opt/rawlead/.env.site.tmp /opt/rawlead/.env.site; "
        "grep STARS_PRICE_XTR /opt/rawlead/.env.site",
        check=False,
    )
    print("STARS on VPS:", (out or "").strip())


def main() -> int:
    print("=== O105-w1 r2 deploy: pay deep links ===")
    for name in _FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    for rel in _THEME_FILES:
        local = _ROOT / rel.replace("/", "\\") if False else _ROOT / rel
        remote = "/opt/rawlead/" + rel
        ssh.upload(local, remote)
        print(f"up {rel}")

    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    _sync_pay_env_site()

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar rawlead-radar-legacy rawlead-bot-poll && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy rawlead-bot-poll && "
        "grep -c send_pay_method /opt/rawlead/src/telegram_control.py && "
        "grep -c pay_sbp /opt/rawlead/wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-card.php && "
        "grep RAWLEAD_CHILD_VERSION /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep STARS_PRICE_XTR /opt/rawlead/.env.site | tail -1 && "
        "curl -sS https://rawlead.ru/pricing/ 2>/dev/null | grep -c '600 ⭐' || true && echo o105_w1_r2_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = text.count("active") >= 4 and "o105_w1_r2_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
