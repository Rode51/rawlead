#!/usr/bin/env python3
"""O258: Playwright chromium on VPS + parser probe cron + FLPARSING alert scripts."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_REMOTE_BASE = "/opt/rawlead"
_SCRIPT_FILES = (
    "scripts/probe_parsers_health_vps.py",
    "scripts/parser_probe_alert.py",
    "scripts/probe_parsers_health_alert_vps.py",
)
_CRON_PATH = "/etc/cron.d/rawlead-parser-probe"
_CRON_LINE = (
    "*/15 * * * * rawlead cd /opt/rawlead && "
    "env RADAR_PROFILE=site PYTHONPATH=/opt/rawlead/src:/opt/rawlead "
    "/opt/rawlead/.venv/bin/python /opt/rawlead/scripts/probe_parsers_health_alert_vps.py "
    ">> /opt/rawlead/data/parser_probe.log 2>&1\n"
)

_CHROMIUM_SMOKE = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    "/opt/rawlead/.venv/bin/python -c "
    "\"from playwright.sync_api import sync_playwright; "
    "p=sync_playwright().start(); "
    "b=p.chromium.launch(headless=True); b.close(); p.stop(); "
    "print('chromium_smoke_ok')\""
)

_CHROMIUM_INSTALL = (
    "cd /opt/rawlead && "
    "echo 'playwright_version:' && sudo -u rawlead .venv/bin/pip show playwright | grep '^Version:' && "
    "sudo -u rawlead .venv/bin/playwright install chromium && "
    "DEBIAN_FRONTEND=noninteractive .venv/bin/playwright install-deps chromium"
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = f"{_REMOTE_BASE}/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print(f"  up  {rel}")
    return remotes


def main() -> int:
    print("=== O258 deploy: playwright chromium + parser probe cron ===")

    print("\n[1/5] Playwright chromium (idempotent)...")
    _, out1, _ = ssh.run(f"{_CHROMIUM_SMOKE} 2>&1 || echo chromium_smoke_fail", check=False)
    text1 = out1 or ""
    print(text1.encode("ascii", errors="replace").decode("ascii"))
    if "chromium_smoke_ok" not in text1:
        print("  chromium missing — installing...")
        _, out_install, _ = ssh.run(_CHROMIUM_INSTALL, check=False)
        print((out_install or "").encode("ascii", errors="replace").decode("ascii"))
        _, out2, _ = ssh.run(_CHROMIUM_SMOKE, check=False)
        text2 = out2 or ""
        print(text2.encode("ascii", errors="replace").decode("ascii"))
        if "chromium_smoke_ok" not in text2:
            print("  chromium install FAILED — check VPS deps")
            return 1
    else:
        print("  chromium already OK — skip install")

    print("\n[2/5] Uploading probe/alert scripts...")
    scr_remotes = _upload(_SCRIPT_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(scr_remotes))

    print("\n[3/5] Installing cron (every 15 min)...")
    cron_payload = _CRON_LINE.replace("'", "'\"'\"'")
    ssh.run(
        f"printf '%s' '{cron_payload}' > {_CRON_PATH} && "
        f"chmod 644 {_CRON_PATH} && "
        f"grep rawlead-parser-probe {_CRON_PATH} && "
        f"touch {_REMOTE_BASE}/data/parser_probe.log && "
        f"chown rawlead:rawlead {_REMOTE_BASE}/data/parser_probe.log",
        check=False,
    )

    print("\n[4/5] Running probe alert once (dry-run)...")
    _, out_probe, _ = ssh.run(
        f"cd {_REMOTE_BASE} && sudo -u rawlead env RADAR_PROFILE=site "
        f"PYTHONPATH={_REMOTE_BASE}/src:{_REMOTE_BASE} "
        f".venv/bin/python scripts/probe_parsers_health_alert_vps.py --dry-run --json",
        check=False,
    )
    print((out_probe or "").strip())

    print("\n[5/5] Last fetch:* outcome= lines...")
    _, out_log, _ = ssh.run(
        f"grep 'fetch:.*outcome=' {_REMOTE_BASE}/data/radar_site.log 2>/dev/null | tail -5 && "
        f"echo o258_deploy_ok",
        check=False,
    )
    print((out_log or "").strip())

    ok = "o258_deploy_ok" in (out_log or "")
    if ok:
        print("\nDEPLOY OK")
        print(f"  cron: {_CRON_PATH} (every 15 min)")
        print(f"  log: {_REMOTE_BASE}/data/parser_probe.log")
        print("  FL browser_error + httpx ok → no alert")
        return 0
    print("\nDEPLOY CHECK — verify manually:")
    print(f"  cat {_CRON_PATH}")
    print(f"  sudo -u rawlead {_REMOTE_BASE}/.venv/bin/python {_REMOTE_BASE}/scripts/probe_parsers_health_alert_vps.py --dry-run")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
