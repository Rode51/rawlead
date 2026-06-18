"""Общая логика join в TG-чаты (CLI и очередь)."""

from __future__ import annotations

import asyncio
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from telethon.errors import FloodWaitError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from config import _PROJECT_ROOT, _path_from_env

def join_queue_csv_path() -> Path:
    """Путь очереди join: env TG_JOIN_QUEUE_CSV (site → v2)."""
    rel = _path_from_env("TG_JOIN_QUEUE_CSV", "docs/ops/TG_JOIN_QUEUE.csv")
    p = Path(rel)
    return p if p.is_absolute() else _PROJECT_ROOT / p


QUEUE_CSV = join_queue_csv_path()
INVITES_FALLBACK = _PROJECT_ROOT / "scripts" / "tg_invites.txt"

_PUBLIC_USERNAME_RE = re.compile(r"^https?://t\.me/([A-Za-z0-9_]+)/?$", re.I)


@dataclass(frozen=True)
class JoinResult:
    ok: bool
    already: bool = False
    chat_id: int | None = None
    error: str | None = None


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


def username_from_invite(invite: str) -> str:
    m = _PUBLIC_USERNAME_RE.match((invite or "").strip())
    return m.group(1) if m else ""


def peer_id_from_chat_id(chat_id: int) -> int:
    cid = int(chat_id)
    s = str(cid)
    if s.startswith("-100"):
        return cid
    return int(f"-100{cid}")


def _registry_keys_for_chat_id(chat_id: int) -> list[int]:
    cid = int(chat_id)
    keys = {cid}
    s = str(cid)
    if s.startswith("-100"):
        keys.add(int(s[4:]))
    else:
        keys.add(peer_id_from_chat_id(cid))
    return list(keys)


def load_chat_registry_from_queue(path: Path | None = None) -> dict[int, dict[str, str]]:
    path = path or join_queue_csv_path()
    """peer_id / short id → {name, invite, username?} из строк CSV со status=done."""
    registry: dict[int, dict[str, str]] = {}
    _, rows = read_queue_csv(path)
    for row in rows:
        if row.get("status", "").strip().lower() != "done":
            continue
        raw = row.get("chat_id", "").strip()
        if not raw:
            continue
        try:
            cid = int(raw)
        except ValueError:
            continue
        invite = row.get("link", "").strip()
        name = row.get("name", "").strip()
        meta = {
            "name": name,
            "invite": invite,
            "username": username_from_invite(invite),
        }
        for key in _registry_keys_for_chat_id(cid):
            registry[key] = meta
    return registry


def read_invite_links(
    extra: list[str] | None = None,
    *,
    account: str | None = None,
) -> list[str]:
    if extra:
        return [a.strip() for a in extra if a.strip()]
    _, rows = read_queue_csv()
    links: list[str] = []
    seen: set[str] = set()
    acc_key = (account or "").strip().lower()
    for row in rows:
        if acc_key and row.get("account", "").strip().lower() != acc_key:
            continue
        link = row.get("link", "").strip()
        if link and link not in seen:
            seen.add(link)
            links.append(link)
    if links:
        return links
    return read_lines(INVITES_FALLBACK)


def invite_hash(link: str) -> str | None:
    for prefix in ("https://t.me/+", "http://t.me/+", "t.me/+"):
        if link.startswith(prefix):
            return link[len(prefix) :].split("?")[0].strip("/")
    if "/+" in link:
        return link.split("/+", 1)[1].split("?")[0].strip("/")
    return None


async def resolve_chat_id(client, link: str) -> int | None:
    try:
        entity = await client.get_entity(link)
        return int(entity.id)
    except Exception:
        return None


async def join_one(client, link: str) -> JoinResult:
    """Join по ссылке; FloodWait — ждёт и повторяет."""
    try:
        invite = invite_hash(link)
        if invite:
            await client(ImportChatInviteRequest(invite))
        else:
            entity = await client.get_entity(link)
            await client(JoinChannelRequest(entity))
        chat_id = await resolve_chat_id(client, link)
        return JoinResult(ok=True, chat_id=chat_id)
    except UserAlreadyParticipantError:
        chat_id = await resolve_chat_id(client, link)
        return JoinResult(ok=True, already=True, chat_id=chat_id)
    except FloodWaitError as exc:
        await asyncio.sleep(exc.seconds)
        return await join_one(client, link)
    except Exception as exc:
        return JoinResult(ok=False, error=f"{type(exc).__name__}: {exc}")


def read_queue_csv(path: Path | None = None) -> tuple[list[str], list[dict[str, str]]]:
    path = path or join_queue_csv_path()
    if not path.is_file():
        return [], []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return fieldnames, rows


def write_queue_csv(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    path: Path | None = None,
) -> None:
    path = path or join_queue_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ordered_join_queue_paths() -> list[Path]:
    """Join tick order: v2 backlog → v3 → v4 (O248)."""
    ops = _PROJECT_ROOT / "docs" / "ops"
    names = (
        "TG_JOIN_QUEUE_v2.csv",
        "TG_JOIN_QUEUE_v3.csv",
        "TG_JOIN_QUEUE_v4.csv",
    )
    paths = [ops / name for name in names if (ops / name).is_file()]
    if paths:
        return paths
    return [join_queue_csv_path()]


def pending_for_account(
    account: str,
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    key = account.strip().lower()
    return [
        row
        for row in rows
        if row.get("account", "").strip().lower() == key
        and row.get("status", "").strip().lower() == "pending"
    ]


def first_pending_row(
    account: str,
    queue_paths: list[Path] | None = None,
) -> tuple[Path, list[str], list[dict[str, str]], dict[str, str]] | None:
    """First pending row for account across ordered queue CSVs."""
    paths = queue_paths or ordered_join_queue_paths()
    key = account.strip().lower()
    for path in paths:
        fieldnames, rows = read_queue_csv(path)
        for row in rows:
            if (
                row.get("account", "").strip().lower() == key
                and row.get("status", "").strip().lower() == "pending"
            ):
                return path, fieldnames, rows, row
    return None


def has_pending_for_account(
    account: str,
    queue_paths: list[Path] | None = None,
) -> bool:
    return first_pending_row(account, queue_paths) is not None


def update_queue_row(
    rows: list[dict[str, str]],
    link: str,
    *,
    status: str,
    chat_id: int | None = None,
) -> None:
    target = link.strip()
    for row in rows:
        if row.get("link", "").strip() == target:
            row["status"] = status
            if chat_id is not None:
                row["chat_id"] = str(chat_id)
            return
