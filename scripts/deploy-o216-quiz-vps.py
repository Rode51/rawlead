#!/usr/bin/env python3
"""O216: quiz tier UX — theme 1.18.96 + API (quiz_adaptive + allowlist).

Steps:
  1. WP theme 1.18.96 (rawlead-quiz.js retake/COMPLETED_KEY, quiz.php, feed.js, cabinet.js)
  2. src/quiz_adaptive.py (allowlist loader already in 1.18.95 code)
  3. data/quiz_pool_allowlist.json (64 curated ids)
  4. Restart rawlead-api
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_THEME_LOCAL = _ROOT / "wordpress" / "rawlead-kadence-child"

_API_FILES = (
    "src/quiz_adaptive.py",
)

_DATA_FILES = (
    "data/quiz_pool_allowlist.json",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O216 deploy: quiz tier UX (theme 1.18.96 + API + allowlist) ===")

    print("\n-- 1. WP theme --")
    n = ssh.sync_project(
        local_root=_THEME_LOCAL,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"uploaded {n} files -> /opt/rawlead/wordpress/rawlead-kadence-child")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    print("rsync -> /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child")

    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    print("theme version:", ver.strip())

    print("\n-- 2. API files --")
    api_remotes = _upload(_API_FILES)
    ssh.run("mkdir -p /opt/rawlead/data && chown rawlead:rawlead /opt/rawlead/data")
    data_remotes = _upload(_DATA_FILES)
    all_remotes = api_remotes + data_remotes
    ssh.run("chown rawlead:rawlead " + " ".join(all_remotes))

    print("\n-- 3. Restart API --")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "curl -sf -o /dev/null -w 'quiz_start=%{http_code}\\n' "
        "http://127.0.0.1:8000/v1/quiz/start && "
        "python3 -c \""
        "import json, pathlib; "
        "d=json.loads(pathlib.Path('/opt/rawlead/data/quiz_pool_allowlist.json').read_text()); "
        "print('allowlist_ids=' + str(len(d)))"
        "\" && "
        "echo o216_ok",
        check=False,
    )
    print(out.strip())

    ok = (
        "o216_ok" in (out or "")
        and "active" in (out or "")
        and "quiz_start=200" in (out or "")
        and "1.18.96" in (ver or "")
    )
    if ok:
        print("\nDEPLOY OK — theme 1.18.96 live, allowlist on VPS, quiz /start 200")
        print("Next: owner DoD D1–D9 smoke on prod")
        return 0
    print("\nDEPLOY CHECK — verify manually:")
    print("  curl http://127.0.0.1:8000/v1/quiz/start")
    print("  cat /opt/rawlead/data/quiz_pool_allowlist.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
