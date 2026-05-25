"""Тик join по CSV (CLI, daemon acc2/3, фон acc1 в tg_monitor)."""

from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass, field
from datetime import datetime

from config import (
    append_telethon_chat_id,
    is_join_night_window,
    load_tg_join_config,
    radar_timestamp,
    telethon_chat_ids_path_for_account,
    telethon_monitor_accounts,
)
from tg_client import connect_client
from tg_join_lib import (
    join_one,
    pending_for_account,
    read_queue_csv,
    update_queue_row,
    write_queue_csv,
)


@dataclass
class JoinTickResult:
    """Итог одного тика join."""

    new_listen_chat_ids: list[int] = field(default_factory=list)


def log_join(cfg, message: str) -> None:
    line = f"{radar_timestamp()} {message}"
    print(line)
    cfg.log_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg.log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _load_state(path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _account_state(state: dict, account: str, now: datetime) -> dict:
    acc = state.setdefault(account, {})
    hour_bucket = now.strftime("%Y-%m-%dT%H")
    day_bucket = now.strftime("%Y-%m-%d")
    if acc.get("hour_bucket") != hour_bucket:
        acc["hour_bucket"] = hour_bucket
        acc["joins_this_hour"] = 0
    if acc.get("day_bucket") != day_bucket:
        acc["day_bucket"] = day_bucket
        acc["joins_today"] = 0
    acc.setdefault("joins_this_hour", 0)
    acc.setdefault("joins_today", 0)
    acc.setdefault("history", [])
    return acc


def _join_delay_sec(cfg) -> int:
    base = random.randint(cfg.min_delay_sec, cfg.max_delay_sec)
    jitter = random.randint(-180, 180)
    return max(60, base + jitter)


async def run_join_tick(
    account: str,
    *,
    client=None,
    max_per_hour: int | None = None,
    cfg=None,
    storage=None,
) -> JoinTickResult:
    """Один тик join. Если client передан — не disconnect (acc1 в tg_main)."""
    result = JoinTickResult()
    cfg = cfg or load_tg_join_config()
    account = account.strip().lower()
    now = datetime.now(cfg.night_tz)
    if is_join_night_window(cfg, now=now):
        log_join(cfg, f"join:skip:ночь account={account}")
        return result

    state = _load_state(cfg.state_path)
    acc_state = _account_state(state, account, now)
    limit_hour = max_per_hour if max_per_hour is not None else cfg.max_per_hour

    joins_hour = int(acc_state.get("joins_this_hour", 0))
    joins_day = int(acc_state.get("joins_today", 0))
    remaining_hour = max(0, limit_hour - joins_hour)
    remaining_day = max(0, cfg.max_per_day - joins_day)

    if remaining_hour <= 0:
        log_join(cfg, f"join:skip:лимит account={account} reason=hour")
        _save_state(cfg.state_path, state)
        return result
    if remaining_day <= 0:
        log_join(cfg, f"join:skip:лимит account={account} reason=day")
        _save_state(cfg.state_path, state)
        return result

    fieldnames, rows = read_queue_csv(cfg.queue_csv)
    if not fieldnames:
        log_join(cfg, f"join:fail account={account} reason=empty_queue_csv")
        return result

    pending = pending_for_account(account, rows)
    if not pending:
        log_join(cfg, f"join:skip account={account} reason=no_pending")
        _save_state(cfg.state_path, state)
        return result

    budget = min(remaining_hour, remaining_day, len(pending))
    own_client = client is None
    if own_client:
        client = await connect_client(account)
    try:
        for row in pending:
            if budget <= 0:
                break

            link = row.get("link", "").strip()
            name = row.get("name", "").strip() or link
            if not link:
                continue

            log_join(cfg, f"join:wait account={account} link={link} name={name!r}")
            if storage is not None:
                from radar_status import record_tg_phase

                record_tg_phase(storage, account, "join", name[:120] or link[:80])
            join_result = await join_one(client, link)
            ts = radar_timestamp(now=now)

            if join_result.ok:
                update_queue_row(
                    rows,
                    link,
                    status="done",
                    chat_id=join_result.chat_id,
                )
                write_queue_csv(fieldnames, rows, cfg.queue_csv)
                acc_state["joins_this_hour"] = int(acc_state["joins_this_hour"]) + 1
                acc_state["joins_today"] = int(acc_state["joins_today"]) + 1
                acc_state["last_join_at"] = ts
                history = acc_state.setdefault("history", [])
                history.append(
                    {
                        "at": ts,
                        "link": link,
                        "status": "done",
                        "chat_id": join_result.chat_id,
                        "already": join_result.already,
                    }
                )
                if len(history) > 200:
                    acc_state["history"] = history[-200:]
                _save_state(cfg.state_path, state)

                cid = join_result.chat_id if join_result.chat_id is not None else "?"
                already = " already=1" if join_result.already else ""
                log_join(
                    cfg,
                    f"join:ok account={account} link={link} chat_id={cid}{already}",
                )
                if storage is not None:
                    from radar_status import record_tg_phase

                    record_tg_phase(
                        storage, account, "join ok", f"chat_id={cid}{already}"
                    )
                if join_result.chat_id is not None:
                    monitor_accounts = telethon_monitor_accounts()
                    if account in monitor_accounts:
                        ids_path = telethon_chat_ids_path_for_account(account)
                        if append_telethon_chat_id(
                            join_result.chat_id,
                            ids_path,
                            account=account,
                        ):
                            log_join(
                                cfg,
                                f"join:listen:add account={account} "
                                f"chat_id={join_result.chat_id} path={ids_path}",
                            )
                            result.new_listen_chat_ids.append(int(join_result.chat_id))
                        else:
                            log_join(
                                cfg,
                                f"join:listen:exists account={account} "
                                f"chat_id={join_result.chat_id}",
                            )
                    else:
                        log_join(cfg, f"join:skip:listen account={account}")
                budget -= 1
                if budget <= 0:
                    break

                delay = _join_delay_sec(cfg)
                log_join(cfg, f"join:wait account={account} sleep_sec={delay}")
                await asyncio.sleep(delay)
                now = datetime.now(cfg.night_tz)
                acc_state = _account_state(state, account, now)
                if int(acc_state.get("joins_this_hour", 0)) >= limit_hour:
                    break
                if int(acc_state.get("joins_today", 0)) >= cfg.max_per_day:
                    break
                if is_join_night_window(cfg, now=now):
                    log_join(cfg, f"join:skip:ночь account={account}")
                    break
            else:
                update_queue_row(rows, link, status="fail")
                write_queue_csv(fieldnames, rows, cfg.queue_csv)
                history = acc_state.setdefault("history", [])
                history.append(
                    {
                        "at": ts,
                        "link": link,
                        "status": "fail",
                        "error": join_result.error,
                    }
                )
                _save_state(cfg.state_path, state)
                log_join(
                    cfg,
                    f"join:fail account={account} link={link} error={join_result.error}",
                )
    finally:
        if own_client:
            await client.disconnect()
    return result
