"""Telethon: connect через прокси и session path (фаза 1, не в main.py)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

from config import _PROJECT_ROOT, normalize_proxy_url

_ACCOUNTS = ("acc1", "acc2", "acc3")


def _load_telethon_env() -> tuple[int, str]:
    load_dotenv(_PROJECT_ROOT / ".env")
    api_id_raw = os.environ.get("TELEGRAM_API_ID", "").strip()
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()

    if not api_id_raw or not api_hash:
        print(
            "Задайте TELEGRAM_API_ID и TELEGRAM_API_HASH в .env "
            "(https://my.telegram.org/apps). Мониторинг чатов не стартует."
        )
        raise SystemExit(1)

    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        print(f"TELEGRAM_API_ID должен быть числом, сейчас: {api_id_raw!r}")
        raise SystemExit(1) from exc

    return api_id, api_hash


def resolve_telethon_account(account: str | None = None) -> tuple[str, str, str]:
    """(account_key, session_path без .session, proxy_url)."""
    load_dotenv(_PROJECT_ROOT / ".env")
    key = (account or "acc1").strip().lower()
    if key not in _ACCOUNTS:
        print(f"Неизвестный аккаунт {key!r}. Допустимо: {', '.join(_ACCOUNTS)}")
        raise SystemExit(1)

    suffix = key.upper()
    session_raw = os.environ.get(f"TELETHON_SESSION_{suffix}", "").strip()
    proxy_raw = os.environ.get(f"TELETHON_PROXY_{suffix}", "").strip()

    if key == "acc1":
        if not session_raw:
            session_raw = os.environ.get("TELETHON_SESSION_PATH", "").strip()
        if not proxy_raw:
            proxy_raw = os.environ.get("TELETHON_PROXY_URL", "").strip()

    if not session_raw:
        print(
            f"Задайте TELETHON_SESSION_{suffix} в .env "
            f"(путь к .session без расширения)."
        )
        raise SystemExit(1)

    if not proxy_raw:
        print(
            f"Задайте TELETHON_PROXY_{suffix} в .env. "
            "Без прокси мониторинговый аккаунт не подключаем (TZ_TG §2)."
        )
        raise SystemExit(1)

    return key, session_raw, proxy_raw


def telethon_proxy_tuple(proxy_url: str) -> tuple:
    """(socks тип, host, port, rdns, user, password) для TelegramClient."""
    try:
        import socks
    except ImportError as exc:
        raise SystemExit("Установите PySocks: pip install PySocks") from exc

    normalized = normalize_proxy_url(proxy_url)
    parsed = urlparse(normalized)
    scheme = (parsed.scheme or "http").lower()
    host = parsed.hostname
    if not host:
        raise ValueError(f"Прокси: не удалось разобрать хост: {proxy_url!r}")
    port = parsed.port or (8080 if scheme in ("http", "https") else 1080)
    user = parsed.username or ""
    password = parsed.password or ""
    if scheme in ("http", "https"):
        kind = socks.HTTP
    elif scheme in ("socks5", "socks5h"):
        kind = socks.SOCKS5
    else:
        raise ValueError(
            f"Прокси: поддерживаются http/https/socks5, сейчас: {scheme!r}"
        )
    return (kind, host, port, True, user, password)


def create_client(account: str | None = None):
    """Клиент Telethon; вызывающий делает connect() / run_until_disconnected()."""
    from proxy_probe import require_proxy_live

    api_id, api_hash = _load_telethon_env()
    key, session_path, proxy_url = resolve_telethon_account(account)
    require_proxy_live(key, proxy_url)

    try:
        from telethon import TelegramClient
    except ImportError as exc:
        raise SystemExit(
            "Установите telethon: pip install telethon PySocks"
        ) from exc
    session = str(Path(session_path))
    proxy = telethon_proxy_tuple(proxy_url)
    return TelegramClient(session, api_id, api_hash, proxy=proxy)


async def connect_client(account: str | None = None):
    client = create_client(account)
    await client.connect()
    if not await client.is_user_authorized():
        print("Сессия не авторизована. Войдите через софт продавца, не с телефона.")
        await client.disconnect()
        raise SystemExit(1)
    return client
