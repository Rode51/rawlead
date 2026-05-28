"""Команды и кнопки паузы/статуса радара через Telegram Bot API (getUpdates)."""

from __future__ import annotations

import json
import re

import requests

from config import Config, telegram_requests_proxies
from radar_status import format_status_message
from storage import ProjectStorage
from tg_chain_log import log_relay_api_call
from tg_relay_allowlist import (
    account_for_user_id,
    is_allowlisted_user,
    mark_message_relayed,
    was_message_relayed,
)

_TELEGRAM_BOT_IN_PATH = re.compile(r"(/bot)[^/\s]+(/)")
_PAUSE_CMDS = frozenset({"/pause", "/стоп"})
_RESUME_CMDS = frozenset({"/resume", "/старт"})
_STATUS_CMDS = frozenset({"/status"})

BTN_PAUSE = "⏸ Пауза"
BTN_RESUME = "▶ Старт"
BTN_STATUS = "ℹ Статус"

_ACTION_PAUSE = "pause"
_ACTION_RESUME = "resume"
_ACTION_STATUS = "status"


class TelegramControlError(RuntimeError):
    """Ошибка опроса или ответа на команды в Telegram."""


def _mask_token(s: str) -> str:
    return _TELEGRAM_BOT_IN_PATH.sub(r"\1***MASKED***\2", s)


def _reply_keyboard_markup() -> str:
    markup = {
        "keyboard": [
            [{"text": BTN_PAUSE}, {"text": BTN_RESUME}],
            [{"text": BTN_STATUS}],
        ],
        "resize_keyboard": True,
    }
    return json.dumps(markup, ensure_ascii=False, separators=(",", ":"))


def _normalize_command(text: str) -> str:
    s = (text or "").strip()
    if not s.startswith("/"):
        return ""
    token = s.split()[0].split("@")[0]
    return token.casefold()


def _resolve_action(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    cmd = _normalize_command(s)
    if cmd in _PAUSE_CMDS:
        return _ACTION_PAUSE
    if cmd in _RESUME_CMDS:
        return _ACTION_RESUME
    if cmd in _STATUS_CMDS:
        return _ACTION_STATUS
    if s == BTN_PAUSE:
        return _ACTION_PAUSE
    if s == BTN_RESUME:
        return _ACTION_RESUME
    if s == BTN_STATUS:
        return _ACTION_STATUS
    return None


def _message_from_user_id(message: dict) -> int | None:
    from_user = message.get("from")
    if not isinstance(from_user, dict):
        return None
    user_id = from_user.get("id")
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def _message_chat_id(message: dict) -> int | None:
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    if chat_id is None:
        return None
    try:
        return int(chat_id)
    except (TypeError, ValueError):
        return None


def relay_message_to_owner_chat(
    cfg: Config,
    *,
    from_chat_id: int,
    message_id: int,
    account: str = "",
    errors: list[str] | None = None,
    timeout_sec: float = 20.0,
) -> bool:
    """Bot API forwardMessage: acc→бот inbox → TELEGRAM_CHAT_ID (владелец)."""
    key_from = int(from_chat_id)
    key_msg = int(message_id)
    if was_message_relayed(key_from, key_msg):
        return True

    proxies = telegram_requests_proxies(cfg)
    owner_chat_id = cfg.telegram_chat_id.strip()
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/forwardMessage"

    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data={
                "chat_id": owner_chat_id,
                "from_chat_id": str(key_from),
                "message_id": str(key_msg),
            },
            timeout=timeout_sec,
            proxies=proxies,
        )
    except requests.RequestException as exc:
        if errors is not None:
            errors.append(f"тг:relay:api:{_mask_token(str(exc))[:160]}")
        return False

    if resp.status_code != 200:
        detail = ""
        try:
            body = resp.json()
            if isinstance(body, dict):
                desc = body.get("description")
                if desc is not None and str(desc).strip():
                    detail = " " + str(desc).strip()
        except ValueError:
            pass
        if errors is not None:
            errors.append(f"тг:relay:forwardMessage HTTP {resp.status_code}.{detail}")
        return False

    try:
        body = resp.json()
    except ValueError:
        if errors is not None:
            errors.append("тг:relay:forwardMessage не-json")
        return False

    if not body.get("ok", False):
        desc = str(body.get("description") or "unknown error")
        if errors is not None:
            errors.append(f"тг:relay:forwardMessage {desc[:160]}")
        return False

    mark_message_relayed(key_from, key_msg)
    if errors is not None:
        try:
            owner_id = int(owner_chat_id)
        except ValueError:
            owner_id = 0
        log_relay_api_call(
            errors,
            owner_chat_id=owner_id,
            from_chat_id=key_from,
            message_id=key_msg,
            account=account,
        )
    return True


def _relay_allowlisted_message(
    message: dict,
    cfg: Config,
    errors: list[str],
) -> bool:
    """Переслать сообщение от acc (allowlist) владельцу через Bot API."""
    user_id = _message_from_user_id(message)
    if user_id is None or not is_allowlisted_user(user_id):
        return False

    msg_id = message.get("message_id")
    from_chat_id = _message_chat_id(message)
    if msg_id is None or from_chat_id is None:
        return False

    text = message.get("text")
    if isinstance(text, str) and text.strip() == "/start":
        return False

    acc = account_for_user_id(user_id) or ""
    ok = relay_message_to_owner_chat(
        cfg,
        from_chat_id=from_chat_id,
        message_id=int(msg_id),
        account=acc,
        errors=errors,
    )
    if ok and acc:
        errors.append(f"тг:relay:{acc}:msg={msg_id}")
    return ok


def _authorized_chat_id(message: dict, cfg: Config) -> bool:
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return False
    chat_id = chat.get("id")
    if chat_id is None:
        return False
    return str(chat_id).strip() == cfg.telegram_chat_id.strip()


def _send_message(
    cfg: Config,
    text: str,
    *,
    with_keyboard: bool = True,
    timeout_sec: float = 20.0,
) -> None:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    data: dict[str, str | bool] = {
        "chat_id": cfg.telegram_chat_id.strip(),
        "text": text,
    }
    if with_keyboard:
        data["reply_markup"] = _reply_keyboard_markup()
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data=data,
            timeout=timeout_sec,
            proxies=proxies,
        )
    except requests.RequestException as exc:
        raise TelegramControlError(
            f"Сетевой сбой sendMessage: {_mask_token(str(exc))}"
        ) from exc

    if resp.status_code != 200:
        detail = ""
        try:
            body = resp.json()
            if isinstance(body, dict):
                desc = body.get("description")
                if desc is not None and str(desc).strip():
                    detail = " " + str(desc).strip()
        except ValueError:
            pass
        raise TelegramControlError(
            f"sendMessage HTTP {resp.status_code}.{detail}"
        )

    try:
        body = resp.json()
    except ValueError as exc:
        raise TelegramControlError("sendMessage: не-JSON ответ.") from exc

    if not body.get("ok", False):
        desc = str(body.get("description") or "unknown error")
        raise TelegramControlError(f"sendMessage: {desc}")


_ACTION_LOG_RU = {
    _ACTION_PAUSE: "пауза",
    _ACTION_RESUME: "старт",
    _ACTION_STATUS: "статус",
}


def send_control_panel(cfg: Config) -> None:
    """Один раз при старте радара: «Поехали» + клавиатура управления."""
    _send_message(
        cfg,
        "Поехали",
    )


def _handle_action(
    action: str,
    cfg: Config,
    storage: ProjectStorage,
) -> None:
    interval = cfg.poll_interval_minutes
    if action == _ACTION_PAUSE:
        if storage.is_radar_paused():
            _send_message(cfg, "Уже на паузе.")
        else:
            storage.set_radar_paused(True)
            if cfg.radar_profile == "site":
                msg = "Site на паузе. FL/Kwork, TG и конвейер отключены."
            else:
                msg = "Dogfood на паузе. Карточки из Neon в @FLPARSINGBOT отключены."
            _send_message(cfg, msg)
        return

    if action == _ACTION_RESUME:
        if not storage.is_radar_paused():
            _send_message(cfg, "Радар уже активен.")
        else:
            storage.set_radar_paused(False)
            label = "Site" if cfg.radar_profile == "site" else "Dogfood"
            _send_message(
                cfg,
                f"{label} активен. Интервал опроса — {interval} мин.",
            )
        return

    if action == _ACTION_STATUS:
        _send_message(cfg, format_status_message(cfg, storage))


def poll_commands(cfg: Config, storage: ProjectStorage) -> list[str]:
    """
    Один короткий getUpdates; команды и кнопки из TELEGRAM_CHAT_ID.
    Возвращает список коротких строк для лога (без токена).
    """
    errors: list[str] = []
    bot_token = cfg.telegram_bot_token.strip()
    offset_initialized = storage.has_tg_update_offset_key(bot_token)
    offset = storage.get_tg_update_offset(bot_token=bot_token)
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/getUpdates"

    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.get(
            api_url,
            params={"offset": offset, "timeout": 0, "allowed_updates": '["message"]'},
            timeout=25.0,
            proxies=proxies,
        )
    except requests.RequestException as exc:
        errors.append(f"тг:бот:{_mask_token(type(exc).__name__ + ': ' + str(exc))[:200]}")
        return errors

    if resp.status_code != 200:
        errors.append(f"тг:бот:getUpdates HTTP {resp.status_code}")
        return errors

    try:
        body = resp.json()
    except ValueError:
        errors.append("тг:бот:getUpdates не-json")
        return errors

    if not body.get("ok", False):
        desc = str(body.get("description") or "unknown")
        errors.append(f"тг:бот:getUpdates {desc[:120]}")
        return errors

    updates = body.get("result")
    if not isinstance(updates, list):
        return errors

    next_offset = offset
    for upd in updates:
        if not isinstance(upd, dict):
            continue
        update_id = upd.get("update_id")
        if isinstance(update_id, int):
            next_offset = max(next_offset, update_id + 1)

    if not offset_initialized:
        storage.set_tg_update_offset(next_offset, bot_token=bot_token)
        if updates:
            bot_id = bot_token.split(":", 1)[0]
            errors.append(
                f"тг:offset:bootstrap bot={bot_id} offset={next_offset} skipped={len(updates)}"
            )
            return errors

    for upd in updates:
        if not isinstance(upd, dict):
            continue
        update_id = upd.get("update_id")

        message = upd.get("message")
        if not isinstance(message, dict):
            continue

        relay_user_id = _message_from_user_id(message)
        if relay_user_id is not None and is_allowlisted_user(relay_user_id):
            _relay_allowlisted_message(message, cfg, errors)
            continue

        if not _authorized_chat_id(message, cfg):
            continue

        text = message.get("text")
        if not isinstance(text, str):
            continue

        action = _resolve_action(text)
        if action is None:
            continue

        try:
            _handle_action(action, cfg, storage)
        except TelegramControlError as exc:
            errors.append(f"тг:бот:{_mask_token(str(exc))[:200]}")
        except Exception as exc:
            errors.append(f"тг:бот:{_mask_token(type(exc).__name__)}:{str(exc)[:120]}")
        else:
            if action == _ACTION_STATUS and isinstance(update_id, int):
                storage.set_tg_update_offset(update_id + 1, bot_token=bot_token)
                errors.append(f"тг:команда:статус update_id={update_id}")
            else:
                errors.append(f"тг:команда:{_ACTION_LOG_RU[action]}")
            if isinstance(update_id, int):
                next_offset = max(next_offset, update_id + 1)

    if next_offset > offset:
        storage.set_tg_update_offset(next_offset, bot_token=bot_token)

    return errors
