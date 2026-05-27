"""Проверка мониторингового аккаунта (+66) и алерт владельцу через бота."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from config import (
    Config,
    _PROJECT_ROOT,
    load_config,
    load_radar_env,
    radar_lock_path,
    radar_timestamp,
    telegram_requests_proxies,
)
from storage import ProjectStorage

_DEFAULT_CHECK_MIN = 15
_DEFAULT_ALERT_COOLDOWN_MIN = 60
_TG_MONITOR_PULSE_KEY = "tg_monitor_last_pulse"
_TG_MONITOR_START_KEY = "tg_monitor_started_at"
# tg_main: пульс раз в 120 с; порог = 2× интервал + запас
_TG_MONITOR_PULSE_MAX_AGE_SEC = 300
# После тг:старт — не считать старый пульс и не слать алерт (гонка с main)
_TG_MONITOR_WARMUP_SEC = 300


@dataclass(frozen=True)
class TelethonHealthResult:
    ok: bool
    account_label: str
    detail: str


def _check_interval_sec() -> int:
    raw = os.environ.get("HEALTH_CHECK_MINUTES", "").strip()
    if not raw:
        return _DEFAULT_CHECK_MIN * 60
    try:
        return max(60, int(raw) * 60)
    except ValueError:
        return _DEFAULT_CHECK_MIN * 60


def _alert_cooldown_sec() -> int:
    raw = os.environ.get("HEALTH_ALERT_COOLDOWN_MINUTES", "").strip()
    if not raw:
        return _DEFAULT_ALERT_COOLDOWN_MIN * 60
    try:
        return max(300, int(raw) * 60)
    except ValueError:
        return _DEFAULT_ALERT_COOLDOWN_MIN * 60


def _tg_main_lock_path() -> Path:
    load_radar_env()
    return radar_lock_path("tg_main")


def is_tg_monitor_active() -> bool:
    """Окно tg_main держит lock-файл — вторая сессия Telethon даст database is locked."""
    lock_path = _tg_main_lock_path()
    if not lock_path.is_file():
        return False
    if sys.platform != "win32":
        return True
    try:
        import msvcrt
    except ImportError:
        return True
    try:
        fh = open(lock_path, "a+b")
    except OSError:
        return False
    try:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        return False
    except OSError:
        return True
    finally:
        fh.close()


def mark_tg_monitor_started(storage: ProjectStorage) -> None:
    """Сбросить устаревший пульс и начать окно прогрева (тг:старт)."""
    now = int(time.time())
    storage.set_setting(_TG_MONITOR_START_KEY, str(now))
    storage.set_setting(_TG_MONITOR_PULSE_KEY, "0")


def write_tg_monitor_pulse(storage: ProjectStorage) -> None:
    storage.set_setting(_TG_MONITOR_PULSE_KEY, str(int(time.time())))


def tg_monitor_warmup_remaining_sec(storage: ProjectStorage) -> int:
    """Секунд до конца прогрева после тг:старт (0 — прогрев закончился)."""
    raw = storage.get_setting(_TG_MONITOR_START_KEY, "0").strip()
    try:
        started = float(raw)
    except ValueError:
        started = 0.0
    if started <= 0:
        return 0
    return max(0, int(_TG_MONITOR_WARMUP_SEC - (time.time() - started)))


def check_tg_monitor_pulse(storage: ProjectStorage) -> TelethonHealthResult:
    """Пока tg_main держит .session — проверяем свежий пульс, без второго connect."""
    label = account_label_from_env()
    raw = storage.get_setting(_TG_MONITOR_PULSE_KEY, "0").strip()
    try:
        last_pulse = float(raw)
    except ValueError:
        last_pulse = 0.0
    age = time.time() - last_pulse
    if last_pulse > 0 and age <= _TG_MONITOR_PULSE_MAX_AGE_SEC:
        return TelethonHealthResult(
            True,
            label,
            f"монитор активен (пульс {int(age)}с назад)",
        )
    warmup = tg_monitor_warmup_remaining_sec(storage)
    if warmup > 0:
        return TelethonHealthResult(
            True,
            label,
            f"прогрев после старта (~{warmup}с, пульс обновится)",
        )
    if last_pulse <= 0:
        detail = "монитор запущен, пульс ещё не записан"
    else:
        detail = f"монитор не пульсирует ({int(age)}с без пульса)"
    return TelethonHealthResult(False, label, detail)


def try_release_stale_tg_main_lock() -> bool:
    """Удалить .tg_main.lock, если процесс tg_main уже не держит его."""
    if is_tg_monitor_active():
        return False
    try:
        _tg_main_lock_path().unlink(missing_ok=True)
        return True
    except OSError:
        return False


def account_label_from_env() -> str:
    raw = os.environ.get("TELETHON_SESSION_PATH", "").strip()
    if not raw:
        return "мониторинговый аккаунт"
    name = Path(raw).name
    if name.endswith("_telethon"):
        name = name[: -len("_telethon")]
    return name or "мониторинговый аккаунт"


async def check_telethon_account() -> TelethonHealthResult:
    """Подключение Telethon + get_me; не бросает наружу."""
    label = account_label_from_env()
    try:
        from tg_client import create_client
    except Exception as exc:
        return TelethonHealthResult(False, label, f"Telethon: {exc}")

    client = None
    try:
        client = create_client()
        await client.connect()
        if not await client.is_user_authorized():
            return TelethonHealthResult(
                False, label, "сессия не авторизована (нужен вход через софт продавца)"
            )
        me = await client.get_me()
        phone = (getattr(me, "phone", None) or "").strip()
        username = (getattr(me, "username", None) or "").strip()
        who = phone or (f"@{username}" if username else "id без телефона")
        return TelethonHealthResult(True, label, who)
    except Exception as exc:
        return TelethonHealthResult(False, label, f"{type(exc).__name__}: {exc}")
    finally:
        if client is not None:
            try:
                await client.disconnect()
            except Exception:
                pass


def _issue_key(result: TelethonHealthResult) -> str:
    if result.ok:
        return "ok"
    return f"fail:{result.detail[:120]}"


def _append_log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")


def send_owner_text(cfg: Config, text: str) -> tuple[bool, str]:
    """sendMessage без кнопок. Возвращает (успех, деталь ошибки)."""
    proxies = telegram_requests_proxies(cfg)
    url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            url,
            data={
                "chat_id": cfg.telegram_chat_id.strip(),
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=25.0,
            proxies=proxies,
        )
    except requests.RequestException as exc:
        return False, f"сеть: {exc}"

    if resp.status_code != 200:
        detail = ""
        try:
            body = resp.json()
            if isinstance(body, dict):
                desc = body.get("description")
                if isinstance(desc, str):
                    detail = desc.strip()
        except ValueError:
            pass
        return False, f"HTTP {resp.status_code} {detail}".strip()

    return True, ""


def _format_fail_message(result: TelethonHealthResult) -> str:
    return (
        f"⚠️ Аккаунт {result.account_label} не отвечает\n\n"
        f"Причина: {result.detail}\n\n"
        "Проверь: прокси TELETHON_PROXY_ACC*, TELETHON_PROXY_PROBE, файл сессии, "
        "stop-radar.bat → start-radar.bat."
    )


def _format_ok_message(result: TelethonHealthResult) -> str:
    return (
        f"✅ Аккаунт {result.account_label} снова на связи\n"
        f"({result.detail})"
    )


def run_health_check(
    cfg: Config,
    storage: ProjectStorage,
    *,
    log_path: Path,
    force: bool = False,
) -> TelethonHealthResult:
    """
    Проверка по расписанию (HEALTH_CHECK_MINUTES) или force=True.
    При сбое — сообщение боту (с cooldown).
    """
    now = time.time()
    interval = _check_interval_sec()
    last_raw = storage.get_setting("health_check_last_run", "0")
    try:
        last_run = float(last_raw)
    except ValueError:
        last_run = 0.0

    if not force and now - last_run < interval:
        return TelethonHealthResult(True, account_label_from_env(), "пропуск:рано")

    try:
        if is_tg_monitor_active():
            result = check_tg_monitor_pulse(storage)
        else:
            result = asyncio.run(check_telethon_account())
    except SystemExit:
        result = TelethonHealthResult(
            False,
            account_label_from_env(),
            "не заданы TELETHON_* в .env",
        )
    storage.set_setting("health_check_last_run", str(int(now)))

    ts = radar_timestamp()
    if result.ok:
        _append_log(
            log_path,
            f"{ts} здравье:ок акк={result.account_label} {result.detail}",
        )
    else:
        _append_log(
            log_path,
            f"{ts} здравье:сбой акк={result.account_label} {result.detail}",
        )

    prev_ok = storage.get_setting("health_check_last_ok", "1") == "1"
    issue = _issue_key(result)
    last_alert_issue = storage.get_setting("health_check_last_alert_issue", "")
    last_alert_at_raw = storage.get_setting("health_check_last_alert_at", "0")
    try:
        last_alert_at = float(last_alert_at_raw)
    except ValueError:
        last_alert_at = 0.0

    cooldown = _alert_cooldown_sec()
    should_alert = False
    text = ""

    if not result.ok:
        if issue != last_alert_issue or now - last_alert_at >= cooldown:
            should_alert = True
            text = _format_fail_message(result)
    elif not prev_ok and result.ok:
        should_alert = True
        text = _format_ok_message(result)

    if should_alert and text:
        ok_send, err = send_owner_text(cfg, text)
        if ok_send:
            storage.set_setting("health_check_last_alert_issue", issue)
            storage.set_setting("health_check_last_alert_at", str(int(now)))
            _append_log(log_path, f"{ts} здравье:уведомление отправлено")
        else:
            _append_log(log_path, f"{ts} здравье:уведомление не отправлено {err}")

    storage.set_setting("health_check_last_ok", "1" if result.ok else "0")
    return result


def run_cli() -> int:
    cfg = load_config()
    from storage import storage_from_config

    storage = storage_from_config(cfg)
    result = run_health_check(cfg, storage, log_path=cfg.radar_log_path, force=True)
    if result.ok:
        print(f"OK: {result.account_label} — {result.detail}")
        return 0
    print(f"FAIL: {result.account_label} — {result.detail}")
    return 1
