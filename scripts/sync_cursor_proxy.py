"""Синхронизация прокси Cursor IDE из `.env`.

Переключатель: CURSOR_PROXY_ENABLED=1|0
URL: CURSOR_PROXY_URL (пусто → TG_PROXY_URL)

Запуск: .venv\\Scripts\\python.exe scripts\\sync_cursor_proxy.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import normalize_proxy_url  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

_CURSOR_SETTINGS = (
    Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "settings.json"
)

_MANAGED_KEYS = (
    "http.proxySupport",
    "http.proxy",
    "https.proxy",
    "http.proxyStrictSSL",
    "cursor.general.disableHttp2",
)


def _truthy(raw: str | None) -> bool:
    if raw is None:
        return False
    v = raw.strip().lower()
    return v in ("1", "true", "yes", "on", "да", "y")


def _load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def _save_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def _mask_proxy(url: str) -> str:
    if "@" in url:
        return url.split("@", 1)[-1]
    return url


def main() -> int:
    load_dotenv(_ROOT / ".env")

    enabled = _truthy(os.environ.get("CURSOR_PROXY_ENABLED"))
    raw_url = (os.environ.get("CURSOR_PROXY_URL") or "").strip()
    if not raw_url:
        raw_url = (os.environ.get("TG_PROXY_URL") or "").strip()

    settings = _load_settings(_CURSOR_SETTINGS)

    for key in _MANAGED_KEYS:
        settings.pop(key, None)

    if enabled:
        if not raw_url:
            print("CURSOR_PROXY_ENABLED=1, но CURSOR_PROXY_URL и TG_PROXY_URL пусты.", file=sys.stderr)
            return 1
        proxy = normalize_proxy_url(raw_url)
        settings["http.proxySupport"] = "on"
        settings["http.proxy"] = proxy
        settings["https.proxy"] = proxy
        settings["http.proxyStrictSSL"] = True
        settings["cursor.general.disableHttp2"] = True
        mode = f"включен, прокси {_mask_proxy(proxy)}"
    else:
        mode = "выключён (прокси-ключи удалены из settings.json)"

    _save_settings(_CURSOR_SETTINGS, settings)
    print(f"Cursor: {mode}")
    print(f"Файл: {_CURSOR_SETTINGS}")
    print("Перезапусти Cursor, если он был открыт.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
