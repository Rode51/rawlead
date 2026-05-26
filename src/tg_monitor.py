"""Telethon: новые сообщения в чатах → тот же pipeline, что у бирж."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from telethon import events, utils
from telethon.errors import FloodWaitError
from telethon.tl.custom.message import Message

from config import (
    TgMonitorConfig,
    is_night_window,
    load_config,
    load_tg_join_config,
    load_tg_monitor_config,
    parse_telethon_chat_ids,
    radar_timestamp,
    telethon_chat_ids_path_for_account,
    tg_join_in_tg_main,
)
from radar_status import (
    record_tg_acc_ready,
    record_tg_message,
    record_tg_monitor_start,
    record_tg_skip,
)
from tg_join_registry import register_monitor_join, unregister_monitor_join
from tg_join_runner import run_join_tick
from budget import extract_budget_text_from_post
from filters import default_listing_filter
from lead_pipeline import process_new_listing_from_tg, short_err
from listing import ListingProject, telegram_source
from public_feed import filter_listen_chat_ids
from pg_storage import pg_storage_from_config
from storage import storage_from_config
from tg_bot_start import ensure_bot_started
from tg_client import connect_client
from tg_join_lib import load_chat_registry_from_queue


@dataclass
class _MonitorSession:
    account: str
    client: object
    chat_ids: set[int]


def _append_log(log_path: Path, line: str) -> None:
    log_path = Path(log_path)
    parent = log_path.parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
    print(line.rstrip("\n"), flush=True)


def _message_text(message: Message) -> str:
    return (message.text or message.message or "").strip()


async def _message_from_bot(event: events.NewMessage.Event) -> bool:
    """Системные/верификационные боты чата — не заказы."""
    try:
        sender = await event.get_sender()
    except Exception:
        return False
    if sender is None:
        return False
    return bool(getattr(sender, "bot", False))


def _channel_id_for_link(chat_id: int) -> int | None:
    """id для https://t.me/c/{id}/msg — без префикса -100."""
    cid = int(chat_id)
    s = str(cid)
    if s.startswith("-100"):
        return int(s[4:])
    if cid < 0:
        return abs(cid)
    return cid


def _message_url(message: Message, *, username: str = "") -> str:
    uname = (username or "").strip().lstrip("@")
    if uname:
        return f"https://t.me/{uname}/{message.id}"
    chat_id = message.chat_id
    if chat_id is None:
        return ""
    channel = _channel_id_for_link(int(chat_id))
    if not channel:
        return ""
    return f"https://t.me/c/{channel}/{message.id}"


def _listing_from_message(
    message: Message,
    *,
    chat_registry: dict[int, dict[str, str]],
    chat_title: str = "",
    chat_username: str = "",
) -> ListingProject | None:
    text = _message_text(message)
    if not text:
        return None
    if message.out:
        return None
    if message.action is not None:
        return None

    chat_id = message.chat_id
    if chat_id is None:
        return None

    title = text.split("\n", 1)[0].strip()[:200] or "Telegram"
    snippet = text[:2000]
    meta = chat_registry.get(int(chat_id), {})
    invite = str(meta.get("invite") or "").strip()
    display_title = str(meta.get("name") or chat_title or "").strip()
    username = (chat_username or meta.get("username") or "").strip().lstrip("@")
    url = _message_url(message, username=username)
    published = ""
    if message.date:
        published = message.date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return ListingProject(
        project_id=int(message.id),
        title=title,
        budget_text=extract_budget_text_from_post(text),
        url=url,
        published_at=published,
        listing_snippet=snippet,
        source=telegram_source(int(chat_id)),
        chat_invite_url=invite,
        chat_title=display_title,
    )


async def _add_monitor_peers(
    client,
    chat_ids: set[int],
    raw_ids: list[int],
    log_path: Path,
    storage,
    *,
    account: str,
) -> list[int]:
    """Добавляет peer_id из списка raw chat id. Возвращает новые peer_id."""
    added: list[int] = []
    for raw_id in raw_ids:
        peer: int | None = None
        candidates = [raw_id]
        if raw_id > 0:
            candidates.append(int(f"-100{raw_id}"))
        for cid in candidates:
            try:
                entity = await client.get_entity(cid)
                peer = utils.get_peer_id(entity)
                break
            except Exception:
                continue
        if peer is None:
            detail = f"пропуск чата {raw_id}"
            _append_log(
                log_path,
                f"{radar_timestamp()} тг:монитор:{account}: {detail}",
            )
            record_tg_skip(storage, account, detail)
            continue
        if peer not in chat_ids:
            chat_ids.add(peer)
            added.append(peer)
    return added


async def _reload_listen_chats(
    client,
    chat_ids: set[int],
    log_path: Path,
    storage,
    account: str,
) -> list[int]:
    ids_path = telethon_chat_ids_path_for_account(account)
    try:
        raw_ids = parse_telethon_chat_ids(str(ids_path))
    except (OSError, ValueError) as exc:
        _append_log(
            log_path,
            f"{radar_timestamp()} тг:монитор:{account}:reload ids: {short_err(exc)}",
        )
        return []
    listen_ids = filter_listen_chat_ids(raw_ids)
    return await _add_monitor_peers(
        client, chat_ids, listen_ids, log_path, storage, account=account
    )


async def _join_loop(
    account: str,
    client,
    chat_ids: set[int],
    log_path: Path,
    storage,
) -> None:
    account = account.strip().lower()
    join_cfg = load_tg_join_config()

    async def _get_client():
        return client

    register_monitor_join(account, _get_client)
    try:
        while True:
            try:
                tick = await run_join_tick(
                    account,
                    client=client,
                    cfg=join_cfg,
                    storage=storage,
                )
                if tick.new_listen_chat_ids:
                    added = await _reload_listen_chats(
                        client, chat_ids, log_path, storage, account
                    )
                    if added:
                        _append_log(
                            log_path,
                            f"{radar_timestamp()} тг:монитор:{account}:listen+ "
                            f"peers={added} всего={len(chat_ids)}",
                        )
            except Exception as exc:
                _append_log(
                    log_path,
                    f"{radar_timestamp()} тг:join:{account}:ошибка {short_err(exc)}",
                )
            await asyncio.sleep(join_cfg.daemon_interval_sec)
    finally:
        unregister_monitor_join(account)


def _register_message_handler(
    session: _MonitorSession,
    *,
    chat_registry: dict[int, dict[str, str]],
    storage: object,
    word_filter,
    cfg,
    pg,
    log_path: Path,
) -> None:
    account = session.account
    client = session.client
    chat_ids = session.chat_ids

    @client.on(events.NewMessage())
    async def on_new_message(event: events.NewMessage.Event) -> None:
        message = event.message
        if not isinstance(message, Message):
            return
        if message.chat_id not in chat_ids:
            return

        if await _message_from_bot(event):
            ts = radar_timestamp()
            _append_log(
                log_path,
                f"{ts} тг:сообщ acc={account} chat={message.chat_id} msg={message.id} "
                f"новый=0 увед=0 ош=пропуск:бот",
            )
            record_tg_skip(storage, account, "пропуск:бот")
            return

        chat_title = ""
        chat_username = ""
        try:
            chat = await event.get_chat()
        except Exception:
            chat = None
        if chat is not None:
            chat_title = str(getattr(chat, "title", "") or "").strip()
            chat_username = str(getattr(chat, "username", "") or "").strip()

        project = _listing_from_message(
            message,
            chat_registry=chat_registry,
            chat_title=chat_title,
            chat_username=chat_username,
        )
        if project is None:
            return

        if storage.is_radar_paused():
            ts = radar_timestamp()
            _append_log(
                log_path,
                f"{ts} тг:сообщ acc={account} chat={message.chat_id} msg={message.id} "
                f"новый=0 увед=0 ош=пропуск:пауза",
            )
            return

        errors: list[str] = []
        display_title = (project.chat_title or chat_title or "").strip()
        was_new, notified = await process_new_listing_from_tg(
            message,
            client,
            project,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
            account=account,
            chat_title=display_title,
        )
        ts = radar_timestamp()
        err_part = "; ".join(errors) if errors else "-"
        record_tg_message(
            storage,
            account,
            was_new=was_new,
            notified=notified,
            error=err_part if errors else None,
        )
        _append_log(
            log_path,
            f"{ts} тг:сообщ acc={account} chat={message.chat_id} msg={message.id} "
            f"новый={int(was_new)} увед={int(notified)} ош={err_part}",
        )


async def run_monitor() -> None:
    cfg = load_config()
    tg_cfg = load_tg_monitor_config()
    storage = storage_from_config(cfg)
    pg = pg_storage_from_config(cfg)
    word_filter = default_listing_filter()
    chat_registry = load_chat_registry_from_queue()
    log_path = tg_cfg.radar_log_path

    sessions: list[_MonitorSession] = []
    for acfg in tg_cfg.accounts:
        if not acfg.chat_ids:
            _append_log(
                log_path,
                f"{radar_timestamp()} тг:монитор:{acfg.account}: пропуск (нет chat_ids)",
            )
            continue
        client = await connect_client(acfg.account)
        await ensure_bot_started(
            client,
            acfg.account,
            log_fn=lambda msg: _append_log(
                log_path, f"{radar_timestamp()} {msg}"
            ),
        )
        listen_ids = filter_listen_chat_ids(list(acfg.chat_ids))
        skipped = len(acfg.chat_ids) - len(listen_ids)
        if skipped > 0:
            _append_log(
                log_path,
                f"{radar_timestamp()} тг:монитор:{acfg.account}: "
                f"P1 listen filter: {len(listen_ids)} из {len(acfg.chat_ids)} чатов",
            )
        chat_ids: set[int] = set()
        await _add_monitor_peers(
            client,
            chat_ids,
            listen_ids,
            log_path,
            storage,
            account=acfg.account,
        )
        if not chat_ids:
            _append_log(
                log_path,
                f"{radar_timestamp()} тг:монитор:{acfg.account}: "
                "ни один чат из списка не найден в сессии",
            )
            await client.disconnect()
            continue
        sessions.append(_MonitorSession(acfg.account, client, chat_ids))
        record_tg_monitor_start(
            storage,
            acfg.account,
            chats_listen=len(chat_ids),
            chats_in_file=len(acfg.chat_ids),
        )

    if not sessions:
        print("Ни один чат ни для одного аккаунта не найден в сессии.")
        raise SystemExit(1)

    night = "да" if is_night_window(tg_cfg) else "нет"
    join_in_main = tg_join_in_tg_main()
    for sess in sessions:
        _append_log(
            log_path,
            f"{radar_timestamp()} тг:монитор:старт account={sess.account} "
            f"чатов={len(sess.chat_ids)} ids={sorted(sess.chat_ids)} "
            f"ночь={night} join_auto={'да' if join_in_main else 'нет'}",
        )

    join_tasks: list[asyncio.Task] = []
    if join_in_main:
        for sess in sessions:
            join_tasks.append(
                asyncio.create_task(
                    _join_loop(
                        sess.account,
                        sess.client,
                        sess.chat_ids,
                        log_path,
                        storage,
                    )
                )
            )

    for sess in sessions:
        _register_message_handler(
            sess,
            chat_registry=chat_registry,
            storage=storage,
            word_filter=word_filter,
            cfg=cfg,
            pg=pg,
            log_path=log_path,
        )

    for sess in sessions:
        try:
            await sess.client.get_me()  # type: ignore[attr-defined]
            record_tg_acc_ready(storage, sess.account)
            _append_log(
                log_path,
                f"{radar_timestamp()} тг:монитор:{sess.account}: ready",
            )
        except Exception as exc:
            detail = f"get_me: {short_err(exc)}"
            record_tg_skip(storage, sess.account, detail)
            _append_log(
                log_path,
                f"{radar_timestamp()} тг:монитор:{sess.account}: {detail}",
            )

    run_tasks = [
        asyncio.create_task(sess.client.run_until_disconnected())  # type: ignore[attr-defined]
        for sess in sessions
    ]
    run_tasks.extend(join_tasks)

    try:
        await asyncio.gather(*run_tasks)
    except FloodWaitError as exc:
        _append_log(log_path, f"тг:монитор FloodWait {exc.seconds}с")
        await asyncio.sleep(exc.seconds)
    finally:
        for task in join_tasks:
            task.cancel()
        for task in join_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        for sess in sessions:
            try:
                await sess.client.disconnect()  # type: ignore[attr-defined]
            except Exception:
                pass


def reconnect_delay_sec(tg_cfg: TgMonitorConfig) -> int:
    if is_night_window(tg_cfg):
        return tg_cfg.reconnect_night_sec
    return tg_cfg.reconnect_sec
