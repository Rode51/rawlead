"""Собрать docs/ops/TG_JOIN_QUEUE_v2.csv из TG_PUBLIC_FEED_ALLOWLIST.txt."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ALLOW = _ROOT / "docs" / "ops" / "TG_PUBLIC_FEED_ALLOWLIST.txt"
_OLD = _ROOT / "docs" / "ops" / "TG_JOIN_QUEUE.csv"
_OUT = _ROOT / "docs" / "ops" / "TG_JOIN_QUEUE_v2.csv"
_TME = re.compile(r"^https?://t\.me/([A-Za-z0-9_]+)/?$", re.I)
_ACC = ("acc1", "acc2", "acc3")


def _norm(link: str) -> str:
    m = _TME.match((link or "").strip())
    return m.group(1).lower() if m else ""


def main() -> int:
    old: dict[str, dict[str, str]] = {}
    if _OLD.is_file():
        with _OLD.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                u = _norm(row.get("link", ""))
                if u:
                    old[u] = row

    links: list[str] = []
    for ln in _ALLOW.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#") and "t.me" in s:
            links.append(s)

    done_rows: list[dict[str, str]] = []
    pending: list[dict[str, str]] = []
    for link in links:
        u = _norm(link)
        prev = old.get(u, {})
        st = (prev.get("status") or "pending").strip().lower()
        cid = (prev.get("chat_id") or "").strip()
        if st == "done" and cid:
            done_rows.append(
                {
                    "link": link,
                    "name": (prev.get("name") or u).strip(),
                    "account": (prev.get("account") or "acc1").strip(),
                    "chat_id": cid,
                }
            )
        else:
            pending.append({"link": link, "name": u or link})

    rows: list[dict[str, str]] = []
    for d in done_rows:
        rows.append(
            {
                "wave": "1",
                "account": d["account"],
                "status": "done",
                "name": d["name"],
                "link": d["link"],
                "chat_id": d["chat_id"],
                "notes": "tier-a-migrated",
            }
        )

    wave = 2
    for i, p in enumerate(pending):
        if i > 0 and i % 3 == 0:
            wave += 1
        rows.append(
            {
                "wave": str(wave),
                "account": _ACC[i % 3],
                "status": "pending",
                "name": p["name"],
                "link": p["link"],
                "chat_id": "",
                "notes": "tier-a-pdf",
            }
        )

    fields = ["wave", "account", "status", "name", "link", "chat_id", "notes"]
    with _OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"{_OUT}: done={len(done_rows)} pending={len(pending)} total={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
