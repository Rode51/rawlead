#!/usr/bin/env python3
"""O217/O221: quiz synthetic card packs — API + data JSON files.

Steps:
  1. src/quiz_adaptive.py (JSON source + legacy Neon fallback)
  2. data/quiz_cards_v1.json (56 synthetic cards)
  3. data/quiz_cards_v2.json (130 synthetic cards, merged at runtime)
  4. Restart rawlead-api
  5. Smoke: /v1/quiz/start returns source=synthetic
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/quiz_adaptive.py",
)

_DATA_FILES = (
    "data/quiz_cards_v1.json",
    "data/quiz_cards_v2.json",
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
    print("=== O217/O221 deploy: quiz synthetic card packs ===")

    print("\n-- 1. API + data files --")
    api_remotes = _upload(_API_FILES)
    ssh.run("mkdir -p /opt/rawlead/data && chown rawlead:rawlead /opt/rawlead/data")
    data_remotes = _upload(_DATA_FILES)
    all_remotes = api_remotes + data_remotes
    ssh.run("chown rawlead:rawlead " + " ".join(all_remotes))

    print("\n-- 2. Restart API --")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "curl -sf http://127.0.0.1:8000/v1/quiz/start | python3 -c \""
        "import json,sys; d=json.load(sys.stdin); "
        "card=d.get('card',{}); src=card.get('source','?'); "
        "print('quiz_source=' + src); "
        "assert src=='synthetic', 'Expected synthetic, got '+src"
        "\" && "
        "python3 -c \""
        "import json, pathlib; "
        "v1=json.loads(pathlib.Path('/opt/rawlead/data/quiz_cards_v1.json').read_text()); "
        "v2=json.loads(pathlib.Path('/opt/rawlead/data/quiz_cards_v2.json').read_text()); "
        "ids=set(c['id'] for c in v1+v2); "
        "print('quiz_cards_v1=' + str(len(v1))); "
        "print('quiz_cards_v2=' + str(len(v2))); "
        "print('quiz_cards_merged=' + str(len(ids)))"
        "\" && "
        "echo o217_ok",
        check=False,
    )
    print(out.strip())

    ok = (
        "o217_ok" in (out or "")
        and "active" in (out or "")
        and "quiz_source=synthetic" in (out or "")
        and "quiz_cards_v1=56" in (out or "")
        and "quiz_cards_v2=130" in (out or "")
        and "quiz_cards_merged=186" in (out or "")
    )
    if ok:
        print("\nDEPLOY OK — quiz uses JSON packs (186 merged cards, source=synthetic)")
        print("Next: owner smoke quiz on /lenta/ incognito — verify PM titles appear")
        return 0
    print("\nDEPLOY CHECK — verify manually:")
    print("  curl http://127.0.0.1:8000/v1/quiz/start | python3 -m json.tool")
    print("  cat /opt/rawlead/data/quiz_cards_v1.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
