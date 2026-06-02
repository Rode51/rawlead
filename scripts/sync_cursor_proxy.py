"""Синхронизация прокси Cursor IDE из `.env`.

Переключатель: CURSOR_PROXY_ENABLED=1|0
URL: CURSOR_PROXY_URL (пусто → TG_PROXY_URL)

Подстраховка (CURSOR_PROXY_AUTO_FALLBACK=1 по умолчанию):
  TCP-probe кандидатов → первый живой → settings.json
  Все мертвы + CURSOR_PROXY_DISABLE_IF_DEAD=1 → выключить прокси в Cursor (прямое соединение)

Запуск:
  .venv\\Scripts\\python.exe scripts\\sync_cursor_proxy.py
  .venv\\Scripts\\python.exe scripts\\sync_cursor_proxy.py --pick-live
  .venv\\Scripts\\python.exe scripts\\sync_cursor_proxy.py --probe-only
  scripts\\cursor-proxy-recovery.bat
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import normalize_proxy_url  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from proxy_probe import mask_proxy_endpoint, probe_proxy_tcp  # noqa: E402

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


def _truthy(raw: str | None, *, default: bool = False) -> bool:
    if raw is None or not str(raw).strip():
        return default
    v = str(raw).strip().lower()
    return v in ("1", "true", "yes", "on", "да", "y")


def _load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    # Не re.sub(//…) — ломает https:// в proxy URL
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def _save_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def _dedup_key(proxy_url: str) -> str:
    return mask_proxy_endpoint(proxy_url)


def _collect_cursor_proxy_candidates() -> list[tuple[str, str]]:
    """Порядок = приоритет для Cursor (US/NL/PT, не RU pool бирж)."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(label: str, raw: str) -> None:
        raw = (raw or "").strip()
        if not raw:
            return
        try:
            norm = normalize_proxy_url(raw)
        except ValueError as exc:
            print(f"  skip {label}: {exc}", file=sys.stderr)
            return
        key = _dedup_key(norm)
        if key in seen:
            return
        seen.add(key)
        out.append((label, norm))

    add("primary", os.environ.get("CURSOR_PROXY_URL", ""))
    raw_pool = os.environ.get("CURSOR_PROXY_POOL_URLS", "").strip()
    if raw_pool:
        for i, part in enumerate(raw_pool.split(",")):
            add(f"pool_{i + 1}", part)
    raw_fb = os.environ.get("CURSOR_PROXY_FALLBACK_URLS", "").strip()
    if raw_fb:
        for i, part in enumerate(raw_fb.split(",")):
            add(f"fallback_{i + 1}", part)
    add("tg_bot", os.environ.get("TG_PROXY_URL", ""))
    for acc in ("ACC1", "ACC2", "ACC3"):
        add(f"telethon_{acc.lower()}", os.environ.get(f"TELETHON_PROXY_{acc}", ""))

    return out


def _probe_candidates(
    candidates: list[tuple[str, str]],
) -> tuple[str, str] | None:
    print("Проверка прокси (TCP)…", flush=True)
    for label, url in candidates:
        ok, detail = probe_proxy_tcp(url)
        host = _dedup_key(url)
        mark = "OK" if ok else "FAIL"
        print(f"  {label:<12} {host:<22} {mark} — {detail}", flush=True)
        if ok:
            return label, url
    return None


def _apply_proxy_settings(settings: dict, proxy: str) -> None:
    for key in _MANAGED_KEYS:
        settings.pop(key, None)
    settings["http.proxySupport"] = "on"
    settings["http.proxy"] = proxy
    settings["https.proxy"] = proxy
    settings["http.proxyStrictSSL"] = True
    settings["cursor.general.disableHttp2"] = True


def _clear_proxy_settings(settings: dict) -> None:
    for key in _MANAGED_KEYS:
        settings.pop(key, None)


def main() -> int:
    load_dotenv(_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Sync Cursor IDE proxy from .env")
    parser.add_argument(
        "--pick-live",
        action="store_true",
        help="TCP-probe кандидатов, взять первый живой",
    )
    parser.add_argument(
        "--probe-only",
        action="store_true",
        help="Только проверка, не менять settings.json",
    )
    parser.add_argument(
        "--disable-if-dead",
        action="store_true",
        help="Если все прокси мертвы — выключить прокси в Cursor",
    )
    parser.add_argument(
        "--off",
        action="store_true",
        help="Выключить прокси в Cursor (игнор CURSOR_PROXY_ENABLED)",
    )
    args = parser.parse_args()

    enabled = _truthy(os.environ.get("CURSOR_PROXY_ENABLED")) and not args.off
    auto_fallback = _truthy(
        os.environ.get("CURSOR_PROXY_AUTO_FALLBACK"), default=True
    )
    disable_if_dead = args.disable_if_dead or _truthy(
        os.environ.get("CURSOR_PROXY_DISABLE_IF_DEAD"), default=True
    )
    use_pick_live = args.pick_live or (enabled and auto_fallback and not args.off)

    settings = _load_settings(_CURSOR_SETTINGS)

    if args.probe_only:
        candidates = _collect_cursor_proxy_candidates()
        if not candidates:
            print("Нет URL в CURSOR_PROXY_URL / FALLBACK / TG_PROXY.", file=sys.stderr)
            return 1
        picked = _probe_candidates(candidates)
        return 0 if picked else 1

    if not enabled:
        _clear_proxy_settings(settings)
        _save_settings(_CURSOR_SETTINGS, settings)
        print("Cursor: выключён (прокси-ключи удалены из settings.json)")
        print(f"Файл: {_CURSOR_SETTINGS}")
        return 0

    use_relay = _truthy(os.environ.get("CURSOR_PROXY_RELAY"))
    if use_relay:
        try:
            port = int(os.environ.get("CURSOR_PROXY_RELAY_PORT", "18777").strip())
        except ValueError:
            port = 18777
        local = f"http://127.0.0.1:{port}"
        _apply_proxy_settings(settings, local)
        _save_settings(_CURSOR_SETTINGS, settings)
        print(f"Cursor: relay mode -> {local}")
        print("Запусти: scripts\\start-cursor-proxy-relay.bat")
        print("Перезапуск Cursor нужен ОДИН РАЗ; дальше relay меняет IP сам.")
        print(f"Файл: {_CURSOR_SETTINGS}")
        return 0

    candidates = _collect_cursor_proxy_candidates()
    if not candidates:
        print(
            "CURSOR_PROXY_ENABLED=1, но нет URL "
            "(CURSOR_PROXY_URL, CURSOR_PROXY_FALLBACK_URLS, TG_PROXY_URL).",
            file=sys.stderr,
        )
        return 1

    picked: tuple[str, str] | None = None
    if use_pick_live:
        picked = _probe_candidates(candidates)

    if picked is None and not use_pick_live:
        label, url = candidates[0]
        picked = (label, url)
        print(f"Без probe: {label} ({_dedup_key(url)})", flush=True)

    if picked is None:
        if disable_if_dead:
            _clear_proxy_settings(settings)
            _save_settings(_CURSOR_SETTINGS, settings)
            print(
                "\nCursor: все прокси недоступны → прокси ВЫКЛЮЧЕН в settings "
                "(прямое соединение). Модели могут дать region error из РФ.",
                flush=True,
            )
            print(
                "Когда прокси оживут: scripts\\cursor-proxy-recovery.bat",
                flush=True,
            )
            print(f"Файл: {_CURSOR_SETTINGS}")
            return 2
        print("Все прокси недоступны. Проверь оплату/VPS или --off.", file=sys.stderr)
        return 1

    label, proxy = picked
    _apply_proxy_settings(settings, proxy)
    _save_settings(_CURSOR_SETTINGS, settings)
    print(f"\nCursor: включен, {label} -> {_dedup_key(proxy)}")
    print(f"Файл: {_CURSOR_SETTINGS}")
    print("Перезапусти Cursor полностью (Quit, не Reload).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
