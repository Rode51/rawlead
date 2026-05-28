"""Собрать PUBLIC_FEED_SOURCES: биржи + tg:{peer} из join queue (done ∩ allowlist)."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
_ALLOWLIST = _ROOT / "docs" / "ops" / "TG_PUBLIC_FEED_ALLOWLIST.txt"
_QUEUE = _ROOT / "docs" / "ops" / "TG_JOIN_QUEUE_v2.csv"
_WEB = _ROOT / "docs" / "ops" / "PUBLIC_FEED_WEB_SOURCES.txt"
_TME = re.compile(r"^https?://t\.me/(?:joinchat/)?([A-Za-z0-9_+/-]+)/?$", re.I)


def _username(value: str) -> str:
    s = (value or "").strip()
    m = _TME.match(s)
    if m:
        user = m.group(1).split("/")[0].strip().lower()
        return "" if user.startswith("+") else user
    return s.lstrip("@").lower()


def _allowlist_usernames() -> frozenset[str]:
    out: set[str] = set()
    for line in _ALLOWLIST.read_text(encoding="utf-8").splitlines():
        user = _username(line)
        if user:
            out.add(user)
    return frozenset(out)


def _web_source_id(line: str) -> str:
    s = line.strip()
    if not s or s.startswith("#"):
        return ""
    head = s.split("|", 1)[0].strip()
    if not head or " " in head:
        return ""
    return head


def _web_sources() -> list[str]:
    out: list[str] = []
    for line in _WEB.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "⏸" in s or "отложен" in s.casefold():
            continue
        src = _web_source_id(line)
        if src:
            out.append(src)
    return out or ["fl", "kwork"]


def _tg_peer_source(chat_id: str) -> str:
    n = int(chat_id)
    peer = n if n < 0 else int(f"-100{n}")
    return f"tg:{peer}"


def build_sources() -> list[str]:
    allowed = _allowlist_usernames()
    tg: list[str] = []
    with _QUEUE.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("status", "").strip().lower() != "done":
                continue
            cid = row.get("chat_id", "").strip()
            if not cid:
                continue
            user = _username(row.get("link", ""))
            if user not in allowed:
                continue
            tg.append(_tg_peer_source(cid))
    web = _web_sources()
    seen: set[str] = set()
    out: list[str] = []
    for src in web + sorted(set(tg), key=lambda x: int(x.split(":")[1])):
        if src not in seen:
            seen.add(src)
            out.append(src)
    return out


def main() -> int:
    sources = build_sources()
    line = "PUBLIC_FEED_SOURCES=" + ",".join(sources)
    if "--print" in sys.argv or len(sys.argv) == 1:
        print(line)
        tg_n = sum(1 for s in sources if s.startswith("tg:"))
        print(f"# web={len(sources) - tg_n} tg={tg_n}", file=sys.stderr)
        print(
            "# вставить в .env и .env.site (Site читает .env.site первым), затем рестарт Site",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
