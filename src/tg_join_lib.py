"""Общая логика join в TG-чаты (CLI и очередь)."""

from __future__ import annotations

import asyncio
import csv
from dataclasses import dataclass
from pathlib import Path

from telethon.errors import FloodWaitError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from config import _PROJECT_ROOT

QUEUE_CSV = _PROJECT_ROOT / "docs" / "ops" / "TG_JOIN_QUEUE.csv"
JOIN_LINKS = _PROJECT_ROOT / "docs" / "ops" / "TG_JOIN_LINKS.txt"
INVITES_FALLBACK = _PROJECT_ROOT / "scripts" / "tg_invites.txt"


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


def read_invite_links(extra: list[str] | None = None) -> list[str]:
    if extra:
        return [a.strip() for a in extra if a.strip()]
    links = read_lines(JOIN_LINKS)
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


def read_queue_csv(path: Path = QUEUE_CSV) -> tuple[list[str], list[dict[str, str]]]:
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
    path: Path = QUEUE_CSV,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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
