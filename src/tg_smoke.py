"""Проверка цепочки Telegram так же, как радар: `load_config()` + getMe + getUpdates + sendMessage.

Запуск из корня репозитория (как `python src/main.py`):

    python src/tg_smoke.py

То же через main:

    python src/main.py --telegram-smoke
"""

from __future__ import annotations

import re
import sys
from typing import Any

import requests

from config import load_config, telegram_requests_proxies


def _tg_json(resp: requests.Response) -> dict[str, Any] | None:
    try:
        out = resp.json()
    except ValueError:
        return None
    return out if isinstance(out, dict) else None


def _api_line(resp: requests.Response, data: dict[str, Any] | None) -> str:
    if data is None:
        return f"HTTP {resp.status_code}, тело ответа не JSON."
    if not data.get("ok", False):
        desc = data.get("description")
        if isinstance(desc, str) and desc.strip():
            return f"HTTP {resp.status_code}: {desc.strip()}"
        return f"HTTP {resp.status_code}: ok=false (нет description в JSON)"
    return f"HTTP {resp.status_code}, ok=true"


def _mask_bot_token_in_text(s: str) -> str:
    return re.sub(r"/bot[^/\s]+", "/bot***MASKED***", s.replace("\n", " "))


def _network_err_hint(exc: requests.RequestException) -> str:
    msg = _mask_bot_token_in_text(str(exc))
    if "proxy" in msg.lower() or isinstance(exc, requests.exceptions.ProxyError):
        return (
            f"Сетевой сбой через TG_PROXY_URL: {msg}\n"
            "Проверьте: хост/порт/логин/пароль в `.env`, прокси доступен с этого ПК, "
            "системный VPN выключен (Bot API ходит только через TG_PROXY_URL)."
        )
    return f"Сетевой сбой Bot API: {msg}"


def _tg_request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    proxies: dict[str, str],
    **kwargs: Any,
) -> requests.Response | None:
    try:
        return session.request(method, url, proxies=proxies, **kwargs)
    except requests.RequestException as exc:
        print(_network_err_hint(exc), file=sys.stderr, flush=True)
        return None


def run_smoke() -> int:
    print("Загрузка конфигурации (файл `.env` в корне репозитория)…", flush=True)
    try:
        cfg = load_config()
    except ValueError as exc:
        print(str(exc), file=sys.stderr, flush=True)
        print(
            "\nПодсказка: откройте `.env` в корне репозитория. "
            "Обязательны TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TG_PROXY_URL — без кавычек "
            "и без пробелов в начале/конце строки.",
            file=sys.stderr,
            flush=True,
        )
        return 2

    token = cfg.telegram_bot_token
    chat_id = cfg.telegram_chat_id
    base = f"https://api.telegram.org/bot{token}/"

    cid = chat_id.strip()
    if re.fullmatch(r"-?\d+", cid):
        print(
            f"   Конфиг: TELEGRAM_CHAT_ID — {len(cid)} символов (только цифры, формат ок).",
            flush=True,
        )
    if not re.fullmatch(r"-?\d+", cid):
        print(
            "Предупреждение: TELEGRAM_CHAT_ID должен быть числом (для лички — ваш user id, "
            "часто 9–10 цифр; для супергруппы — отрицательное число). "
            "Без @, без букв, без кавычек в `.env`.",
            file=sys.stderr,
            flush=True,
        )

    session = requests.Session()
    session.trust_env = False
    proxies = telegram_requests_proxies(cfg)
    print("   Telegram: запросы только через TG_PROXY_URL из `.env`.", flush=True)

    print("1) getMe …", flush=True)
    r = _tg_request(session, "GET", f"{base}getMe", proxies=proxies, timeout=30)
    if r is None:
        return 1
    j = _tg_json(r)
    if not (j and j.get("ok")):
        print(_api_line(r, j), file=sys.stderr, flush=True)
        if r.status_code == 401 or (isinstance(j, dict) and j.get("error_code") == 401):
            print(
                "401 Unauthorized: токен не принят API. "
                "В Telegram откройте @BotFather → выберите бота → API Token — "
                "тот же токен должен быть в строке TELEGRAM_BOT_TOKEN в `.env`. "
                "Если токен отзывали — выпустите новый и вставьте в `.env`, сохраните файл.",
                file=sys.stderr,
                flush=True,
            )
        return 1

    result = j.get("result") if j else None
    hint_bot = ""
    bot_username = ""
    if isinstance(result, dict):
        u = result.get("username")
        if isinstance(u, str) and u.strip():
            bot_username = u.strip().lstrip("@")
            hint_bot = f" @{bot_username}"
    print(f"   getMe: ок, бот{hint_bot}", flush=True)
    if bot_username:
        print(f"   Ссылка на бота: https://t.me/{bot_username}", flush=True)

    print("2) getUpdates (limit=5) …", flush=True)
    r2 = _tg_request(
        session,
        "GET",
        f"{base}getUpdates",
        proxies=proxies,
        params={"limit": 5, "timeout": 0},
        timeout=35,
    )
    if r2 is None:
        return 1
    j2 = _tg_json(r2)
    if not (j2 and j2.get("ok")):
        print(_api_line(r2, j2), file=sys.stderr, flush=True)
        return 1
    updates = j2.get("result")
    n = len(updates) if isinstance(updates, list) else 0
    print(f"   getUpdates: записей в ответе: {n}", flush=True)
    if n == 0:
        print(
            "   Подсказка: пустой getUpdates — бот пока не получил входящих апдейтов "
            "(или их уже «забрал» другой клиент с этим токеном). "
            "Откройте ссылку на бота выше → «Запустить»/«Start» с того аккаунта, "
            "чей id в TELEGRAM_CHAT_ID в `.env`; затем снова: python src/tg_smoke.py",
            flush=True,
        )

    wh = _tg_request(
        session, "GET", f"{base}getWebhookInfo", proxies=proxies, timeout=15
    )
    whj = _tg_json(wh) if wh is not None else None
    if whj and whj.get("ok") and isinstance(whj.get("result"), dict):
        wurl = whj["result"].get("url")
        if isinstance(wurl, str) and wurl.strip():
            print(
                "   Заметка: у бота настроен webhook — getUpdates часто пустой; "
                "на sendMessage это обычно не мешает. Если гоняли эксперименты — сбросьте webhook "
                "(Bot API deleteWebhook или новый токен в BotFather).",
                flush=True,
            )

    print("3) sendMessage в TELEGRAM_CHAT_ID из `.env` …", flush=True)
    send_chat: str | int = chat_id
    if re.fullmatch(r"-?\d+", cid):
        send_chat = int(cid)

    r3 = _tg_request(
        session,
        "POST",
        f"{base}sendMessage",
        proxies=proxies,
        data={
            "chat_id": send_chat,
            "text": (
                "FL Radar: тестовая отправка (проверка tg_smoke). "
                "Если видите это — sendMessage вернулся успешно."
            ),
            "disable_notification": True,
        },
        timeout=30,
    )
    if r3 is None:
        return 1
    j3 = _tg_json(r3)
    if not (j3 and j3.get("ok")):
        print(_api_line(r3, j3), file=sys.stderr, flush=True)
        desc_l = ""
        if j3 and isinstance(j3.get("description"), str):
            desc_l = j3["description"].lower()
        if "chat not found" in desc_l or "chat_id is empty" in desc_l:
            print(
                "Частая причина: TELEGRAM_CHAT_ID не совпадает с аккаунтом, который открыл чат с ботом, "
                "или в `.env` не тот числовой id.",
                file=sys.stderr,
                flush=True,
            )
            print(
                "Что сделать: 1) С того аккаунта, куда хотите уведомления, напишите боту "
                "@userinfobot любое сообщение — он покажет ваш Id (число). "
                "2) Вставьте только это число в строку TELEGRAM_CHAT_ID в `.env` (без кавычек). "
                "3) Откройте «Ссылка на бота» из вывода шага 1 и нажмите Start. "
                "4) Снова запустите smoke.",
                file=sys.stderr,
                flush=True,
            )
        if r3.status_code == 403 and "bot was blocked" in desc_l:
            print(
                "Бот заблокирован пользователем: в настройках чата с ботом нажмите «Разблокировать».",
                file=sys.stderr,
                flush=True,
            )
        return 1

    print("   sendMessage: ок. Проверьте Telegram — должно прийти тестовое сообщение.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_smoke())
