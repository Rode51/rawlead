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
FEED_ANON_DELAY_MINUTES = 30
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
    delay_minutes: int = FEED_ANON_DELAY_MINUTES,
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
    """O190-auto: trust telethon file — return all ids (dedupe by peer)."""
    out: list[int] = []
    seen: set[int] = set()
    for cid in raw_ids:
        peer = int(cid)
        if peer not in seen:
            seen.add(peer)
            out.append(peer)
    return out


def append_link_to_allowlist(
    link: str,
    *,
    allowlist_path: Path | None = None,
) -> bool:
    """Append one link to TG allowlist if missing. Returns True if newly added."""
    s = (link or "").strip()
    if not s:
        return False
    key = _tg_link_key(s)
    if not key or key in _tg_allowlist_link_keys():
        return False
    target = allowlist_path or _ALLOWLIST_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        if target.is_file() and target.stat().st_size > 0:
            fh.write("\n")
        fh.write(s + "\n")
    clear_tg_listen_caches()
    return True


def clear_tg_listen_caches() -> None:
    _tg_allowlist_link_keys.cache_clear()
    tg_listen_allowed_chat_ids.cache_clear()
    tg_join_queue_done_chat_ids.cache_clear()
    tg_test_group_chat_keys.cache_clear()


# Owner smoke / prompt-test (O206-t3)
TG_TEST_GROUP_RAW_ID = 5177575757


@lru_cache(maxsize=1)
def tg_test_group_chat_keys() -> frozenset[int]:
    return frozenset(_chat_id_keys(TG_TEST_GROUP_RAW_ID))


@lru_cache(maxsize=1)
def tg_join_queue_done_chat_ids() -> frozenset[int]:
    """chat_id from done rows across TG_JOIN_QUEUE*.csv (all ops copies)."""
    try:
        from tg_join_lib import read_queue_csv
    except ModuleNotFoundError:
        from src.tg_join_lib import read_queue_csv  # type: ignore[no-redef]

    ids: set[int] = set()
    for path in default_join_queue_paths():
        if not path.is_file():
            continue
        _, rows = read_queue_csv(path)
        for row in rows:
            if row.get("status", "").strip().lower() != "done":
                continue
            raw_cid = row.get("chat_id", "").strip()
            if not raw_cid:
                continue
            try:
                ids.add(int(raw_cid))
            except ValueError:
                continue
    return frozenset(ids)


def chat_in_tg_interest_set(chat_id: int | None) -> bool:
    """Log-worthy unlistened chat: allowlist, test group, or join queue done (O206-t1)."""
    if chat_id is None:
        return False
    keys = _chat_id_keys(int(chat_id))
    if keys & tg_test_group_chat_keys():
        return True
    for cid in tg_listen_allowed_chat_ids():
        if keys & _chat_id_keys(cid):
            return True
    for cid in tg_join_queue_done_chat_ids():
        if keys & _chat_id_keys(cid):
            return True
    return False


def default_join_queue_paths() -> tuple[Path, ...]:
    ops = _PROJECT_ROOT / "docs" / "ops"
    names = (
        "TG_JOIN_QUEUE.csv",
        "TG_JOIN_QUEUE_v2.csv",
        "TG_JOIN_QUEUE_v3.csv",
        "TG_JOIN_QUEUE_v4.csv",
    )
    return tuple(ops / name for name in names if (ops / name).is_file())


def collect_done_links_from_queues(
    queue_paths: tuple[Path, ...] | list[Path] | None = None,
) -> list[str]:
    """Уникальные link из done-строк активной очереди (v2+v3 merge)."""
    try:
        from tg_join_lib import read_queue_csv
    except ModuleNotFoundError:
        from src.tg_join_lib import read_queue_csv  # type: ignore[no-redef]

    paths = tuple(queue_paths) if queue_paths else default_join_queue_paths()
    seen: set[str] = set()
    out: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        _, rows = read_queue_csv(path)
        for row in rows:
            if row.get("status", "").strip().lower() != "done":
                continue
            link = row.get("link", "").strip()
            if not link or link in seen:
                continue
            seen.add(link)
            out.append(link)
    return out


def link_in_allowlist(link: str) -> bool:
    key = _tg_link_key(link)
    return bool(key and key in _tg_allowlist_link_keys())


def expand_allowlist_from_done_queues(
    *,
    allowlist_path: Path | None = None,
    queue_paths: tuple[Path, ...] | list[Path] | None = None,
    dry_run: bool = False,
) -> int:
    """Append done queue links missing from allowlist (Option A). Returns count added."""
    target = allowlist_path or _ALLOWLIST_PATH
    existing_keys = set(_tg_allowlist_link_keys())
    if target != _ALLOWLIST_PATH:
        existing_keys = set()
        for line in _read_nonempty_lines(target):
            key = _tg_link_key(line)
            if key:
                existing_keys.add(key)

    to_add: list[str] = []
    for link in collect_done_links_from_queues(queue_paths):
        key = _tg_link_key(link)
        if not key or key in existing_keys:
            continue
        existing_keys.add(key)
        to_add.append(link)

    if not to_add or dry_run:
        return len(to_add)

    block = ["", "# --- O190 done queue (auto-expanded) ---"]
    block.extend(to_add)
    with target.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(block) + "\n")
    clear_tg_listen_caches()
    return len(to_add)
