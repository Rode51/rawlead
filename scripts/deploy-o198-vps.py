#!/usr/bin/env python3
"""O198 + O195-w2-tail: complexity rank, quiz pool cx1-2, WP weight_delta proxy."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.76"

_API_FILES = (
    "src/quiz_adaptive.py",
    "src/rank.py",
    "src/api_server.py",
    "src/owner_admin.py",
    "src/ops_funnel.py",
)


def _upload_api() -> list[str]:
    remotes: list[str] = []
    for rel in _API_FILES:
        local = _ROOT / rel
        if not local.is_file():
            raise FileNotFoundError(local)
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    return remotes


def _vps_smoke() -> bool:
    _, out, _ = ssh.run(
        "grep -c complexity_multiplier /opt/rawlead/src/rank.py; "
        "grep -c weight_delta "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php; "
        "grep -c cx_pref /opt/rawlead/src/quiz_adaptive.py; "
        "grep -c weight_delta /opt/rawlead/src/api_server.py; "
        "systemctl is-active rawlead-api; "
        "systemctl is-active rawlead-radar; "
        f"grep \"RAWLEAD_CHILD_VERSION', '{THEME_VER}'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php; "
        "echo o198_vps_smoke_ok",
        check=False,
    )
    text = out or ""
    print(text.strip())
    return (
        "o198_vps_smoke_ok" in text
        and "active" in text
        and THEME_VER in text
        and text.count("\n") >= 5
    )


def _public_smoke() -> bool:
    ok = True

    def _get_json(url: str) -> dict:
        with urllib.request.urlopen(url, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _head_status(url: str) -> int:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=45) as resp:
            return int(resp.status)

    for label, url in (
        ("api quiz/start", "https://api.rawlead.ru/v1/quiz/start"),
        ("wp quiz/start", "https://rawlead.ru/wp-json/rawlead/v1/quiz/start"),
    ):
        try:
            data = _get_json(url)
            card = data.get("card") or data
            card_id = card.get("card_id") or card.get("id")
            cx = card.get("complexity")
            print(f"{label}: card_id={card_id} complexity={cx}")
            if not card_id:
                print(f"{label}: FAIL — no card_id")
                ok = False
        except Exception as exc:
            print(f"{label}: retry after API warm-up — {exc}")
            import time

            time.sleep(5)
            try:
                data = _get_json(url)
                card = data.get("card") or data
                card_id = card.get("card_id") or card.get("id")
                cx = card.get("complexity")
                print(f"{label}: card_id={card_id} complexity={cx}")
                if not card_id:
                    print(f"{label}: FAIL — no card_id")
                    ok = False
            except Exception as exc2:
                print(f"{label}: FAIL — {exc2}")
                ok = False

    try:
        status = _head_status("https://rawlead.ru/quiz/")
        print(f"quiz page: HTTP {status}")
        if status != 200:
            ok = False
    except Exception as exc:
        print(f"quiz page: FAIL — {exc}")
        ok = False

    return ok


def main() -> int:
    print("=== O198 deploy: complexity rank + weight_delta proxy ===")
    _upload_api()

    print("\n=== O198 theme sync ===")
    theme_rc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
        cwd=str(_ROOT),
        check=False,
    )
    if theme_rc.returncode != 0:
        print("THEME DEPLOY FAILED")
        return 1

    print("\n=== restart rawlead-api (radar untouched) ===")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && "
        "for i in 1 2 3 4 5 6 7 8 9 10; do "
        "systemctl is-active rawlead-api && break; sleep 2; done",
        check=False,
    )
    print((out or "").strip())
    if "active" not in (out or ""):
        print("API RESTART FAILED")
        return 1

    print("\n=== VPS smoke ===")
    if not _vps_smoke():
        print("VPS SMOKE FAILED — verify manually")
        return 1

    print("\n=== public smoke ===")
    if not _public_smoke():
        print("PUBLIC SMOKE WARN — check quiz/start or /quiz/ manually")
        return 1

    print("\nO198 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
