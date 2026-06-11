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
FEED_VISIBILITY_DAYS = 7
INBOX_VISIBILITY_DAYS = 7
FEED_SOURCE_KEYS = frozenset(
    {"fl", "kwork", "tg", "youdo", "freelance_ru", "freelancejob", "pchyol"}
)
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
    s = (source or "").strip()
    enabled = public_feed_sources()
    if s in enabled:
        return True
    if not s.startswith("tg:"):
        return False
    try:
        cid = int(s.split(":", 1)[1])
    except ValueError:
        return False
    keys = _chat_id_keys(cid)
    for entry in enabled:
        if not entry.startswith("tg:"):
            continue
        try:
            ecid = int(entry.split(":", 1)[1])
        except ValueError:
            continue
        if keys & _chat_id_keys(ecid):
            return True
    return False


def public_feed_source_sql() -> tuple[str, list[Any]]:
    """SQL-фрагмент + params для фильтра source (один param = массив source)."""
    sources = sorted(public_feed_sources())
    return " AND source = ANY(%s::text[])", [sources]


def parse_feed_source_param(raw: str) -> list[str]:
    """Comma keys from GET /v1/feed?source=fl,kwork (empty → no extra filter)."""
    if not (raw or "").strip():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        key = part.strip().lower()
        if not key or key not in FEED_SOURCE_KEYS or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def feed_source_filter_sql(
    source_keys: list[str],
    *,
    alias: str = "",
) -> tuple[str, list[Any]]:
    """Optional multi-source filter: exact keys + tg → source LIKE 'tg:%'."""
    if not source_keys:
        return "", []
    prefix = f"{alias}." if alias else ""
    exact = [k for k in source_keys if k != "tg"]
    has_tg = "tg" in source_keys
    parts: list[str] = []
    params: list[Any] = []
    if exact:
        parts.append(f"{prefix}source = ANY(%s::text[])")
        params.append(exact)
    if has_tg:
        # Param binding — literal '%' in SQL breaks psycopg (% placeholder parser).
        parts.append(f"{prefix}source LIKE %s")
        params.append("tg:%")
    if not parts:
        return "", []
    if len(parts) == 1:
        return f" AND {parts[0]}", params
    return f" AND ({' OR '.join(parts)})", params


def inbox_replies_where_sql(*, alias: str = "ulr") -> tuple[str, list[Any]]:
    """Inbox: user's replies in window; no leads.is_visible requirement."""
    prefix = f"{alias}."
    sql = (
        f"{prefix}deleted_at IS NULL"
        f" AND {prefix}created_at >= NOW() - make_interval(days => %s)"
    )
    return sql, [INBOX_VISIBILITY_DAYS]


def feed_visibility_where_sql(
    *,
    alias: str = "",
    apply_delay_minutes: int | None = None,
    delay_minutes: int = 15,
) -> tuple[str, list[Any]]:
    """O75: is_visible + public sources + created_at within FEED_VISIBILITY_DAYS."""
    prefix = f"{alias}." if alias else ""
    src_sql, src_params = public_feed_source_sql()
    if prefix:
        src_sql = src_sql.replace(" AND source", f" AND {prefix}source", 1)
    sql = (
        f"{prefix}is_visible = TRUE"
        + src_sql
        + f" AND {prefix}created_at >= NOW() - make_interval(days => %s)"
    )
    params: list[Any] = [*src_params, FEED_VISIBILITY_DAYS]
    if apply_delay_minutes is not None:
        sql += f" AND {prefix}created_at <= NOW() - make_interval(mins => %s)"
        params.append(int(apply_delay_minutes))
    return sql, params


def _tg_link_key(value: str) -> str:
    """Username или invite-hash для сопоставления с allowlist / join queue."""
    s = (value or "").strip()
    if not s:
        return ""
    try:
        from tg_join_lib import invite_hash, username_from_invite
    except ModuleNotFoundError:
        from src.tg_join_lib import invite_hash, username_from_invite  # type: ignore[no-redef]
    user = username_from_invite(s)
    if user:
        return user.lower()
    h = invite_hash(s)
    if h:
        return h.lower()
    m = _TME_RE.match(s)
    if m:
        tail = m.group(1).split("/")[0].strip().lower()
        if tail and not tail.startswith("+"):
            return tail
    return s.lstrip("@").lower()


@lru_cache(maxsize=1)
def _tg_allowlist_link_keys() -> frozenset[str]:
    out: set[str] = set()
    for line in _read_nonempty_lines(_ALLOWLIST_PATH):
        key = _tg_link_key(line)
        if key:
            out.add(key)
    return frozenset(out)


def _tg_join_queue_path() -> Path:
    rel = os.getenv("TG_JOIN_QUEUE_CSV", "docs/ops/TG_JOIN_QUEUE.csv").strip()
    p = Path(rel)
    return p if p.is_absolute() else _PROJECT_ROOT / p


@lru_cache(maxsize=1)
def tg_listen_allowed_chat_ids() -> frozenset[int]:
    """Peer/chat id: allowlist ∩ join queue (done). TG-A JSON и droplist не используются."""
    allowed_keys = set(_tg_allowlist_link_keys())
    if not allowed_keys:
        return frozenset()

    try:
        from tg_join_lib import read_queue_csv
    except ModuleNotFoundError:
        from src.tg_join_lib import read_queue_csv  # type: ignore[no-redef]

    ids: set[int] = set()
    _, rows = read_queue_csv(_tg_join_queue_path())
    for row in rows:
        if row.get("status", "").strip().lower() != "done":
            continue
        raw_cid = row.get("chat_id", "").strip()
        if not raw_cid:
            continue
        link = row.get("link", "").strip()
        key = _tg_link_key(link)
        if not key or key not in allowed_keys:
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
    elif cid < 0:
        keys.add(int(f"-100{abs(cid)}"))
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
