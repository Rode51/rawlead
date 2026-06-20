#!/usr/bin/env python3
"""One-off: mint PREPROD token on VPS (prod Postgres) and sync to local .env.site."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.site", override=True)

import deploy_vps_ssh as ssh  # noqa: E402


def _write_env_site(key: str, value: str) -> None:
    env_site = _ROOT / ".env.site"
    lines = env_site.read_text(encoding="utf-8").splitlines() if env_site.is_file() else []
    prefix = f"{key}="
    out: list[str] = []
    found = False
    for line in lines:
        if line.strip().startswith(prefix):
            out.append(f"{prefix}{value}")
            found = True
        else:
            out.append(line)
    if not found:
        if out and out[-1].strip():
            out.append("")
        out.append(f"# {key} — synced from VPS mint")
        out.append(f"{prefix}{value}")
    env_site.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    mint_cmd = (
        "bash -lc 'cd /opt/rawlead && set -a && "
        "[ -f .env ] && source .env; "
        "[ -f .env.site ] && source .env.site; set +a && "
        ".venv/bin/python scripts/preprod_mint_token.py --account acc1 --write-env-site'"
    )
    code, out, err = ssh.run(mint_cmd, check=False)
    print("--- mint ---")
    print(out.strip())
    if err.strip():
        print(err.strip()[:800], file=sys.stderr)
    if code != 0:
        return code

    _, line, _ = ssh.run(
        "grep '^RAWLEAD_PREPROD_ACCESS_TOKEN=' /opt/rawlead/.env.site | head -1",
        check=True,
    )
    line = line.strip()
    if not line.startswith("RAWLEAD_PREPROD_ACCESS_TOKEN="):
        print("token line missing on VPS", file=sys.stderr)
        return 1
    token = line.split("=", 1)[1].strip().strip('"').strip("'")
    _write_env_site("RAWLEAD_PREPROD_ACCESS_TOKEN", token)
    print("local .env.site updated: RAWLEAD_PREPROD_ACCESS_TOKEN")

    req = urllib.request.Request(
        "https://api.rawlead.ru/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(300).decode("utf-8", "replace")
        print(f"api /v1/me: {resp.status}", "OK" if resp.status == 200 else "WARN")
        if resp.status != 200:
            print(body[:200], file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"api /v1/me FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
