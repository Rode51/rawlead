"""Команды и кнопки паузы/статуса радара через Telegram Bot API (getUpdates)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time

import requests

from config import Config, _PROJECT_ROOT
from tg_proxy_pool import tg_http_request
from radar_status import format_status_message
from storage import ProjectStorage
from match_push import (
    handle_tg_draft_callback,
    handle_tg_nope_callback,
    upsert_subscriber_chat_id,
)
from premium_pay import (
    handle_owner_pay_callback,
    handle_user_pay_callback,
    pay_available,
    send_pay_method,
)
from stars_billing import (
    answer_pre_checkout,
    handle_successful_payment,
    stars_available,
)
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
_STOP_RADAR_CMDS = frozenset({"/stop-radar", "/stop_radar"})
_START_CMD = "/start"

BTN_PAUSE = "⏸ Пауза"
BTN_RESUME = "▶ Старт"
BTN_STOP = "🛑 Стоп"
BTN_STATUS = "ℹ Статус"

_ACTION_PAUSE = "pause"
_ACTION_RESUME = "resume"
_ACTION_STATUS = "status"
_ACTION_STOP_HARD = "stop_hard"

_WELCOME_SUBSCRIBER = "RawLead — лента заказов: https://rawlead.ru/lenta/"
_WELCOME_LOGIN = (
    "RawLead — откройте ссылку ниже, чтобы войти в кабинет на сайте."
)


class TelegramControlError(RuntimeError):
    """Ошибка опроса или ответа на команды в Telegram."""


def _mask_token(s: str) -> str:
    return _TELEGRAM_BOT_IN_PATH.sub(r"\1***MASKED***\2", s)


def _admin_user_ids() -> frozenset[int]:
    raw = os.environ.get("TELEGRAM_ADMIN_USER_IDS", "").strip()
    if not raw:
        return frozenset()
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return frozenset(out)


def is_radar_admin(user_id: int | None, chat_id: int | None, cfg: Config) -> bool:
    """Admin = TELEGRAM_CHAT_ID (+ опц. TELEGRAM_ADMIN_USER_IDS)."""
    owner_chat = cfg.telegram_chat_id.strip()
    if not owner_chat or chat_id is None:
        return False
    if str(chat_id).strip() != owner_chat:
        return False
    allowed_users = _admin_user_ids()
    if not allowed_users:
        return True
    if user_id is None:
        return False
    return int(user_id) in allowed_users


def _reply_keyboard_markup() -> str:
    markup = {
        "keyboard": [
            [{"text": BTN_PAUSE}, {"text": BTN_RESUME}],
            [{"text": BTN_STOP}, {"text": BTN_STATUS}],
        ],
        "resize_keyboard": True,
    }
    return json.dumps(markup, ensure_ascii=False, separators=(",", ":"))


def _remove_keyboard_markup() -> str:
    return json.dumps({"remove_keyboard": True}, separators=(",", ":"))


def _inline_url_markup(url: str, label: str) -> str:
    markup = {"inline_keyboard": [[{"text": label, "url": url}]]}
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
    if cmd in _STOP_RADAR_CMDS:
        return _ACTION_STOP_HARD
    if s == BTN_PAUSE:
        return _ACTION_PAUSE
    if s == BTN_RESUME:
        return _ACTION_RESUME
    if s == BTN_STOP:
        return _ACTION_STOP_HARD
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

    owner_chat_id = cfg.telegram_chat_id.strip()
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/forwardMessage"

    try:
        session = requests.Session()
        session.trust_env = False
        resp = tg_http_request(
            "POST",
            api_url,
            session=session,
            data={
                "chat_id": owner_chat_id,
                "from_chat_id": str(key_from),
                "message_id": str(key_msg),
            },
            timeout=timeout_sec,
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
    if isinstance(text, str) and text.strip().casefold().startswith(_START_CMD):
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


def _send_to_chat(
    cfg: Config,
    chat_id: int | str,
    text: str,
    *,
    with_admin_keyboard: bool = False,
    remove_keyboard: bool = False,
    reply_markup: str | None = None,
    timeout_sec: float = 20.0,
) -> None:
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    data: dict[str, str | bool] = {
        "chat_id": str(chat_id).strip(),
        "text": text,
    }
    if reply_markup is not None:
        data["reply_markup"] = reply_markup
    elif with_admin_keyboard:
        data["reply_markup"] = _reply_keyboard_markup()
    elif remove_keyboard:
        data["reply_markup"] = _remove_keyboard_markup()
    try:
        session = requests.Session()
        session.trust_env = False
        resp = tg_http_request(
            "POST",
            api_url,
            session=session,
            data=data,
            timeout=timeout_sec,
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


def _send_message(
    cfg: Config,
    text: str,
    *,
    with_keyboard: bool = True,
    timeout_sec: float = 20.0,
) -> None:
    _send_to_chat(
        cfg,
        cfg.telegram_chat_id.strip(),
        text,
        with_admin_keyboard=with_keyboard,
        timeout_sec=timeout_sec,
    )


def _radar_ctl_script() -> os.PathLike[str] | None:
    script = _PROJECT_ROOT / "deploy" / "radar-ctl.sh"
    return script if script.is_file() else None


_UNIT_STATES_OK = frozenset(
    {"active", "inactive", "failed", "dead", "activating", "deactivating"}
)


def _run_radar_ctl(cfg: Config, cmd: str) -> tuple[bool, str]:
    script = _radar_ctl_script()
    profile = cfg.radar_profile.strip().lower() or "site"
    if script is None:
        return False, "radar-ctl.sh не найден (ожидается VPS)."
    try:
        proc = subprocess.run(
            ["sudo", str(script), cmd, profile],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)[:160]
    out = (proc.stdout or proc.stderr or "").strip()
    state = out.lower()
    if cmd == "status":
        if state in _UNIT_STATES_OK:
            return True, state
        if state:
            return True, state
        detail = out or f"exit {proc.returncode}"
        return False, detail[:200]
    if proc.returncode != 0:
        detail = out or f"exit {proc.returncode}"
        return False, detail[:200]
    return True, out or "ok"


def _unit_label(cfg: Config) -> str:
    return "Site" if cfg.radar_profile == "site" else "Dogfood"


_ACTION_LOG_RU = {
    _ACTION_PAUSE: "пауза",
    _ACTION_RESUME: "старт",
    _ACTION_STATUS: "статус",
    _ACTION_STOP_HARD: "стоп",
}

_ACK_RU = {
    _ACTION_PAUSE: "✓ Принято: пауза",
    _ACTION_RESUME: "✓ Принято: старт",
    _ACTION_STATUS: "✓ Секунду…",
    _ACTION_STOP_HARD: "✓ Принято: останавливаю радар…",
}


def send_control_panel(cfg: Config) -> None:
    """Один раз при старте радара: «Поехали» + клавиатура управления (только владельцу)."""
    _send_message(cfg, "Поехали")


def _send_admin_ack(cfg: Config, action: str) -> None:
    msg = _ACK_RU.get(action)
    if msg:
        _send_message(cfg, msg)


def _handle_action(
    action: str,
    cfg: Config,
    storage: ProjectStorage,
) -> None:
    interval = cfg.poll_interval_minutes
    label = _unit_label(cfg)

    if action == _ACTION_STOP_HARD:
        ok, detail = _run_radar_ctl(cfg, "stop")
        if ok:
            storage.set_radar_paused(True)
            try:
                _send_message(
                    cfg,
                    f"{label}: процесс остановлен (systemd stop). {detail}",
                )
            except TelegramControlError:
                pass
        else:
            _send_message(cfg, f"{label}: не удалось остановить процесс. {detail}")
        return

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
        unit_ok, unit_state = _run_radar_ctl(cfg, "status")
        us = unit_state.strip().lower() if unit_ok else ""
        if us != "active":
            started, start_detail = _run_radar_ctl(cfg, "start")
            if started:
                storage.set_radar_paused(False)
                _send_message(
                    cfg,
                    f"{label}: процесс запущен (systemd start). {start_detail}",
                )
                return
            _send_message(cfg, f"{label}: не удалось запустить процесс. {start_detail}")
            return

        if not storage.is_radar_paused():
            _send_message(cfg, "Радар уже активен.")
        else:
            storage.set_radar_paused(False)
            _send_message(
                cfg,
                f"{label} активен. Интервал опроса — {interval} мин.",
            )
        return

    if action == _ACTION_STATUS:
        unit_ok, unit_state = _run_radar_ctl(cfg, "status")
        us = unit_state.strip() if unit_ok else None
        body = format_status_message(cfg, storage, unit_state=us)
        _send_message(cfg, body)


def _start_raw_payload(text: str) -> str:
    parts = (text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


def _start_payload(text: str) -> str:
    return _start_raw_payload(text).casefold()


def _handle_bot_login_link(
    cfg: Config,
    message: dict,
    *,
    chat_id: int,
    user_id: int,
    errors: list[str],
) -> bool:
    from_user = message.get("from") if isinstance(message.get("from"), dict) else {}
    username = str(from_user.get("username") or "").strip() or None
    first_name = str(from_user.get("first_name") or "").strip() or None
    try:
        from bot_auth import mint_bot_first_login_url

        return_url = mint_bot_first_login_url(
            tg_user_id=int(user_id),
            tg_chat_id=int(chat_id),
            username=username,
            first_name=first_name,
            photo_url=None,
        )
        upsert_subscriber_chat_id(
            cfg.database_url,
            tg_user_id=int(user_id),
            tg_chat_id=int(chat_id),
        )
    except Exception as exc:
        errors.append(f"bot_login:err {type(exc).__name__}:{str(exc)[:80]}")
        return True

    errors.append("bot_login:ok")
    try:
        _send_to_chat(
            cfg,
            chat_id,
            _WELCOME_LOGIN,
            reply_markup=_inline_url_markup(return_url, "Открыть кабинет"),
        )
    except TelegramControlError:
        pass
    return True


_BOT_AUTH_FAIL_RU: dict[str, str] = {
    "session expired": (
        "Сессия входа истекла. Вернитесь на сайт и нажмите «Войти через Telegram» снова."
    ),
    "session consumed": "Эта ссылка уже использована. Получите новый QR на сайте.",
    "session not found": "Ссылка входа недействительна. Получите новый QR на сайте.",
    "session bound to another user": (
        "Сессия привязана к другому аккаунту. Начните вход заново на сайте."
    ),
    "db error": (
        "Ошибка сервера при входе. Попробуйте через минуту или напишите в поддержку."
    ),
    "empty token": "Ошибка входа. Получите новый QR на сайте.",
}
_BOT_AUTH_FAIL_DEFAULT = "Не удалось подтвердить вход. Вернитесь на сайт и попробуйте снова."


def _bot_auth_fail_message(err: str) -> str:
    key = (err or "").strip().casefold()
    return _BOT_AUTH_FAIL_RU.get(key, _BOT_AUTH_FAIL_DEFAULT)


def _handle_bot_auth_start(
    cfg: Config,
    message: dict,
    *,
    auth_token: str,
    chat_id: int,
    user_id: int,
    errors: list[str],
) -> bool:
    from_user = message.get("from") if isinstance(message.get("from"), dict) else {}
    username = str(from_user.get("username") or "").strip() or None
    first_name = str(from_user.get("first_name") or "").strip() or None
    photo_url = None
    try:
        from bot_auth import authorize_bot_auth_session

        ok, return_url, err = authorize_bot_auth_session(
            auth_token=auth_token,
            tg_user_id=int(user_id),
            tg_chat_id=int(chat_id),
            username=username,
            first_name=first_name,
            photo_url=photo_url,
        )
    except Exception as exc:
        errors.append(f"bot_auth:err {type(exc).__name__}:{str(exc)[:80]}")
        try:
            _send_to_chat(cfg, chat_id, _bot_auth_fail_message("db error"))
        except TelegramControlError:
            pass
        return True

    if not ok:
        errors.append(f"bot_auth:fail {err[:80]}")
        try:
            _send_to_chat(cfg, chat_id, _bot_auth_fail_message(err))
        except TelegramControlError:
            pass
        return True

    upsert_subscriber_chat_id(
        cfg.database_url,
        tg_user_id=int(user_id),
        tg_chat_id=int(chat_id),
    )
    errors.append("bot_auth:ok")
    try:
        _send_to_chat(
            cfg,
            chat_id,
            "✓ Вход подтверждён. Нажмите кнопку ниже, чтобы вернуться в кабинет.",
            reply_markup=_inline_url_markup(return_url, "Вернуться на сайт"),
        )
    except TelegramControlError:
        pass
    return True


def _resolve_pay_start_payload(payload: str) -> str:
    """start=pay_sbp|pay_crypto|pay_stars|pay|stars → method key."""
    p = payload.strip().casefold()
    if p in ("pay_sbp", "sbp"):
        return "sbp"
    if p in ("pay_crypto", "crypto"):
        return "crypto"
    if p in ("pay_stars", "stars"):
        return "stars"
    if p in ("pay", ""):
        return "menu"
    return ""


def _send_pay_flow(
    cfg: Config,
    chat_id: int,
    user_id: int,
    errors: list[str],
    *,
    method: str = "menu",
) -> None:
    """O174b: оплата только на сайте (ЮKassa)."""
    del method, user_id
    try:
        _send_to_chat(
            cfg,
            chat_id,
            "Оплата Premium — на сайте:\nhttps://rawlead.ru/pricing\n\n"
            "Trial 1 ₽ / 3 дня · далее 790 ₽/мес.",
            reply_markup=_inline_url_markup(
                "https://rawlead.ru/pricing",
                "Открыть тарифы →",
            ),
        )
    except TelegramControlError:
        pass


def _handle_subscriber_message(
    message: dict,
    cfg: Config,
    text: str,
    errors: list[str],
    *,
    is_admin: bool,
) -> bool:
    """/start · /pay · оплата — для всех (в т.ч. владелец TELEGRAM_CHAT_ID)."""
    chat_id = _message_chat_id(message)
    user_id = _message_from_user_id(message)
    if chat_id is None or user_id is None:
        return True

    cmd = _normalize_command(text)
    if cmd in ("/login", "/cabinet"):
        return _handle_bot_login_link(
            cfg,
            message,
            chat_id=int(chat_id),
            user_id=int(user_id),
            errors=errors,
        )

    if cmd == _START_CMD:
        raw_payload = _start_raw_payload(text)
        if raw_payload.lower().startswith("auth_"):
            token = raw_payload[5:]
            if token:
                return _handle_bot_auth_start(
                    cfg,
                    message,
                    auth_token=token,
                    chat_id=int(chat_id),
                    user_id=int(user_id),
                    errors=errors,
                )
        upsert_subscriber_chat_id(
            cfg.database_url,
            tg_user_id=int(user_id),
            tg_chat_id=int(chat_id),
        )
        payload = _start_payload(text)
        try:
            if payload == "login":
                return _handle_bot_login_link(
                    cfg,
                    message,
                    chat_id=int(chat_id),
                    user_id=int(user_id),
                    errors=errors,
                )
            elif payload.startswith("pay") or payload == "stars":
                pay_method = _resolve_pay_start_payload(payload)
                _send_pay_flow(cfg, chat_id, int(user_id), errors, method=pay_method or "menu")
            else:
                _send_to_chat(cfg, chat_id, _WELCOME_SUBSCRIBER, remove_keyboard=True)
        except TelegramControlError:
            pass
        return True

    if cmd == "/pay":
        _send_pay_flow(cfg, chat_id, int(user_id), errors, method="menu")
        return True
    if cmd == "/stars":
        _send_pay_flow(cfg, chat_id, int(user_id), errors, method="stars")
        return True

    payment = message.get("successful_payment")
    if isinstance(payment, dict):
        handle_successful_payment(
            cfg,
            tg_user_id=int(user_id),
            tg_chat_id=int(chat_id),
            payment=payment,
            errors=errors,
        )
        try:
            _send_to_chat(
                cfg,
                chat_id,
                "✓ Оплата принята. Доступ к ленте и L2 активен.",
                remove_keyboard=True,
            )
        except TelegramControlError:
            pass
        return True

    if not is_admin and _resolve_action(text) is not None:
        return True

    return False


def _handle_non_admin_message(
    message: dict,
    cfg: Config,
    text: str,
    errors: list[str],
) -> bool:
    """Legacy wrapper."""
    return _handle_subscriber_message(
        message, cfg, text, errors, is_admin=False
    )


def ensure_bot_polling_mode(cfg: Config) -> list[str]:
    """O55c: webhook блокирует getUpdates — сброс при старте bot-poll."""
    lines: list[str] = []
    token = cfg.telegram_bot_token.strip()
    if not token:
        lines.append("тг:webhook:skip no_token")
        return lines

    base = f"https://api.telegram.org/bot{token}/"
    try:
        session = requests.Session()
        session.trust_env = False
        info_resp = tg_http_request(
            "GET",
            base + "getWebhookInfo",
            session=session,
            timeout=15.0,
        )
        if info_resp.status_code != 200:
            lines.append(f"тг:webhook:info HTTP {info_resp.status_code}")
            return lines
        info = info_resp.json()
        if not info.get("ok"):
            lines.append("тг:webhook:info not ok")
            return lines
        url = str((info.get("result") or {}).get("url") or "").strip()
        if not url:
            lines.append("тг:webhook:none")
            return lines
        del_resp = tg_http_request(
            "POST",
            base + "deleteWebhook",
            session=session,
            data={"drop_pending_updates": "false"},
            timeout=15.0,
        )
        if del_resp.status_code == 200 and del_resp.json().get("ok"):
            lines.append("тг:webhook:deleted")
        else:
            lines.append(f"тг:webhook:delete HTTP {del_resp.status_code}")
    except requests.RequestException as exc:
        lines.append(f"тг:webhook:err {type(exc).__name__}")
    return lines


def poll_commands(cfg: Config, storage: ProjectStorage) -> list[str]:
    """
    Один короткий getUpdates; admin-команды только из TELEGRAM_CHAT_ID.
    Возвращает список коротких строк для лога (без токена).
    """
    errors: list[str] = []
    bot_token = cfg.telegram_bot_token.strip()
    offset_initialized = storage.has_tg_update_offset_key(bot_token)
    offset = storage.get_tg_update_offset(bot_token=bot_token)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/getUpdates"

    try:
        session = requests.Session()
        session.trust_env = False
        resp = tg_http_request(
            "GET",
            api_url,
            session=session,
            params={
                "offset": offset,
                "timeout": 0,
                "allowed_updates": '["message","callback_query","pre_checkout_query"]',
            },
            timeout=25.0,
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

        callback_query = upd.get("callback_query")
        if isinstance(callback_query, dict):
            if handle_tg_nope_callback(cfg, callback_query, errors):
                if isinstance(update_id, int):
                    next_offset = max(next_offset, update_id + 1)
                continue
            if handle_tg_draft_callback(cfg, callback_query, errors):
                if isinstance(update_id, int):
                    next_offset = max(next_offset, update_id + 1)
                continue
            if handle_user_pay_callback(cfg, callback_query, errors):
                if isinstance(update_id, int):
                    next_offset = max(next_offset, update_id + 1)
                continue
            if handle_owner_pay_callback(cfg, callback_query, errors):
                if isinstance(update_id, int):
                    next_offset = max(next_offset, update_id + 1)
                continue

        pre_checkout = upd.get("pre_checkout_query")
        if isinstance(pre_checkout, dict):
            qid = pre_checkout.get("id")
            if qid is not None:
                answer_pre_checkout(cfg, str(qid), ok=stars_available(cfg))
            if isinstance(update_id, int):
                next_offset = max(next_offset, update_id + 1)
            continue

        message = upd.get("message")
        if not isinstance(message, dict):
            continue

        relay_user_id = _message_from_user_id(message)
        if relay_user_id is not None and is_allowlisted_user(relay_user_id):
            _relay_allowlisted_message(message, cfg, errors)
            continue

        user_id = _message_from_user_id(message)
        chat_id = _message_chat_id(message)
        text = message.get("text")
        if not isinstance(text, str):
            text = ""

        admin = is_radar_admin(user_id, chat_id, cfg)
        if _handle_subscriber_message(message, cfg, text, errors, is_admin=admin):
            if isinstance(update_id, int):
                next_offset = max(next_offset, update_id + 1)
            continue

        if not admin:
            continue

        action = _resolve_action(text)
        if action is None:
            try:
                _send_message(
                    cfg,
                    "Не понял. Кнопки: ⏸ Пауза · ▶ Старт · 🛑 Стоп · ℹ Статус",
                )
            except TelegramControlError as exc:
                errors.append(f"тг:бот:{_mask_token(str(exc))[:200]}")
            if isinstance(update_id, int):
                next_offset = max(next_offset, update_id + 1)
            continue

        try:
            _send_admin_ack(cfg, action)
        except TelegramControlError as exc:
            errors.append(f"тг:бот:ack:{_mask_token(str(exc))[:120]}")

        # stop гасит systemd unit — offset нужно сохранить до systemctl stop.
        if action == _ACTION_STOP_HARD and isinstance(update_id, int):
            storage.set_tg_update_offset(update_id + 1, bot_token=bot_token)

        try:
            _handle_action(action, cfg, storage)
        except TelegramControlError as exc:
            errors.append(f"тг:бот:{_mask_token(str(exc))[:200]}")
            try:
                _send_message(cfg, f"Ошибка команды: {str(exc)[:160]}")
            except TelegramControlError:
                pass
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
