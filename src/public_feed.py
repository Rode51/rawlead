"""Публичная лента /lenta/: whitelist источников и TG listen (P1)."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_SOURCES = ("fl", "kwork")
_PUBLIC_FEED_SOURCES_ENV = "PUBLIC_FEED_SOURCES"
_ALLOWLIST_PATH = _PROJECT_ROOT / "docs" / "ops" / "TG_PUBLIC_FEED_ALLOWLIST.txt"
_TME_RE = re.compile(
    r"^https?://t\.me/(?:joinchat/)?([A-Za-z0-9_+/-]+)/?$",
    re.I,
)


def _read_nonempty_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


@lru_cache(maxsize=1)
def public_feed_sources() -> frozenset[str]:
    """Источники в GET /v1/feed и /v1/skills/catalog. Пустой env → fl,kwork."""
    raw = os.getenv(_PUBLIC_FEED_SOURCES_ENV, "").strip()
    if not raw:
        return frozenset(_DEFAULT_SOURCES)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return frozenset(parts) if parts else frozenset(_DEFAULT_SOURCES)


def is_public_feed_source(source: str) -> bool:
    return (source or "").strip() in public_feed_sources()


def public_feed_source_sql() -> tuple[str, list[Any]]:
    """SQL-фрагмент + params для фильтра source (один param = массив source)."""
    sources = sorted(public_feed_sources())
    return " AND source = ANY(%s::text[])", [sources]


def _normalize_tg_username(value: str) -> str:
    s = (value or "").strip().lstrip("@").lower()
    m = _TME_RE.match(s)
    if m:
        user = m.group(1).split("/")[0].strip().lower()
        if user.startswith("+"):
            return ""
        return user
    if s.startswith("+"):
        return ""
    return s


@lru_cache(maxsize=1)
def _tg_allowlist_usernames() -> frozenset[str]:
    out: set[str] = set()
    for line in _read_nonempty_lines(_ALLOWLIST_PATH):
        user = _normalize_tg_username(line)
        if user:
            out.add(user)
    return frozenset(out)


def _tg_join_queue_path() -> Path:
    rel = os.getenv("TG_JOIN_QUEUE_CSV", "docs/ops/TG_JOIN_QUEUE.csv").strip()
    p = Path(rel)
    return p if p.is_absolute() else _PROJECT_ROOT / p


@lru_cache(maxsize=1)
def tg_listen_allowed_chat_ids() -> frozenset[int]:
    """Peer/chat id: allowlist ∩ join queue (done). TG-A JSON и droplist не используются."""
    allowed_users = set(_tg_allowlist_usernames())
    if not allowed_users:
        return frozenset()

    try:
        from tg_join_lib import read_queue_csv, username_from_invite
    except ModuleNotFoundError:
        from src.tg_join_lib import read_queue_csv, username_from_invite  # type: ignore[no-redef]

    ids: set[int] = set()
    _, rows = read_queue_csv(_tg_join_queue_path())
    for row in rows:
        if row.get("status", "").strip().lower() != "done":
            continue
        raw_cid = row.get("chat_id", "").strip()
        if not raw_cid:
            continue
        link = row.get("link", "").strip()
        user = username_from_invite(link) or _normalize_tg_username(link)
        if not user or user.lower() not in allowed_users:
            continue
        try:
            ids.add(int(raw_cid))
        except ValueError:
            continue
    return frozenset(ids)


def _chat_id_keys(chat_id: int) -> set[int]:
    cid = int(chat_id)
    keys = {cid, abs(cid)}
    s = str(cid)
    if s.startswith("-100"):
        keys.add(int(s[4:]))
    elif cid > 0:
        keys.add(int(f"-100{cid}"))
    return keys


def filter_listen_chat_ids(raw_ids: list[int]) -> list[int]:
    """Оставить только id из allowlist (done в join queue); пустой allowlist → []."""
    allowed = tg_listen_allowed_chat_ids()
    if not allowed:
        return []
    allowed_keys: set[int] = set()
    for aid in allowed:
        allowed_keys |= _chat_id_keys(aid)
    out: list[int] = []
    seen: set[int] = set()
    for cid in raw_ids:
        keys = _chat_id_keys(cid)
        if not keys & allowed_keys:
            continue
        peer = int(cid)
        if peer not in seen:
            seen.add(peer)
            out.append(peer)
    return out
