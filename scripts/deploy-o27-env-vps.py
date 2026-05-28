#!/usr/bin/env python3
"""Post-deploy: MATCH_PUSH + STARS env on VPS + service restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_ENV_LINES = (
    ("MATCH_PUSH", "1"),
    ("STARS_ENABLED", "1"),
    ("STARS_PRICE_XTR", "300"),
    ("STARS_SUBSCRIPTION_DAYS", "30"),
)


def _ensure_env_line(key: str, value: str) -> str:
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's/^{key}=.*/{key}={value}/' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    parts = [_ensure_env_line(k, v) for k, v in _ENV_LINES]
    parts.append("grep -E '^(MATCH_PUSH|STARS_)' /opt/rawlead/.env.site")
    parts.append("systemctl restart rawlead-api rawlead-bot-poll rawlead-radar")
    parts.append("systemctl is-active rawlead-api rawlead-bot-poll rawlead-radar")
    parts.append(
        "grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1"
    )
    parts.append("curl -s http://127.0.0.1:8000/health")
    _, out, _ = ssh.run(" && ".join(parts), check=False)
    print(out)
    ok = "active" in out and "1.7.21" in out
    print("ENV DEPLOY OK" if ok else "ENV DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
